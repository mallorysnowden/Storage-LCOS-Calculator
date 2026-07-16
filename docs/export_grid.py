"""Export the precomputed landscape grid for the client-side (Tier 3) prototype.

Writes two files that the browser fetches once and then interpolates locally —
no Python server in the interaction loop:

  grid.f32  — float32 binary, C-order, THREE tensors concatenated in this order:
              new_lcos (Arctic), base_lcos (temperate), change_lcos (%)
              each of shape (nPow, nCost, nRate, nLife, nTech, nDD, nCPY).
              NaN marks infeasible (DD*2*CPY > 8760) cells and survives float32.

  meta.json — axes, DD/CPY plot values, tech names + colors, tensor shape.

Run:  uv run python tier3_prototype/export_grid.py   (from arctic_lcos_app/)
      or:  python tier3_prototype/export_grid.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
G = np.load(HERE.parent / "precomputed_landscape.npz", allow_pickle=False)

# Mirror core/engine.py TECH_COLORS (keyed by tech name).
TECH_COLORS = {
    "Hydrogen": "#2ca02c", "Pumped Hydro": "#1f77b4", "Li-Ion": "#d62728",
    "Compressed Air": "#e377c2", "Flywheel": "#9467bd",
}

new = G["new_lcos"].astype(np.float32)
base = G["base_lcos"].astype(np.float32)
change = G["change_lcos"].astype(np.float32)
assert new.shape == base.shape == change.shape

buf = np.concatenate([new.ravel(order="C"),
                      base.ravel(order="C"),
                      change.ravel(order="C")]).astype(np.float32)
(HERE / "grid.f32").write_bytes(buf.tobytes())

techs = [str(t) for t in G["TECHS"]]
meta = {
    "shape": [int(x) for x in new.shape],  # [nPow,nCost,nRate,nLife,nTech,nDD,nCPY]
    "power_axis": G["POWER_AXIS"].astype(float).tolist(),
    "cost_axis": G["POWERCOST_AXIS"].astype(float).tolist(),
    "rate_axis": G["RATE_AXIS"].astype(float).tolist(),      # fractions, e.g. 0.08
    "life_axis": G["LIFESPAN_AXIS"].astype(float).tolist(),
    "DD_values": G["DD_values"].astype(float).tolist(),
    "CPY_values": G["CPY_values"].astype(float).tolist(),
    "techs": techs,
    "colors": [TECH_COLORS[t] for t in techs],
}
(HERE / "meta.json").write_text(json.dumps(meta))

mb = (HERE / "grid.f32").stat().st_size / 1024 / 1024
print(f"wrote grid.f32: {mb:.2f} MB  (shape {new.shape}, 3 tensors)")
print(f"wrote meta.json: {len(techs)} techs")
