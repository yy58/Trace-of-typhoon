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
    df = pd.read_csv(path, parse_dates=['datetime'])
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
    groups = defaultdict(lambda: Typhoon(None, None))
    for _, row in df.iterrows():
        tid = row['id']
        if groups[tid].id is None:
            groups[tid] = Typhoon(tid, row.get('name', tid))
        groups[tid].add(row['datetime'], row['lat'], row['lon'], row['wind_knots'])
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
    wn = max(0.0, min(1.0, (wind - 10) / 140.0))
    # hue from 0.6 (blue) down to 0.0 (red)
    h = 0.6 * (1.0 - wn)
    r, g, b = colorsys.hsv_to_rgb(h, 0.85, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)


def main(argv):
    # default to the sample CSV bundled with the package (script-relative)
    here = __file__
    import os
    here_dir = os.path.dirname(os.path.abspath(here))
    path = os.path.join(here_dir, 'sample_typhoons.csv')
    if len(argv) > 1:
        path = argv[1]

    df = load_csv(path)
    typhoons = build_typhoons(df)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    running = True
    t0 = time.time()

    while running:
        dt = clock.tick(30) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG)

        now = time.time() - t0

        # create an overlay surface for trails with alpha
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # draw each typhoon as a moving spiral at interpolated position
        for ty in typhoons:
            interp = ty.interpolated(now, speed=0.22)
            if interp is None:
                continue
            lat, lon, wind = interp
            x, y = latlon_to_xy(lat, lon)

            # record trail (recent positions)
            ty.trail.append((x, y, wind, now))

            # draw fading trail
            trail_list = list(ty.trail)
            L = len(trail_list)
            for i, (tx, ty_y, tw, tt) in enumerate(trail_list):
                age_frac = (i + 1) / max(1, L)
                a = int(40 + 215 * age_frac)
                col = wind_to_color(tw) + (a,)
                radius_dot = max(1, int(2 + (tw / 150.0) * 6 * age_frac))
                pygame.draw.circle(overlay, col, (tx, ty_y), radius_dot)

            # map wind to radius and color for main spiral
            radius = 8 + (wind / 100.0) * 160
            color = wind_to_color(wind)
            angle = now * 0.9
            draw_spiral(screen, (x, y), radius, angle, color, thickness=3)

            # label
            font = pygame.font.SysFont(None, 20)
            label = font.render(f"{ty.name} ({int(wind)} kt)", True, (220, 220, 220))
            screen.blit(label, (x + 10, y + 10))

        # blit trails overlay last so it sits under/over as desired
        screen.blit(overlay, (0, 0))

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main(sys.argv)
