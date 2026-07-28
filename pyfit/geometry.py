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

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
from shapely.geometry import Polygon


Point = Tuple[float, float]


@dataclass
class Part:
  # polygon is a closed 2D outline in the part's own local coordinate
  # frame; rotation/mirroring are applied about the local origin (0, 0)
  # before a solved placement translates it into sheet coordinates, so
  # callers should give the polygon relative to whatever local reference
  # point they want rotation to pivot around (e.g. one corner, or the
  # centroid).
  name: str
  polygon: List[Point]
  quantity: int
  allow_mirror: bool = True


@dataclass
class Sheet:
  width: float
  height: float


@dataclass
class Placement:
  part_name: str
  sheet_index: int
  position: Point           # translation applied after rotation/mirroring
  rotation_degrees: float
  mirrored: bool
  polygon: List[Point]       # final polygon in sheet coordinates, for
                              # convenience (export/verification don't have
                              # to re-derive it from the transform fields)


@dataclass
class NestResult:
  sheets_used: int
  placements: List[Placement] = field(default_factory=list)
  utilization_by_sheet: List[float] = field(default_factory=list)


def polygon_area(polygon: List[Point]) -> float:
  return Polygon(polygon).area


def bounding_box(polygon: List[Point]) -> Tuple[float, float, float, float]:
  xs = [p[0] for p in polygon]
  ys = [p[1] for p in polygon]
  return (min(xs), min(ys), max(xs), max(ys))


def translate_polygon(polygon: List[Point], dx: float, dy: float) -> List[Point]:
  return [(x + dx, y + dy) for x, y in polygon]


def rotate_polygon(polygon: List[Point], degrees: float) -> List[Point]:
  # rotated about the local origin (0, 0), not the polygon's own centroid
  # -- see Part's docstring
  theta = np.radians(degrees)
  cos_t, sin_t = np.cos(theta), np.sin(theta)
  return [(x * cos_t - y * sin_t, x * sin_t + y * cos_t) for x, y in polygon]


def mirror_polygon(polygon: List[Point]) -> List[Point]:
  # reflect across the local Y axis (x -> -x); combined with
  # rotate_polygon, this reaches every orientation of both the shape and
  # its mirror image
  return [(-x, y) for x, y in polygon]


def orient_ccw(polygon: List[Point]) -> List[Point]:
  # the shoelace signed area is positive for a counter-clockwise polygon;
  # NFP computation (see nfp.py) assumes consistently-wound input, so
  # every polygon this module hands off gets normalized here rather than
  # trusting the caller's winding
  signed_area = sum(
    polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
    - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
    for i in range(len(polygon))
  ) / 2.0
  return polygon if signed_area > 0 else list(reversed(polygon))


def transform_polygon(polygon: List[Point], rotation_degrees: float, mirrored: bool,
                       dx: float, dy: float) -> List[Point]:
  # canonical order: mirror, then rotate, then translate -- matches how
  # Placement's fields are interpreted everywhere else in this package
  poly = mirror_polygon(polygon) if mirrored else polygon
  poly = rotate_polygon(poly, rotation_degrees)
  poly = translate_polygon(poly, dx, dy)
  return poly
