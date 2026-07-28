# pyFit

A general-purpose 2D irregular-polygon nesting (bin-packing) tool: given a set of 2D shapes and how many of each you need, arranges them onto rectangular sheet stock (plywood, acrylic, sheet metal, ...) with minimal wasted material.

This started as a follow-on to [pyDome](../Geodesic-Dome-Design/pyDome) — pyDome's Bill of Materials tells you exactly which triangular panel shapes a geodesic dome needs and how many of each, but has nothing to say about how to lay them out on actual material. `pyfit` is deliberately **not** a pyDome module, though — it's a standalone tool that happens to read the DXF files pyDome (or any other CAD tool) can produce, so it's equally usable for unrelated 2D cutting/fabrication problems.

## Installation

```
pip install -e .
```

For running the test suite:

```
pip install -e ".[test]"
pytest
```

## Usage

```
pyfit -j job.json -o output/nest
```

writes `output/nest_sheet1.dxf`, `output/nest_sheet2.dxf`, ... (one file per sheet actually used) plus `output/nest_report.json`, and prints the same report to stdout. Add `-P/--preview` to also write `output/nest_sheet1.png`, ... — a quick 2D render of each sheet's layout (boundary plus every placed part's outline) for a fast sanity check without opening a DXF viewer.

While a large job packs, `pyfit` prints a `placed N/M parts (checking sheet K)...` heartbeat to stderr every couple of seconds, so a slow run doesn't look frozen (stdout stays clean JSON either way). Pass `-q/--quiet` to suppress it.

A job spec is JSON describing the sheet size and the parts to nest:

```json
{
  "sheet": {"width": 96, "height": 48},
  "parts": [
    {"name": "shapeA", "dxf": "facetype1.dxf", "quantity": 120, "allow_mirror": true},
    {"name": "shapeB", "polygon": [[0, 0], [1, 0], [0, 1]], "quantity": 10, "allow_mirror": false}
  ]
}
```

