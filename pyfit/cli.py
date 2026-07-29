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

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Callable

from .api import nest_result_report, run_nest, write_nest_files

# Minimum time between progress heartbeats printed to stderr -- packer.pack
# can call on_progress far more often than this on a large or scrap-reuse-
# heavy job (see packer.py), so this throttles wall-clock output rate, not
# how often the packer itself reports in.
PROGRESS_MIN_INTERVAL_SECONDS = 2.0

_JOB_SPEC_EXAMPLE = """\
Job spec example:

  {
    "sheet": {"width": 96, "height": 48},
    "parts": [
      {"name": "shapeA", "dxf": "facetype1.dxf", "quantity": 120, "allow_mirror": true},
      {"name": "shapeB", "polygon": [[0,0],[1,0],[0,1]], "quantity": 10, "allow_mirror": false}
    ]
  }

Each part gives its outline either as "dxf" (a path to a DXF file containing
exactly one closed loop, e.g. one of pyLair's own "-T/--face-templates" panel
cutting templates) or "polygon" (an inline list of [x, y] points), plus
"quantity" (how many of that shape are needed) and optionally "allow_mirror"
(default true; set false for chirality-sensitive material, where a
mirror-image placement isn't interchangeable with the original).
"""


def _make_progress_printer() -> Callable[[int, int, int], None]:
    """A packer.pack on_progress callback that prints a throttled heartbeat
    to stderr (see PROGRESS_MIN_INTERVAL_SECONDS)."""
    state = {"last_printed": 0.0}

    def _on_progress(placed: int, total: int, sheet_index: int) -> None:
        now = time.monotonic()
        if now - state["last_printed"] < PROGRESS_MIN_INTERVAL_SECONDS:
            return
        state["last_printed"] = now
        print(
            f"pyfit: placed {placed}/{total} parts (checking sheet {sheet_index + 1})...",
            file=sys.stderr,
            flush=True,
        )

    return _on_progress


def _build_parser() -> argparse.ArgumentParser:
    """The `pyfit` command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="pyfit",
        description="A general-purpose 2D nesting (bin-packing) tool. "
        "Copyright 2026 by Emily Williams.",
        epilog=_JOB_SPEC_EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-j",
        "--job",
        metavar="PATH",
        required=True,
        help="Path to a job spec JSON file describing the sheet size and the "
        "parts to nest (see the job spec example below).",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        required=True,
        help='Path prefix for output file(s). Writes "<output>_sheet1.dxf", '
        '"<output>_sheet2.dxf", ... (one file per sheet actually used) and '
        '"<output>_report.json".',
    )
    parser.add_argument(
        "-R",
        "--rotation-step",
        metavar="DEGREES",
        type=float,
        default=15.0,
        help="Degrees between candidate rotation angles tried during "
        "placement search. A smaller step considers more orientations "
        "(denser search, better packing, slower); a larger step is faster "
        "but coarser. Must be greater than zero and less than 360. "
        "Default 15.",
    )
    parser.add_argument(
        "-P",
        "--preview",
        action="store_true",
        help='Also save a quick 2D preview image ("<output>_sheet1.png", '
        '"<output>_sheet2.png", ...) of each sheet\'s layout -- the sheet '
        "boundary plus every placed part's outline -- so a result can be "
        "sanity-checked without opening a DXF viewer.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help='Suppress the "placed N/M parts..." progress heartbeat this '
        "command otherwise prints to stderr every couple of seconds while "
        "packing a large job, so a slow run doesn't look frozen.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    if argv is None:
        argv = sys.argv[1:]

    # Running with no arguments at all prints full usage help (to stdout,
    # like -h/--help) rather than argparse's terser "required arguments
    # missing" error -- friendlier for someone who just typed `pyfit`.
    if not argv:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args(argv)

    if not (0 < args.rotation_step < 360):
        parser.error("-R/--rotation-step must be greater than zero and less than 360.")

    with open(args.job) as f:
        job = json.load(f)

    on_progress = None if args.quiet else _make_progress_printer()

    try:
        sheet, result = run_nest(
            job, rotation_step_degrees=args.rotation_step, on_progress=on_progress
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    files_written = write_nest_files(sheet, result, args.output, preview=args.preview)

    report = nest_result_report(result)
    report["files_written"] = files_written
    report_path = f"{args.output}_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
