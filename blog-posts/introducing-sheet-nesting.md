# Sheet-Nesting (or, How Our Heroine Stopped Wasting Perfectly Good Aluminum)

Cutting two hundred and forty triangular panels for a geodesic secret laboratory is, it turns out, a great deal easier than figuring out how to actually get two hundred and forty triangles out of a stack of aluminum sheets without half of each sheet ending up as scrap. Even a supervillain has a materials budget, and "just buy more aluminum" stopped being a satisfying answer somewhere around the fourth wasted sheet. Our heroine had pyDome telling her exactly which panel shapes she needed and how many of each — but nothing telling her how to *arrange* them.

That arranging problem has a name — nesting, or irregular bin-packing — and it turns out to be interesting (and hard) enough to deserve its own tool rather than a bolted-on pyDome feature. So: Sheet-Nesting.
# What It Does

Sheet-Nesting takes a list of 2D shapes, how many of each you need, and the size of your sheet stock, and figures out how to lay them out with as little wasted material as possible. Feed it a job description — sheet dimensions plus a list of parts, each either an inline polygon or a DXF file — and it hands back one DXF per sheet actually used (ready to load into a laser cutter or CNC router) plus a JSON report of exactly where every piece landed, at what rotation, and whether it got flipped over.

Critically, it is **not** a pyDome feature. It is its own standalone project, living as a sibling to `Geodesic-Dome-Design/pyDome` rather than inside it, with zero code dependency in either direction. Our heroine's secret lair is not the only thing that will eventually need cutting — control panel faceplates, viewport bezels, whatever comes next — and she'd rather solve "how do I not waste sheet stock" once, generally, than reinvent it every time a new project needs shapes cut from flat material.
# Why We Need It

pyDome's Bill of Materials is extremely precise about *what* you need: exactly which triangular panel shapes, exactly how many of each, down to the millimeter. What it has never had an opinion on is *how those shapes actually fit on a physical sheet*. Left to her own devices, our heroine's first instinct was to eyeball it — draw a triangle, copy-paste it around the sheet in her CAD software, squint, adjust, repeat two hundred and forty times. This is exactly the kind of tedious, error-prone, "a computer should be doing this" work that got pyDome written in the first place, so the same instinct applied here.

The catch: this isn't a simple problem. Deciding how to optimally pack arbitrary shapes onto a sheet is what computer scientists call NP-hard, which is a polite way of saying "there is no known shortcut, and there provably might never be one." Real nesting software doesn't solve it exactly — it uses heuristics that get *close* to optimal, fast enough to actually be useful. Sheet-Nesting does the same.
# How It Works

**No-fit-polygons.** The core idea nesting software leans on is the no-fit-polygon (NFP): given a shape that's already placed on the sheet, the NFP describes the "keep-out zone" for a second shape's reference point — step inside that zone and the two shapes overlap; step outside it (or land exactly on its boundary) and they don't. Computing this correctly, especially for oddly-shaped polygons, is genuinely fiddly geometry — the kind of thing where hand-rolling your own math is a great way to introduce a bug that only shows up on the fortieth shape you nest. So Sheet-Nesting leans on [`pyclipper`](https://github.com/fonttools/pyclipper) (mature C++ polygon-clipping bindings) to compute the underlying Minkowski-sum math, and [`shapely`](https://shapely.readthedocs.io/) for general polygon geometry — the only two places in this project where our heroine (via Claude Code) chose to stand on a trusted library's shoulders rather than build from scratch, exactly because this particular sub-problem is a solved one elsewhere, unlike pyDome's actual specialty (geodesic subdivision math).

**Bottom-left-fill.** With NFPs in hand, Sheet-Nesting places the largest shapes first (so the big pieces claim their space before the small ones have to awkwardly fill in around them), and for each shape, tries a range of rotation angles — and mirrored orientations, unless a shape is flagged as mirror-sensitive — picking whichever valid position lands furthest to the left, then furthest to the bottom. Do that for every shape, spill onto a new sheet whenever nothing fits, and you have a nesting.

