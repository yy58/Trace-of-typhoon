Typhoon Update0 — Visualization README

Quick overview

This folder contains a pygame-based generative visualization of IBTrACS-like typhoon tracks.
The main script is `main.py`. It reads a CSV of storm observations and draws animated spirals, colored by wind.

Quick reproducible example

Run inside the project virtualenv (example):

    .venv/bin/python typhoon_update0/main.py \
        --jitter 40 \
        --spread cell \
        --grid-size 120 \
        --spread-radius 48 \
        --use-datetime \
        --playback-duration 120 \
        --min-wind 0 \
        --zero-is-nan \
        --debug-grid \
        --debug-density 8 \
        --seed 12345 \
        --deterministic-time

This command is a reproducible example I used when testing. The important options for reproducibility are `--seed` and `--deterministic-time` (they fix randomness and use frame-based time so stdout/states are repeatable).

Defaults changed: `--seed` now defaults to `12345` and `--deterministic-time` is ON by default, so running `main.py` without these flags will still produce reproducible layouts and deterministic output. To opt out, pass `--seed 0` (or any other value) and `--deterministic-time` can be turned off by modifying the code or passing an explicit flag in the future.

Flags and what they do

- path (positional): optional CSV path. If omitted, `sample_typhoons.csv` in this folder is used.
- --jitter N            : max per-typhoon random pixel offset (default 40)
- --spread [none|cell]  : layout mode; `cell` spreads typhoons inside map grid cells to reduce stacking
- --grid-size N         : grid cell size (pixels) used by `cell` spread
- --spread-radius N     : base radius (pixels) used when distributing typhoons inside a cell
- --use-datetime        : map animation to actual observation datetimes (if present)
- --playback-duration S : seconds for one full datetime playback loop
- --min-wind K          : hide observations with wind < K kt
- --zero-is-nan         : treat wind==0 as missing (NaN) during import
- --debug-grid          : draw grid lines and anchors (useful to tune grid-size/spread-radius)
- --debug-density N     : only show anchors for grid cells with >= N storms (keeps debug overlay clean)
- --seed S              : optional RNG seed for reproducible jitter/spread
- --deterministic-time  : use frame-count based time instead of wall-clock (makes stdout deterministic)

Notes about common issues

- "All storms in bottom-right": usually caused by longitude values in the CSV being in 0..360 range. The loader auto-normalizes longitudes (0..360 -> -180..180) when detected.
- "Flashing long lines": caused by large jumps between drawn positions; `--deterministic-time` + fixed `--seed` + the code's jump-threshold reduce or remove these flashes.
- Randomness: jitter and some spread jitter are random unless a seed is provided.

If you want defaults changed (for example, turn `--deterministic-time` on by default or set a default seed), say which behavior you prefer and I will make that change.

Files

- `main.py`  : visualization script (entry point)
- `sample_typhoons.csv` : sample IBTrACS-like CSV used by default
- `README.md` : (this file)

Troubleshooting

- If you don't see the debug grid or the timestamp:
  - make sure you started the script with `--debug-grid` and `--use-datetime` respectively; they are opt-in.
  - to reproduce exactly, include `--seed <N>` and `--deterministic-time` on the command line.

Want me to change defaults?

I can set sensible defaults (for example enable `--deterministic-time` and a default `--seed`) if you'd like. Reply with "set defaults" and mention which flags to enable by default.

Exact terminal command (copy-paste)

```bash
/Users/yyg/Desktop/polyu/SD5913\ creative\ programming/Trace-of-typhoon/.venv/bin/python \
  "/Users/yyg/Desktop/polyu/SD5913 creative programming/Trace-of-typhoon/typhoon_update0/main.py" \
  --jitter 40 --spread cell --grid-size 120 --spread-radius 48 --use-datetime \
  --playback-duration 120 --min-wind 0 --zero-is-nan --debug-grid --debug-density 8 \
  --seed 12345 --deterministic-time
```
