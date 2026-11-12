"""Estimate Zdiff on an ideal section of the PixGate USB pair.

Run with Python, NumPy and SciPy. The electrostatic model uses antisymmetry,
a continuous opposite ground plane and optional coplanar ground on both
sides. It omits solder mask, trace tapers, vias and breaks in the ground
pour. Results describe the nominal cross-section only.
"""
import numpy as np
from scipy.constants import c, epsilon_0
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

CORE_THICKNESS = 1.51
CORE_PERMITTIVITY = 4.5
COPPER_THICKNESS = 0.035
TRACE_WIDTH = 0.25
PAIR_GAP = 0.25
COPLANAR_GAP = 0.25
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def capacitance(step, dielectric, coplanar):
    x_axis = np.arange(0, 4 + step / 2, step)
    y_axis = np.arange(-round(CORE_THICKNESS / step) * step, 2 + step / 2, step)
    x, y = np.meshgrid(x_axis, y_axis)
    tolerance = step / 10
    metal = (y >= -tolerance) & (y < COPPER_THICKNESS - tolerance)
    signal_start = PAIR_GAP / 2
    signal_end = signal_start + TRACE_WIDTH
    signal = metal & (x >= signal_start - tolerance) & (x < signal_end - tolerance)

    # The symmetry axis and the outer boundaries are at zero volts.
    fixed = signal.copy()
    fixed[:, [0, -1]] = True
    fixed[[0, -1], :] = True
    if coplanar:
        fixed |= metal & (x >= signal_end + COPLANAR_GAP - tolerance)

    voltage = np.zeros(x.shape)
    voltage[signal] = 0.5
    permittivity = np.where(y < 0, dielectric, 1.0)
    unknown = np.full(x.shape, -1)
    unknown[~fixed] = np.arange((~fixed).sum())
    row, col = np.where(~fixed)
    diagonal = np.zeros(len(row))
    right_hand_side = np.zeros(len(row))
    matrix_rows, matrix_cols, coefficients = [], [], []

    def interface(row, col, adj_row, adj_col):
        here = permittivity[row, col]
        there = permittivity[adj_row, adj_col]
        return 2 * here * there / (here + there)

    for dy, dx in NEIGHBORS:
        adj_row, adj_col = row + dy, col + dx
        weight = interface(row, col, adj_row, adj_col)
        diagonal += weight
        boundary = fixed[adj_row, adj_col]
        right_hand_side[boundary] += weight[boundary] * voltage[adj_row[boundary], adj_col[boundary]]
        matrix_rows.extend(unknown[row[~boundary], col[~boundary]])
        matrix_cols.extend(unknown[adj_row[~boundary], adj_col[~boundary]])
        coefficients.extend(-weight[~boundary])

    matrix_rows.extend(unknown[row, col])
    matrix_cols.extend(unknown[row, col])
    coefficients.extend(diagonal)
    matrix = coo_matrix((coefficients, (matrix_rows, matrix_cols)), shape=(len(row), len(row)))
    voltage[row, col] = spsolve(matrix.tocsc(), right_hand_side)

    row, col = np.where(signal)
    charge = 0.0
    for dy, dx in NEIGHBORS:
        adj_row, adj_col = row + dy, col + dx
        charge += np.sum(interface(row, col, adj_row, adj_col) * (0.5 - voltage[adj_row, adj_col]))
    # The two signal voltages are +0.5 V and -0.5 V, so Q / Vdiff = Q.
    return charge * epsilon_0


def main():
    for step in (0.025, 0.0125):
        for coplanar in (True, False):
            air = capacitance(step, 1.0, coplanar)
            loaded = capacitance(step, CORE_PERMITTIVITY, coplanar)
            differential_impedance = 1 / (c * np.sqrt(air * loaded))
            print(f"Malha {step} mm, GND lateral {coplanar}: {differential_impedance:.1f} Ω")


if __name__ == "__main__":
    main()
