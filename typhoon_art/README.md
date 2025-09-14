Typhoon generative art (pygame)

Files:
- `main.py` — main pygame visualization
- `sample_typhoons.csv` — sample CSV input
- `requirements.txt` — dependencies

Run (macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Notes:
- Pygame opens a GUI window; in headless environments this will fail.
- The script uses a simple equirectangular projection and sample CSV; replace with real typhoon CSV data with columns: id,name,datetime,lat,lon,wind_knots
