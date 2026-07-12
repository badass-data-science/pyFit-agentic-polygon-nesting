#    Sheet-Nesting:  A general-purpose 2D nesting (bin-packing) tool
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

import getopt
import json
import sys

from .geometry import Part, Sheet
from .io_dxf import import_polygons_from_dxf, write_sheet_dxf
from .packer import pack


def display_help():
  help_text = """sheetnest:  A general-purpose 2D nesting (bin-packing) tool. Copyright 2026 by Emily Williams

Required Command-Line Input:

\t-j, --job=\tPath to a job spec JSON file describing the sheet size and the parts to nest. Example:
\t\t{
\t\t  "sheet": {"width": 96, "height": 48},
\t\t  "parts": [
\t\t    {"name": "shapeA", "dxf": "facetype1.dxf", "quantity": 120, "allow_mirror": true},
\t\t    {"name": "shapeB", "polygon": [[0,0],[1,0],[0,1]], "quantity": 10, "allow_mirror": false}
\t\t  ]
\t\t}
\t\tEach part gives its outline either as "dxf" (a path to a DXF file containing exactly one closed
\t\tloop, e.g. one of pyDome's own "-T/--face-templates" panel cutting templates) or "polygon" (an
\t\tinline list of [x, y] points), plus "quantity" (how many of that shape are needed) and optionally
\t\t"allow_mirror" (default true; set false for chirality-sensitive material, where a mirror-image
\t\tplacement isn't interchangeable with the original).

\t-o, --output=\tPath prefix for output file(s). Writes "<output>_sheet1.dxf", "<output>_sheet2.dxf",
\t\t... (one file per sheet actually used) and "<output>_report.json".

Options:

\t-R, --rotation-step\tDegrees between candidate rotation angles tried during placement search. A smaller
\t\tstep considers more orientations (denser search, better packing, slower); a larger step is faster
\t\tbut coarser. Must be a positive floating point number less than 360. Default 15.

\t-h, --help\tShow usage and exit.
"""
  print(help_text)


def _load_part(spec: dict) -> Part:
  if "dxf" in spec:
    loops = import_polygons_from_dxf(spec["dxf"])
    if len(loops) != 1:
      print('Part %r: DXF file %r must contain exactly one closed loop, found %d. Exiting.'
            % (spec.get("name", "?"), spec["dxf"], len(loops)))
      sys.exit(-1)
    polygon = loops[0]
  elif "polygon" in spec:
    polygon = [(float(x), float(y)) for x, y in spec["polygon"]]
  else:
    print('Part %r must specify either "dxf" or "polygon". Exiting.' % spec.get("name", "?"))
    sys.exit(-1)

  return Part(
    name=spec["name"],
    polygon=polygon,
    quantity=int(spec["quantity"]),
    allow_mirror=bool(spec.get("allow_mirror", True)),
  )


def main():
  job_path = None
  output_path = None
  rotation_step_degrees = 15.0

  if len(sys.argv[1:]) == 0:
    display_help()
    sys.exit(-1)

  try:
    opts, args = getopt.getopt(sys.argv[1:], 'j:o:R:h',
                                ['job=', 'output=', 'rotation-step=', 'help'])
  except getopt.error as msg:
    print(str(msg) + ' (for help use --help)')
    sys.exit(-1)

  for o, a in opts:
    if o in ('-h', '--help'):
      display_help()
      sys.exit(0)
    if o in ('-j', '--job'):
      job_path = a
    if o in ('-o', '--output'):
      output_path = a
    if o in ('-R', '--rotation-step'):
      try:
        rotation_step_degrees = float(a)
      except ValueError:
        print('-R or --rotation-step argument must be a floating point number. Exiting.')
        sys.exit(-1)
      if not (0 < rotation_step_degrees < 360):
        print('-R or --rotation-step argument must be greater than zero and less than 360. Exiting.')
        sys.exit(-1)

  if job_path is None:
    print('A job spec path is required. Use the -j argument. Exiting.')
    sys.exit(-1)
  if output_path is None:
    print('An output path and filename prefix is required. Use the -o argument. Exiting.')
    sys.exit(-1)

  with open(job_path) as f:
    job = json.load(f)

  sheet = Sheet(width=float(job["sheet"]["width"]), height=float(job["sheet"]["height"]))
  parts = [_load_part(spec) for spec in job["parts"]]

  try:
    result = pack(parts, sheet, rotation_step_degrees=rotation_step_degrees)
  except ValueError as e:
    print(str(e))
    sys.exit(-1)

  files_written = []
  for sheet_index in range(result.sheets_used):
    placements_on_sheet = [p for p in result.placements if p.sheet_index == sheet_index]
    sheet_path = '%s_sheet%d.dxf' % (output_path, sheet_index + 1)
    write_sheet_dxf(placements_on_sheet, sheet, sheet_path)
    files_written.append(sheet_path)

  report = {
    'sheets_used': result.sheets_used,
    'utilization_by_sheet': result.utilization_by_sheet,
    'files_written': files_written,
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
  report_path = '%s_report.json' % output_path
  with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

  print(json.dumps(report, indent=2))


if __name__ == "__main__":
  main()
