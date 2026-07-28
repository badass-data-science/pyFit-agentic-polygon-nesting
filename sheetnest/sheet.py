#    agentic-irregular-polygon-nesting:  A general-purpose 2D nesting (bin-packing) tool
#    Copyright (C) 2026  Emily Williams
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import List, Optional, Tuple

from .geometry import Placement, Sheet, bounding_box, polygon_area


def inner_fit_bounds(sheet: Sheet, oriented_polygon: List) -> Optional[Tuple[float, float, float, float]]:
  # The valid range of translation (dx, dy) for which `oriented_polygon`
  # (already rotated/mirrored, not yet translated) stays entirely inside
  # the sheet's [0, width] x [0, height] rectangle. Because the sheet is
  # an axis-aligned rectangle, containment reduces independently per axis
  # to the polygon's own bounding box fitting within it -- this is exact
  # for any polygon (convex or not), not an approximation, so there is no
  # need for a Minkowski-erosion computation here the way there is for
  # part-against-part collision (see nfp.py). Returns None if the shape
  # is too big to fit on the sheet in this orientation at all.
  minx, miny, maxx, maxy = bounding_box(oriented_polygon)
  dx_lo, dx_hi = -minx, sheet.width - maxx
  dy_lo, dy_hi = -miny, sheet.height - maxy
  if dx_lo > dx_hi or dy_lo > dy_hi:
    return None
  return (dx_lo, dy_lo, dx_hi, dy_hi)


def sheet_utilization(sheet: Sheet, placements_on_sheet: List[Placement]) -> float:
  placed_area = sum(polygon_area(p.polygon) for p in placements_on_sheet)
  return placed_area / (sheet.width * sheet.height)
