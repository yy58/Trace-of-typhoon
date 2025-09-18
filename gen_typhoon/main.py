import argparse
import math
import random
import time

import pygame
import numpy as np

from typhoon_art.loader import load_typhoon_csv


WIDTH = 1280
HEIGHT = 800


def latlon_to_xy(lat, lon, w=WIDTH, h=HEIGHT):
    # equirectangular projection: lon [-180,180] -> x [0,w], lat [-90,90] -> y [h,0]
    x = (lon + 180.0) / 360.0 * w
    y = (90.0 - lat) / 180.0 * h
    return x, y


def wind_to_brightness(wind, scale=1.0):
    # map wind (knots) to brightness 0..1
    return min(1.0, max(0.0, (wind / 150.0) * scale))


def pressure_to_flicker(pressure, scale=1.0):
    # lower pressure -> faster flicker; pressure in hPa typical range 870..1050
    # normalized low->high flicker frequency
    if pressure is None:
        return 0.5 * scale
    p = float(pressure)
    freq = (1050.0 - p) / (1050.0 - 870.0)
    return max(0.05, freq * scale)


def make_glow_surface(radius, color, intensity=1.0):
    # simple gaussian-like alpha falloff
    size = max(2, int(radius * 2))
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size / 2.0
    for y in range(size):
        for x in range(size):
            dx = x - cx + 0.5
            dy = y - cy + 0.5
            d = math.hypot(dx, dy)
            t = max(0.0, 1.0 - (d / (size / 2.0)))
            alpha = int((t**2) * 255 * intensity)
            if alpha:
                surf.set_at((x, y), (*color, alpha))
    return surf


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default='gen_typhoon/sample_typhoons.csv')
    ap.add_argument('--width', type=int, default=WIDTH)
    ap.add_argument('--height', type=int, default=HEIGHT)
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--brightness-scale', type=float, default=1.0)
    ap.add_argument('--flicker-scale', type=float, default=1.0)
    args = ap.parse_args(argv)

    random.seed(args.seed)
    np.random.seed(args.seed)

    data = load_typhoon_csv(args.csv)

    pygame.init()
    screen = pygame.display.set_mode((args.width, args.height))
    clock = pygame.time.Clock()

    # Instead of grouping into map cells, place each data point on a centered polar shell
    cx = args.width / 2.0
    cy = args.height / 2.0
    max_r = min(args.width, args.height) * 0.45
    inner_r = min(60, max_r * 0.15)

    particles = []
    for _, row in data.iterrows():
        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            wind = float(row['wind'])
        except Exception:
            continue
        # normalize lon into -180..180
        if lon > 180:
            lon = lon - 360
        # map lat -> radius (polar shell), lon -> angle
        frac_lat = (lat + 90.0) / 180.0
        r = inner_r + (1.0 - frac_lat) * (max_r - inner_r)
        # add small random radial jitter so points don't overlap exactly
        r += random.uniform(-6.0, 6.0)
        angle0 = math.radians(lon)
        # rotation speed depends on wind (stronger winds rotate slightly faster)
        rot_speed = 0.05 + (max(0.0, wind) / 400.0)
        phase = random.random() * math.pi * 2
        size = max(2.0, min(28.0, wind / 3.0 if wind is not None else 3.0))
        brightness = wind_to_brightness(wind, scale=args.brightness_scale)
        particles.append({
            'angle0': angle0,
            'r': r,
            'rot_speed': rot_speed,
            'phase': phase,
            'size': size,
            'brightness': brightness,
            'wind': wind,
        })

    # precompute glow surfaces cache
    glow_cache = {}

    running = True
    t0 = time.time()
    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        screen.fill((6, 8, 15))  # night sky

        now = time.time() - t0

        # draw revolving particles placed on a shell around center
        for p in particles:
            angle = p['angle0'] + now * p['rot_speed']
            x = cx + math.cos(angle) * p['r']
            y = cy + math.sin(angle) * p['r']

            b = p['brightness']
            # flicker using pseudo-pressure heuristic
            approx_pressure = 1010.0 - (p['wind'] * 0.5) if p['wind'] is not None else None
            flicker = pressure_to_flicker(approx_pressure, scale=args.flicker_scale)
            flick = 0.6 + 0.4 * math.sin(now * (1.0 + flicker * 6.0) + p['phase'])
            intensity = b * flick

            radius = max(2.0, p['size'] * (0.6 + intensity))
            key = (int(radius), int(max(1, min(255, intensity * 255))))
            color = (200, 220, 255)
            surf = glow_cache.get(key)
            if surf is None:
                surf = make_glow_surface(radius, color, intensity=1.0)
                glow_cache[key] = surf

            sx = int(x - surf.get_width() / 2)
            sy = int(y - surf.get_height() / 2)
            screen.blit(surf, (sx, sy), special_flags=pygame.BLEND_ADD)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
