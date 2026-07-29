# AGENTS.md

Agent-facing guide to working in this repo. For user-facing docs (CLI usage, job
spec format, algorithm explanation, known limitations) see [README.md](README.md).

## What this is

**pyFit** (directory `pyFit-agentic-polygon-nesting`; importable package and CLI
command are `pyfit`/`pyfit-mcp`, but the PyPI distribution name is
`pyfit-agentic-polygon-nesting` — see "Naming note" below for why it diverges) is a
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

Optional extras: `mcp` (`mcp<2.0` — pinned like pyLair's own `mcp` extra, since
`mcp` 2.0.0 removed `mcp.server.fastmcp` entirely; `pyfit/mcp_server.py`'s
`FastMCP`/`Image` imports and `tests/test_mcp_server.py` both 404 on 2.0.0's new
module layout), and `lint` (`ruff`, `mypy`, `types-shapely` — what CI runs).
`test` also pulls in `pytest-cov`; run `pytest --cov=pyfit --cov-report=term-missing`
for a coverage report (note `pyfit/cli.py` will show as ~0% covered even
though `tests/test_cli.py` exercises it thoroughly — those tests invoke it as
a subprocess, which `coverage.py` can't see into without extra
`COVERAGE_PROCESS_START` plumbing this project doesn't bother with; it's a
measurement gap, not an actual testing gap).

## Packaging / PyPI readiness

`pyproject.toml` has PyPI-ready metadata: `classifiers`, `keywords`,
`[project.urls]` (Homepage/Repository/Issues/Changelog, all pointing at this
GitHub repo), and `[tool.setuptools.package-data]` shipping `pyfit/py.typed`
(PEP 561 — this package's type hints are meant to be consumed by downstream
type checkers, not just its own CI). Verify packaging changes with `python -m
build` (needs the `build` package) followed by `twine check dist/*` (needs
`twine`) before trusting them — `pyproject.toml` syntax errors and missing
files don't otherwise surface until an actual publish attempt. Nothing has
been published to PyPI yet; publishing is a separate, deliberate step (not
something to do as a side effect of a metadata change).

## Test

```
pytest
```

- One test module per `pyfit/*.py` source module, plus `tests/test_cli.py`
  (subprocess-level CLI integration tests) and `tests/test_mcp_server.py`
  (direct calls into the `@mcp.tool()`-decorated functions, auto-skipped via
  `pytest.importorskip("mcp")` unless the `mcp` extra is installed — same
  pattern as pyLair's own MCP test).
- No golden-value/oracle test harness exists yet (unlike pyLair's
  `test_geometry_oracle.py`) — if you touch NFP or placement logic, verify
  correctness against an independent method (e.g. convex hull of pairwise vertex
  sums, or manual overlap/containment checks) rather than trusting a single
  hand-computed case. See the "real gotcha" below for why.

Every public function/class across `pyfit/` has a real docstring (not a `#`
comment above the `def`) — this is deliberate, not a style nit: docstrings
are what `help()`, IDEs, and Sphinx-style doc generation actually pick up,
comments aren't. Private `_helpers` should have one too where the "why", not
just the "what", isn't obvious from the name and signature alone. Keep new
code consistent with this rather than reverting to comments.

CI (`.github/workflows/ci.yml`) runs `ruff check` and `mypy` (config in
`pyproject.toml`'s `[tool.ruff]`/`[tool.mypy]`, extras installed via the `lint`
optional-dependency group) plus `pytest --cov`, on Python 3.9 and 3.12.
`mypy`'s `disallow_untyped_defs` is on — every function, including private
`_helpers`, needs a full signature (all parameters plus the return type), not
just the public API.

The codebase is formatted with `ruff format` (standard 4-space/Black-style
PEP8 — the whole `pyfit/` tree was reformatted from an earlier 2-space
convention on 2026-07-28, see CHANGELOG). CI enforces this (`ruff format
--check`), so run `ruff format pyfit tests` after editing rather than
hand-matching the surrounding style.

## Layout

| File | Responsibility |
|---|---|
| `pyfit/geometry.py` | `Part`/`Sheet`/`Placement`/`NestResult` data model, plus polygon transforms (rotate/mirror/translate about a local origin) and area/bounding-box helpers. |
| `pyfit/nfp.py` | No-fit-polygon computation via `pyclipper`, with a Minkowski-sum union fix (see below). |
| `pyfit/packer.py` | The bottom-left-fill placement heuristic, including trying every already-opened sheet in order before starting a new one, plus an optional `on_progress(placed, total, sheet_index)` callback (see "Progress reporting" below). `pack`'s docstring states its worst-case complexity explicitly (also summarized in README's "How it works") — update both if you change the candidate search's structure. |
| `pyfit/sheet.py` | Sheet-boundary containment (`inner_fit_bounds`, exact bounding-box math, no NFP needed) and utilization reporting. |
| `pyfit/io_dxf.py` | A minimal hand-written raw DXF reader/writer, no DXF library dependency. |
| `pyfit/preview.py` | Renders a quick 2D preview PNG (`-P/--preview`) of a sheet's layout. |
| `pyfit/api.py` | Shared entry point for the CLI and MCP server: `load_part`/`run_nest` (job-spec parsing + packing, `ValueError` on bad input) and `nest_result_report`/`write_nest_files` (structured report / file output). |
| `pyfit/mcp_server.py` | MCP server (`pyfit-mcp`, optional `mcp` extra): `design_nest`/`preview_nest`/`get_nest_report`/`export_nest`, all built on `api.py`. |
| `pyfit/cli.py` | `argparse`-based command-line entry point, built on `api.py`. |
| `pyfit/__init__.py` | `__version__` (from installed package metadata via `importlib.metadata`, not hardcoded — don't duplicate `pyproject.toml`'s version here) and re-exports of the small public surface (`Part`, `Sheet`, `Placement`, `NestResult`, `pack`, `run_nest`, `load_part`, `nest_result_report`, `write_nest_files`), so `import pyfit` is directly useful. |
| `skills/pyfit/SKILL.md` | OpenClaw skill (see "OpenClaw skill" below) teaching an OpenClaw agent when/how to invoke the `pyfit` CLI directly, no MCP setup required. |
| `openclaw.config.snippet.jsonc` | A fragment for `~/.openclaw/openclaw.json` registering the skill above. |
| `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json` | Tracked graphify knowledge-graph snapshot (see "Knowledge graph (graphify)" below). The rest of `graphify-out/` is gitignored. |

