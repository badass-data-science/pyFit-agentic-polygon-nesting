---
name: pyfit
description: Nest 2D shapes onto rectangular sheet stock with minimal waste and export ready-to-cut DXF files, via the pyfit CLI. Use when the user wants to lay out/pack/nest parts on plywood, acrylic, sheet metal, or similar stock for a laser cutter or CNC router, or asks how many of a shape fit on a sheet.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["pyfit"] },
      },
  }
---

pyfit is a general-purpose 2D irregular-polygon nesting (bin-packing) tool:
given a set of 2D shapes and how many of each are needed, it arranges them
onto rectangular sheet stock with minimal wasted material, via a
no-fit-polygon bottom-left-fill heuristic. It reads part outlines from DXF
files or inline polygons and writes one ready-to-cut DXF file per sheet used,
plus a JSON placement report.

Not installed as a bundled OpenClaw skill dependency — install it first:

```
pip install pyfit-agentic-polygon-nesting
```

(The distribution name is `pyfit-agentic-polygon-nesting`; the installed
command is `pyfit`.)

## When to use this

Reach for `pyfit` whenever the user wants to:

- Figure out how to arrange/pack/nest a set of 2D shapes onto sheet stock
  with minimal wasted material.
- Know how many copies of a shape fit on a sheet of a given size.
- Produce cut-ready DXF files for a laser cutter or CNC router from a list
  of part outlines.

## Running a job

1. Write a job spec JSON file describing the sheet size and the parts to nest:

   ```json
   {
     "sheet": {"width": 96, "height": 48},
     "parts": [
       {"name": "shapeA", "dxf": "facetype1.dxf", "quantity": 120, "allow_mirror": true},
       {"name": "shapeB", "polygon": [[0, 0], [1, 0], [0, 1]], "quantity": 10, "allow_mirror": false}
     ]
   }
   ```

   Each part gives its outline either as `"dxf"` (a path to a DXF file
   containing exactly one closed loop) or `"polygon"` (an inline list of
   `[x, y]` points), a `"quantity"`, and optionally `"allow_mirror"` (default
   `true`; set `false` for chirality-sensitive material, e.g. wood grain or a
   printed pattern, where a mirror-image placement isn't interchangeable
   with the original).

2. Run it:

   ```
   pyfit -j job.json -o output/nest
   ```

   Writes `output/nest_sheet1.dxf`, `output/nest_sheet2.dxf`, ... (one file
   per sheet actually used) plus `output/nest_report.json`, and prints the
   same report as JSON to stdout. Add `-P/--preview` to also write a quick
   2D preview PNG per sheet (`output/nest_sheet1.png`, ...) for a fast
   sanity check without opening a DXF viewer.

3. Read `sheets_used`, `utilization_by_sheet`, and `placements` from the
   printed/written report to answer the user's question or continue
   iterating (e.g. try a larger sheet, or a finer `-R/--rotation-step` for a
   denser but slower search — default 15 degrees, must be greater than 0 and
   less than 360).

A malformed job spec (missing fields, wrong types, an out-of-range rotation
step) makes `pyfit` exit non-zero with a clear error message on stderr;
stdout is reserved for the JSON report on success, so it's safe to always
try parsing stdout as JSON when the exit code is 0.

## Programmatic / agentic alternative

If direct tool calls (rather than shelling out and parsing stdout) are
preferred, `pyfit` also ships an MCP server (`pyfit-mcp`, requires the `mcp`
extra: `pip install "pyfit-agentic-polygon-nesting[mcp]"`) exposing
`design_nest`, `preview_nest`, `get_nest_report`, and `export_nest` tools
over the same job-spec schema described above. See this project's README
for how to point an MCP-capable client at it.
