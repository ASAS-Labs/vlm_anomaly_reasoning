"""Plotting helpers: full-curve Plotly + HTML video/timeupdate bridge."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

import plotly.graph_objects as go
import streamlit.components.v1 as components


def series_values(seq: list[list[float]], series: str) -> list[float]:
    idx = 0 if series == "velocity" else 1
    return [row[idx] for row in seq]


def time_axis(n: int, hz: float) -> list[float]:
    return [i / hz for i in range(n)]


def y_label(series: str) -> str:
    return "Velocity (mph)" if series == "velocity" else "Heading (deg)"


VEL_Y_LO = 0.0
VEL_Y_HI = 20.0


def y_axis_range(ys: list[float], series: str) -> list[float] | None:
    """Nominal velocity scale is 0–20 mph; expand only if data exceeds it."""
    if series != "velocity" or not ys:
        return None
    data_lo = min(ys)
    data_hi = max(ys)
    return [min(VEL_Y_LO, data_lo), max(VEL_Y_HI, data_hi)]


def video_duration_seconds(video_path: Path) -> float | None:
    """Duration from container metadata (ffprobe), falling back to frames/fps."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            dur = float(out)
            if dur > 0:
                return dur
    except (OSError, ValueError, subprocess.CalledProcessError):
        pass
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=nb_frames,avg_frame_rate,r_frame_rate",
                "-of",
                "json",
                str(video_path),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        info = json.loads(out)
        stream = (info.get("streams") or [{}])[0]
        nb = stream.get("nb_frames")
        rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/0"
        num_s, den_s = rate.split("/", 1)
        fps = float(num_s) / float(den_s) if float(den_s) else 0.0
        if nb is not None and fps > 0:
            return float(nb) / fps
    except (OSError, ValueError, subprocess.CalledProcessError, IndexError, ZeroDivisionError):
        pass
    return None


def trim_sequence_to_duration(
    seq: list[list[float]],
    hz: float,
    duration_s: float | None,
) -> list[list[float]]:
    """Keep samples with t_i = i/hz within the video duration; drop the rest."""
    if not seq or duration_s is None or duration_s <= 0 or hz <= 0:
        return seq
    keep = [row for i, row in enumerate(seq) if (i / hz) <= duration_s + 1e-9]
    return keep if keep else seq[:1]


def build_figure(
    seq: list[list[float]],
    hz: float,
    series: str,
    cursor_t: float | None = None,
    *,
    height: int = 420,
    duration_s: float | None = None,
    video_path: Path | None = None,
) -> go.Figure:
    if duration_s is None and video_path is not None:
        duration_s = video_duration_seconds(video_path)
    seq = trim_sequence_to_duration(seq, hz, duration_s)
    ys = series_values(seq, series)
    xs = time_axis(len(ys), hz)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines+markers",
            name=series,
            line=dict(width=2),
            marker=dict(size=3),
        )
    )
    if cursor_t is not None and xs:
        t_max = xs[-1]
        t = max(0.0, min(float(cursor_t), t_max))
        fig.add_vline(x=t, line_width=2, line_dash="dash", line_color="#c0392b")
    yrange = y_axis_range(ys, series)
    xaxis: dict = {"title": "Time (s)"}
    if duration_s is not None and duration_s > 0:
        xaxis["range"] = [0.0, duration_s]
    fig.update_layout(
        margin=dict(l=40, r=10, t=10, b=30),
        height=height,
        xaxis=xaxis,
        yaxis_title=y_label(series),
        yaxis=dict(range=yrange) if yrange is not None else {},
        showlegend=False,
    )
    return fig


def render_synced_player(
    video_path: Path,
    seq: list[list[float]],
    hz: float,
    series: str,
    *,
    media_height: int = 420,
    height: int | None = None,
) -> None:
    """Embed HTML5 video + Plotly chart; cursor tracks video currentTime.

    ``height`` is accepted as an alias of ``media_height`` (Streamlit may keep a
    stale module signature across hot-reloads).
    """
    if height is not None:
        media_height = height
    duration_s = video_duration_seconds(video_path)
    seq = trim_sequence_to_duration(seq, hz, duration_s)
    ys = series_values(seq, series)
    xs = time_axis(len(ys), hz)
    video_b64 = base64.b64encode(video_path.read_bytes()).decode("ascii")
    ylabel = y_label(series)
    yrange = y_axis_range(ys, series)
    yaxis_obj: dict = {"title": ylabel}
    if yrange is not None:
        yaxis_obj["range"] = yrange
    xaxis_obj: dict = {"title": "Time (s)"}
    if duration_s is not None and duration_s > 0:
        xaxis_obj["range"] = [0.0, duration_s]
    yaxis_json = json.dumps(yaxis_obj)
    xaxis_json = json.dumps(xaxis_obj)
    xs_json = json.dumps(xs)
    ys_json = json.dumps(ys)
    iframe_height = media_height + 8
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    html, body {{ margin: 0; height: 100%; overflow: hidden; font-family: sans-serif; background: transparent; }}
    .row {{ display: flex; gap: 8px; align-items: stretch; height: {media_height}px; }}
    .col {{ flex: 1; min-width: 0; display: flex; }}
    video {{ width: 100%; height: 100%; object-fit: contain; background: #111; border-radius: 4px; }}
    #plot {{ width: 100%; height: 100%; }}
  </style>
</head>
<body>
  <div class="row">
    <div class="col">
      <video id="vid" controls playsinline autoplay muted loop src="data:video/mp4;base64,{video_b64}"></video>
    </div>
    <div class="col">
      <div id="plot"></div>
    </div>
  </div>
  <script>
    const xs = {xs_json};
    const ys = {ys_json};
    const tMax = xs.length ? xs[xs.length - 1] : 0;
    const layout = {{
      margin: {{l: 44, r: 8, t: 8, b: 32}},
      height: {media_height},
      xaxis: {xaxis_json},
      yaxis: {yaxis_json},
      shapes: []
    }};
    const data = [{{
      x: xs, y: ys, mode: "lines+markers",
      line: {{width: 2}}, marker: {{size: 3}},
      hovertemplate: "%{{x:.2f}}s: %{{y:.2f}}<extra></extra>"
    }}];
    Plotly.newPlot("plot", data, layout, {{responsive: true, displayModeBar: false}});

    function setCursor(t) {{
      const clamped = Math.max(0, Math.min(t, tMax));
      Plotly.relayout("plot", {{
        shapes: [{{
          type: "line",
          x0: clamped, x1: clamped,
          y0: 0, y1: 1, yref: "paper",
          line: {{color: "#c0392b", width: 2, dash: "dash"}}
        }}]
      }});
    }}

    const vid = document.getElementById("vid");
    vid.muted = true;
    vid.loop = true;
    vid.addEventListener("timeupdate", () => setCursor(vid.currentTime));
    vid.addEventListener("seeked", () => setCursor(vid.currentTime));
    setCursor(0);
    vid.play().catch(() => {{}});
  </script>
</body>
</html>
"""
    components.html(html, height=iframe_height, scrolling=False)
