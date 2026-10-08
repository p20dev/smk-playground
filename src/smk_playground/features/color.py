"""Small deterministic sRGB -> OKLab -> OKLCH implementation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

ACHROMATIC_EPSILON = 1e-7
COLOR_IMPLEMENTATION = "internal-oklab-published-matrices-v1"
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class ConvertedColor:
    hex: str
    srgb_r: float
    srgb_g: float
    srgb_b: float
    oklab_l: float
    oklab_a: float
    oklab_b: float
    oklch_l: float
    oklch_c: float
    oklch_h_deg: float | None


def _linear_channel(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def hex_to_oklab(value: str) -> ConvertedColor:
    if not isinstance(value, str) or not HEX_RE.fullmatch(value):
        raise ValueError(f"Invalid #RRGGBB color: {value!r}")
    canonical = value.casefold()
    r = int(canonical[1:3], 16) / 255.0
    g = int(canonical[3:5], 16) / 255.0
    b = int(canonical[5:7], 16) / 255.0
    linear_r, linear_g, linear_b = map(_linear_channel, (r, g, b))

    l = 0.4122214708 * linear_r + 0.5363325363 * linear_g + 0.0514459929 * linear_b
    m = 0.2119034982 * linear_r + 0.6806995451 * linear_g + 0.1073969566 * linear_b
    s = 0.0883024619 * linear_r + 0.2817188376 * linear_g + 0.6299787005 * linear_b
    l_root = math.copysign(abs(l) ** (1 / 3), l)
    m_root = math.copysign(abs(m) ** (1 / 3), m)
    s_root = math.copysign(abs(s) ** (1 / 3), s)
    oklab_l = 0.2104542553 * l_root + 0.7936177850 * m_root - 0.0040720468 * s_root
    oklab_a = 1.9779984951 * l_root - 2.4285922050 * m_root + 0.4505937099 * s_root
    oklab_b = 0.0259040371 * l_root + 0.7827717662 * m_root - 0.8086757660 * s_root
    chroma, hue = oklab_to_oklch(oklab_l, oklab_a, oklab_b)[1:]
    return ConvertedColor(
        hex=canonical,
        srgb_r=r,
        srgb_g=g,
        srgb_b=b,
        oklab_l=oklab_l,
        oklab_a=oklab_a,
        oklab_b=oklab_b,
        oklch_l=oklab_l,
        oklch_c=chroma,
        oklch_h_deg=hue,
    )


def oklab_to_oklch(lightness: float, a: float, b: float) -> tuple[float, float, float | None]:
    chroma = math.hypot(a, b)
    if chroma < ACHROMATIC_EPSILON:
        return lightness, chroma, None
    return lightness, chroma, math.degrees(math.atan2(b, a)) % 360.0

