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


from .geometry import Placement, Point, Sheet

# Coordinate matching tolerance when reconstructing closed loops out of
# independent LINE entities (e.g. pyLair's own face-template DXFs, which
# are 3 separate LINE entities per triangle, not a closed POLYLINE):
# endpoints within this distance of each other are treated as the same
# vertex.
_MATCH_DECIMALS = 6


def _read_line_entities(path: str) -> list[tuple]:
  # Minimal raw DXF reader: walks the group-code stream looking for LINE
  # entities and their start (10/20)/end (11/21) coordinates, ignoring Z
  # (this package is 2D-only) and everything else (layers, colors,
  # non-LINE entities). No DXF library dependency, matching pyLair's own
  # hand-written DXF writers.
  with open(path) as f:
    lines = [line.rstrip("\n") for line in f]

  entities = []
  i = 0
  in_line_entity = False
  values: dict[str, str] = {}
  while i < len(lines) - 1:
    code, value = lines[i].strip(), lines[i + 1].strip()
    if code == "0":
      if in_line_entity and all(k in values for k in ("10", "20", "11", "21")):
        entities.append((
          (float(values["10"]), float(values["20"])),
          (float(values["11"]), float(values["21"])),
        ))
      in_line_entity = (value == "LINE")
      values = {}
    elif in_line_entity and code in ("10", "20", "11", "21"):
      values[code] = value
    i += 2

  if in_line_entity and all(k in values for k in ("10", "20", "11", "21")):
    entities.append((
      (float(values["10"]), float(values["20"])),
      (float(values["11"]), float(values["21"])),
    ))
  return entities


def _key(point: Point) -> Point:
  return (round(point[0], _MATCH_DECIMALS), round(point[1], _MATCH_DECIMALS))


def _reconstruct_loops(segments: list[tuple]) -> list[list[Point]]:
  # Groups line segments into connected components, then walks each
  # component as a simple cycle to recover an ordered polygon loop.
  # Every vertex in a valid closed shape must have exactly 2 segment
  # endpoints touching it; anything else means the input isn't a set of
  # simple closed loops, which is treated as a hard error rather than
  # guessed at.
  adjacency: dict[Point, list[Point]] = {}
  original_points: dict[Point, Point] = {}
  for p0, p1 in segments:
    k0, k1 = _key(p0), _key(p1)
    original_points.setdefault(k0, p0)
    original_points.setdefault(k1, p1)
    adjacency.setdefault(k0, []).append(k1)
    adjacency.setdefault(k1, []).append(k0)

  for k, neighbors in adjacency.items():
    if len(neighbors) != 2:
      raise ValueError(
        f"DXF import expects simple closed loops, but vertex {original_points[k]!r} has "
        f"{len(neighbors)} connected segment endpoints (expected exactly 2)."
      )

  visited = set()
  loops = []
  for start in adjacency:
    if start in visited:
      continue
    loop = [start]
    visited.add(start)
    prev, current = None, start
    while True:
      next_candidates = [n for n in adjacency[current] if n != prev]
      # a 2-segment-long loop (a degenerate "shape" with only 2 vertices)
      # would otherwise have both neighbors equal to prev; fall back to
      # the other occurrence in that case
      next_node = next_candidates[0] if next_candidates else adjacency[current][0]
      if next_node == start:
        break
      loop.append(next_node)
      visited.add(next_node)
      prev, current = current, next_node
    loops.append([original_points[k] for k in loop])
  return loops


def import_polygons_from_dxf(path: str) -> list[list[Point]]:
  segments = _read_line_entities(path)
  return _reconstruct_loops(segments)


def write_sheet_dxf(placements_on_sheet: list[Placement], sheet: Sheet, path: str) -> None:
  with open(path, "w") as outfile:
    outfile.write("0\nSECTION\n2\nENTITIES\n")

    # sheet boundary, so the output is visually self-describing without
    # needing the width/height passed alongside it
    boundary = [(0., 0.), (sheet.width, 0.), (sheet.width, sheet.height), (0., sheet.height)]
    for i in range(4):
      _write_line(outfile, boundary[i], boundary[(i + 1) % 4])

    for placement in placements_on_sheet:
      polygon = placement.polygon
      n = len(polygon)
      for i in range(n):
        _write_line(outfile, polygon[i], polygon[(i + 1) % n])

    outfile.write("0\nENDSEC\n0\nEOF\n")


def _write_line(outfile, p0: Point, p1: Point) -> None:
  outfile.write("0\nLINE\n8\n1\n")
  outfile.write(f"10\n{p0[0]}\n20\n{p0[1]}\n30\n0.0\n")
  outfile.write(f"11\n{p1[0]}\n21\n{p1[1]}\n31\n0.0\n")
