"""Generative art: moving spiral visualization of typhoon tracks and intensity using pygame.

Run with: python -m typhoon_art.main (or python main.py)
"""
import sys
import math
import csv
import time
from collections import defaultdict, deque
import colorsys

import pygame
import pandas as pd
import numpy as np

WIDTH, HEIGHT = 1000, 800
BG = (10, 10, 18)

def load_csv(path):
    """Load CSV and normalize columns for IBTrACS format.

    Returns a DataFrame with columns: id, name, datetime, lat, lon, wind_knots
    """
    print(f"Loading data from: {path}")
    
    # Read CSV file
    df = pd.read_csv(path, low_memory=False)
    print(f"Original data shape: {df.shape}")
    
    # Map IBTrACS columns to expected format
    column_mapping = {
        'SID': 'id',
        'NAME': 'name', 
        'ISO_TIME': 'datetime',
        'LAT': 'lat',
        'LON': 'lon',
        'WMO_WIND': 'wind_knots'
    }
    
    # Rename columns if they exist
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df[new_col] = df[old_col]
    
    # Filter for recent data (2000+)
    if 'SEASON' in df.columns:
        df['SEASON'] = pd.to_numeric(df['SEASON'], errors='coerce')
        df = df[df['SEASON'] >= 2000]
    
    # Clean and convert data types
    df = df.dropna(subset=['lat', 'lon'])
    
    if 'wind_knots' in df.columns:
        df['wind_knots'] = pd.to_numeric(df['wind_knots'], errors='coerce').fillna(0.0)
    else:
        df['wind_knots'] = 0.0

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    
    print(f"Cleaned data shape: {df.shape}")
    print(f"Unique storms: {df['id'].nunique() if 'id' in df.columns else 'Unknown'}")
    
    return df


def latlon_to_xy(lat, lon, w=WIDTH, h=HEIGHT):
    # simple equirectangular projection centered on Asia-Pacific
    # lon range ~100..160 => map to width, lat range ~5..40 => map to height
    lon_min, lon_max = 90, 160
    lat_min, lat_max = -10, 45
    x = (lon - lon_min) / (lon_max - lon_min) * w
    y = h - (lat - lat_min) / (lat_max - lat_min) * h
    return int(x), int(y)


class Typhoon:
    def __init__(self, id_, name):
        self.id = id_
        self.name = name
        self.points = []  # list of (time, lat, lon, wind)
        self.trail = deque(maxlen=64)

    def add(self, time_, lat, lon, wind):
        self.points.append((time_, lat, lon, wind))

    def get_path(self):
        return self.points

    def interpolated(self, now, speed=0.25):
        """Return interpolated (lat, lon, wind) for the current time.
        Loops over points smoothly.
        """
        pts = self.points
        n = len(pts)
        if n == 0:
            return None
        if n == 1:
            return pts[0][1], pts[0][2], pts[0][3]

        idx = (now * speed) % n
        i0 = int(math.floor(idx))
        i1 = (i0 + 1) % n
        t = idx - i0
        _, lat0, lon0, w0 = pts[i0]
        _, lat1, lon1, w1 = pts[i1]
        lat = lat0 * (1 - t) + lat1 * t
        lon = lon0 * (1 - t) + lon1 * t
        wind = w0 * (1 - t) + w1 * t
        return lat, lon, wind


def build_typhoons(df):
    groups = {}
    for i, row in df.iterrows():
        # create a stable id: prefer 'id', fall back to name+index
        tid = row.get('id') if 'id' in row.index else None
        if pd.isna(tid) or tid is None:
            name = row.get('name') if 'name' in row.index else None
            tid = f"{name or 'storm'}_{i}"

        # safety: ensure lat/lon present
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
        groups[tid].add(row.get('datetime'), float(lat), float(lon), wind)

    return list(groups.values())


def draw_spiral(surface, center, radius, angle, color, thickness=2):
    # parametric spiral: r = a + b * t ; here t in [0,1]
    points = []
    steps = 90
    for i in range(steps):
        t = i / (steps - 1)
        r = radius * t
        # fewer coils for clearer form
        a = angle + t * 6 * math.pi
        x = center[0] + r * math.cos(a)
        y = center[1] + r * math.sin(a)
        points.append((int(x), int(y)))
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, thickness)


