from pathlib import Path

import pytest

pytest.importorskip("mcp")

from sheetnest.mcp_server import design_nest, preview_nest, get_nest_report, export_nest


#
# direct calls: @mcp.tool() leaves the decorated function callable as a
# plain Python function, so these exercise the tool bodies without
# spinning up a protocol session -- same approach as pyLair's own
# test_mcp_server.py
#

UNIT_SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1]]


def _parts(quantity, allow_mirror=False):
    return [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": quantity, "allow_mirror": allow_mirror}]


def test_design_nest_returns_summary_without_placements():
    result = design_nest(sheet_width=3, sheet_height=2, parts=_parts(6), rotation_step_degrees=90.0)

    assert result["sheets_used"] == 1
    assert result["utilization_by_sheet"][0] == 1.0
    assert "placements" not in result


def test_preview_nest_returns_one_text_and_image_pair_per_sheet():
    from mcp.server.fastmcp import Image

    content = preview_nest(sheet_width=2, sheet_height=2, parts=_parts(5), rotation_step_degrees=90.0)

    # 5 unit squares on a 2x2 sheet -> 4 fit per sheet, forces a 2nd sheet
    assert len(content) == 4
    assert isinstance(content[0], str) and "sheet 1" in content[0]
    assert isinstance(content[1], Image)
    assert isinstance(content[2], str) and "sheet 2" in content[2]
    assert isinstance(content[3], Image)


def test_get_nest_report_includes_full_placements_and_no_files():
    report = get_nest_report(sheet_width=3, sheet_height=2, parts=_parts(6), rotation_step_degrees=90.0)

    assert report["sheets_used"] == 1
    assert len(report["placements"]) == 6
    assert "files_written" not in report


def test_export_nest_writes_files_and_returns_report(tmp_path):
    out = tmp_path / "nest"

    report = export_nest(output_path=str(out), sheet_width=3, sheet_height=2,
                          parts=_parts(6), rotation_step_degrees=90.0, preview=True)

    assert report["sheets_used"] == 1
    assert len(report["placements"]) == 6
    assert report["files_written"] == [str(out) + "_sheet1.dxf", str(out) + "_sheet1.png"]
    for f in report["files_written"]:
        assert Path(f).exists()


def test_bad_job_spec_raises_value_error():
    with pytest.raises(ValueError, match="quantity"):
        design_nest(sheet_width=3, sheet_height=2,
                     parts=[{"name": "sq", "polygon": UNIT_SQUARE}])