## A real gotcha worth knowing about (`pyfit/nfp.py`)

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

## Progress reporting

`packer.pack`'s optional `on_progress(placed, total, sheet_index)` fires once
per sheet tried per part instance — more than once per instance on a
scrap-reuse-heavy job, which is exactly the case a single instance's own
placement can be slow. `api.py:run_nest` forwards it through unchanged.

- **CLI**: `cli.py`'s `_make_progress_printer` throttles it to a heartbeat on
  stderr every `PROGRESS_MIN_INTERVAL_SECONDS` (2s), leaving stdout as clean
  JSON. `-q/--quiet` disables it.
- **MCP**: all four tools in `mcp_server.py` are `async def` and accept an
  implicit `ctx: Context | None` (excluded from the tool's public schema by
  FastMCP). This is load-bearing, not incidental: a *synchronous* FastMCP tool
  blocks the server's event loop for its entire duration (confirmed by reading
  `FuncMetadata.call_fn_with_arg_validation` — a sync tool is called directly,
  not offloaded), so it could never emit a progress notification mid-call no
  matter what `pack()` did internally. The fix is `_run_nest` in
  `mcp_server.py`: it runs `run_nest` in a worker thread via
  `asyncio.to_thread` and bridges the synchronous `on_progress` callback back
  onto the event loop with `asyncio.run_coroutine_threadsafe(ctx.report_progress(...), loop)`.
  Verified live: a 5.6s job produced ~33 progress notifications spread across
  the whole call, not bunched at the end, confirming the loop stays responsive
  throughout rather than just at the start/end. If you touch this, keep it
  that way — reverting the tools to `def` (non-async) would silently break
  progress reporting even though every existing test would probably still
  pass, since the tests use a fake `Context` and don't assert on timing.

## OpenClaw skill

