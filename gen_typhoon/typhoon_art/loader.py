import pandas as pd

def load_typhoon_csv(path, lat_col_candidates=('LAT','lat','Latitude'), lon_col_candidates=('LON','lon','Longitude'), wind_col_candidates=('WMO_WIND','WIND','wind')):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}

    def pick(candidates):
        for c in candidates:
            if c in df.columns:
                return c
            if c.lower() in cols:
                return cols[c.lower()]
        return None

    lat_col = pick(lat_col_candidates)
    lon_col = pick(lon_col_candidates)
    wind_col = pick(wind_col_candidates)

    if lat_col is None or lon_col is None or wind_col is None:
        raise ValueError('CSV must contain LAT, LON, and WMO_WIND (or equivalents)')

    sub = df[[lat_col, lon_col, wind_col]].rename(columns={lat_col: 'lat', lon_col: 'lon', wind_col: 'wind'})
    sub['lat'] = pd.to_numeric(sub['lat'], errors='coerce')
    sub['lon'] = pd.to_numeric(sub['lon'], errors='coerce')
    sub['wind'] = pd.to_numeric(sub['wind'], errors='coerce')
    sub = sub.dropna()
    return sub
