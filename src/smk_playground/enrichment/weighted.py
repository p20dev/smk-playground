"""Weighted enrichment palette parsing, features, and exact palette transport."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from smk_playground.features.color import HEX_RE, hex_to_oklab
from smk_playground.features.extract import palette_features

TOKEN_RE = re.compile(r"\S+")


def parse_weighted_palette(raw: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(raw, str) or not raw.strip():
        return [], {"status": "missing", "token_count": 0, "valid_token_count": 0,
                    "invalid_tokens": [], "unique_color_count": 0}
    tokens = TOKEN_RE.findall(raw)
    valid = [token.casefold() for token in tokens if HEX_RE.fullmatch(token)]
    invalid = [token for token in tokens if not HEX_RE.fullmatch(token)]
    if not valid:
        return [], {"status": "malformed", "token_count": len(tokens),
                    "valid_token_count": 0, "invalid_tokens": invalid,
                    "unique_color_count": 0}
    counts = Counter(valid)
    first_positions = {color: valid.index(color) for color in counts}
    ordered = sorted(counts, key=lambda color: first_positions[color])
    total = len(valid)
    rows = []
    for rank, color in enumerate(ordered, 1):
        converted = hex_to_oklab(color)
        rows.append({
            "palette_rank": rank, "hex": color, "token_count": counts[color],
            "weight": counts[color] / total, "srgb_r": converted.srgb_r,
            "srgb_g": converted.srgb_g, "srgb_b": converted.srgb_b,
            "oklab_l": converted.oklab_l, "oklab_a": converted.oklab_a,
            "oklab_b": converted.oklab_b, "oklch_l": converted.oklch_l,
            "oklch_c": converted.oklch_c, "oklch_h_deg": converted.oklch_h_deg,
        })
    status = "valid" if not invalid else "partial_invalid"
    return rows, {"status": status, "token_count": len(tokens),
                  "valid_token_count": total, "invalid_tokens": invalid,
                  "unique_color_count": len(rows)}


def weighted_features(palette: list[dict[str, Any]]) -> dict[str, Any]:
    features, flags = palette_features(palette)
    entropy = -math.fsum(row["weight"] * math.log(row["weight"])
                         for row in palette if row["weight"] > 0)
    dominant = max(palette, key=lambda row: (row["weight"], -row["palette_rank"])) if palette else None
    return {
        **features, "palette_entropy": entropy if palette else None,
        "dominant_color_weight": dominant["weight"] if dominant else None,
        "dominant_color_hex": dominant["hex"] if dominant else None,
        "feature_quality_flags": flags,
    }


def palette_transport_distance(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> float:
    """Exact min-cost flow between two tiny weighted palettes in OKLab."""
    if not left or not right:
        raise ValueError("Palette transport requires two non-empty palettes")
    left_weights = [float(row["weight"]) for row in left]
    right_weights = [float(row["weight"]) for row in right]
    if not math.isclose(math.fsum(left_weights), 1.0, abs_tol=1e-9):
        raise ValueError("Left palette weights must sum to one")
    if not math.isclose(math.fsum(right_weights), 1.0, abs_tol=1e-9):
        raise ValueError("Right palette weights must sum to one")
    costs = [[math.sqrt(
        (a["oklab_l"] - b["oklab_l"]) ** 2
        + (a["oklab_a"] - b["oklab_a"]) ** 2
        + (a["oklab_b"] - b["oklab_b"]) ** 2
    ) for b in right] for a in left]
    n_left, n_right = len(left), len(right)
    source = n_left + n_right
    sink = source + 1
    size = sink + 1
    graph: list[list[dict[str, float | int]]] = [[] for _ in range(size)]

    def add_edge(start: int, end: int, capacity: float, cost: float) -> None:
        forward = {"to": end, "reverse": len(graph[end]), "capacity": capacity, "cost": cost}
        reverse = {"to": start, "reverse": len(graph[start]), "capacity": 0.0, "cost": -cost}
        graph[start].append(forward)
        graph[end].append(reverse)

    for i, weight in enumerate(left_weights):
        add_edge(source, i, weight, 0.0)
    for i in range(n_left):
        for j in range(n_right):
            add_edge(i, n_left + j, 1.0, costs[i][j])
    for j, weight in enumerate(right_weights):
        add_edge(n_left + j, sink, weight, 0.0)

    total_cost = 0.0
    remaining = 1.0
    while remaining > 1e-12:
        distance = [math.inf] * size
        parent: list[tuple[int, int] | None] = [None] * size
        distance[source] = 0.0
        for _ in range(size - 1):
            changed = False
            for node, edges in enumerate(graph):
                if distance[node] == math.inf:
                    continue
                for edge_index, edge in enumerate(edges):
                    if float(edge["capacity"]) <= 1e-12:
                        continue
                    target = int(edge["to"])
                    candidate = distance[node] + float(edge["cost"])
                    if candidate < distance[target] - 1e-15:
                        distance[target] = candidate
                        parent[target] = (node, edge_index)
                        changed = True
            if not changed:
                break
        if parent[sink] is None:
            raise RuntimeError("No augmenting palette-transport path")
        amount = remaining
        node = sink
        while node != source:
            previous, edge_index = parent[node]
            amount = min(amount, float(graph[previous][edge_index]["capacity"]))
            node = previous
        node = sink
        while node != source:
            previous, edge_index = parent[node]
            edge = graph[previous][edge_index]
            reverse = graph[node][int(edge["reverse"])]
            edge["capacity"] = float(edge["capacity"]) - amount
            reverse["capacity"] = float(reverse["capacity"]) + amount
            total_cost += amount * float(edge["cost"])
            node = previous
        remaining -= amount
    return max(0.0, total_cost)
