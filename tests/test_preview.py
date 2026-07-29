from pyfit.geometry import Placement, Sheet
from pyfit.preview import render_sheet_preview_png_bytes, save_sheet_preview


def _placement(polygon, sheet_index=0):
    return Placement(
        part_name="p",
        sheet_index=sheet_index,
        position=(0.0, 0.0),
        rotation_degrees=0.0,
        mirrored=False,
        polygon=polygon,
    )


def test_render_sheet_preview_png_bytes_produces_a_valid_png():
    placements = [_placement([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])]
    png_bytes = render_sheet_preview_png_bytes(Sheet(width=3, height=2), placements)

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_sheet_preview_png_bytes_handles_an_empty_sheet():
    # an edge case worth covering explicitly: no placements at all
    # (e.g. a sheet report requested before any part got assigned to it)
    # must still produce a valid image, not crash on an empty patch list
    png_bytes = render_sheet_preview_png_bytes(Sheet(width=3, height=2), [])

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_save_sheet_preview_writes_a_png_file(tmp_path):
    placements = [_placement([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])]
    out_path = tmp_path / "preview.png"

    save_sheet_preview(
        Sheet(width=3, height=2), placements, str(out_path), sheet_number=1, utilization=0.75
    )

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
