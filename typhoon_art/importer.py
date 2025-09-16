"""Simple CSV importer for typhoon project.

Provides load_any(path) -> pandas.DataFrame with canonical columns:
  ['id','name','datetime','lat','lon','wind_knots']

Heuristics are used to find likely columns in IBTrACS/JTWC-style files.
"""
from __future__ import annotations
import re
from typing import Optional
import pandas as pd


def _find_col(df: pd.DataFrame, keywords) -> Optional[str]:
    cols = list(df.columns)
    lowmap = {c: c.lower() for c in cols}
    # exact matches first
    for k in keywords:
        for c, lc in lowmap.items():
            if lc == k:
                return c
    # contains
    for k in keywords:
        for c, lc in lowmap.items():
            if k in lc:
                return c
    return None


def _first_existing(df: pd.DataFrame, patterns):
    for p in patterns:
        c = _find_col(df, [p])
        if c:
            return c
    return None


def _drop_unit_row(df: pd.DataFrame) -> pd.DataFrame:
    # IBTrACS sometimes has a second row containing units like 'kts' or 'degrees'.
    if df.shape[0] < 1:
        return df
    first = df.iloc[0].astype(str).str.lower().to_list()
    joined = " ".join(first)
    if re.search(r'kts|kt\b|degrees|deg\b|^knot', joined):
        return df.iloc[1:].reset_index(drop=True)
    return df


def load_any(path: str) -> pd.DataFrame:
    """Load IBTrACS-like CSV, skip units row, coalesce wind columns, and normalize columns."""
    df = pd.read_csv(path, low_memory=False)
    # Skip units row if present (row 2, usually with 'degrees'/'kts')
    first_row = df.iloc[0].astype(str).str.lower().to_list()
    if any('degree' in x or 'kts' in x or 'mb' in x for x in first_row):
        df = df.iloc[1:].reset_index(drop=True)

    # Coalesce wind columns
    wind_cols = ['WMO_WIND','USA_WIND','TOKYO_WIND','CMA_WIND','HKO_WIND','BOM_WIND']
    wind_vals = []
    for col in wind_cols:
        if col in df.columns:
            wind_vals.append(pd.to_numeric(df[col], errors='coerce'))
    if wind_vals:
        wind = pd.concat(wind_vals, axis=1).max(axis=1, skipna=True)
    else:
        wind = pd.Series([None]*len(df))

    # Normalize columns
    out = pd.DataFrame()
    out['id'] = df['SID'] if 'SID' in df.columns else None
    out['name'] = df['NAME'] if 'NAME' in df.columns else None
    out['datetime'] = pd.to_datetime(df['ISO_TIME'], errors='coerce') if 'ISO_TIME' in df.columns else pd.NaT
    out['lat'] = pd.to_numeric(df['LAT'], errors='coerce') if 'LAT' in df.columns else None
    out['lon'] = pd.to_numeric(df['LON'], errors='coerce') if 'LON' in df.columns else None
    out['wind_knots'] = wind

    # Drop rows without lat/lon
    out = out.dropna(subset=['lat','lon']).reset_index(drop=True)
    return out


if __name__ == '__main__':
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else 'sample_typhoons.csv'
    df = load_any(p)
    print('rows', len(df))
    print('wind non-null', df['wind_knots'].notna().sum())
