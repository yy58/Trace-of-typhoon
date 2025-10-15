# Typhoon Update0 — Visualization
**Typhoon Update0** is a generative art project that transforms **global typhoon track data** into **dynamic spiral animations**.  
Built with `pygame`, it visualizes storm **paths, intensities, and movement over time** in an abstract, expressive style.

---

## Example Output

<img width="1187" height="856" alt="截屏2025-10-15 15 52 06" src="https://github.com/user-attachments/assets/a76f2d36-fe16-4a58-8da5-faa9ec7d4dce" />

---

## How It Works

Each typhoon observation (from the CSV) becomes a **spiral entity**, animated according to:

- **Position (lat/lon)** → screen coordinates  
- **Wind speed** → color and spiral size  
- **Datetime** → animation playback over time

The project supports both **data-accurate** (datetime-based) and **deterministic frame-based** animation, ensuring reproducibility across runs.

---

## Getting Started

### Recommended environment

- Python `3.12+` (recommended)
- `pygame` (see `requirements.txt`)

### macOS / Linux

```bash
# Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r typhoon_update0/requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r typhoon_update0\requirements.txt
```

### Windows (cmd.exe)

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r typhoon_update0\requirements.txt
```

---

## Run the Visualization (Reproducible Example)

Run this example inside the project directory:

```bash
python typhoon_update0/main.py \
  --jitter 40 --spread cell --grid-size 120 --spread-radius 48 --use-datetime \
  --playback-duration 120 --min-wind 0 --zero-is-nan --debug-density 8 \
  --seed 12345 --deterministic-time
```

> By default, `--seed 12345` and `--deterministic-time` are enabled,  
> so running `main.py` without flags will still produce reproducible layouts.

---

## Flags and Options

| Flag | Description |
|------|--------------|
| `path` | Optional CSV path. Defaults to `sample_typhoons.csv`. |
| `--jitter N` | Max per-typhoon random pixel offset (default `40`). |
| `--spread [none|cell]` | Layout mode. `cell` spreads typhoons within map grid cells. |
| `--grid-size N` | Grid cell size (px) for `cell` spread. |
| `--spread-radius N` | Base radius (px) for distribution within a cell. |
| `--use-datetime` | Use real observation datetimes for playback. |
| `--playback-duration S` | Seconds for one full datetime playback loop. |
| `--min-wind K` | Hide observations with wind < K kt. |
| `--zero-is-nan` | Treat wind==0 as missing (NaN). |
| `--debug-grid` | Show debug grid lines and anchors. |
| `--debug-density N` | Show anchors only for grid cells with ≥ N storms. |
| `--seed S` | RNG seed for reproducible jitter/spread. |
| `--deterministic-time` | Use frame-count-based time for deterministic output. |

---

## Files

```
typhoon_update0/
├── main.py                # Visualization script (entry point)
├── sample_typhoons.csv    # Default dataset (IBTrACS-like sample)
└── requirements.txt      # Dependencies
```

## Acknowledgments

- **Global Typhoon Track Data** — [IBTrACS](https://www.ncdc.noaa.gov/ibtracs/)  
- **pygame** for real-time rendering  
- **Inspiration** from generative weather visualization and data art
