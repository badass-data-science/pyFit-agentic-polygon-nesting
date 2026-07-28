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

import io

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Rectangle


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

  title = 'sheetnest preview'
  if sheet_number is not None:
    title += ' -- sheet %d' % sheet_number
  if utilization is not None:
    title += ' (%.1f%% utilized)' % (utilization * 100.)
  ax.set_title(title)

  buf = io.BytesIO()
  fig.savefig(buf, format='png', dpi=130)
  plt.close(fig)
  return buf.getvalue()


def save_sheet_preview(sheet, placements_on_sheet, the_filename, sheet_number=None, utilization=None):
  with open(the_filename, 'wb') as outfile:
    outfile.write(render_sheet_preview_png_bytes(sheet, placements_on_sheet, sheet_number, utilization))
