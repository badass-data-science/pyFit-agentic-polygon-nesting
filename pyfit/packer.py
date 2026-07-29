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

from collections.abc import Iterator
from itertools import combinations
from typing import Callable, cast

from shapely.geometry import GeometryCollection, LinearRing, MultiLineString, MultiPoint, Point, box
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from .geometry import (
    NestResult,
    Part,
    Placement,
    Sheet,
    polygon_area,
    transform_polygon,
)
from .nfp import no_fit_polygon
from .sheet import inner_fit_bounds, sheet_utilization

OVERLAP_AREA_TOLERANCE = 1e-9
BOUNDS_TOLERANCE = 1e-9


def _extract_points(geom: BaseGeometry) -> list[tuple[float, float]]:
    """Flattens any shapely intersection result (Point, MultiPoint,
    LineString -- from collinear/overlapping edges, MultiLineString, or a
    GeometryCollection mixing those) down to a flat list of coordinate
    points."""
    if geom.is_empty:
        return []
    if isinstance(geom, Point):
        return [(geom.x, geom.y)]
    if geom.geom_type == "LineString":
        return [(x, y) for x, y, *_ in geom.coords]
    if isinstance(geom, (MultiPoint, MultiLineString, GeometryCollection)):
        points: list[tuple[float, float]] = []
        for sub_geom in cast(BaseMultipartGeometry, geom).geoms:
            points.extend(_extract_points(sub_geom))
        return points
    return []


def _candidate_orientations(
    part: Part, rotation_step_degrees: float
) -> Iterator[tuple[float, bool]]:
    """Yields (rotation_degrees, mirrored) pairs to try for `part`: every
    multiple of `rotation_step_degrees` in [0, 360), each both unmirrored and
    (if `part.allow_mirror`) mirrored."""
    angle = 0.0
    while angle < 360.0:
        yield angle, False
        if part.allow_mirror:
            yield angle, True
        angle += rotation_step_degrees


def _overlaps_any(polygon: list, placed_polygons: list[list]) -> bool:
    """Whether `polygon` overlaps (by more than `OVERLAP_AREA_TOLERANCE` of
    area) any polygon already in `placed_polygons`."""
    shp = ShapelyPolygon(polygon)
    for placed in placed_polygons:
        if shp.intersection(ShapelyPolygon(placed)).area > OVERLAP_AREA_TOLERANCE:
            return True
    return False


def _valid_candidate_points(
    bounds: tuple[float, float, float, float], oriented_polygon: list, placed_polygons: list[list]
) -> list[tuple[float, float]]:
    """Bottom-left-fill candidate positions for `oriented_polygon`: the
    sheet's own 4 corners, every vertex of the NFP of `oriented_polygon`
    against each already-placed part, every point where an NFP boundary
    crosses the sheet's own boundary, and every point where two different
    placed parts' NFP boundaries cross each other.

    The last of these matters more than it might look: e.g. packing plain
    unit squares in a grid, the position that lets a 3rd square slot in
    between two already-placed squares is exactly such an NFP-NFP crossing,
    not a vertex of either NFP alone -- without it, this heuristic silently
    starts unnecessary extra sheets even for a trivially-tileable case
    (verified: a 3x2 sheet with six unit squares needed this to actually fit
    all six on one sheet instead of two).

    This still isn't full NFP-boundary tracing (the true valid region's
    boundary can in principle need higher-order crossing points too), but
    every candidate here is explicitly re-validated below, so it can only
    produce a non-optimal placement, never an invalid one.

    Costs O(P) no-fit-polygon computations plus O(P^2) pairwise NFP-ring
    intersection checks, where P is the number of parts already placed on
    this sheet -- see `pack`'s docstring for how that compounds across a
    full run.
    """
    dx_lo, dy_lo, dx_hi, dy_hi = bounds
    candidates = [(dx_lo, dy_lo), (dx_hi, dy_lo), (dx_lo, dy_hi), (dx_hi, dy_hi)]
    sheet_ring = box(dx_lo, dy_lo, dx_hi, dy_hi).exterior

    nfp_rings = []
    for placed in placed_polygons:
        for nfp_polygon in no_fit_polygon(placed, oriented_polygon):
            candidates.extend(nfp_polygon)
            ring = LinearRing(nfp_polygon)
            candidates.extend(_extract_points(ring.intersection(sheet_ring)))
            nfp_rings.append(ring)

    for ring_a, ring_b in combinations(nfp_rings, 2):
        candidates.extend(_extract_points(ring_a.intersection(ring_b)))

    valid = []
    for dx, dy in candidates:
        if not (
            dx_lo - BOUNDS_TOLERANCE <= dx <= dx_hi + BOUNDS_TOLERANCE
            and dy_lo - BOUNDS_TOLERANCE <= dy <= dy_hi + BOUNDS_TOLERANCE
        ):
            continue
        translated = [(x + dx, y + dy) for x, y in oriented_polygon]
        if _overlaps_any(translated, placed_polygons):
            continue
        valid.append((dx, dy))
    return valid


