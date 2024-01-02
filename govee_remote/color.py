from __future__ import annotations

from matplotlib.colors import CSS4_COLORS


RGB = tuple[int, int, int]


def get_color(name: str) -> RGB:
    name = name.lower()
    if name not in CSS4_COLORS:
        raise ValueError(f"Unknown color: {name}")
    val = CSS4_COLORS[name]
    r, g, b = (int(val[i : i + 2], 16) for i in range(1, 7, 2))
    return r, g, b


def get_luma(rgb: RGB) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
