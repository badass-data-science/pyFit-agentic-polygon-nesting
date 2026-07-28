import pytest

from pyfit.geometry import (
    bounding_box,
    mirror_polygon,
    orient_ccw,
    polygon_area,
    rotate_polygon,
    transform_polygon,
    translate_polygon,
)


def test_polygon_area_of_unit_square():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert polygon_area(square) == pytest.approx(1.0)


def test_bounding_box():
    triangle = [(0, 0), (3, 0), (0, 4)]
    assert bounding_box(triangle) == (0, 0, 3, 4)


def test_translate_polygon():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    moved = translate_polygon(square, 2, 3)
    assert moved == [(2, 3), (3, 3), (3, 4), (2, 4)]


def test_rotate_polygon_90_degrees_about_origin():
    point = [(1, 0)]
    rotated = rotate_polygon(point, 90)
    assert rotated[0][0] == pytest.approx(0, abs=1e-9)
    assert rotated[0][1] == pytest.approx(1, abs=1e-9)


def test_mirror_polygon_reflects_across_local_y_axis():
    triangle = [(0, 0), (3, 0), (0, 4)]
    mirrored = mirror_polygon(triangle)
    assert mirrored == [(0, 0), (-3, 0), (0, 4)]


def test_orient_ccw_leaves_a_ccw_polygon_unchanged():
    ccw_square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert orient_ccw(ccw_square) == ccw_square


def test_orient_ccw_reverses_a_cw_polygon():
    cw_square = [(0, 0), (0, 1), (1, 1), (1, 0)]
    result = orient_ccw(cw_square)
    assert result == list(reversed(cw_square))
    # both describe the same shape either way
    assert polygon_area(result) == pytest.approx(polygon_area(cw_square))


def test_transform_polygon_order_is_mirror_then_rotate_then_translate():
    # a point at (1, 0): mirrored -> (-1, 0); rotated 90 -> (0, -1);
    # translated by (5, 5) -> (5, 4)
    result = transform_polygon([(1, 0)], rotation_degrees=90, mirrored=True, dx=5, dy=5)
    assert result[0][0] == pytest.approx(5, abs=1e-9)
    assert result[0][1] == pytest.approx(4, abs=1e-9)
