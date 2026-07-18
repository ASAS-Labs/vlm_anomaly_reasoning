"""Streamlit app: manual validation of inverse-dynamics trajectories.

Run from repo root:

    uv run --group validation streamlit run data/cosmos3/data_validation/app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from io_utils import (
    COL_COMMENT,
    COL_HEURISTIC,
    COL_LABEL,
    discover_videos,
    find_repo_root,
    hz_for_mode,
    list_browsable_folders,
    load_csv,
    load_skip_filenames,
    load_trajectory,
    lookup_row,
    parse_flags_file,
    resolve_under_root,
    trajectory_path,
    upsert_csv,
)
from plotting import build_figure, render_synced_player
from prompt_utils import prompt_sentence_for

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(SCRIPT_DIR)
GENERATED_VIDS_DIR = REPO_ROOT / "data/datasets/generated_vids"
PROMPTS_ROOT = Path(
    os.environ.get("PROMPTS_ROOT", REPO_ROOT / "data/cosmos3/video_gen_prompts")
)
FLAGS_PATH = GENERATED_VIDS_DIR / "inverse_dynamics_flags.txt"
CSV_PATH = SCRIPT_DIR / "inverse_dynamics_filter.csv"
NEG_SKIP_PATH = SCRIPT_DIR / "negative_scenarios_variants_filter.csv"
POS_SKIP_PATH = SCRIPT_DIR / "positive_scenarios_variants_filter.csv"
NEG_VARIANTS_DIR = "negative_scenarios_variants"
POS_VARIANTS_DIR = "positive_scenarios_variants"


def _init_state() -> None:
    defaults = {
        "folder_rel": "final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered",
        "video_paths": [],
        "index": 0,
        "traj_mode": "downsampled",
        "series": "velocity",
        "comment": "",
        "comment_for_index": None,  # which index `comment` was last synced for
        "csv_df": load_csv(CSV_PATH),
        "flag_map": parse_flags_file(FLAGS_PATH),
        "skip_neg": load_skip_filenames(NEG_SKIP_PATH),
        "skip_pos": load_skip_filenames(POS_SKIP_PATH),
        "loaded": False,
        "status_msg": "",
        "pending_toasts": [],
        "folder_picker_open": False,
        "browse_folder_choice": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _current_rel() -> Path | None:
    paths = st.session_state.video_paths
    if not paths:
        return None
    i = st.session_state.index
    if i < 0 or i >= len(paths):
        return None
    return paths[i]


def _should_skip(rel: Path) -> bool:
    """True if this variants video's filename is on the matching skip list."""
    parts = rel.parts
    name = rel.name
    if NEG_VARIANTS_DIR in parts:
        return name in st.session_state.skip_neg
    if POS_VARIANTS_DIR in parts:
        return name in st.session_state.skip_pos
    return False


def _find_nonskip_index(start: int, direction: int) -> tuple[int | None, list[str]]:
    """Walk from start in direction; return first non-skip index and skipped names."""
    paths = st.session_state.video_paths
    n = len(paths)
    i = start
    skipped: list[str] = []
    while 0 <= i < n:
        rel = paths[i]
        if not _should_skip(rel):
            return i, skipped
        skipped.append(rel.name)
        i += direction
    return None, skipped


def _sync_comment_from_csv(rel: Path) -> None:
    """Load comment for rel. Must run before the Comment widget exists."""
    rel_posix = rel.as_posix()
    row = lookup_row(st.session_state.csv_df, rel_posix)
    if row is None:
        st.session_state.comment = ""
    else:
        st.session_state.comment = row[COL_COMMENT]
        label = row[COL_LABEL]
        msg = f"Already in CSV ({label})." if label else "Already in CSV."
        _queue_toast(msg)


def _ensure_comment_synced() -> None:
    """Sync comment from CSV when the video index changes (pre-widget)."""
    paths = st.session_state.video_paths
    if not paths:
        return
    i = st.session_state.index
    if st.session_state.comment_for_index == i:
        return
    _sync_comment_from_csv(paths[i])
    st.session_state.comment_for_index = i


def _queue_toast(message: str) -> None:
    st.session_state.pending_toasts.append(message)


