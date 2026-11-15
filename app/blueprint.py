"""Engineering-drawing rendering of a module wall (ADR-056): flat material fills with CAD hatching, region outlines,
a 10 cm / 50 cm grid. One image is used by the wall editor, the fire animation and the design maps, so all of them look
like the same drawing. Display only - no physics here.
"""

from __future__ import annotations

import base64
import io

import numpy as np

PX = 12  # image pixels per 10 cm cell
OPEN = (11, 20, 38)
FILL = {"F": (150, 122, 78), "A": (52, 120, 150), "M": (86, 96, 116), "H": (30, 150, 92)}
EDGE = {"F": (236, 200, 140), "A": (140, 225, 255), "M": (176, 188, 210), "H": (120, 255, 170)}
LABEL = {"F": "fabric", "A": "acrylic", "M": "metal", ".": "open", "H": "hatch"}


def render_rgb(layout: np.ndarray, px: int = PX) -> np.ndarray:
    """RGB image (h*px, w*px, 3) of the wall drawn as an engineering sheet."""
    h, w = layout.shape
    codes = np.repeat(np.repeat(np.asarray(layout, dtype="U1"), px, axis=0), px, axis=1)
    H, W = codes.shape
    img = np.empty((H, W, 3), dtype=np.float32)
    img[:] = OPEN
    yy, xx = np.indices((H, W))
    # drawing grid: 10 cm minor, 50 cm major, 1 m strong (faint blueprint lines on open space)
    minor = (xx % px == 0) | (yy % px == 0)
    major = (xx % (5 * px) == 0) | (yy % (5 * px) == 0)
    metre = (xx % (10 * px) == 0) | (yy % (10 * px) == 0)
    img[minor] += np.array([10, 16, 30])
    img[major] += np.array([16, 26, 46])
    img[metre] += np.array([18, 30, 54])
    for code, col in FILL.items():
        m = codes == code
        img[m] = col
        if code == "F":  # soft goods: 45 degree hatch
            img[m & ((xx + yy) % 8 == 0)] = np.array(col) * 1.28
        elif code == "A":  # glazing: sparse double diagonal
            d = (xx - yy) % 18
            img[m & ((d == 0) | (d == 3))] = np.array(col) * 1.55
        elif code == "M":  # structure: fine horizontal lines
            img[m & (yy % 4 == 0)] = np.array(col) * 1.22
        elif code == "H":  # hatch: vertical stripes
            img[m & (xx % 6 < 2)] = np.array(col) * 1.25
    # region outlines: a pixel on the boundary between two different materials takes its own material's edge colour
    edge = np.zeros((H, W), dtype=bool)
    edge[:, :-1] |= codes[:, :-1] != codes[:, 1:]
    edge[:, 1:] |= codes[:, 1:] != codes[:, :-1]
    edge[:-1, :] |= codes[:-1, :] != codes[1:, :]
    edge[1:, :] |= codes[1:, :] != codes[:-1, :]
    for code, col in EDGE.items():
        img[edge & (codes == code)] = col
    return np.clip(img, 0, 255).astype(np.uint8)


def png_b64(rgb: np.ndarray) -> str:
    from PIL import Image

    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def data_uri(layout: np.ndarray, px: int = PX) -> str:
    return "data:image/png;base64," + png_b64(render_rgb(layout, px))
