# Inverse-dynamics trajectory validation

Streamlit app for manually labeling velocity/heading trajectories against generated videos.

## Run

From the repo root:

```bash
uv sync --group validation
uv run --group validation streamlit run data/cosmos3/data_validation/app.py
```

Optional: set `PROMPTS_ROOT` if prompts are not under `data/cosmos3/video_gen_prompts`.

## Outputs

Labels are upserted into [`inverse_dynamics_filter.csv`](inverse_dynamics_filter.csv):

| Column | Meaning |
| --- | --- |
| Video filepath relative to `data/datasets/generated_vids` | posix path to `.mp4` |
| Valid/Invalid | manual label |
| Heuristic Validation | `FLAGGED` or `OK` from `inverse_dynamics_flags.txt` |
| Comment | free text |
