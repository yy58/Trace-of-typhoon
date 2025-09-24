"""
Generative art: moving spiral visualization of typhoon tracks and intensity using pygame.
Run with: python main.py
"""
import sys
import os
import random
import math
import time
import pygame
import pandas as pd
import colorsys
from collections import deque

WIDTH, HEIGHT = 1200, 900
BG = (10, 18, 28)

class Typhoon:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.points = []
        # use a deque with a cap to limit memory and draw cost
        self.trail = deque(maxlen=90)
    def add(self, dt, lat, lon, wind):
        self.points.append((dt, lat, lon, wind))
    def interpolated(self, t, speed=0.22, use_datetime=False, global_start=None, global_end=None, playback_seconds=60.0):
        """
        Return interpolated (lat, lon, wind).
        - If use_datetime is False: treat t as seconds and advance along point indices with fractional interpolation for smooth movement.
        - If use_datetime is True and points contain datetimes, map t into the global datetime span and interpolate between the two bracketing observations.
        """
        if not self.points:
            return None
        n = len(self.points)
        # smooth index-based interpolation (default)
        if not use_datetime:
            f = t * speed
            # clamp to avoid wrapping from last to first which causes teleport flashes
            max_f = max(0.0, n - 1 - 1e-6)
            if f > max_f:
                f = max_f
            idx0 = int(math.floor(f))
            frac = f - math.floor(f)
            idx1 = min(idx0 + 1, n - 1)
            dt0, lat0, lon0, w0 = self.points[idx0]
            dt1, lat1, lon1, w1 = self.points[idx1]
            try:
                lat = lat0 + (lat1 - lat0) * frac
                lon = lon0 + (lon1 - lon0) * frac
                wind = float(w0 + (w1 - w0) * frac)
            except Exception:
                # fallback to nearest
                _, lat, lon, wind = self.points[idx0]
            return lat, lon, wind
        # datetime-based playback
        if use_datetime and global_start is not None and global_end is not None:
            # compute a target timestamp inside global span based on t and playback_seconds
            span = (global_end - global_start).total_seconds() if (hasattr(global_end, 'tzinfo') or isinstance(global_end, (pd.Timestamp,))) else None
            if span is None or span <= 0:
                # fallback to index-based
                return self.interpolated(t, speed=speed, use_datetime=False)
            frac = ((t % playback_seconds) / float(playback_seconds))
            target_ts = global_start + pd.to_timedelta(frac * span, unit='s')
            # find surrounding points
            # ensure points are sorted by datetime
            pts = [p for p in self.points if p[0] is not None]
            if not pts:
                return self.interpolated(t, speed=speed, use_datetime=False)
            # linear scan (points per typhoon are usually small)
            prev = pts[0]
            for p in pts[1:]:
                if p[0] >= target_ts:
                    dt0, lat0, lon0, w0 = prev
                    dt1, lat1, lon1, w1 = p
                    total = (dt1 - dt0).total_seconds() if dt1 != dt0 else 1.0
                    alpha = ((target_ts - dt0).total_seconds()) / total if total != 0 else 0.0
                    lat = lat0 + (lat1 - lat0) * alpha
                    lon = lon0 + (lon1 - lon0) * alpha
                    wind = float(w0 + (w1 - w0) * alpha)
                    return lat, lon, wind
                prev = p
            # if target after last point, return last
            return pts[-1][1], pts[-1][2], float(pts[-1][3])

