#    pyFit:  A general-purpose 2D nesting (bin-packing) tool
#    Copyright (c) 2026 Emily Williams
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#    THE SOFTWARE.

from typing import List

import pyclipper
from shapely.geometry import Polygon
from shapely.ops import unary_union

from .geometry import Point, orient_ccw

# pyclipper works in scaled 64-bit integer coordinates, not floats; this
# scale factor was chosen to give ~6 decimal digits of sub-unit precision
# without risking integer overflow for sheets/parts sized in the tens of
# thousands of units (pyclipper's internal range comfortably covers
# coordinates up to roughly +-4.6e18 at this scale).
SCALE = 10 ** 6


def _to_int(polygon: List[Point]):
  return [(int(round(x * SCALE)), int(round(y * SCALE))) for x, y in polygon]


def _from_int(polygon) -> List[Point]:
  return [(x / SCALE, y / SCALE) for x, y in polygon]


def no_fit_polygon(stationary: List[Point], moving: List[Point]) -> List[List[Point]]:
  # The outer NFP of `moving` around a fixed `stationary`: the set of
  # reference-point positions where `moving` (translated so its local
  # origin lands on that position, with no rotation/mirroring applied --
  # callers are responsible for rotating/mirroring `moving` themselves
  # before calling this) touches or overlaps `stationary`. Computed as
  # the Minkowski sum of `stationary` and the point-reflection of
  # `moving` through its own local origin (NFP(A, B) = A (+) (-B)), the
  # standard technique -- verified against the hand-computable case of
  # two unit squares (reference corner at origin), which must give the
  # exact 2x2 square from (-1,-1) to (1,1): a moving-part reference point
  # strictly inside the returned polygon overlaps the stationary shape;
  # on the boundary, the two touch; outside, they don't overlap at all.
  #
  # Usually a single polygon for the convex shapes this package is built
  # around, but the return type is always a list since a genuinely
  # non-convex NFP could in principle be disjoint.
  #
  # pyclipper's MinkowskiSum(pattern, path, True) sweeps `pattern` along
  # each edge of the closed `path` and returns the *raw* swept contours
  # rather than a single resolved polygon -- for a pattern that's small
  # relative to the path, this includes an inner contour with opposite
  # winding that looks like it's marking a hole, but isn't one: the true
  # Minkowski sum of two convex filled shapes is always itself convex
  # (hence simply connected, no holes possible -- verified against an
  # independent ground truth, the convex hull of all pairwise
  # vertex-sums, on a small-pattern/large-path case where the raw
  # Clipper output was misleading). The fix is to treat every returned
  # contour as an independent *solid* region and take their union (via
  # shapely, ignoring winding direction) rather than trusting Clipper's
  # winding-implied fill rule -- confirmed to recover the correct
  # hole-free result on that same case.
  #
  # This union-of-solids treatment assumes the true result has no
  # legitimate holes, which holds for the convex shapes this package
  # targets (pyDome's triangular panels, and irregular-but-simple shapes
  # generally) but would be wrong for a genuinely non-convex NFP with a
  # real unreachable pocket -- out of scope for this package.
  reflected_moving = [(-x, -y) for x, y in moving]
  stationary_int = _to_int(orient_ccw(stationary))
  reflected_int = _to_int(orient_ccw(reflected_moving))

  raw_contours = pyclipper.MinkowskiSum(reflected_int, stationary_int, True)
  solids = [Polygon(_from_int(poly)) for poly in raw_contours]
  resolved = unary_union(solids)

  polygons = resolved.geoms if resolved.geom_type == "MultiPolygon" else [resolved]
  return [orient_ccw(list(poly.exterior.coords)[:-1]) for poly in polygons]