def wind_to_color(wind):
    """Map wind (knots) to an RGB tuple using an HSV ramp (blue -> yellow -> red)."""
    # normalize expected wind range 0..150
    wn = max(0.0, min(1.0, (wind - 5) / 145.0))
    # hue from 0.65 (blue) down to 0.0 (red)
    h = 0.65 * (1.0 - wn)
    # increase saturation/brightness for better contrast
    r, g, b = colorsys.hsv_to_rgb(h, 0.92, 0.98)
    return int(r * 255), int(g * 255), int(b * 255)


def main(argv):
    # default to the sample CSV bundled with the package (script-relative)
    here = __file__
    import os
    here_dir = os.path.dirname(os.path.abspath(here))
    path = os.path.join(here_dir, 'sample_typhoons.csv')
    if len(argv) > 1:
        path = argv[1]

    print("=== 台风轨迹可视化程序 ===")
    df = load_csv(path)
    typhoons = build_typhoons(df)
    
    print(f"成功加载 {len(typhoons)} 个台风")
    if len(typhoons) == 0:
        print("错误: 没有找到有效的台风数据!")
        return
    
    # 显示前几个台风的信息
    for i, ty in enumerate(typhoons[:3]):
        print(f"台风 {i+1}: {ty.name} (ID: {ty.id}), 数据点: {len(ty.points)}")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("台风轨迹可视化 - 按ESC退出")
    clock = pygame.time.Clock()

    running = True
    t0 = time.time()
    frame_count = 0

    print("开始渲染... 按ESC键退出")

    while running:
        dt = clock.tick(30) / 1000.0
        frame_count += 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill(BG)

        now = time.time() - t0

        # create an overlay surface for trails with alpha
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # draw each typhoon as a moving spiral at interpolated position
        visible_typhoons = 0
        for ty in typhoons:
            # only draw reasonably populated storms and those that map inside view
            interp = ty.interpolated(now, speed=0.22)
            if interp is None:
                continue
            lat, lon, wind = interp
            x, y = latlon_to_xy(lat, lon)

            # simple in-view filter
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                continue

            visible_typhoons += 1

            # treat missing/zero wind as a small baseline so visuals are visible
            wind_display = float(wind) if wind is not None else 0.0
            if wind_display <= 5.0:
                wind_display = 28.0

            # record trail (recent positions)
            ty.trail.append((x, y, wind_display, now))

            # draw fading trail (overlay for alpha)
            trail_list = list(ty.trail)
            L = len(trail_list)
            for i, (tx, ty_y, tw, tt) in enumerate(trail_list):
                age_frac = (i + 1) / max(1, L)
                # stronger base alpha for visibility
                a = int(80 + 175 * age_frac)
                col = wind_to_color(tw) + (a,)
                radius_dot = max(2, int(3 + (tw / 150.0) * 8 * age_frac))
                circ = pygame.Surface((radius_dot * 2 + 2, radius_dot * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(circ, col, (radius_dot + 1, radius_dot + 1), radius_dot)
                overlay.blit(circ, (tx - radius_dot - 1, ty_y - radius_dot - 1))

            # map wind to radius and color for main spiral (bigger)
            radius = 16 + (wind_display / 100.0) * 200
            color = wind_to_color(wind_display)
            angle = now * 0.9
            # draw thicker, more visible spiral
            draw_spiral(screen, (x, y), radius, angle, color, thickness=5)

            # label
            font = pygame.font.SysFont(None, 20)
            label = font.render(f"{ty.name} ({int(wind)} kt)", True, (220, 220, 220))
            screen.blit(label, (x + 10, y + 10))

        # blit trails overlay last so it sits under/over as desired
        screen.blit(overlay, (0, 0))
        
        # 显示状态信息
        if frame_count % 30 == 0:  # 每秒更新一次
            print(f"时间: {now:.1f}s, 可见台风: {visible_typhoons}")

        pygame.display.flip()

    print("程序结束")
    pygame.quit()


if __name__ == '__main__':
    main(sys.argv)