def load_csv(path, zero_is_nan=False):
    # Read with low_memory=False to avoid dtype inference warnings
    df = pd.read_csv(path, low_memory=False)

    # Normalize column names (strip and uppercase) for detection
    cols_upper = {c: c.strip() for c in df.columns}

    def find_col(candidates):
        for cand in candidates:
            for c in df.columns:
                if c.strip().lower() == cand.strip().lower():
                    return c
        return None

    # Common alternatives mapping
    lat_col = find_col(['lat', 'latitude', 'lat_deg', 'lat_dd', 'LAT'])
    lon_col = find_col(['lon', 'longitude', 'lon_deg', 'lon_dd', 'LON'])
    time_col = find_col(['datetime', 'iso_time', 'time', 'ISO_TIME'])
    name_col = find_col(['name', 'NAME'])
    id_col = find_col(['id', 'sid', 'SID'])
    # Wind candidates from multiple agencies
    wind_col = find_col(['wind_knots', 'wmo_wind', 'usa_wind', 'tokyo_wind', 'cma_wind', 'bom_wind', 'reunion_wind', 'nadi_wind', 'wellington_wind', 'WMO_WIND'])

    rename_map = {}
    if lat_col:
        rename_map[lat_col] = 'lat'
    if lon_col:
        rename_map[lon_col] = 'lon'
    if time_col:
        rename_map[time_col] = 'datetime'
    if name_col:
        rename_map[name_col] = 'name'
    if id_col:
        rename_map[id_col] = 'id'
    if wind_col:
        rename_map[wind_col] = 'wind_knots'

    if rename_map:
        df = df.rename(columns=rename_map)

    # Remove an initial units row if it looks like non-numeric lat
    try:
        if 'lat' in df.columns and isinstance(df.iloc[0].get('lat', None), str) and not df.iloc[0]['lat'].replace('.', '', 1).replace('-', '', 1).isdigit():
            df = df.iloc[1:].reset_index(drop=True)
    except Exception:
        pass

    # Convert common numeric columns to proper dtypes
    for col in ['lat', 'lon', 'wind_knots']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Parse datetime column if available
    if 'datetime' in df.columns:
        try:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        except Exception:
            pass
    # Optionally treat zeros in wind as missing; also auto-detect if many zeros
    if 'wind_knots' in df.columns:
        nonnull = df['wind_knots'].notna().sum()
        zero_count = (df['wind_knots'] == 0).sum()
        if zero_is_nan:
            df.loc[df['wind_knots'] == 0, 'wind_knots'] = pd.NA
            print(f"load_csv: converting {zero_count} zero wind values to NaN (forced)")
        else:
            # auto-detect: if over 60% of non-null values are zero, treat zero as missing
            try:
                if nonnull > 0 and (zero_count / float(nonnull)) > 0.6:
                    df.loc[df['wind_knots'] == 0, 'wind_knots'] = pd.NA
                    print(f"load_csv: auto-converted {zero_count} zero wind values to NaN (heuristic)")
            except Exception:
                pass

    # Auto-normalize longitude if values are in 0..360 range
    if 'lon' in df.columns:
        try:
            lon_max = df['lon'].max(skipna=True)
            if lon_max is not None and lon_max > 180:
                # remap to -180..180
                df['lon'] = ((df['lon'] + 180) % 360) - 180
                print(f"load_csv: normalized longitudes from 0..360 to -180..180 (max before: {lon_max})")
        except Exception:
            pass

    # Detect and remove obvious placeholder points at exactly (0,0)
    if 'lat' in df.columns and 'lon' in df.columns:
        try:
            total = len(df)
            zero_latlon_count = int(((df['lat'] == 0) & (df['lon'] == 0)).sum())
            if zero_latlon_count > 0:
                # if many rows are exactly (0,0) treat them as missing data and drop
                if total > 0 and (zero_latlon_count / float(total)) > 0.005:
                    df = df.loc[~((df['lat'] == 0) & (df['lon'] == 0))].reset_index(drop=True)
                    print(f"load_csv: dropped {zero_latlon_count} placeholder (0,0) points ({zero_latlon_count/total:.2%})")
                else:
                    # if only a few, leave them but warn
                    print(f"load_csv: warning - {zero_latlon_count} points at exact (0,0) found; leaving them in place")
        except Exception:
            pass

    return df

def build_typhoons(df):
    groups = {}
    for i, row in df.iterrows():
        tid = row.get('id') if 'id' in row.index else None
        if pd.isna(tid) or tid is None:
            name = row.get('name') if 'name' in row.index else None
            tid = f"{name or 'storm'}_{i}"
        lat = row.get('lat')
        lon = row.get('lon')
        if pd.isna(lat) or pd.isna(lon):
            continue
        if tid not in groups:
            groups[tid] = Typhoon(tid, row.get('name', tid))
        wind = row.get('wind_knots', 0.0)
        try:
            wind = float(wind) if not pd.isna(wind) else 0.0
        except Exception:
            wind = 0.0
        # ensure datetime is a pandas Timestamp or None
        dt = row.get('datetime') if 'datetime' in row.index else None
        try:
            if pd.isna(dt):
                dt = None
        except Exception:
            pass
        groups[tid].add(dt, float(lat), float(lon), wind)
    return list(groups.values())

def latlon_to_xy(lat, lon):
    # Improved equirectangular projection that centers on dataset mean later
    # Standard mapping: lon -180..180 -> x 0..WIDTH; lat -90..90 -> y 0..HEIGHT (top to bottom)
    x = (lon + 180.0) / 360.0 * WIDTH
    # map lat -90..90 to y 0..HEIGHT (flip so north is up)
    y = (90.0 - lat) / 180.0 * HEIGHT
    return int(x), int(y)

