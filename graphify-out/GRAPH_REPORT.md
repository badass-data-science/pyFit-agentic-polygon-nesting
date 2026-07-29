# Graph Report - .  (2026-07-29)

## Corpus Check
- Corpus is ~23,050 words - fits in a single context window. You may not need a graph.

## Summary
- 234 nodes · 544 edges · 10 communities (9 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.88)
- Token cost: 116,754 input · 0 output

## Community Hubs (Navigation)
- Project Documentation & Design Rationale
- Shared API & File I/O
- Polygon Geometry Primitives
- MCP Server Tools
- CLI Entry Point
- No-Fit-Polygon Computation
- Bottom-Left-Fill Packing & Tests
- CLI Integration Tests
- Nesting Result Visualization
- Package Distribution Name

## God Nodes (most connected - your core abstractions)
1. `Sheet` - 34 edges
2. `pack()` - 25 edges
3. `Part` - 18 edges
4. `run_nest()` - 17 edges
5. `pyFit Project` - 17 edges
6. `Placement` - 16 edges
7. `pyFit Overview` - 16 edges
8. `write_nest_files()` - 14 edges
9. `"Introducing pyFit" Blog Post` - 13 edges
10. `load_part()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Progress Reporting / Heartbeat` --semantically_similar_to--> `Progress Reporting Mechanism`  [INFERRED] [semantically similar]
  blog-posts/introducing-pyfit.md → AGENTS.md
- `Agentic MCP Interface` --semantically_similar_to--> `MCP Interface Tools Table`  [INFERRED] [semantically similar]
  blog-posts/introducing-pyfit.md → README.md
- `Programmatic/Agentic MCP Alternative` --semantically_similar_to--> `MCP Interface Tools Table`  [INFERRED] [semantically similar]
  skills/pyfit/SKILL.md → README.md
- `The Ghost Hole Bug` --semantically_similar_to--> `Minkowski-Sum Ghost-Hole Bug`  [INFERRED] [semantically similar]
  blog-posts/introducing-pyfit.md → AGENTS.md
- `Job Spec Format (Skill Doc)` --semantically_similar_to--> `Usage / Job Spec Format`  [INFERRED] [semantically similar]
  skills/pyfit/SKILL.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Agent-Facing Interfaces to pyFit Core (CLI, MCP Server, OpenClaw Skill)** — agents_cli_module, agents_mcp_server_module, skills_pyfit_skill_skill_definition, agents_api_module [INFERRED 0.85]
- **Documentation Set That Must Stay in Sync (README, Blog Post, OpenClaw Skill)** — readme_pyfit_overview, agents_docs_sync_requirement, blog_posts_introducing_pyfit_post, skills_pyfit_skill_skill_definition [EXTRACTED 1.00]
- **Project Naming History Narrative (Sheet-Nesting to agentic-irregular-polygon-nesting to pyFit)** — agents_naming_history, changelog_2026_07_28_entry, agents_pypi_distribution_naming [EXTRACTED 1.00]
- **Nesting Result Visualization Pattern** — blog_posts_images_nest_sheet1_pylair_triangles_chart, blog_posts_images_nest_sheet1_pylair_triangles_pyfit, blog_posts_images_nest_sheet1_pylair_triangles_utilization_metric, blog_posts_images_nest_sheet1_pylair_triangles_triangle_polygon_nesting [INFERRED 0.75]

## Communities (10 total, 1 thin omitted)

### Community 0 - "Project Documentation & Design Rationale"
Cohesion: 0.07
Nodes (54): pyfit/api.py, pyfit/cli.py, Docs-Stay-in-Sync Requirement, FastMCP, pyfit/geometry.py, pyfit/__init__.py, pyfit/io_dxf.py, pyfit/mcp_server.py (+46 more)

### Community 1 - "Shared API & File I/O"
Cohesion: 0.11
Nodes (35): Write one DXF (and, if preview=True, one PNG) per sheet actually     used to "<o, write_nest_files(), NestResult, Placement, A rectangular piece of stock, `width` x `height`, origin at one corner., Where one part instance ended up: sheet, transform, and final polygon., The outcome of a `packer.pack` run: sheet count, placements, utilization., Sheet (+27 more)

