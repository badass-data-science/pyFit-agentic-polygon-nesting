import asyncio
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from sheetnest.mcp_server import design_nest, preview_nest, get_nest_report, export_nest


#
# All four tools are async (see mcp_server.py for why: packing runs in a
# worker thread so the event loop stays free to send progress
# notifications mid-call), so direct calls here go through asyncio.run
# rather than being plain synchronous calls -- still exercising the tool
# bodies without spinning up a protocol session, same idea as pyLair's
# own test_mcp_server.py.
#

UNIT_SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1]]


class _FakeContext:
    """A minimal stand-in for mcp.server.fastmcp.Context: just enough of
    report_progress's interface to prove the tools call it, without
    needing a real MCP session/request context in a unit test."""

    def __init__(self):
        self.calls = []

    async def report_progress(self, progress, total=None, message=None):
        self.calls.append((progress, total, message))


def _parts(quantity, allow_mirror=False):
    return [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": quantity, "allow_mirror": allow_mirror}]


def test_design_nest_returns_summary_without_placements():
    result = asyncio.run(design_nest(sheet_width=3, sheet_height=2, parts=_parts(6),
                                      rotation_step_degrees=90.0))

    assert result["sheets_used"] == 1
    assert result["utilization_by_sheet"][0] == 1.0
    assert "placements" not in result


def test_preview_nest_returns_one_text_and_image_pair_per_sheet():
    from mcp.server.fastmcp import Image

    content = asyncio.run(preview_nest(sheet_width=2, sheet_height=2, parts=_parts(5),
                                        rotation_step_degrees=90.0))

    # 5 unit squares on a 2x2 sheet -> 4 fit per sheet, forces a 2nd sheet
    assert len(content) == 4
    assert isinstance(content[0], str) and "sheet 1" in content[0]
    assert isinstance(content[1], Image)
    assert isinstance(content[2], str) and "sheet 2" in content[2]
    assert isinstance(content[3], Image)


def test_get_nest_report_includes_full_placements_and_no_files():
    report = asyncio.run(get_nest_report(sheet_width=3, sheet_height=2, parts=_parts(6),
                                          rotation_step_degrees=90.0))

    assert report["sheets_used"] == 1
    assert len(report["placements"]) == 6
    assert "files_written" not in report


def test_export_nest_writes_files_and_returns_report(tmp_path):
    out = tmp_path / "nest"

    report = asyncio.run(export_nest(output_path=str(out), sheet_width=3, sheet_height=2,
                                      parts=_parts(6), rotation_step_degrees=90.0, preview=True))

    assert report["sheets_used"] == 1
    assert len(report["placements"]) == 6
    assert report["files_written"] == [str(out) + "_sheet1.dxf", str(out) + "_sheet1.png"]
    for f in report["files_written"]:
        assert Path(f).exists()


def test_bad_job_spec_raises_value_error():
    with pytest.raises(ValueError, match="quantity"):
        asyncio.run(design_nest(sheet_width=3, sheet_height=2,
                                 parts=[{"name": "sq", "polygon": UNIT_SQUARE}]))


def test_no_context_means_no_progress_reporting():
    # ctx defaults to None (e.g. a direct call, like every other test in
    # this file) -- packing still runs (in a worker thread either way),
    # it just has nothing to report progress to.
    result = asyncio.run(design_nest(sheet_width=3, sheet_height=2, parts=_parts(6),
                                      rotation_step_degrees=90.0, ctx=None))
    assert result["sheets_used"] == 1


def test_context_receives_progress_heartbeats():
    ctx = _FakeContext()

    result = asyncio.run(get_nest_report(sheet_width=3, sheet_height=2, parts=_parts(6),
                                          rotation_step_degrees=90.0, ctx=ctx))

    assert result["sheets_used"] == 1
    # exact count depends on asyncio scheduling of the cross-thread
    # notifications relative to when the worker thread finishes -- at
    # least one heartbeat is the meaningful guarantee here, not an exact
    # count matching placements
    assert len(ctx.calls) >= 1
    for placed, total, message in ctx.calls:
        assert total == 6
        assert 0 <= placed <= 6
        assert isinstance(message, str) and "checking sheet" in message
