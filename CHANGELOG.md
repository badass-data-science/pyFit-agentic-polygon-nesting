# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project has not yet adopted semantic version releases; entries are grouped
by date instead.

## 2026-07-28

### Changed

- Renamed the project from **Sheet-Nesting** to
  **agentic-irregular-polygon-nesting** (directory and `pyproject.toml`
  distribution name). The importable Python package, console-script command,
  and internal module paths were left unchanged at the time (`sheetnest`) —
  see the second rename below, same day.
- Switched license from GPL-3.0-or-later to MIT; added `LICENSE`.
- Updated the blog post's pyDome references to pyLair, and fixed its links to
  point to pyLair's own repo and this project's renamed directory.
- Renamed the project again, same day, from **agentic-irregular-polygon-nesting**
  to **pyFit** (directory now `pyFit-agentic-polygon-nesting`). This time it's a
  full rename: the distribution name, the importable package (`sheetnest/` →
  `pyfit/`), the CLI command (`sheetnest` → `pyfit`), and the MCP console script
  (`sheetnest-mcp` → `pyfit-mcp`) are all `pyfit`, matching pyLair's own
  convention. All source file license headers were also brought in line with
  the MIT switch above (they'd still said GPL).

### Added

- `AGENTS.md`: agent-facing guide to setup, testing, module layout, and the
  Minkowski-sum NFP gotcha.
- MCP interface (`pyfit-mcp`, optional `mcp` extra): a `FastMCP` server
  exposing `design_nest`/`preview_nest`/`get_nest_report`/`export_nest` tools,
  mirroring pyLair's own MCP server pattern. `pyfit/api.py` factors the
  job-spec parsing and packing logic (previously private to `cli.py`) into a
  shared entry point (`load_part`, `run_nest`, `nest_result_report`,
  `write_nest_files`) used by both the CLI and the MCP server.
- Progress reporting for long-running jobs, so a slow nest doesn't look
  frozen: `packer.pack` gained an `on_progress(placed, total, sheet_index)`
  callback, fired once per sheet tried per part instance. The CLI prints a
  throttled `placed N/M parts (checking sheet K)...` heartbeat to stderr every
  ~2s (`-q/--quiet` to disable); the MCP tools became `async` and report MCP
  progress notifications via `Context.report_progress` when the calling
  client requests them, running the actual packing in a worker thread
  (`asyncio.to_thread`) so the server's event loop stays free to send them
  mid-call.

## 2026-07-14

### Added

- Cross-sheet scrap reuse: each part instance now tries every already-opened
  sheet, earliest first, before a new one is opened, so leftover space on an
  earlier sheet gets reused instead of every miss opening a fresh sheet.
- An exact, safe area pre-check that skips a sheet outright when there isn't
  enough aggregate remaining area to fit a part, to offset the added search
  cost of scrap reuse.
- `-P`/`--preview`: renders a quick 2D preview PNG of each sheet's layout
  (boundary plus every placed part's outline) alongside the DXF/JSON output.
- Blog post updated to describe scrap reuse and the preview image feature.

## 2026-07-12

### Added

- Initial MVP: a general-purpose 2D irregular-polygon nesting (bin-packing)
  tool. No-fit-polygon (NFP) computation via `pyclipper`'s Minkowski-sum
  technique (with a union-based fix for spurious inner contours), and a
  bottom-left-fill placement heuristic trying a range of rotation angles and
  mirrored orientations per part.
- DXF and inline-polygon part input; DXF and JSON report output per sheet.
- `sheetnest` CLI (`sheetnest -j job.json -o output/nest`) — see the
  2026-07-28 entries above for this project's two subsequent renames; the
  CLI command is `pyfit` as of the second one.
- Test suite covering geometry, NFP, packing, DXF I/O, and CLI integration.
- Blog post introducing the project and its relationship to pyLair (then
  pyDome).
