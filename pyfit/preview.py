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

import io

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle


def render_sheet_preview_png_bytes(sheet, placements_on_sheet, sheet_number=None, utilization=None):
  fig, ax = plt.subplots()

  ax.add_patch(Rectangle((0, 0), sheet.width, sheet.height, fill=False,
                          edgecolor='black', linewidth=1.2))
  for placement in placements_on_sheet:
    ax.add_patch(MplPolygon(placement.polygon, closed=True, facecolor='steelblue',
                             edgecolor='black', linewidth=0.6, alpha=0.6))

  # a small margin outside the sheet boundary, so the sheet's own edge
  # doesn't get clipped by the axes -- proportional to sheet size so it
  # looks right whether the sheet is inches or meters
  margin = max(sheet.width, sheet.height) * 0.03
  ax.set_xlim(-margin, sheet.width + margin)
  ax.set_ylim(-margin, sheet.height + margin)
  ax.set_aspect('equal')

  title = 'pyfit preview'
  if sheet_number is not None:
    title += f' -- sheet {sheet_number}'
  if utilization is not None:
    title += f' ({utilization * 100.:.1f}% utilized)'
  ax.set_title(title)

  buf = io.BytesIO()
  fig.savefig(buf, format='png', dpi=130)
  plt.close(fig)
  return buf.getvalue()


def save_sheet_preview(sheet, placements_on_sheet, the_filename, sheet_number=None, utilization=None):
  with open(the_filename, 'wb') as outfile:
    outfile.write(render_sheet_preview_png_bytes(sheet, placements_on_sheet, sheet_number, utilization))