**The ghost hole.** While building this, Claude Code hit a genuinely subtle bug worth telling on: the very first hand-computable test case (two identically-sized squares) passed cleanly, so it looked safe to build on top of. A second test case — a small square swept around a much larger one — revealed that the underlying Clipper library doesn't actually hand back a clean, resolved shape; it hands back raw sweep geometry that, for mismatched shape sizes, includes an inner contour that *looks* like a hole in the result but mathematically cannot be one (the Minkowski sum of two solid convex shapes is always itself solid — there's no way to get a legitimate hole out of it). The first test case happened to be exactly the one size ratio where that spurious inner contour doesn't show up, so it didn't catch anything. The fix — union everything Clipper hands back as solid regions instead of trusting the library's own hole-marking convention — was confirmed against an independently-computed ground truth (the convex hull of every pairwise vertex sum, a completely different method for computing the same quantity) before being trusted. The lesson, which now lives in project memory for next time: one passing hand-computable test case is not enough — you have to vary the *proportions* of the case, not just try a second random one, before you can trust a geometry primitive.

**Chirality-aware mirroring.** pyDome's own panel Bill of Materials already flags when two "identical" triangular panels are actually mirror images of each other rather than true duplicates — relevant for directional materials like wood grain or a printed film. Sheet-Nesting's `allow_mirror` flag on each part plugs directly into that: set it to `false` for a chirality-sensitive shape, and the nester will only ever rotate it, never flip it, so the output never quietly asks you to cut a mirror image of a piece that specifically shouldn't be one.
# How It Connects to pyDome

The connection is deliberately shallow: a file, not an import statement. `pydome ... -T` writes one DXF cutting template per unique panel shape and reports exactly how many of each are needed; point a Sheet-Nesting job spec's `"dxf"` field at those files and `"quantity"` at those counts, and Sheet-Nesting will figure out how to actually lay them out on real stock. Neither project imports the other, and Sheet-Nesting's DXF importer has no idea (and no need to know) that a shape it's reading came from a geodesic dome rather than, say, a birdhouse or a cosplay prop. pyDome tells you what to cut; Sheet-Nesting tells you where to cut it from.
# Next Steps

* The bottom-left-fill candidate search isn't fully exhaustive — it considers NFP vertices, NFP-boundary crossings, and sheet corners, which is enough to perfectly tile trivially-tileable cases, but true full NFP-boundary tracing would occasionally find a tighter fit than the current heuristic does.
* A proper refinement pass on top of the base placement — simulated annealing or a genetic reordering of the placement sequence, the way more sophisticated nesting tools do — would likely close a meaningful chunk of the remaining gap between "good heuristic" and "actually optimal."
* Rectangular sheets only, for now. Real stock sometimes has irregular shape, existing cutouts, or is itself an offcut from a previous job — none of that is supported yet.
* Sheets are packed independently of each other, so leftover space on sheet one is never considered when starting sheet two. Reusing scrap across a whole job is a real efficiency gain left on the table.
* A preview image, the way pyDome can render a quick PNG of a dome before committing to an export, would make it a lot faster to sanity-check a nesting result without opening a DXF viewer.
# Conclusion

Our heroine now has a computer figuring out both *what* shapes her secret laboratory needs and *how to cut them out of the smallest possible pile of aluminum* — freeing her up to worry about the genuinely hard problems, like where exactly to hide the door.
# Works Consulted

* [`shapely`](https://shapely.readthedocs.io/). General-purpose 2D geometry: polygon area, bounds, intersection tests, and the union operation that resolved the Minkowski-sum ghost-hole bug described above.
* [`pyclipper`](https://github.com/fonttools/pyclipper). Python bindings to the Clipper polygon-clipping library, used for the underlying no-fit-polygon (Minkowski-sum) computation.
* The general family of bottom-left-fill, no-fit-polygon nesting algorithms as implemented by tools like SVGnest and DeepNest, which Sheet-Nesting's own heuristic follows the shape of (though its implementation is original, not ported from either).
# Code

Sheet-Nesting is available [here](https://github.com/badass-data-science/Engineering/tree/main/Sheet-Nesting).
# AI Use Statement

Unlike pyDome, which our heroine wrote by hand before bringing in Claude Code for refactoring and new features, Sheet-Nesting was designed and built collaboratively with Claude Code from a standing start: she scoped the requirements (a general-purpose tool, not a pyDome module; a real NFP-based nester, not a bounding-box approximation; ship a working MVP, not just a design doc) and reviewed the results, while Claude Code designed the module layout, implemented the algorithm, caught and fixed the Minkowski-sum bug described above, and wrote the test suite and this post's technical explanations.
# Tags

geodesic
nesting
bin packing
no-fit-polygon
NFP
laser cutting
CNC
sheet metal
DXF
Python
shapely
pyclipper
Claude Code
agentic AI
Ultimate Cunning Master Plan