def _play_toast_sound(n: int = 1) -> None:
    """Short beep(s) via Web Audio API (works after a user gesture)."""
    n = max(1, min(int(n), 5))
    components.html(
        f"""
        <script>
        (function() {{
          const n = {n};
          const AC = window.AudioContext || window.webkitAudioContext;
          if (!AC) return;
          const ctx = new AC();
          for (let i = 0; i < n; i++) {{
            const t0 = ctx.currentTime + i * 0.12;
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.type = "sine";
            o.frequency.value = 880;
            g.gain.setValueAtTime(0.0001, t0);
            g.gain.exponentialRampToValueAtTime(0.12, t0 + 0.02);
            g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.18);
            o.connect(g);
            g.connect(ctx.destination);
            o.start(t0);
            o.stop(t0 + 0.2);
          }}
          setTimeout(() => ctx.close(), 500 + n * 120);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def _flush_toasts() -> None:
    msgs = list(st.session_state.pending_toasts)
    st.session_state.pending_toasts = []
    if not msgs:
        return
    for msg in msgs:
        st.toast(msg)
    _play_toast_sound(len(msgs))


def _emit_skip_toast(skipped: list[str]) -> None:
    if not skipped:
        return
    if len(skipped) == 1:
        msg = f"Skipped {skipped[0]} (on filter list)."
    else:
        msg = f"Skipped {len(skipped)} filtered video(s): {', '.join(skipped)}."
    _queue_toast(msg)


def _navigate(direction: int) -> None:
    """Move one step in direction, skipping filter-listed variants; toast at ends."""
    paths = st.session_state.video_paths
    if not paths:
        return
    n = len(paths)
    start = st.session_state.index + direction
    if direction > 0 and start >= n:
        _queue_toast("End of folder — no next video.")
        return
    if direction < 0 and start < 0:
        _queue_toast("Start of folder — no previous video.")
        return
    target, skipped = _find_nonskip_index(start, direction)
    _emit_skip_toast(skipped)
    if target is None:
        if direction > 0:
            _queue_toast("End of folder — no next video.")
        else:
            _queue_toast("Start of folder — no previous video.")
        return
    st.session_state.index = target
    st.session_state.comment_for_index = None


def _set_index(new_index: int, *, direction: int | None = None) -> None:
    """Jump to new_index (e.g. on Load), auto-skipping filter-listed variants."""
    paths = st.session_state.video_paths
    if not paths:
        return
    n = len(paths)
    old = st.session_state.index
    if direction is None:
        direction = 1 if new_index >= old else -1
    start = max(0, min(new_index, n - 1))
    target, skipped = _find_nonskip_index(start, direction)
    if target is None:
        edge = n - 1 if direction > 0 else 0
        target, skipped_back = _find_nonskip_index(edge, -direction)
        skipped = skipped + skipped_back
        if target is None:
            st.session_state.index = start
            st.session_state.comment_for_index = None
            _emit_skip_toast(skipped)
            return
    st.session_state.index = target
    st.session_state.comment_for_index = None
    _emit_skip_toast(skipped)


def _install_arrow_key_shortcuts() -> None:
    """Left/Right arrows click Prev/Next (ignored while typing in inputs)."""
    components.html(
        """
        <script>
        (function() {
          const w = window.parent;
          if (w.__idValArrowNavInstalled) return;
          w.__idValArrowNavInstalled = true;
          w.document.addEventListener('keydown', function(e) {
            const t = e.target;
            if (t && (t.closest('input, textarea, select, [contenteditable="true"]'))) {
              return;
            }
            if (e.key === 'ArrowLeft') {
              const prev = w.document.querySelector('div.st-key-nav_prev button');
              if (prev) { e.preventDefault(); prev.click(); }
            } else if (e.key === 'ArrowRight') {
              const next = w.document.querySelector('div.st-key-nav_next button');
              if (next) { e.preventDefault(); next.click(); }
            }
          });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def _load_folder() -> None:
    folder = resolve_under_root(GENERATED_VIDS_DIR, st.session_state.folder_rel)
    if folder is None:
        st.session_state.video_paths = []
        st.session_state.loaded = False
        st.session_state.comment_for_index = None
        st.session_state.status_msg = (
            "Invalid folder: must exist under data/datasets/generated_vids "
            "(no '..' path segments)."
        )
        return
    videos = discover_videos(folder, GENERATED_VIDS_DIR)
    st.session_state.video_paths = videos
    st.session_state.index = 0
    st.session_state.comment_for_index = None
    st.session_state.loaded = True
    st.session_state.status_msg = f"Loaded {len(videos)} video(s)."
    st.session_state.csv_df = load_csv(CSV_PATH)
    st.session_state.flag_map = parse_flags_file(FLAGS_PATH)
    st.session_state.skip_neg = load_skip_filenames(NEG_SKIP_PATH)
    st.session_state.skip_pos = load_skip_filenames(POS_SKIP_PATH)
    if videos:
        # Land on first non-skipped video.
        _set_index(0, direction=1)


def _save_label(label: str) -> None:
    rel = _current_rel()
    if rel is None:
        return
    rel_posix = rel.as_posix()
    heuristic = "FLAGGED" if rel_posix in st.session_state.flag_map else "OK"
    st.session_state.csv_df = upsert_csv(
        CSV_PATH,
        st.session_state.csv_df,
        rel_posix,
        label=label,
        heuristic=heuristic,
        comment=st.session_state.comment,
    )
    n = len(st.session_state.video_paths)
    i = st.session_state.index
    if i + 1 < n:
        _navigate(1)
        _queue_toast(f"Saved {label} for {rel_posix}; advanced.")
    else:
        st.session_state.comment_for_index = None
        _queue_toast(f"Saved {label} for {rel_posix}. End of folder.")

def main() -> None:
    st.set_page_config(page_title="ID Trajectory Validation", layout="wide")
    _init_state()

    # Collapse Streamlit chrome / padding so the page fits one viewport.
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] { display: none; }
          [data-testid="stToolbar"] { display: none; }
          .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            max-width: 100%;
          }
          div[data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
          [data-testid="stMetricValue"] { font-size: 1.1rem; }
          [data-testid="stMetricLabel"] { display: none; }
          /* Circular side Prev/Next — larger, green, bold icons */
          div.st-key-nav_prev, div.st-key-nav_next {
            display: flex;
            justify-content: center;
            align-items: center;
          }
          div.st-key-nav_prev button, div.st-key-nav_next button {
            border-radius: 50% !important;
            width: 3.6rem !important;
            height: 3.6rem !important;
            min-width: 3.6rem !important;
            min-height: 3.6rem !important;
            padding: 0 !important;
            font-size: 2rem !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            background-color: #2e7d32 !important;
            border-color: #1b5e20 !important;
            color: #ffffff !important;
          }
          div.st-key-nav_prev button:hover, div.st-key-nav_next button:hover {
            background-color: #388e3c !important;
            border-color: #2e7d32 !important;
            color: #ffffff !important;
          }
          /* Green toast notifications */
          [data-testid="stToast"] {
            background-color: #2e7d32 !important;
            color: #ffffff !important;
            border: 1px solid #1b5e20 !important;
          }
          [data-testid="stToast"] * {
            color: #ffffff !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _install_arrow_key_shortcuts()

    if "pending_folder_rel" in st.session_state:
        st.session_state.folder_rel = st.session_state.pop("pending_folder_rel")
        _load_folder()

    folder_col, browse_col, load_col, meta_col = st.columns([3.4, 0.45, 1, 1])
    with folder_col:
        st.text_input(
            "Folder",
            key="folder_rel",
            label_visibility="collapsed",
            placeholder="Folder under data/datasets/generated_vids",
        )
    with browse_col:
        if st.button(
            "📁",
            key="browse_folder_btn",
            help="Browse folders under generated_vids",
            use_container_width=True,
        ):
            st.session_state.folder_picker_open = not st.session_state.folder_picker_open
    with load_col:
        if st.button("Load", type="primary", use_container_width=True):
            st.session_state.folder_picker_open = False
            _load_folder()
    with meta_col:
        paths = st.session_state.video_paths
        if paths:
            st.metric("Video", f"{st.session_state.index + 1}/{len(paths)}")
        else:
            st.metric("Video", "—")

    if st.session_state.folder_picker_open:
        options = list_browsable_folders(GENERATED_VIDS_DIR)
        if not options:
            st.caption("No folders with videos found under generated_vids.")
        else:
            current = st.session_state.folder_rel.strip().strip("/") or options[0]
            try:
                default_idx = options.index(current)
            except ValueError:
                default_idx = 0
            pick_col, use_col = st.columns([4, 1])
            with pick_col:
                choice = st.selectbox(
                    "Browse folder",
                    options=options,
                    index=default_idx,
                    key="browse_folder_choice",
                    label_visibility="collapsed",
                )
            with use_col:
                if st.button("Select", type="primary", use_container_width=True):
                    st.session_state.pending_folder_rel = choice
                    st.session_state.folder_picker_open = False
                    st.rerun()

    _flush_toasts()

    if st.session_state.status_msg:
        st.caption(st.session_state.status_msg)

    if not st.session_state.video_paths:
        if st.session_state.loaded:
            st.warning("No .mp4 files found in that folder.")
        else:
            st.info("Enter a folder path and click Load to begin.")
        return

    # If the current landing spot is filter-listed, skip forward.
    cur = _current_rel()
    if cur is not None and _should_skip(cur):
        _set_index(st.session_state.index, direction=1)
        landed = _current_rel()
        if landed is not None and _should_skip(landed):
            st.warning(
                "Every video in this folder is on a variants filter list; nothing left to review."
            )
            _flush_toasts()
            return
        st.rerun()

    # Before any widget with key="comment" is created.
    _ensure_comment_synced()
    _flush_toasts()

    rel = _current_rel()
    assert rel is not None
    rel_posix = rel.as_posix()
    video_abs = GENERATED_VIDS_DIR / rel

    # --- Action sentence + heuristic note ---------------------------------
    sentence = prompt_sentence_for(rel, PROMPTS_ROOT)
    if sentence:
        st.markdown(f"**Action:** {sentence}")
    else:
        st.caption("Action sentence unavailable")

    flag_detail = st.session_state.flag_map.get(rel_posix)
    if flag_detail is not None:
        st.warning(f"FLAGGED — {flag_detail}")

    st.caption(rel_posix)

    # --- Controls (nav is beside media) ------------------------------------
    c3, c4, c5 = st.columns([2, 2, 2])
    with c3:
        st.radio(
            "Trajectory",
            options=["downsampled", "full_fps"],
            format_func=lambda m: "5 Hz" if m == "downsampled" else "10 Hz",
            key="traj_mode",
            horizontal=True,
            label_visibility="collapsed",
        )
    with c4:
        st.radio(
            "Series",
            options=["velocity", "heading"],
            format_func=lambda s: "Velocity" if s == "velocity" else "Heading",
            key="series",
            horizontal=True,
            label_visibility="collapsed",
        )
    with c5:
        # Use value= (not a session_state key) so the box defaults checked.
        realtime_plot = st.checkbox("Real-time plot", value=True)

    # --- Trajectory load + side nav ---------------------------------------
    traj_file = trajectory_path(video_abs, st.session_state.traj_mode)
    seq, traj_err = load_trajectory(traj_file)
    hz = hz_for_mode(st.session_state.traj_mode)
    media_h = 420

    nav_l, mid, nav_r = st.columns([0.06, 0.88, 0.06], vertical_alignment="center")
    with nav_l:
        if st.button("◀", key="nav_prev", help="Previous video (←)"):
            _navigate(-1)
            st.rerun()
    with mid:
        if traj_err:
            st.error(
                f"**Trajectory error** ({st.session_state.traj_mode}): {traj_err}  \n"
                f"Expected: `{traj_file}`"
            )
            if video_abs.is_file():
                st.video(str(video_abs))
            else:
                st.error(f"Video file missing: {video_abs}")
        elif realtime_plot:
            render_synced_player(
                video_abs,
                seq,
                hz,
                st.session_state.series,
                height=media_h,
            )
        else:
            left, right = st.columns(2)
            with left:
                st.video(str(video_abs))
            with right:
                fig = build_figure(
                    seq,
                    hz,
                    st.session_state.series,
                    height=media_h,
                    video_path=video_abs,
                )
                st.plotly_chart(
                    fig, use_container_width=True, config={"displayModeBar": False}
                )
    with nav_r:
        if st.button("▶", key="nav_next", help="Next video (→)"):
            _navigate(1)
            st.rerun()
    # --- Labeling ---------------------------------------------------------
    prior = lookup_row(st.session_state.csv_df, rel_posix)
    prior_bits = ""
    if prior:
        prior_bits = f" · prior: {prior[COL_LABEL]}/{prior[COL_HEURISTIC]}"

    comment_col, vcol, icol = st.columns([4, 1, 1])
    with comment_col:
        st.text_input(
            f"Comment{prior_bits}",
            key="comment",
            label_visibility="collapsed",
            placeholder=f"Comment{prior_bits}",
        )
    with vcol:
        if st.button("Valid", type="primary", use_container_width=True):
            _save_label("Valid")
            st.rerun()
    with icol:
        if st.button("Invalid", use_container_width=True):
            _save_label("Invalid")
            st.rerun()


if __name__ == "__main__":
    main()