def wind_to_color(wind):
    wn = max(0.0, min(1.0, (wind - 5) / 145.0))
    h = 0.65 * (1.0 - wn)
    r, g, b = colorsys.hsv_to_rgb(h, 0.92, 0.98)
    return int(r * 255), int(g * 255), int(b * 255)

def draw_spiral(surface, center, radius, angle, color, thickness=2):
    points = []
    steps = 90
    for i in range(steps):
        t = i / (steps - 1)
        r = radius * t
        a = angle + t * 6 * math.pi
        x = center[0] + r * math.cos(a)
        y = center[1] + r * math.sin(a)
        points.append((int(x), int(y)))
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, thickness)

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description='Typhoon visualization')
    parser.add_argument('path', nargs='?', default=None, help='CSV path (optional)')
    parser.add_argument('--jitter', type=float, default=40.0, help='max jitter offset in pixels (applied +/-)')
    parser.add_argument('--spread', choices=['none', 'cell'], default='none', help='enable spread mode to avoid stacking')
    parser.add_argument('--grid-size', type=int, default=80, help='grid cell size in pixels for cell spread')
    parser.add_argument('--spread-radius', type=float, default=30.0, help='base spread radius in pixels inside a cell')
    parser.add_argument('--use-datetime', action='store_true', help='animate along actual observation times if available')
    parser.add_argument('--playback-duration', type=float, default=60.0, help='seconds for a full datetime playback loop')
    parser.add_argument('--min-wind', type=float, default=0.0, help='minimum wind (kt) to display; set >0 to hide weak/no-wind points')
    parser.add_argument('--zero-is-nan', action='store_true', help='treat wind==0 as missing (NaN) in importer)')
   # parser.add_argument('--debug-grid', action='store_true', help='draw grid cell boundaries and anchors for tuning')
    parser.add_argument('--debug-density', type=int, default=6, help='only show anchors for cells with this many or more typhoons')
    parser.add_argument('--seed', type=int, default=12345, help='optional RNG seed to make jitter/spread reproducible (default=12345)')
    parser.add_argument('--deterministic-time', action='store_true', default=True, help='use frame-count based time instead of wall-clock to make stdout deterministic (default ON)')
    parser.add_argument('--no-center', action='store_true', default=False, help='do not center visualization on dataset mean; use raw geographic positions')
    args = parser.parse_args(argv[1:])
    here = __file__
    here_dir = os.path.dirname(os.path.abspath(here))
    path = args.path or os.path.join(here_dir, 'sample_typhoons.csv')
    print("Typhoon Track Visualization")
    df = load_csv(path, zero_is_nan=getattr(args, 'zero_is_nan', False))
    typhoons = build_typhoons(df)
    print(f"Loaded {len(typhoons)} typhoons")
    if len(typhoons) == 0:
        print("Error: No valid typhoon data found!")
        return
    for i, ty in enumerate(typhoons[:3]):
        print(f"Typhoon {i+1}: {ty.name} (ID: {ty.id}), Points: {len(ty.points)}")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Typhoon Track Visualization - Press ESC to exit")
    clock = pygame.time.Clock()
    running = True
    t0 = time.time()
    frame_count = 0
    print("Rendering... Press ESC to exit")
    # seed RNG if requested for reproducible layout
    # seed RNG (defaults to 12345) for reproducible layouts
    if getattr(args, 'seed', None) is not None:
        random.seed(int(args.seed))
    # debug messages
    if getattr(args, 'debug_grid', False):
        print(f"Debug grid ON (grid-size={getattr(args,'grid_size',80)}, density={getattr(args,'debug_density',6)})")
    # Assign a random jitter offset to each typhoon
    jitter_amount = float(getattr(args, 'jitter', 40.0))
    print(f"Using jitter amount: +/-{jitter_amount} pixels")
    jitter_offsets = {ty.id: (random.uniform(-jitter_amount, jitter_amount), random.uniform(-jitter_amount, jitter_amount)) for ty in typhoons}
    # compute anchors (avg lat/lon) for all typhoons (useful for debug overlay)
    anchors = {}
    for ty in typhoons:
        if ty.points:
            avg_lat = sum(p[1] for p in ty.points) / len(ty.points)
            avg_lon = sum(p[2] for p in ty.points) / len(ty.points)
            ax, ay = latlon_to_xy(avg_lat, avg_lon)
        else:
            ax, ay = 0, 0
        anchors[ty.id] = (ax, ay)

    # Compute dataset center in lat/lon and corresponding pixel offset so visual is centered
    all_lats = [p[1] for ty in typhoons for p in ty.points if p[1] is not None]
    all_lons = [p[2] for ty in typhoons for p in ty.points if p[2] is not None]
    center_offset = (0, 0)
    try:
        if not getattr(args, 'no_center', False) and all_lats and all_lons:
            mean_lat = sum(all_lats) / len(all_lats)
            mean_lon = sum(all_lons) / len(all_lons)
            mean_x, mean_y = latlon_to_xy(mean_lat, mean_lon)
            # desired center is screen center
            target_x = WIDTH // 2
            target_y = HEIGHT // 2
            offset_x = target_x - mean_x
            offset_y = target_y - mean_y
            center_offset = (int(offset_x), int(offset_y))
            print(f"Centering visualization: mean lat/lon ({mean_lat:.2f}, {mean_lon:.2f}) -> pixel offset {center_offset}")
        else:
            if getattr(args, 'no_center', False):
                print("Centering disabled (--no-center); using raw geographic projection")
    except Exception:
        center_offset = (0, 0)

    # compute optional spread offsets based on anchor positions (average lat/lon)
    spread_offsets = {ty.id: (0, 0) for ty in typhoons}
    if args.spread == 'cell':
        grid = int(getattr(args, 'grid_size', 80))
        spread_radius = float(getattr(args, 'spread_radius', 30.0))
        # group by grid cell
        cells = {}
        for tid, (ax, ay) in anchors.items():
            cell_key = (ax // grid, ay // grid)
            cells.setdefault(cell_key, []).append(tid)
        # assign offsets within each cell
        for cell_key, tids in cells.items():
            n = len(tids)
            if n == 1:
                spread_offsets[tids[0]] = (0, 0)
                continue
            # if cell crowded, increase ring spacing and add small random angle jitter
            base_ring = 1
            for i, tid in enumerate(tids):
                # distribute on multiple rings of up to 8 per ring
                ring_idx = i // 8
                pos_in_ring = i % 8
                slots = min(8, n - ring_idx * 8)
                angle = 2 * math.pi * (pos_in_ring / max(1, slots)) + random.uniform(-0.12, 0.12)
                ring = base_ring + ring_idx
                r = spread_radius * ring
                sx = int(round(math.cos(angle) * r))
                sy = int(round(math.sin(angle) * r))
                spread_offsets[tid] = (sx, sy)
    # pre-create font and dot cache and spiral detail
    font = pygame.font.SysFont(None, 20)
    dot_surf_cache = {}
    spiral_steps = 32
    # when an interpolated jump is large, clear the trail to avoid long flashing lines
    jump_threshold = 200
    # compute global datetime span (used for playback and to show year-range overlay)
    global_start = None
    global_end = None
    dts = [p[0] for ty in typhoons for p in ty.points if p[0] is not None]
    if dts:
        try:
            global_start = min(dts)
            global_end = max(dts)
        except Exception:
            global_start, global_end = None, None
    else:
        if args.use_datetime:
            print("Warning: --use-datetime specified but no datetime values found in data; falling back to index-based animation")

    fps = 30.0
    while running:
        # use deterministic frame time if requested for reproducible stdout
        if getattr(args, 'deterministic_time', False):
            frame_dt = 1.0 / fps
            now = frame_count * frame_dt
            clock.tick(int(fps))
        else:
            dt = clock.tick(int(fps)) / 1000.0
            now = time.time() - t0
        frame_count += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        screen.fill(BG)
        now = time.time() - t0
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        visible_typhoons = 0
        for ty in typhoons:
            interp = ty.interpolated(now, speed=0.22, use_datetime=args.use_datetime, global_start=global_start, global_end=global_end, playback_seconds=args.playback_duration)
            if interp is None:
                continue
            lat, lon, wind = interp
            # filter tiny/zero winds if requested
            if wind is None:
                continue
            if args.min_wind and float(wind) < float(args.min_wind):
                continue
            x, y = latlon_to_xy(lat, lon)
            # Apply jitter
            dx, dy = jitter_offsets.get(ty.id, (0, 0))
            x += int(dx)
            y += int(dy)
            # Apply spread offset (cell/grid-based) so points don't stack
            sx, sy = spread_offsets.get(ty.id, (0, 0))
            x += int(sx)
            y += int(sy)
            # apply global centering offset
            ox, oy = center_offset
            x += ox
            y += oy
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                continue
            visible_typhoons += 1
            wind_display = float(wind) if wind is not None else 0.0
            # clear trail if this step teleports too far from previous to avoid drawing long flashes
            prev_pt = ty.trail[-1] if len(ty.trail) > 0 else None
            if prev_pt is not None:
                dxp = x - prev_pt[0]
                dyp = y - prev_pt[1]
                if dxp * dxp + dyp * dyp > jump_threshold * jump_threshold:
                    ty.trail.clear()
            ty.trail.append((x, y, wind_display, now))
            trail_list = list(ty.trail)
            L = len(trail_list)
            for i, (tx, ty_y, tw, tt) in enumerate(trail_list):
                age_frac = (i + 1) / max(1, L)
                a = int(80 + 175 * age_frac)
                col = wind_to_color(tw) + (a,)
                radius_dot = max(2, int(3 + (tw / 150.0) * 6 * age_frac))
                key = (radius_dot, col)
                if key not in dot_surf_cache:
                    s = pygame.Surface((radius_dot * 2 + 2, radius_dot * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, col, (radius_dot + 1, radius_dot + 1), radius_dot)
                    dot_surf_cache[key] = s
                overlay.blit(dot_surf_cache[key], (tx - radius_dot - 1, ty_y - radius_dot - 1))
            # cap spiral radius
            radius = min(160, 16 + (wind_display / 100.0) * 120)
            color = wind_to_color(wind_display)
            angle = now * 0.9
            # draw simplified spiral
            points = []
            for si in range(spiral_steps):
                t = si / max(1, (spiral_steps - 1))
                r = radius * t
                a = angle + t * 6 * math.pi
                px = x + r * math.cos(a)
                py = y + r * math.sin(a)
                points.append((int(px), int(py)))
            if len(points) > 1:
                pygame.draw.lines(screen, color, False, points, 4)
            label = font.render(f"{ty.name} ({int(wind)} kt)", True, (220, 220, 220))
            screen.blit(label, (x + 10, y + 10))
        screen.blit(overlay, (0, 0))
        # draw debug overlays (grid and anchors)
        if getattr(args, 'debug_grid', False):
            grid = int(getattr(args, 'grid_size', 80))
            density_threshold = int(getattr(args, 'debug_density', 6))
            # draw grid lines
            for gx in range(0, WIDTH, grid):
                pygame.draw.line(screen, (40, 40, 60), (gx, 0), (gx, HEIGHT), 1)
            for gy in range(0, HEIGHT, grid):
                pygame.draw.line(screen, (40, 40, 60), (0, gy), (WIDTH, gy), 1)
            # compute cell densities
            cell_counts = {}
            for tid, (ax, ay) in anchors.items():
                cell_key = (int(ax) // grid, int(ay) // grid)
                cell_counts[cell_key] = cell_counts.get(cell_key, 0) + 1
            # map typhoon ids to short indexes for labels
            id_to_idx = {ty.id: idx for idx, ty in enumerate(typhoons, start=1)}
            # draw anchors only for cells with enough density
            for tid, (ax, ay) in anchors.items():
                cell_key = (int(ax) // grid, int(ay) // grid)
                if cell_counts.get(cell_key, 0) < density_threshold:
                    continue
                # draw anchor dot
                pygame.draw.circle(screen, (200, 160, 40), (int(ax), int(ay)), 4)
                # short label like '#12'
                idx = id_to_idx.get(tid, None)
                if idx is not None:
                    try:
                        txt = font.render(f"#{idx}", True, (220, 220, 200))
                        screen.blit(txt, (int(ax) + 6, int(ay) - 6))
                    except Exception:
                        pass
        # draw a timestamp overlay if using datetime playback
        if args.use_datetime and global_start is not None and global_end is not None:
            frac = ((now % args.playback_duration) / float(args.playback_duration))
            try:
                span_td = (global_end - global_start)
                target_ts = global_start + span_td * frac
                ts_str = target_ts.strftime('%Y-%m-%d %H:%M') if hasattr(target_ts, 'strftime') else str(target_ts)
            except Exception:
                ts_str = ''
            if ts_str:
                ts_surf = font.render(ts_str, True, (200, 200, 200))
                screen.blit(ts_surf, (8, 8))
        # Always show data year-range if datetimes are present
        if global_start is not None and global_end is not None:
            try:
                start_year = getattr(global_start, 'year', None) or str(global_start)[:4]
                end_year = getattr(global_end, 'year', None) or str(global_end)[:4]
                yr_str = f"Data span: {start_year} — {end_year}"
                yr_surf = font.render(yr_str, True, (180, 180, 180))
                screen.blit(yr_surf, (8, 28))
            except Exception:
                pass
        if frame_count % 30 == 0:
            print(f"Time: {now:.1f}s, Visible typhoons: {visible_typhoons}")
        pygame.display.flip()
    print("Program ended")
    pygame.quit()

if __name__ == '__main__':
    main(sys.argv)