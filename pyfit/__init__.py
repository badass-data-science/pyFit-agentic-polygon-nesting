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
"""pyFit: a general-purpose 2D irregular-polygon nesting (bin-packing) tool.

Arranges a set of 2D shapes onto rectangular sheet stock with minimal
wasted material, via a no-fit-polygon bottom-left-fill heuristic. See
`pyfit.api.run_nest` for the main programmatic entry point, or the `pyfit`
console script for command-line use.
"""

from importlib.metadata import PackageNotFoundError, version

from .api import load_part, nest_result_report, run_nest, write_nest_files
from .geometry import NestResult, Part, Placement, Sheet
from .packer import pack

try:
    __version__ = version("pyfit-agentic-polygon-nesting")
except PackageNotFoundError:
    # not installed (e.g. running from a checkout without `pip install -e .`)
    __version__ = "0.0.0"

__all__ = [
    "NestResult",
    "Part",
    "Placement",
    "Sheet",
    "load_part",
    "nest_result_report",
    "pack",
    "run_nest",
    "write_nest_files",
]
