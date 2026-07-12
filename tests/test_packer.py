from itertools import combinations, groupby

import pytest
from shapely.geometry import Polygon

from sheetnest.geometry import Part, Sheet
from sheetnest.packer import pack


def _assert_no_overlaps_per_sheet(result):
    by_sheet = sorted(result.placements, key=lambda p: p.sheet_index)
    for _, group in groupby(by_sheet, key=lambda p: p.sheet_index):
        polygons = [Polygon(p.polygon) for p in group]
        for a, b in combinations(polygons, 2):
            assert a.intersection(b).area < 1e-9


def _assert_within_sheet_bounds(result, sheet):
    for placement in result.placements:
        xs = [x for x, y in placement.polygon]
        ys = [y for x, y in placement.polygon]
        assert min(xs) >= -1e-6
        assert max(xs) <= sheet.width + 1e-6
        assert min(ys) >= -1e-6
        assert max(ys) <= sheet.height + 1e-6


def test_unit_squares_pack_perfectly_onto_an_exactly_sized_sheet():
    # six unit squares have exactly the area of a 3x2 sheet, and are
    # perfectly tileable -- this is a strong check that the candidate
    # point search finds the tight-fitting positions, not just any
    # valid ones
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    parts = [Part(name="sq", polygon=square, quantity=6, allow_mirror=False)]
    sheet = Sheet(width=3, height=2)

    result = pack(parts, sheet, rotation_step_degrees=90)

    assert result.sheets_used == 1
    assert result.utilization_by_sheet[0] == pytest.approx(1.0)
    assert len(result.placements) == 6
    _assert_no_overlaps_per_sheet(result)
    _assert_within_sheet_bounds(result, sheet)


def test_triangles_all_get_placed_without_overlap_or_going_out_of_bounds():
    triangle = [(0, 0), (3, 0), (0, 4)]
    parts = [Part(name="tri", polygon=triangle, quantity=10, allow_mirror=True)]
    sheet = Sheet(width=6, height=8)

    result = pack(parts, sheet, rotation_step_degrees=15)

    assert len(result.placements) == 10
    _assert_no_overlaps_per_sheet(result)
    _assert_within_sheet_bounds(result, sheet)


def test_mixed_shapes_all_get_placed_without_overlap():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    triangle = [(0, 0), (1, 0), (0, 1)]
    parts = [
        Part(name="sq", polygon=square, quantity=3, allow_mirror=False),
        Part(name="tri", polygon=triangle, quantity=5, allow_mirror=True),
    ]
    sheet = Sheet(width=5, height=5)

    result = pack(parts, sheet, rotation_step_degrees=30)

    assert len(result.placements) == 8
    _assert_no_overlaps_per_sheet(result)
    _assert_within_sheet_bounds(result, sheet)


def test_mirror_disallowed_part_is_never_mirrored():
    triangle = [(0, 0), (2, 0), (0, 1)]  # scalene -- mirroring is a real, detectable change
    parts = [Part(name="tri", polygon=triangle, quantity=8, allow_mirror=False)]
    sheet = Sheet(width=6, height=6)

    result = pack(parts, sheet, rotation_step_degrees=30)

    assert len(result.placements) == 8
    assert all(not p.mirrored for p in result.placements)


def test_overflow_to_multiple_sheets_when_parts_dont_fit_on_one():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    parts = [Part(name="sq", polygon=square, quantity=5, allow_mirror=False)]
    sheet = Sheet(width=2, height=2)  # only room for 4 unit squares per sheet

    result = pack(parts, sheet, rotation_step_degrees=90)

    assert result.sheets_used == 2
    assert len(result.placements) == 5
    _assert_no_overlaps_per_sheet(result)


def test_part_too_large_for_an_empty_sheet_raises_a_clear_error():
    huge_square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    parts = [Part(name="huge", polygon=huge_square, quantity=1, allow_mirror=False)]
    sheet = Sheet(width=2, height=2)

    with pytest.raises(ValueError, match="does not fit"):
        pack(parts, sheet, rotation_step_degrees=90)
