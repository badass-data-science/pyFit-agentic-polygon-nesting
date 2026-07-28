# AGENTS.md

Agent-facing guide to working in this repo. For user-facing docs (CLI usage, job
spec format, algorithm explanation, known limitations) see [README.md](README.md).

## What this is

`agentic-irregular-polygon-nesting` (Python package/CLI command: `sheetnest`) is a
general-purpose 2D irregular-polygon nesting (bin-packing) tool: given a set of 2D
shapes and how many of each are needed, it arranges them onto rectangular sheet
stock with minimal wasted material, via a no-fit-polygon (NFP) bottom-left-fill
heuristic. It reads part outlines from DXF files or inline polygons and writes one
DXF per sheet used plus a JSON utilization report.

It was originally a sibling project to pyLair (`pyLair-agentic-geodesics`, a
geodesic dome calculator) in this same `Engineering` repo, but has zero code
dependency on it — the only link is file-level (pyLair's cutting-template DXF
output can be fed in as job-spec input). pyLair has since moved to its own repo;
this project is standalone.

## Setup

```
pip install -e ".[test]"
```

## Test

```
pytest
```

- One test module per `sheetnest/*.py` source module, plus `tests/test_cli.py`
  (subprocess-level CLI integration tests).
- No golden-value/oracle test harness exists yet (unlike pyLair's
  `test_geometry_oracle.py`) — if you touch NFP or placement logic, verify
  correctness against an independent method (e.g. convex hull of pairwise vertex
  sums, or manual overlap/containment checks) rather than trusting a single
  hand-computed case. See the "real gotcha" below for why.

No linter/formatter is configured — match the surrounding style in whichever file
you're editing.

## Layout

| File | Responsibility |
|---|---|
| `sheetnest/geometry.py` | `Part`/`Sheet`/`Placement`/`NestResult` data model, plus polygon transforms (rotate/mirror/translate about a local origin) and area/bounding-box helpers. |
| `sheetnest/nfp.py` | No-fit-polygon computation via `pyclipper`, with a Minkowski-sum union fix (see below). |
| `sheetnest/packer.py` | The bottom-left-fill placement heuristic, including trying every already-opened sheet in order before starting a new one. |
| `sheetnest/sheet.py` | Sheet-boundary containment (`inner_fit_bounds`, exact bounding-box math, no NFP needed) and utilization reporting. |
| `sheetnest/io_dxf.py` | A minimal hand-written raw DXF reader/writer, no DXF library dependency. |
| `sheetnest/preview.py` | Renders a quick 2D preview PNG (`-P/--preview`) of a sheet's layout. |
| `sheetnest/cli.py` | `getopt`-based command-line entry point. |

## A real gotcha worth knowing about (`sheetnest/nfp.py`)

`pyclipper.MinkowskiSum` on a closed path doesn't return a single resolved
polygon — it returns the *raw* sweep contours, which for a small pattern swept
around a larger path includes an inner contour that looks like a hole but isn't
one (the Minkowski sum of two convex filled shapes is always itself convex, hence
never has a hole). The fix is to treat every returned contour as an independent
solid region and take their union via `shapely` rather than trusting Clipper's own
winding-direction-implied fill rule. This assumes the true NFP has no legitimate
holes, which holds for the convex/simple shapes this package targets but would be
wrong for a genuinely non-convex shape with a real unreachable pocket.

This bug passed a first hand-computable test case (two unit squares) cleanly —
it only showed up on a size-mismatched second case. If you touch NFP logic, vary
shape/size across multiple cases, not just one, before trusting the result.

## Known limitations

See README.md's "Known limitations" section (candidate placement points aren't
fully exhaustive, rectangular sheets only, scrap-reuse search cost on large
many-sheet jobs) before assuming a gap is an oversight rather than a deliberate
MVP scope cut.

## Naming note

The distribution name is `agentic-irregular-polygon-nesting` (this directory,
`pyproject.toml`'s `name`, README title) but the importable Python package,
console-script command, and all internal module paths are still `sheetnest` —
this was a deliberate partial rename (2026-07-28) to avoid touching every
import/test. Don't "fix" this into a full rename without checking with the user
first.

## Docs stay in sync

`README.md` and `blog-posts/introducing-sheet-nesting.md` (filename kept as a
historical artifact) both describe this project. The blog post also references
pyLair by name and links to its repo — if pyLair moves again or this project's
directory/repo location changes again, that post's links will go stale and need
another pass.
