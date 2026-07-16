# Arctic Energy Storage LCOS Calculator — web app

Static, client-side interactive version of the Competitive Landscape from
*A Technoeconomic Assessment of Energy Storage Potential in Arctic Grid Systems*
(Snowden, 2025). Hosted via GitHub Pages from this `docs/` folder.

All interpolation runs in the browser — there is no server. Moving a slider
re-interpolates the precomputed LCOS grid locally and redraws, so updates are
real-time.

## Files
- `index.html` — the app (raw Plotly + a 4-D linear interpolator over the grid).
- `grid.f32` — precomputed LCOS tensors (new/base/change), float32, C-order.
- `meta.json` — grid axes, DD/CPY plot values, tech names and colors.
- `export_grid.py` — regenerates `grid.f32` + `meta.json` from the source
  `precomputed_landscape.npz` produced by the modeling pipeline.

## Regenerating the grid
Run the modeling app's `precompute_grid.py` to (re)build `precomputed_landscape.npz`,
then `python export_grid.py` to refresh `grid.f32` and `meta.json` here.
