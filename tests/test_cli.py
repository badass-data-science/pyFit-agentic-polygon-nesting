import json
import subprocess
import sys


def run_cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "sheetnest", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_help_flag_prints_usage():
    result = run_cli(["-h"])
    assert result.returncode == 0
    assert "Required Command-Line Input" in result.stdout


def test_no_arguments_prints_help_and_exits_nonzero():
    result = run_cli([])
    assert result.returncode != 0
    assert "Required Command-Line Input" in result.stdout


def test_missing_job_path_reports_a_clear_error(tmp_path):
    out = tmp_path / "nest"
    result = run_cli(["-o", str(out)])
    assert result.returncode != 0
    assert "job spec" in result.stdout.lower()


def test_missing_output_path_reports_a_clear_error(tmp_path):
    job = tmp_path / "job.json"
    job.write_text(json.dumps({
        "sheet": {"width": 5, "height": 5},
        "parts": [{"name": "sq", "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]], "quantity": 1}],
    }))
    result = run_cli(["-j", str(job)])
    assert result.returncode != 0
    assert "output path" in result.stdout.lower()


def test_inline_polygon_job_nests_successfully_and_writes_expected_files(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps({
        "sheet": {"width": 3, "height": 2},
        "parts": [{
            "name": "sq",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "quantity": 6,
            "allow_mirror": False,
        }],
    }))
    out = tmp_path / "nest"

    result = run_cli(["-j", str(job_path), "-o", str(out), "-R", "90"])

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["sheets_used"] == 1
    assert report["utilization_by_sheet"][0] == 1.0
    assert len(report["placements"]) == 6

    sheet_file = out.parent / "nest_sheet1.dxf"
    report_file = out.parent / "nest_report.json"
    assert sheet_file.exists()
    assert report_file.exists()
    assert json.loads(report_file.read_text()) == report


def test_dxf_sourced_job_nests_successfully(tmp_path):
    pydome_output = None
    try:
        import pydome.output as pydome_output
    except ImportError:
        import pytest
        pytest.skip("pydome not installed")

    triangle_path = tmp_path / "facetype1.dxf"
    pydome_output.OutputFaceTemplateDXF((3.0, 4.0, 5.0), str(triangle_path))

    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps({
        "sheet": {"width": 12, "height": 12},
        "parts": [{"name": "tri", "dxf": str(triangle_path), "quantity": 4, "allow_mirror": True}],
    }))
    out = tmp_path / "nest"

    result = run_cli(["-j", str(job_path), "-o", str(out), "-R", "30"])

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert len(report["placements"]) == 4


def test_preview_flag_writes_one_png_per_sheet(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps({
        "sheet": {"width": 2, "height": 2},
        "parts": [{
            "name": "sq",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "quantity": 5,  # 4 fit per sheet -> forces a 2nd sheet
            "allow_mirror": False,
        }],
    }))
    out = tmp_path / "nest"

    result = run_cli(["-j", str(job_path), "-o", str(out), "-R", "90", "-P"])

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["sheets_used"] == 2

    for n in (1, 2):
        png_file = out.parent / ("nest_sheet%d.png" % n)
        assert png_file.exists()
        assert png_file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        assert str(png_file) in report["files_written"]


def test_no_preview_flag_means_no_png_files(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps({
        "sheet": {"width": 3, "height": 2},
        "parts": [{
            "name": "sq",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "quantity": 6,
            "allow_mirror": False,
        }],
    }))
    out = tmp_path / "nest"

    result = run_cli(["-j", str(job_path), "-o", str(out), "-R", "90"])

    assert result.returncode == 0
    assert not (out.parent / "nest_sheet1.png").exists()


def test_nonpositive_rotation_step_reports_a_clear_error(tmp_path):
    job = tmp_path / "job.json"
    job.write_text(json.dumps({
        "sheet": {"width": 5, "height": 5},
        "parts": [{"name": "sq", "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]], "quantity": 1}],
    }))
    out = tmp_path / "nest"

    for step in ["0", "-5", "400"]:
        result = run_cli(["-j", str(job), "-o", str(out), "-R", step])
        assert result.returncode != 0
        assert "rotation-step" in result.stdout.lower()
