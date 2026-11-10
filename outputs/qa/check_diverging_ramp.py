"""Check the brief's diverging ramp: CIELAB lightness profile and adjacent-class colour differences
(CIE76 ΔE) for normal vision and simulated protanopia, deuteranopia and tritanopia (Machado et al. 2009,
severity 1.0). Run: uv run python outputs/qa/check_diverging_ramp.py"""
import numpy as np
RAMP = ["#1D4E6F", "#3B7CA6", "#8DBAD6", "#C9DDE9", "#F2EFE9", "#F6CBA6", "#F4A26B", "#D9542B", "#A1201A"]
M = {"protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
     "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
     "tritan": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]}
def lin(c): c = c / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lab(rgb_lin):
    X = rgb_lin @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    X = X / np.array([0.95047, 1.0, 1.08883])
    f = np.where(X > 216 / 24389, np.cbrt(X), (24389 / 27 * X + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)
rgb = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in RAMP], float)
L = lin(rgb)
for name, m in [("normal", np.eye(3))] + list(M.items()):
    lb = lab(np.clip(L @ np.array(m).T, 0, 1))
    de = np.linalg.norm(np.diff(lb, axis=0), axis=1)
    ends = np.linalg.norm(lb[1] - lb[7])
    print(f"{name:7s} L*: {' '.join(f'{v:4.0f}' for v in lb[:, 0])} | adjacent ΔE min {de.min():.1f} | ΔE(-4..-6 vs +4..+6 classes) {ends:.1f}")