### Community 2 - "Polygon Geometry Primitives"
Cohesion: 0.14
Nodes (27): bounding_box(), mirror_polygon(), orient_ccw(), polygon_area(), Point, The polygon reflected across the local Y axis (x -> -x). Combined with     `rota, The polygon, reversed if necessary so it winds counter-clockwise.      The shoel, The polygon mirrored (if `mirrored`), then rotated, then translated --     the c (+19 more)

### Community 3 - "MCP Server Tools"
Cohesion: 0.17
Nodes (22): Context, design_nest(), export_nest(), get_nest_report(), _job(), preview_nest(), Render a quick 2D preview of every sheet's layout (boundary plus     every place, Pack a set of parts onto sheet stock and return the full placement     report as (+14 more)

### Community 4 - "CLI Entry Point"
Cohesion: 0.13
Nodes (23): ArgumentParser, parametrize, load_part(), nest_result_report(), The structured, file-free part of a nesting report: sheet count,     per-sheet u, Build a Part from one job-spec part dict: {"name", "quantity",     "dxf" or "pol, Parse a job spec dict ({"sheet": {"width", "height"}, "parts": [...]})     and r, run_nest() (+15 more)

### Community 5 - "No-Fit-Polygon Computation"
Cohesion: 0.15
Nodes (17): BaseGeometry, _from_int(), no_fit_polygon(), Point, `polygon`'s coordinates scaled and rounded to pyclipper's integer space., The inverse of `_to_int`: pyclipper's integer coordinates back to floats., The outer no-fit-polygon (NFP) of `moving` around a fixed `stationary`.      The, _to_int() (+9 more)

### Community 6 - "Bottom-Left-Fill Packing & Tests"
Cohesion: 0.30
Nodes (17): Part, A shape to be nested, and how many copies of it are needed.      `polygon` is a, _candidate_orientations(), pack(), Bottom-left-fill packing of `parts` onto (possibly several) `sheet`-sized     sh, Yields (rotation_degrees, mirrored) pairs to try for `part`: every     multiple, _assert_no_overlaps_per_sheet(), _assert_within_sheet_bounds() (+9 more)

### Community 7 - "CLI Integration Tests"
Cohesion: 0.29
Nodes (12): run_cli(), test_dxf_sourced_job_nests_successfully(), test_help_flag_prints_usage(), test_inline_polygon_job_nests_successfully_and_writes_expected_files(), test_missing_job_path_reports_a_clear_error(), test_missing_output_path_reports_a_clear_error(), test_no_arguments_prints_help_and_exits_nonzero(), test_no_preview_flag_means_no_png_files() (+4 more)

### Community 8 - "Nesting Result Visualization"
Cohesion: 0.83
Nodes (4): Nest Sheet 1 Triangles Preview Chart, pyFit Nesting Tool, Triangle Polygon Nesting, Sheet Utilization Metric (60.9%)

## Knowledge Gaps
- **13 isolated node(s):** `pyfit-agentic-polygon-nesting`, `Ruff Lint Check Step`, `Ruff Format Check Step`, `Mypy Type Check Step`, `Pytest Coverage Step` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Sheet` connect `Shared API & File I/O` to `Polygon Geometry Primitives`, `MCP Server Tools`, `CLI Entry Point`, `Bottom-Left-Fill Packing & Tests`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `run_nest()` connect `CLI Entry Point` to `Shared API & File I/O`, `MCP Server Tools`, `Bottom-Left-Fill Packing & Tests`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `pack()` connect `Bottom-Left-Fill Packing & Tests` to `Shared API & File I/O`, `Polygon Geometry Primitives`, `CLI Entry Point`, `No-Fit-Polygon Computation`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `pyfit-agentic-polygon-nesting`, `Ruff Lint Check Step`, `Ruff Format Check Step` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Project Documentation & Design Rationale` be split into smaller, more focused modules?**
  _Cohesion score 0.06568832983927324 - nodes in this community are weakly interconnected._
- **Should `Shared API & File I/O` be split into smaller, more focused modules?**
  _Cohesion score 0.11463414634146342 - nodes in this community are weakly interconnected._
- **Should `Polygon Geometry Primitives` be split into smaller, more focused modules?**
  _Cohesion score 0.13763440860215054 - nodes in this community are weakly interconnected._