def pack(
    parts: list[Part],
    sheet: Sheet,
    rotation_step_degrees: float = 15.0,
    on_progress: Callable[[int, int, int], None] | None = None,
) -> NestResult:
    """Bottom-left-fill packing of `parts` onto (possibly several) `sheet`-sized
    sheets, with NFP-based collision avoidance.

    A heuristic, not a globally optimal solver (irregular 2D bin-packing is
    NP-hard) -- see `nfp.py` and this package's README for the algorithm and
    its known limitations.

    Complexity: for one part instance trying one sheet, the candidate-point
    search (`_valid_candidate_points`) costs O(P) NFP computations plus
    O(P^2) pairwise NFP-ring intersection checks, where P is the number of
    parts already placed on that sheet. That's repeated once per candidate
    orientation (O(360 / rotation_step_degrees) of them, doubled if
    mirroring is allowed), and, when scrap reuse forces trying more than one
    already-opened sheet before finding room, once per sheet tried. So a
    full run of N part instances costs on the order of N * orientations *
    P^2 geometry operations in the worst case -- which is why a finer
    `rotation_step_degrees` and heavier scrap reuse (more, fuller sheets to
    search) directly trade off against wall-clock time on a large job, as
    measured in the README's "Known limitations" section.

    `on_progress`, if given, is called as `on_progress(placed_so_far,
    total_instances, sheet_index)` once per sheet tried for the current part
    instance -- i.e. more than once per part on a scrap-reuse-heavy job that
    has to check several already-opened sheets before finding room, which is
    exactly the case where a single part instance's own placement can take a
    while. It's a heartbeat, not a percentage: an instance count alone can
    go quiet for a long stretch if one instance is expensive to place, which
    is the scenario a caller displaying "still working" progress most needs
    to hear about.
    """
    instances: list[Part] = []
    for part in parts:
        instances.extend([part] * part.quantity)
    instances.sort(key=lambda p: polygon_area(p.polygon), reverse=True)
    total_instances = len(instances)

    placements: list[Placement] = []
    sheets_polygons: list[list[list]] = [[]]
    sheet_area = sheet.width * sheet.height
    # running (area already placed) per sheet, checked before doing any
    # NFP work -- reusing scrap means every part instance can end up
    # trying many already-full sheets before reaching one with room, and
    # the full candidate-point search (NFP against every placed part) is
    # the expensive part of this algorithm. A part can never fit where
    # its own area doesn't, so this is a cheap, exact (never wrongly
    # skips a sheet that could actually fit) filter that turns an
    # already-full sheet into an O(1) skip instead of a full NFP sweep.
    sheets_placed_area: list[float] = [0.0]

    for part in instances:
        placed_this_part = False
        sheet_index = 0
        part_area = polygon_area(part.polygon)

        while not placed_this_part:
            if on_progress is not None:
                on_progress(len(placements), total_instances, sheet_index)

            if sheet_index >= len(sheets_polygons):
                sheets_polygons.append([])
                sheets_placed_area.append(0.0)

            best = None  # (dx, dy, rotation, mirrored, oriented_polygon)

            if part_area <= sheet_area - sheets_placed_area[sheet_index] + OVERLAP_AREA_TOLERANCE:
                for rotation, mirrored in _candidate_orientations(part, rotation_step_degrees):
                    oriented = transform_polygon(part.polygon, rotation, mirrored, 0.0, 0.0)
                    bounds = inner_fit_bounds(sheet, oriented)
                    if bounds is None:
                        continue
                    for dx, dy in _valid_candidate_points(
                        bounds, oriented, sheets_polygons[sheet_index]
                    ):
                        if best is None or (dx, dy) < (best[0], best[1]):
                            best = (dx, dy, rotation, mirrored, oriented)

            if best is not None:
                dx, dy, rotation, mirrored, oriented = best
                final_polygon = [(x + dx, y + dy) for x, y in oriented]
                placements.append(
                    Placement(
                        part_name=part.name,
                        sheet_index=sheet_index,
                        position=(dx, dy),
                        rotation_degrees=rotation,
                        mirrored=mirrored,
                        polygon=final_polygon,
                    )
                )
                sheets_polygons[sheet_index].append(final_polygon)
                sheets_placed_area[sheet_index] += part_area
                placed_this_part = True
            elif len(sheets_polygons[sheet_index]) == 0:
                raise ValueError(
                    f"Part {part.name!r} does not fit on an empty {sheet.width}x{sheet.height} sheet in any orientation."
                )
            else:
                # this sheet is full for this part, but earlier/later sheets may
                # still have room -- try the next one (opened fresh above if it
                # doesn't exist yet) before giving up, so leftover scrap on an
                # earlier sheet gets reused instead of every miss opening a new
                # sheet
                sheet_index += 1

    utilization = [
        sheet_utilization(sheet, [p for p in placements if p.sheet_index == i])
        for i in range(len(sheets_polygons))
    ]

    return NestResult(
        sheets_used=len(sheets_polygons), placements=placements, utilization_by_sheet=utilization
    )
