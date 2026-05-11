"""Admin hisobotlari uchun bir xil HTML sarlavhalar."""

from __future__ import annotations


def admin_section_title(
    emoji: str,
    title: str,
    *,
    count: int | None = None,
    page: tuple[int, int] | None = None,
) -> str:
    lines = [f"{emoji} <b>{title}</b>"]
    if count is not None:
        lines.append(f"<i>Jami yozuvlar: {count}</i>")
    if page is not None:
        a, b = page
        lines.append(f"<i>Qism {a}/{b}</i>")
    return "\n".join(lines)


def admin_empty_note(text: str) -> str:
    return f"<i>{text}</i>"
