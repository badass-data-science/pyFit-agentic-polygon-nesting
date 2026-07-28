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
# MCP server exposing sheetnest as tools for an agentic assistant to nest
# parts onto sheet stock interactively: try a job spec, see each sheet's
# layout rendered inline, get a structured placement report -- all
# without shelling out to the `sheetnest` CLI and parsing stdout. Mirrors
# pyLair's own mcp_server.py (design/preview/report/export tools, all
# built on a shared api.py). Requires the optional `mcp` dependency
# (`pip install -e ".[mcp]"`); console script `sheetnest-mcp`.
#
import asyncio
from typing import List, Optional

from mcp.server.fastmcp import Context, FastMCP, Image

from .api import run_nest, nest_result_report, write_nest_files
from .preview import render_sheet_preview_png_bytes

mcp = FastMCP("sheetnest")

# Shared parameters across all four tools:
#   sheet_width, sheet_height, parts, rotation_step_degrees
# `parts` is a list of job-spec part dicts, each: {"name", "quantity",
# "dxf" (path to a DXF file with exactly one closed loop) or "polygon"
# (inline [[x, y], ...] list), "allow_mirror" (optional, default true)}.
# A malformed job/part spec or an out-of-range rotation_step_degrees
# raises ValueError, which FastMCP's dispatcher turns into an
# isError=True tool result -- see api.py:load_part/run_nest.
#
# Every tool also accepts an implicit MCP Context (excluded from the
# tool's own parameter schema, per FastMCP's find_context_parameter) and
# is async: run_nest's actual packing work is synchronous and can run
# long on a large or scrap-reuse-heavy job, so it's offloaded to a
# worker thread (asyncio.to_thread) to keep the event loop free to
# actually send progress notifications while it runs, rather than
# blocking the whole server for the duration of one tool call. If the
# calling client requested progress (a progressToken on the request --
# see Context.report_progress), it gets a heartbeat each time
# packer.pack tries a sheet for the current part instance, so a slow
# job doesn't look frozen mid-call. With no context (e.g. calling these
# functions directly, as tests do) or no progressToken, this is a no-op
# and packing still runs in a thread -- just silently.


def _job(sheet_width: float, sheet_height: float, parts: List[dict]) -> dict:
  return {"sheet": {"width": sheet_width, "height": sheet_height}, "parts": parts}


async def _run_nest(job: dict, rotation_step_degrees: float, ctx: Optional[Context]):
  loop = asyncio.get_running_loop()

  def on_progress(placed, total, sheet_index):
    if ctx is None:
      return
    message = 'placed %d/%d parts (checking sheet %d)' % (placed, total, sheet_index + 1)
    asyncio.run_coroutine_threadsafe(ctx.report_progress(placed, total, message), loop)

  return await asyncio.to_thread(
      run_nest, job, rotation_step_degrees=rotation_step_degrees,
      on_progress=on_progress if ctx is not None else None)


@mcp.tool()
async def design_nest(sheet_width: float, sheet_height: float, parts: List[dict],
                       rotation_step_degrees: float = 15.0, ctx: Optional[Context] = None) -> dict:
  """Pack a set of parts onto sheet stock (no files written) and return
  a summary -- sheets used and per-sheet utilization -- so an agent can
  cheaply try job specs (part counts, sheet size, rotation step) before
  asking for a full placement report or file export. Reports MCP
  progress (a placement heartbeat) on a large job if the caller
  requested it."""
  sheet, result = await _run_nest(_job(sheet_width, sheet_height, parts), rotation_step_degrees, ctx)
  return {
      'sheets_used': result.sheets_used,
      'utilization_by_sheet': result.utilization_by_sheet,
  }


@mcp.tool()
async def preview_nest(sheet_width: float, sheet_height: float, parts: List[dict],
                        rotation_step_degrees: float = 15.0, ctx: Optional[Context] = None) -> List:
  """Render a quick 2D preview of every sheet's layout (boundary plus
  every placed part's outline, labeled with utilization) and return them
  inline as images, so a nesting result can be seen in-conversation
  before committing to any file export. Reports MCP progress (a
  placement heartbeat) on a large job if the caller requested it."""
  sheet, result = await _run_nest(_job(sheet_width, sheet_height, parts), rotation_step_degrees, ctx)
  content: List = []
  for sheet_index in range(result.sheets_used):
    placements_on_sheet = [p for p in result.placements if p.sheet_index == sheet_index]
    png_bytes = render_sheet_preview_png_bytes(
        sheet, placements_on_sheet, sheet_number=sheet_index + 1,
        utilization=result.utilization_by_sheet[sheet_index])
    content.append('sheet %d: %d parts, %.1f%% utilized'
                    % (sheet_index + 1, len(placements_on_sheet),
                       result.utilization_by_sheet[sheet_index] * 100.))
    content.append(Image(data=png_bytes, format="png"))
  return content


@mcp.tool()
async def get_nest_report(sheet_width: float, sheet_height: float, parts: List[dict],
                           rotation_step_degrees: float = 15.0, ctx: Optional[Context] = None) -> dict:
  """Pack a set of parts onto sheet stock and return the full placement
  report as structured data (sheets used, per-sheet utilization, and
  every part instance's sheet index, position, rotation, and mirror
  flag) without writing any files. Reports MCP progress (a placement
  heartbeat) on a large job if the caller requested it."""
  sheet, result = await _run_nest(_job(sheet_width, sheet_height, parts), rotation_step_degrees, ctx)
  return nest_result_report(result)


@mcp.tool()
async def export_nest(output_path: str, sheet_width: float, sheet_height: float,
                       parts: List[dict], rotation_step_degrees: float = 15.0,
                       preview: bool = False, ctx: Optional[Context] = None) -> dict:
  """Pack a set of parts and write output files to disk (mirrors the
  `sheetnest` CLI): one DXF per sheet actually used, written to
  "<output_path>_sheet<N>.dxf". preview=True also writes
  "<output_path>_sheet<N>.png". Returns the list of files written
  alongside the full placement report. Reports MCP progress (a
  placement heartbeat) on a large job if the caller requested it."""
  sheet, result = await _run_nest(_job(sheet_width, sheet_height, parts), rotation_step_degrees, ctx)
  files_written = write_nest_files(sheet, result, output_path, preview=preview)
  report = nest_result_report(result)
  report['files_written'] = files_written
  return report


def main():
  mcp.run(transport="stdio")


if __name__ == "__main__":
  main()
