# Architectural line plans

Top (X/Z, looking down −Y) and side (X/Y, looking toward −Z) drawings project canonical assembled mesh vertices, independently of 3D visibility or explosion. Default scope is timber plus plywood; temporary steel is an explicit optional layer, and roof reference envelopes are always excluded. The model is never mutated.

Feature edges use the existing welded/coplanar-edge filter. Hidden lines are classified by sampled edge segments against spatially indexed projected triangles; the optional dashed display is illustrative, not exact manufacturing hidden-line removal. Overall bounds and component axis extents are calculated from current meshes, not a manually redrawn model. Extents are not stock sizes or saw settings. Source/provisional status and unresolved ground/bearing heights remain explicit.

SVG downloads retain title, axes, units, warnings and a graphical scale bar. Paper size/zoom never implies a fixed print scale. Temporary steel hole/section geometry is illustrative, not drilling or fabrication data.

QA: deterministic projection/bounds/default-exclusion/non-mutation tests; viewer modal/repeated-open-close/navigation-pause regression; actual generated top and side SVGs rendered with Inkscape and PNGs visually inspected. No live browser QA was performed in this worktree.
