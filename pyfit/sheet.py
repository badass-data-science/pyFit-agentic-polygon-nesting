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

from __future__ import annotations

from .geometry import Placement, Sheet, bounding_box, polygon_area


def inner_fit_bounds(
    sheet: Sheet, oriented_polygon: list
) -> tuple[float, float, float, float] | None:
    """The valid range of translation (dx, dy) for which `oriented_polygon`
    (already rotated/mirrored, not yet translated) stays entirely inside the
    sheet's [0, width] x [0, height] rectangle, as (dx_lo, dy_lo, dx_hi,
    dy_hi). Returns None if the shape is too big to fit on the sheet in this
    orientation at all.

    Because the sheet is an axis-aligned rectangle, containment reduces
    independently per axis to the polygon's own bounding box fitting within
    it -- this is exact for any polygon (convex or not), not an
    approximation, so there is no need for a Minkowski-erosion computation
    here the way there is for part-against-part collision (see `nfp.py`).
    """
    minx, miny, maxx, maxy = bounding_box(oriented_polygon)
    dx_lo, dx_hi = -minx, sheet.width - maxx
    dy_lo, dy_hi = -miny, sheet.height - maxy
    if dx_lo > dx_hi or dy_lo > dy_hi:
        return None
    return (dx_lo, dy_lo, dx_hi, dy_hi)


def sheet_utilization(sheet: Sheet, placements_on_sheet: list[Placement]) -> float:
    """The fraction (0 to 1) of `sheet`'s area covered by `placements_on_sheet`."""
    placed_area = sum(polygon_area(p.polygon) for p in placements_on_sheet)
    return placed_area / (sheet.width * sheet.height)
