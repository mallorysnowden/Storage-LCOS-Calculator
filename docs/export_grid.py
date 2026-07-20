"""Export the precomputed grid for the static client-side calculator.

Reads ../precomputed_landscape.npz and writes into this folder:

  landscape.f32.gz -- EAGER (fetched on page open). Tensors: base_lcos, new_lcos
                      (temperate / Arctic LCOS, USD/kWh). Interpolated client-side
                      (log-power + linear cost/rate/life) for the winner maps.
  lifetime.f32.gz  -- LAZY (fetched when the Lifetime Cost tab opens). Tensors:
                      capex_base, capex_arctic, repl_base, repl_arctic,
                      contrib_0..7 (signed %-point contributions), and
                      arctic_lcos_dlo / arctic_lcos_dhi (the Arctic-LCOS
                      uncertainty band as absolute $/kWh deltas from new_lcos).
  meta.json        -- axes, DD/CPY values, techs + colors, factors, tensor order,
                      shape.

All tensors float32, C-order, gzipped (GitHub Pages won't gzip a binary, so we
ship .gz and inflate with DecompressionStream in JS).

Run (from arctic_lcos_app/):  python tier3_prototype/export_grid.py
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
G = np.load(HERE.parent / "precomputed_landscape.npz", allow_pickle=False)

TECH_COLORS = {
    "Hydrogen": "#2ca02c", "Pumped Hydro": "#1f77b4", "Li-Ion": "#d62728",
    "Compressed Air": "#e377c2", "Flywheel": "#9467bd",
}
techs = [str(t) for t in G["TECHS"]]
factors = [str(f) for f in G["FACTORS"]]

LANDSCAPE = ["base_lcos", "new_lcos"]
LIFETIME = (["capex_base", "capex_arctic", "repl_base", "repl_arctic",
             "D_base", "D_arctic"]
            + [f"contrib_{i}" for i in range(len(factors))]
            + ["arctic_lcos_dlo", "arctic_lcos_dhi"])


def write_gz(path, names):
    raw = np.concatenate([G[n].astype(np.float32).ravel(order="C")
                          for n in names]).astype(np.float32).tobytes()
    blob = gzip.compress(raw, 9)
    path.write_bytes(blob)
    return len(raw), len(blob)


l_raw, l_gz = write_gz(HERE / "landscape.f32.gz", LANDSCAPE)
c_raw, c_gz = write_gz(HERE / "lifetime.f32.gz", LIFETIME)

shape = [int(x) for x in G["base_lcos"].shape]
meta = {
    "shape": shape,
    "power_axis": G["POWER_AXIS"].astype(float).tolist(),
    "cost_axis": G["POWERCOST_AXIS"].astype(float).tolist(),
    "rate_axis": G["RATE_AXIS"].astype(float).tolist(),
    "life_axis": G["LIFESPAN_AXIS"].astype(float).tolist(),
    "DD_values": G["DD_values"].astype(float).tolist(),
    "CPY_values": G["CPY_values"].astype(float).tolist(),
    "techs": techs,
    "colors": [TECH_COLORS[t] for t in techs],
    "factors": factors,
    "landscape_tensors": LANDSCAPE,
    "lifetime_tensors": LIFETIME,
}
(HERE / "meta.json").write_text(json.dumps(meta))

mb = lambda b: b / 1024 / 1024
print(f"landscape.f32.gz: {mb(l_gz):.2f} MB gz (raw {mb(l_raw):.1f} MB, {LANDSCAPE})")
print(f"lifetime.f32.gz : {mb(c_gz):.2f} MB gz (raw {mb(c_raw):.1f} MB, {len(LIFETIME)} tensors)")
print(f"meta.json       : shape {shape}")