Each part gives its outline either as `"dxf"` (a path to a DXF file containing exactly one closed loop) or `"polygon"` (an inline list of `[x, y]` points), a `"quantity"`, and optionally `"allow_mirror"` (default `true`; set `false` for chirality-sensitive material, where flipping a shape over isn't the same as another copy of it — e.g. wood grain, a printed pattern, or a one-sided finish).

### Using pyDome's panel templates as input

pyDome's `-T/--face-templates` flag writes one DXF cutting template per unique panel shape (`<output>_facetype1.dxf`, ...) and reports a `panel_count` for each in its Bill of Materials. Point a `pyfit` job spec's `"dxf"` fields at those files and their `"quantity"` at the reported counts, and `pyfit` will figure out how to arrange them on your actual stock. There's no code coupling between the two projects — pyDome writes plain DXF files, and `pyfit`'s DXF importer doesn't know or care where a shape came from, the same way any CAD tool could read pyDome's output.

## MCP interface

For agentic use (an LLM assistant interactively nesting parts), install the `mcp` extra:

```
pip install -e ".[mcp]"
```

This provides a `pyfit-mcp` console command: an [MCP](https://modelcontextprotocol.io) server (stdio transport) exposing four tools, all sharing one parameter schema (`sheet_width`, `sheet_height`, `parts` — a list of job-spec part dicts, see above — and `rotation_step_degrees`):

| Tool | Purpose |
|---|---|
| `design_nest` | Packs the parts (no files written) and returns sheets-used and per-sheet utilization — a cheap way to try job specs. |
| `preview_nest` | Renders each sheet's 2D layout and returns them as inline images, so a result can be seen in-conversation before any file is written. |
| `get_nest_report` | Returns the full placement report (sheet index, position, rotation, mirror flag per part instance) as structured data, no files. |
| `export_nest` | Writes one DXF per sheet actually used to disk (optionally a preview PNG too, via `preview=True`). Returns the paths written plus the full placement report. |

Configure it in an MCP client (e.g. Claude Code/Desktop) by pointing at the `pyfit-mcp` command. All four tools share the same validation as the CLI (`pyfit/api.py:run_nest`/`load_part`) — a malformed job spec or an out-of-range rotation step raises a clear error rather than producing a bad or silent result.

All four tools also report [MCP progress notifications](https://modelcontextprotocol.io) on a large job, if the calling client requested them (i.e. sent a progress token): a heartbeat each time the packer tries a sheet for the current part instance, so a slow call doesn't look frozen mid-request. This works because packing itself runs in a worker thread while the tool `await`s it, keeping the server's event loop free to actually send those notifications out. With no progress token (or when calling the tool functions directly, e.g. in tests), this is simply a no-op.

## How it works

A closed 2D shape's set of legal (non-overlapping) placements relative to another fixed shape is described by their **no-fit-polygon (NFP)**: the region a moving shape's reference point must stay outside of to avoid overlapping the stationary one. `pyfit` computes NFPs via [`pyclipper`](https://github.com/fonttools/pyclipper) (Python bindings to the mature Clipper library) using the standard Minkowski-sum technique, verified against a hand-computable case (the NFP of two unit squares is exactly the 2×2 square from (-1,-1) to (1,1)) before anything was built on top of it.

On top of that primitive, `pyfit` runs a **bottom-left-fill heuristic**: place the largest parts first, and for each part instance, try a range of rotation angles (and mirrored orientations, unless `allow_mirror` is `false`) at a configurable step size (`-R/--rotation-step`, default 15°), computing the combined set of valid positions against every already-placed part plus the sheet boundary, and picking the leftmost-then-bottommost one. Each part instance tries every already-opened sheet in order, earliest first, before a new one gets opened — so leftover scrap on an earlier sheet gets reused instead of every miss immediately starting a fresh sheet.

This is a **heuristic, not a globally optimal solver** — irregular 2D bin-packing is NP-hard, and this is the same family of approach used by tools like SVGnest/DeepNest. A refinement pass (simulated annealing or genetic reordering on top of this base placement) would be a natural future improvement, not something this MVP attempts.

### A real gotcha worth knowing about

`pyclipper.MinkowskiSum` on a closed path doesn't return a single resolved polygon — it returns the *raw* sweep contours, which for a small pattern swept around a larger path includes an inner contour that looks like a hole but isn't one (the Minkowski sum of two convex filled shapes is always itself convex, hence never has a hole — verified against an independent ground truth, the convex hull of all pairwise vertex sums, on a case where the raw Clipper output was misleading). The fix, in `pyfit/nfp.py`, is to treat every returned contour as an independent solid region and take their union via `shapely` rather than trusting Clipper's own winding-direction-implied fill rule. This assumes the true NFP has no legitimate holes, which holds for the convex/simple shapes this package targets, but would be wrong for a genuinely non-convex shape with a real unreachable pocket — out of scope here.

### Known limitations

- **Candidate placement points aren't fully exhaustive.** The bottom-left-fill search considers the sheet's own corners, every NFP vertex, every NFP-vs-sheet-boundary crossing, and every NFP-vs-NFP crossing between different already-placed parts — this is what lets, for example, six unit squares tile a 3×2 sheet perfectly rather than needlessly spilling onto a second sheet. It still isn't full NFP-boundary tracing, so it can occasionally miss an even tighter placement. Every candidate is explicitly re-validated for overlap and sheet containment before being accepted, though, so this can only produce a *non-optimal* placement, never an *invalid* one.
- **Rectangular sheets only.** No support (yet) for irregular stock outlines or offcuts with existing cutouts.
- **Reusing scrap across sheets costs real search time on large, many-sheet jobs.** Every part instance now tries each already-opened sheet in turn, and each try means a full NFP-based candidate search against everything already placed there. A cheap area check skips sheets with too little *aggregate* remaining area to possibly fit (an exact, safe filter — it never wrongly skips a sheet that could actually fit), but a sheet can still have plenty of leftover area in a shape nothing fits, and that case still costs a full search per miss. Measured on a real 40-panel, 3-sheet job of small pyDome triangles: about 3x slower than the previous (no-reuse) behavior at the default rotation step, but back to roughly the same speed at a coarser one. `-R/--rotation-step` is the direct lever for this trade-off (fewer tried orientations means fewer NFP computations per sheet-miss) — widen it for a large job if packing feels slow, at the cost of a somewhat coarser search.

## Project structure

| File | Responsibility |
|---|---|
| `pyfit/geometry.py` | `Part`/`Sheet`/`Placement`/`NestResult` data model, plus polygon transforms (rotate/mirror/translate about a local origin) and area/bounding-box helpers. |
| `pyfit/nfp.py` | No-fit-polygon computation via `pyclipper`, with the Minkowski-sum union fix described above. |
| `pyfit/packer.py` | The bottom-left-fill placement heuristic, including trying every already-opened sheet in order before starting a new one, plus an optional `on_progress` callback (a heartbeat, fired per sheet tried per part instance) for the CLI/MCP progress reporting described above. |
| `pyfit/sheet.py` | Sheet-boundary containment (`inner_fit_bounds`, exact for a rectangular sheet via bounding-box math, no NFP needed) and utilization reporting. |
| `pyfit/io_dxf.py` | A minimal hand-written raw DXF reader (reconstructs closed loops from independent `LINE` entities, e.g. pyDome's face templates) and writer (one file per sheet), with no DXF library dependency — matching pyDome's own writers. |
| `pyfit/preview.py` | Renders a quick 2D preview PNG (`-P/--preview`) of a sheet's layout (boundary plus every placed part's outline), the same role as pyDome's own preview module. |
| `pyfit/api.py` | Programmatic entry point shared by the CLI and the MCP server: `run_nest(...)`/`load_part(...)` (job-spec parsing and packing) and `nest_result_report(...)`/`write_nest_files(...)` (structured report and file output), all `ValueError`-raising on bad input rather than printing and exiting. |
| `pyfit/mcp_server.py` | MCP server (`pyfit-mcp` console command, optional `mcp` extra): `design_nest`/`preview_nest`/`get_nest_report`/`export_nest` tools built on `pyfit/api.py`. |
| `pyfit/cli.py` | `getopt`-based command-line entry point, built on `pyfit/api.py`. |
| `tests/` | pytest suite: unit tests per module, plus subprocess-level CLI integration tests. |

## License

MIT.
