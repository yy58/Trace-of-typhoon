"""Cartopy-based example plotting for typhoon tracks.

Saves a PNG `cartopy_example.png` showing a single storm track colored by wind speed.
If Cartopy is not available, falls back to a simple Matplotlib scatter in lon/lat.
"""
from __future__ import annotations
import os
import sys
import pandas as pd

URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/csv/ibtracs.WP.list.v04r00.csv"
LOCAL_SAMPLE = os.path.join(os.path.dirname(__file__), 'sample_typhoons.csv')


def load_ibtracs(path_or_url=URL):
    # prefer local sample if present to avoid network/SSL issues
    if os.path.exists(LOCAL_SAMPLE):
        path_or_url = LOCAL_SAMPLE
    df = pd.read_csv(path_or_url, low_memory=False)
    # select and normalize useful columns
    # coerce numeric fields; drop obviously invalid rows
    for c in ['SEASON', 'LAT', 'LON']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # coalesce wind columns into a single WIND column
    wind_cols = [c for c in ['WMO_WIND', 'USA_WIND', 'TOKYO_WIND', 'CMA_WIND', 'HKO_WIND', 'BOM_WIND'] if c in df.columns]
    if wind_cols:
        # take the max of available numeric wind values per row
        df['WIND'] = df[wind_cols].apply(pd.to_numeric, errors='coerce').max(axis=1)
    else:
        df['WIND'] = pd.NA

    # keep core columns if present
    keep = [c for c in ['SID', 'NAME', 'SEASON', 'ISO_TIME', 'LAT', 'LON', 'WIND'] if c in df.columns]
    df2 = df[keep].copy()
    df2 = df2.dropna(subset=['LAT', 'LON'])
    return df2


def plot_example(out_path='typhoon_art/cartopy_example.png'):
    df = load_ibtracs()
    # filter seasons and pick an example storm with enough points
    df = df[df['SEASON'] >= 2000]
    sids = df['SID'].unique()
    # find a sid with > 6 points
    sid = None
    for s in sids:
        count = (df['SID'] == s).sum()
        if count >= 6:
            sid = s
            break
    if sid is None and len(sids) > 0:
        sid = sids[0]

    storm = df[df['SID'] == sid]
    lon = storm['LON'].astype(float)
    lat = storm['LAT'].astype(float)
    wind = storm['WMO_WIND'] if 'WMO_WIND' in storm.columns else None

    try:
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature

        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([100, 160, 0, 50], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=True)

        sc = ax.scatter(lon, lat, c=wind, cmap='plasma', s=40, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(sc, orientation='vertical', shrink=0.6, pad=0.05)
        cbar.set_label('Wind Speed (knots)')
        plt.title(f"Typhoon Track Example: {storm['NAME'].iloc[0]} ({storm['SEASON'].iloc[0]})")
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        print('wrote', out_path)
    except Exception as e:
        # fallback: simple lon/lat plot
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10,6))
        plt.scatter(lon, lat, c=wind if wind is not None else 'b', cmap='plasma', s=40)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title(f"Typhoon Track Example (fallback): {sid}")
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        print('wrote fallback', out_path, 'error:', e)


if __name__ == '__main__':
    out = 'typhoon_art/cartopy_example.png'
    plot_example(out)
