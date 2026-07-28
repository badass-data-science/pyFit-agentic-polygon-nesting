#    agentic-irregular-polygon-nesting:  A general-purpose 2D nesting (bin-packing) tool
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

#
# Shared programmatic entry point used by both the `sheetnest` CLI and the
# MCP server, so job-spec parsing and packing logic lives in exactly one
# place. Domain errors (a malformed part spec, a bad job spec) raise
# ValueError rather than printing and exiting, so callers -- including
# FastMCP's tool dispatcher, which turns an uncaught ValueError into an
# isError=True tool result -- can handle them however's appropriate.
#
from typing import List, Tuple

from .geometry import Part, Sheet, NestResult
from .io_dxf import import_polygons_from_dxf, write_sheet_dxf
from .packer import pack
from .preview import save_sheet_preview


def load_part(spec: dict) -> Part:
  """Build a Part from one job-spec part dict: {"name", "quantity",
  "dxf" or "polygon", "allow_mirror" (optional, default True)}. Raises
  ValueError if the spec is missing a required field, gives neither "dxf"
  nor "polygon", or points at a DXF file that isn't exactly one closed
  loop."""
  name = spec.get("name")
  if name is None:
    raise ValueError('Part spec is missing required field "name".')
  if "quantity" not in spec:
    raise ValueError('Part %r is missing required field "quantity".' % name)

  if "dxf" in spec:
    loops = import_polygons_from_dxf(spec["dxf"])
    if len(loops) != 1:
      raise ValueError(
          'Part %r: DXF file %r must contain exactly one closed loop, found %d.'
          % (name, spec["dxf"], len(loops)))
    polygon = loops[0]
  elif "polygon" in spec:
    polygon = [(float(x), float(y)) for x, y in spec["polygon"]]
  else:
    raise ValueError('Part %r must specify either "dxf" or "polygon".' % name)

  return Part(
      name=name,
      polygon=polygon,
      quantity=int(spec["quantity"]),
      allow_mirror=bool(spec.get("allow_mirror", True)),
  )


def run_nest(job: dict, rotation_step_degrees: float = 15.0) -> Tuple[Sheet, NestResult]:
  """Parse a job spec dict ({"sheet": {"width", "height"}, "parts": [...]})
  and run the bottom-left-fill packer. Returns the parsed Sheet alongside
  the NestResult so callers that go on to write files (see
  write_nest_files) don't have to re-parse the job spec. Raises
  ValueError on a malformed job/part spec or a rotation step outside
  (0, 360)."""
  if not (0 < rotation_step_degrees < 360):
    raise ValueError(
        'rotation_step_degrees (CLI: -R/--rotation-step) must be greater than zero and less than 360.')

  sheet = Sheet(width=float(job["sheet"]["width"]), height=float(job["sheet"]["height"]))
  parts = [load_part(spec) for spec in job["parts"]]
  result = pack(parts, sheet, rotation_step_degrees=rotation_step_degrees)
  return sheet, result


def nest_result_report(result: NestResult) -> dict:
  """The structured, file-free part of a nesting report: sheet count,
  per-sheet utilization, and every part's final placement. Callers that
  write files (the CLI, export_nest) add their own "files_written" key
  on top of this."""
  return {
      'sheets_used': result.sheets_used,
      'utilization_by_sheet': result.utilization_by_sheet,
      'placements': [
          {
              'part_name': p.part_name,
              'sheet_index': p.sheet_index,
              'position': list(p.position),
              'rotation_degrees': p.rotation_degrees,
              'mirrored': p.mirrored,
          }
          for p in result.placements
      ],
  }


def write_nest_files(sheet: Sheet, result: NestResult, output_path: str,
                      preview: bool = False) -> List[str]:
  """Write one DXF (and, if preview=True, one PNG) per sheet actually
  used to "<output_path>_sheet<N>.<ext>". Returns the list of paths
  written, in the same order the CLI reports them."""
  files_written = []
  for sheet_index in range(result.sheets_used):
    placements_on_sheet = [p for p in result.placements if p.sheet_index == sheet_index]
    sheet_path = '%s_sheet%d.dxf' % (output_path, sheet_index + 1)
    write_sheet_dxf(placements_on_sheet, sheet, sheet_path)
    files_written.append(sheet_path)

    if preview:
      preview_path = '%s_sheet%d.png' % (output_path, sheet_index + 1)
      save_sheet_preview(sheet, placements_on_sheet, preview_path,
                          sheet_number=sheet_index + 1,
                          utilization=result.utilization_by_sheet[sheet_index])
      files_written.append(preview_path)
  return files_written
