"""Gas-mixture rules (vectorised over rows).

Viscosity: Wilke form, NASA RP-1311 (Gordon & McBride 1994, CEA Part I) Eqs. (5.3) and (5.5).
Frozen thermal conductivity: same form with psi_ij, RP-1311 Eqs. (5.4) and (5.6) (Mason-Saxena type).
Eq. (5.5) is algebraically identical to the Wilke Phi_ij in docs/FORMULAS.md section 1:
(1/4) * sqrt(2 M_j / (M_i + M_j)) = 1 / sqrt(8 (1 + M_i / M_j)).
The sums in the denominators run over j != i (the i-th term is the explicit x_i).
cp of the mixture: mass-fraction weighted (FORMULAS.md section 1).
Inputs: mole fractions as a 2-D array (rows x species), species order given by ``species``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .properties import gas_prop, molar_mass


def mass_fractions(x: np.ndarray, species: list[str]) -> np.ndarray:
    M = np.array([molar_mass(s) for s in species])
    w = x * M
    return w / w.sum(axis=1, keepdims=True)


def mixture_molar_mass(x: np.ndarray, species: list[str]) -> np.ndarray:
    """M_mix = sum x_i M_i [kg/mol]."""
    M = np.array([molar_mass(s) for s in species])
    return (x * M).sum(axis=1)


def _phi(mu: np.ndarray, M: np.ndarray) -> np.ndarray:
    """phi_ij (RP-1311 Eq. 5.5) for each row: shape (rows, n, n)."""
    mi, mj = mu[:, :, None], mu[:, None, :]
    Mi, Mj = M[None, :, None], M[None, None, :]
    return 0.25 * (1 + np.sqrt(mi / mj) * (Mj / Mi) ** 0.25) ** 2 * np.sqrt(2 * Mj / (Mi + Mj))


def _mix(x: np.ndarray, prop: np.ndarray, inter: np.ndarray) -> np.ndarray:
    n = x.shape[1]
    off = ~np.eye(n, dtype=bool)
    denom = x + np.einsum("rij,rj->ri", inter * off[None], x)
    with np.errstate(invalid="ignore", divide="ignore"):
        terms = np.where(x > 0, x * prop / denom, 0.0)
    return terms.sum(axis=1)


def mixture_viscosity(x: np.ndarray, species: list[str], T: ArrayLike) -> np.ndarray:
    """eta_mix [Pa s] at temperature T [K] (RP-1311 Eqs. 5.3, 5.5)."""
    T = np.broadcast_to(np.asarray(T, dtype=float), (x.shape[0],))
    mu = np.stack([gas_prop(s, "mu", T) for s in species], axis=1)
    M = np.array([molar_mass(s) for s in species])
    return _mix(x, mu, _phi(mu, M))


def mixture_conductivity(x: np.ndarray, species: list[str], T: ArrayLike) -> np.ndarray:
    """Frozen lambda_mix [W/(m K)] at T [K] (RP-1311 Eqs. 5.4, 5.6)."""
    T = np.broadcast_to(np.asarray(T, dtype=float), (x.shape[0],))
    mu = np.stack([gas_prop(s, "mu", T) for s in species], axis=1)
    k = np.stack([gas_prop(s, "k", T) for s in species], axis=1)
    M = np.array([molar_mass(s) for s in species])
    phi = _phi(mu, M)
    Mi, Mj = M[None, :, None], M[None, None, :]
    psi = phi * (1 + 2.41 * (Mi - Mj) * (Mi - 0.142 * Mj) / (Mi + Mj) ** 2)
    return _mix(x, k, psi)


def mixture_cp(x: np.ndarray, species: list[str], T: ArrayLike) -> np.ndarray:
    """cp_mix [J/(kg K)] = sum Y_i cp_i(T)."""
    T = np.broadcast_to(np.asarray(T, dtype=float), (x.shape[0],))
    Y = mass_fractions(x, species)
    cp = np.stack([gas_prop(s, "cp", T) for s in species], axis=1)
    return (Y * cp).sum(axis=1)
