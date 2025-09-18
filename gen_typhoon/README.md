Generative Typhoon Constellation

This minimal project visualizes typhoon tracks as glowing particles using Pygame.

Concept
- Each typhoon point is a luminous particle on an equirectangular world map.
- Brightness ∝ wind speed (WMO_WIND).
- Flicker frequency ∝ low pressure (lower pressure → faster flicker).
- The visual goal is a night-sky / nebula effect where typhoons form a "storm constellation".

Run
1. create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r gen_typhoon/requirements.txt
```

2. Run the demo with the included sample CSV:

```bash
python gen_typhoon/main.py --csv sample_typhoons_small.csv
```

Flags: `--csv`, `--width`, `--height`, `--seed`, `--brightness-scale`, `--flicker-scale`.
