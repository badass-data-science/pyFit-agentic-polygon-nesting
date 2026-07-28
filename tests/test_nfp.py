import pytest

from pyfit.nfp import no_fit_polygon


def test_nfp_of_two_unit_squares_is_the_hand_computable_2x2_square():
    # NFP(A, B) = Minkowski sum of A and the point-reflection of B; for
    # two unit squares (reference corner at the local origin), this has
    # a known closed-form answer: the 2x2 square from (-1,-1) to (1,1).
    # Everything else in this package depends on this primitive being
    # right, so it's checked against a hand-computable case rather than
    # only against itself.
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]

    result = no_fit_polygon(square, square)

    assert len(result) == 1
    assert sorted(result[0]) == sorted([(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)])


def test_nfp_boundary_matches_known_touching_and_overlapping_positions():
    from shapely.geometry import Point, Polygon

    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    nfp = Polygon(no_fit_polygon(square, square)[0])

    # a moving-square reference point at (2, 0): the moving square would
    # occupy [2,3]x[0,1], a full unit away from the stationary square --
    # legal (no overlap), so this point must lie outside the NFP
    assert not nfp.contains(Point(2, 0)) and not nfp.boundary.contains(Point(2, 0))

    # at (1, 0): the moving square would occupy [1,2]x[0,1], exactly
    # touching the stationary square along the shared edge x=1 -- legal,
    # so this point must lie exactly on the NFP boundary
    assert nfp.boundary.contains(Point(1, 0))

    # at (0.5, 0): the moving square would occupy [0.5,1.5]x[0,1],
    # genuinely overlapping the stationary square -- illegal, so this
    # point must lie strictly inside the NFP
    assert nfp.contains(Point(0.5, 0))


def test_nfp_of_a_small_shape_around_a_large_one_is_scaled_accordingly():
    small_square = [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)]
    large_square = [(0, 0), (2, 0), (2, 2), (0, 2)]

    result = no_fit_polygon(large_square, small_square)

    assert len(result) == 1
    xs = [p[0] for p in result[0]]
    ys = [p[1] for p in result[0]]
    # NFP(large, small) should span from -0.5 to 2 on each axis: the
    # small square's own extent (0.5) added to the large square's
    assert min(xs) == pytest.approx(-0.5)
    assert max(xs) == pytest.approx(2.0)
    assert min(ys) == pytest.approx(-0.5)
    assert max(ys) == pytest.approx(2.0)
