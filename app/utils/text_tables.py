"""Monospace tables for Telegram HTML (<pre>)."""

from __future__ import annotations


def _pad(s: str, width: int) -> str:
    t = (s or "").replace("\n", " ").replace("\t", " ")
    if len(t) > width:
        t = t[: max(0, width - 1)] + "…"
    return t.ljust(width)


def html_pre_table(headers: list[str], widths: list[int], rows: list[list[str]]) -> str:
    sep = "+" + "+".join("-" * w for w in widths) + "+"
    head = "|" + "|".join(_pad(h, w) for h, w in zip(headers, widths)) + "|"
    body_lines = [
        "|" + "|".join(_pad(c, w) for c, w in zip(row, widths)) + "|" for row in rows
    ]
    inner = "\n".join([sep, head, sep, *body_lines, sep])
    return f"<pre>{inner}</pre>"


def html_pre_tables_batched(
    headers: list[str],
    widths: list[int],
    rows: list[list[str]],
    *,
    batch_size: int = 25,
) -> list[str]:
    if not rows:
        return [html_pre_table(headers, widths, [])]
    return [
        html_pre_table(headers, widths, rows[i : i + batch_size])
        for i in range(0, len(rows), batch_size)
    ]