`skills/pyfit/SKILL.md` follows [OpenClaw](https://docs.openclaw.ai)'s skill
format: YAML frontmatter (`name`, `description`, and here a
`metadata.openclaw.requires.bins: ["pyfit"]` gate so the skill only offers
itself when the `pyfit` command is actually installed and on `PATH`) followed
by a markdown body of instructions for the agent. OpenClaw discovers skills
by scanning configured roots for `<root>/<skill-name>/SKILL.md` (up to 6
levels deep) — hence the nested `skills/pyfit/` directory, not a bare
`SKILL.md` at the repo root. `openclaw.config.snippet.jsonc` is a fragment
(not a complete config) meant to be merged into `~/.openclaw/openclaw.json`:
it adds this repo's `skills/` directory to `skills.load.extraDirs` and
enables the `pyfit` entry under `skills.entries`.

This is a separate, additive integration from the MCP server
(`mcp_server.py`) above — the skill teaches an OpenClaw agent to shell out to
the `pyfit` CLI directly (same as a human would), while `pyfit-mcp` is for
any MCP-capable client making structured tool calls instead. Keep the skill
body's job-spec/flag description in sync with `cli.py`'s actual `argparse`
definitions and README's "Usage" section if either changes — it's a third
place (after README and the CLI's own `--help`) that duplicates this same
information for a different audience (an agent, not a human).

## Knowledge graph (graphify)

`graphify-out/graph.html`/`GRAPH_REPORT.md`/`graph.json` are a tracked
snapshot from running the [graphify](https://github.com/safishamsi/graphify)
skill (`/graphify`) over this repo — nodes/edges for the codebase and docs,
with community detection and an audit trail (EXTRACTED/INFERRED/AMBIGUOUS
confidence per edge). `.gitignore` ignores everything else under
`graphify-out/` (`.graphify_python`, `.graphify_root`, `cache/`, `cost.json`,
`manifest.json`, `.graphify_labels.json`) as local/derived state that
shouldn't be shared.

This is a point-in-time snapshot, not auto-regenerated on every commit — it
will drift as the codebase changes. Re-run `/graphify` and re-commit the
three tracked files if you want it current again; there's no CI job
enforcing freshness.

`graph.json` also carries one manually-added fact the extractor didn't
find on its own: `references` edges (marked `"_origin": "manual"`,
INFERRED, confidence_score 0.95) from the four CI step nodes
(`github_workflows_ci_ruff_lint_step`, `..._ruff_format_step`,
`..._mypy_step`, `..._pytest_coverage_step`) to three new nodes
(`pyproject_ruff_config`, `pyproject_mypy_config`,
`pyproject_coverage_config`) representing the `pyproject.toml` config
sections those CI steps actually enforce — closing a gap the graph itself
surfaced (the steps only linked to the parent "CI Pipeline" node, not to
what they configure). **A full `/graphify` rebuild will overwrite
`graph.json` and silently drop this manual edge** (it isn't part of the
deterministic AST pass or reproducible from the semantic-extraction prompt
as currently written); re-add it by hand afterward, or extend the
extraction-spec prompt to look for CI-step-to-config-section links
generally, if this class of gap matters enough to keep fixing per-run.

## Known limitations

See README.md's "Known limitations" section (candidate placement points aren't
fully exhaustive, rectangular sheets only, scrap-reuse search cost on large
many-sheet jobs) before assuming a gap is an oversight rather than a deliberate
MVP scope cut.

## Naming note

This project has been renamed twice (both 2026-07-28): first **Sheet-Nesting** →
**agentic-irregular-polygon-nesting** (directory + `pyproject.toml` distribution
name only, package/CLI left as `sheetnest` — a deliberate partial rename at the
time), then **agentic-irregular-polygon-nesting** → **pyFit**
(`pyFit-agentic-polygon-nesting` directory, `pyfit` distribution name, and this
time a *full* rename: the package folder, all internal imports, the CLI command,
and the MCP console script all became `pyfit`/`pyfit-mcp`, matching pyLair's own
convention of distribution name = package name = CLI command). If you find a
stray `sheetnest` reference anywhere, it's a leftover from the first rename that
should become `pyfit`, not a second naming scheme to preserve.

A third naming event happened on 2026-07-28 while making the project
PyPI-ready: the PyPI distribution name became **pyfit-agentic-polygon-nesting**
(matching the repo directory name), breaking the "distribution name = package
name = CLI command" convention the second rename had established. This wasn't
optional — PyPI already has an unrelated package named `pyfit` (a neural-net
library), so publishing under that name isn't possible. The importable
package, CLI command, and MCP console script are unaffected (still
`pyfit`/`pyfit-mcp`); only `pyproject.toml`'s `[project] name` field and
PyPI-facing install instructions changed. If you're about to rename this
project again, check name availability on PyPI *before* picking a name (e.g.
`curl -s https://pypi.org/pypi/<name>/json` — a 404 means available), not
after.

## Docs stay in sync

`README.md` and `blog-posts/introducing-pyfit.md` (renamed from
`introducing-sheet-nesting.md` on 2026-07-28, alongside the project's own rename
to pyFit — its narrative content was updated to match at the same time, unlike
the two earlier project renames, where the post's prose was deliberately left
as historical flavor) both describe this project. The blog post also references
pyLair by name and links to its repo — if pyLair moves again or this project's
directory/repo location changes again, that post's links will go stale and need
another pass.

`skills/pyfit/SKILL.md` is a fourth place (alongside README, the blog post,
and `cli.py --help`) describing how to actually run a nesting job — if the
job-spec schema or CLI flags change, all four need updating, not just the
ones that are obviously code.
