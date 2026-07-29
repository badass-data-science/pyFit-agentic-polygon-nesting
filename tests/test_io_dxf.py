import numpy as np
import pytest

from pyfit.geometry import Placement, Sheet
from pyfit.io_dxf import import_polygons_from_dxf, write_sheet_dxf


def _write_raw_dxf(path, segments):
    with open(path, "w") as f:
        f.write("0\nSECTION\n2\nENTITIES\n")
        for p0, p1 in segments:
            f.write("0\nLINE\n8\n1\n")
            f.write("10\n{}\n20\n{}\n30\n0.0\n".format(*p0))
            f.write("11\n{}\n21\n{}\n31\n0.0\n".format(*p1))
        f.write("0\nENDSEC\n0\nEOF\n")


def test_import_recovers_a_hand_written_triangle(tmp_path):
    segments = [((0.0, 0.0), (3.0, 0.0)), ((3.0, 0.0), (0.0, 4.0)), ((0.0, 4.0), (0.0, 0.0))]
    path = tmp_path / "triangle.dxf"
    _write_raw_dxf(str(path), segments)

    loops = import_polygons_from_dxf(str(path))

    assert len(loops) == 1
    assert sorted(loops[0]) == sorted([(0.0, 0.0), (3.0, 0.0), (0.0, 4.0)])


def test_import_from_pylair_face_template_matches_reported_edge_lengths(tmp_path):
    pylair_output = pytest.importorskip("pylair.output")
    edge_lengths = (3.0, 4.0, 5.0)
    path = tmp_path / "facetype1.dxf"
    pylair_output.OutputFaceTemplateDXF(edge_lengths, str(path))

    loops = import_polygons_from_dxf(str(path))

    assert len(loops) == 1
    polygon = loops[0]
    n = len(polygon)
    recovered = sorted(
        np.linalg.norm(np.array(polygon[i]) - np.array(polygon[(i + 1) % n])) for i in range(n)
    )
    assert recovered == pytest.approx(sorted(edge_lengths), abs=1e-6)


def test_import_rejects_a_vertex_shared_by_more_than_two_segments(tmp_path):
    # two triangles sharing a corner at the origin -- not a simple set
    # of closed loops, so the importer must refuse to guess rather than
    # silently produce a wrong loop
    segments = [
        ((0.0, 0.0), (1.0, 0.0)), ((1.0, 0.0), (0.0, 1.0)), ((0.0, 1.0), (0.0, 0.0)),
        ((0.0, 0.0), (-1.0, 0.0)), ((-1.0, 0.0), (0.0, -1.0)), ((0.0, -1.0), (0.0, 0.0)),
    ]
    path = tmp_path / "shared_vertex.dxf"
    _write_raw_dxf(str(path), segments)

    with pytest.raises(ValueError, match="exactly 2"):
        import_polygons_from_dxf(str(path))


def test_write_sheet_dxf_round_trips_through_the_importer(tmp_path):
    # placements kept well inside the sheet (not touching its boundary)
    # so the exported file's loops -- 1 sheet-boundary rectangle plus 2
    # triangles -- stay simple and unambiguous for the importer to
    # recover, unlike a tightly-packed real nesting result where parts
    # legitimately touch the sheet edge or each other
    sheet = Sheet(width=10, height=10)
    placements = [
        Placement(part_name="a", sheet_index=0, position=(1, 1), rotation_degrees=0,
                   mirrored=False, polygon=[(1, 1), (3, 1), (1, 2)]),
        Placement(part_name="a", sheet_index=0, position=(6, 6), rotation_degrees=0,
                   mirrored=False, polygon=[(6, 6), (8, 6), (6, 7)]),
    ]
    path = tmp_path / "sheet1.dxf"

    write_sheet_dxf(placements, sheet, str(path))
    loops = import_polygons_from_dxf(str(path))

    assert len(loops) == 3  # sheet boundary + 2 triangles
    areas = sorted(
        abs(sum(
            loop[i][0] * loop[(i + 1) % len(loop)][1] - loop[(i + 1) % len(loop)][0] * loop[i][1]
            for i in range(len(loop))
        )) / 2.0
        for loop in loops
    )
    # two triangles of area 1.0 each, plus the 10x10 sheet boundary
    assert areas == pytest.approx([1.0, 1.0, 100.0])
