"""
Generates a self-contained HTML dashboard: a calendar heatmap colored by
each day's dominant emotion, plus emotion totals. No internet needed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from emotions import all_emotions, emotion_color
from models import JournalEntry


def _daily_dominant_emotion(entries: list[JournalEntry]) -> dict[date, str]:
    by_day: dict[date, Counter] = defaultdict(Counter)
    for entry in entries:
        day = entry.timestamp.date()
        for emotion, score in entry.emotions.items():
            by_day[day][emotion] += score

    result = {}
    for day, counter in by_day.items():
        if counter and max(counter.values()) > 0:
            result[day] = counter.most_common(1)[0][0]
        else:
            result[day] = "neutral"
    return result


def _build_calendar_grid(dominant_by_day: dict[date, str], weeks: int = 26) -> str:
    today = datetime.now().date()
    start = today - timedelta(days=weeks * 7)
    start -= timedelta(days=(start.weekday() + 1) % 7)

    cells = []
    current = start
    while current <= today:
        emotion = dominant_by_day.get(current, None)
        color = emotion_color(emotion) if emotion else "#1e1e1e"
        title = f"{current.isoformat()}: {emotion or 'no entry'}"
        cells.append((current, color, title))
        current += timedelta(days=1)

    columns = [cells[i:i + 7] for i in range(0, len(cells), 7)]

    col_html = []
    for col in columns:
        day_cells = "".join(
            f'<div class="cell" style="background:{color}" title="{title}"></div>'
            for _, color, title in col
        )
        col_html.append(f'<div class="week">{day_cells}</div>')

    return "".join(col_html)


def _emotion_totals(entries: list[JournalEntry]) -> dict[str, float]:
    totals: Counter = Counter()
    for entry in entries:
        for emotion, score in entry.emotions.items():
            totals[emotion] += score
    return dict(totals)


def generate_dashboard_html(entries: list[JournalEntry], output_path: str = "dashboard.html") -> str:
    dominant_by_day = _daily_dominant_emotion(entries)
    calendar_html = _build_calendar_grid(dominant_by_day)
    totals = _emotion_totals(entries)

    max_total = max(totals.values()) if totals else 1
    bars_html = ""
    for emotion, total in sorted(totals.items(), key=lambda kv: -kv[1]):
        pct = (total / max_total) * 100 if max_total else 0
        bars_html += f"""
        <div class="bar-row">
            <span class="bar-label">{emotion}</span>
            <div class="bar-track">
                <div class="bar-fill" style="width:{pct:.1f}%; background:{emotion_color(emotion)}"></div>
            </div>
            <span class="bar-value">{total:.1f}</span>
        </div>"""

    legend_html = "".join(
        f'<span class="legend-item"><span class="dot" style="background:{emotion_color(e)}"></span>{e}</span>'
        for e in all_emotions() + ["neutral"]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Journal Emotion Dashboard</title>
<style>
    body {{ background: #121212; color: #e8e8e8; font-family: -apple-system, Segoe UI, Roboto, sans-serif; padding: 40px; max-width: 900px; margin: 0 auto; }}
    h1 {{ font-weight: 600; margin-bottom: 4px; }}
    .subtitle {{ color: #999; margin-bottom: 32px; }}
    .section {{ margin-bottom: 40px; }}
    .section h2 {{ font-size: 16px; text-transform: uppercase; letter-spacing: 0.05em; color: #aaa; margin-bottom: 16px; }}
    .calendar {{ display: flex; gap: 3px; overflow-x: auto; padding-bottom: 8px; }}
    .week {{ display: flex; flex-direction: column; gap: 3px; }}
    .cell {{ width: 12px; height: 12px; border-radius: 2px; }}
    .legend {{ display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 13px; color: #ccc; text-transform: capitalize; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    .bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
    .bar-label {{ width: 80px; text-transform: capitalize; font-size: 14px; color: #ccc; }}
    .bar-track {{ flex: 1; background: #262626; border-radius: 4px; height: 14px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}
    .bar-value {{ width: 40px; text-align: right; font-size: 13px; color: #999; }}
</style>
</head>
<body>
    <h1>Your Emotional Landscape</h1>
    <div class="subtitle">{len(entries)} entries analyzed &middot; generated {datetime.now():%Y-%m-%d %H:%M}</div>

    <div class="section">
        <h2>Calendar (last 26 weeks)</h2>
        <div class="calendar">{calendar_html}</div>
        <div class="legend">{legend_html}</div>
    </div>

    <div class="section">
        <h2>Emotion totals</h2>
        {bars_html if bars_html else '<p style="color:#777">Not enough data yet - write a few entries first.</p>'}
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path