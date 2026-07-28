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

import getopt
import json
import sys

from .api import run_nest, nest_result_report, write_nest_files


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

\t-P, --preview\tAlso save a quick 2D preview image ("<output>_sheet1.png", "<output>_sheet2.png", ...)
\t\tof each sheet's layout -- the sheet boundary plus every placed part's outline -- so a result can
\t\tbe sanity-checked without opening a DXF viewer.

\t-h, --help\tShow usage and exit.
"""
  print(help_text)


def main():
  job_path = None
  output_path = None
  rotation_step_degrees = 15.0
  preview_output = False

  if len(sys.argv[1:]) == 0:
    display_help()
    sys.exit(-1)

  try:
    opts, args = getopt.getopt(sys.argv[1:], 'j:o:R:Ph',
                                ['job=', 'output=', 'rotation-step=', 'preview', 'help'])
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
    if o in ('-P', '--preview'):
      preview_output = True
    if o in ('-R', '--rotation-step'):
      try:
        rotation_step_degrees = float(a)
      except ValueError:
        print('-R or --rotation-step argument must be a floating point number. Exiting.')
        sys.exit(-1)

  if job_path is None:
    print('A job spec path is required. Use the -j argument. Exiting.')
    sys.exit(-1)
  if output_path is None:
    print('An output path and filename prefix is required. Use the -o argument. Exiting.')
    sys.exit(-1)

  with open(job_path) as f:
    job = json.load(f)

  try:
    sheet, result = run_nest(job, rotation_step_degrees=rotation_step_degrees)
  except ValueError as e:
    print(str(e))
    sys.exit(-1)

  files_written = write_nest_files(sheet, result, output_path, preview=preview_output)

  report = nest_result_report(result)
  report['files_written'] = files_written
  report_path = '%s_report.json' % output_path
  with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

  print(json.dumps(report, indent=2))


if __name__ == "__main__":
  main()
