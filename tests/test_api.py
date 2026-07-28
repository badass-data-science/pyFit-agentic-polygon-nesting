from pathlib import Path

import pytest

from pyfit.api import load_part, run_nest, nest_result_report, write_nest_files


UNIT_SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1]]


def test_load_part_from_inline_polygon():
    part = load_part({"name": "sq", "polygon": UNIT_SQUARE, "quantity": 3})
    assert part.name == "sq"
    assert part.quantity == 3
    assert part.allow_mirror is True
    assert part.polygon == [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_load_part_respects_allow_mirror_false():
    part = load_part({"name": "sq", "polygon": UNIT_SQUARE, "quantity": 1, "allow_mirror": False})
    assert part.allow_mirror is False


def test_load_part_missing_name_raises():
    with pytest.raises(ValueError, match="name"):
        load_part({"polygon": UNIT_SQUARE, "quantity": 1})


def test_load_part_missing_quantity_raises():
    with pytest.raises(ValueError, match="quantity"):
        load_part({"name": "sq", "polygon": UNIT_SQUARE})


def test_load_part_missing_outline_raises():
    with pytest.raises(ValueError, match="dxf.*polygon"):
        load_part({"name": "sq", "quantity": 1})


def test_run_nest_packs_parts_and_returns_sheet_and_result():
    job = {
        "sheet": {"width": 3, "height": 2},
        "parts": [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": 6, "allow_mirror": False}],
    }
    sheet, result = run_nest(job, rotation_step_degrees=90.0)

    assert sheet.width == 3
    assert sheet.height == 2
    assert result.sheets_used == 1
    assert result.utilization_by_sheet[0] == 1.0
    assert len(result.placements) == 6


@pytest.mark.parametrize("bad_step", [0, -5, 400])
def test_run_nest_rejects_out_of_range_rotation_step(bad_step):
    job = {
        "sheet": {"width": 5, "height": 5},
        "parts": [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": 1}],
    }
    with pytest.raises(ValueError, match="rotation-step"):
        run_nest(job, rotation_step_degrees=bad_step)


def test_nest_result_report_structure():
    job = {
        "sheet": {"width": 3, "height": 2},
        "parts": [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": 2, "allow_mirror": False}],
    }
    sheet, result = run_nest(job, rotation_step_degrees=90.0)
    report = nest_result_report(result)

    assert report["sheets_used"] == 1
    assert len(report["placements"]) == 2
    placement = report["placements"][0]
    assert set(placement) == {"part_name", "sheet_index", "position", "rotation_degrees", "mirrored"}


def test_write_nest_files_writes_one_dxf_per_sheet(tmp_path):
    job = {
        "sheet": {"width": 2, "height": 2},
        "parts": [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": 5, "allow_mirror": False}],
    }
    sheet, result = run_nest(job, rotation_step_degrees=90.0)
    assert result.sheets_used == 2

    out = tmp_path / "nest"
    files = write_nest_files(sheet, result, str(out), preview=False)

    assert files == [str(out) + "_sheet1.dxf", str(out) + "_sheet2.dxf"]
    for f in files:
        assert Path(f).exists()


def test_write_nest_files_preview_true_also_writes_png(tmp_path):
    job = {
        "sheet": {"width": 2, "height": 2},
        "parts": [{"name": "sq", "polygon": UNIT_SQUARE, "quantity": 1, "allow_mirror": False}],
    }
    sheet, result = run_nest(job, rotation_step_degrees=90.0)

    out = tmp_path / "nest"
    files = write_nest_files(sheet, result, str(out), preview=True)

    assert files == [str(out) + "_sheet1.dxf", str(out) + "_sheet1.png"]
