import argparse
import math
import random
import time

import pygame
import numpy as np

from typhoon_art.loader import load_typhoon_csv


DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 800


def latlon_to_polar(lat, lon, w, h, inner=80, outer_scale=0.42):
    # Map latitude -> radial distance, longitude -> angle
    # center is screen center; lat -90..90 -> radius inner..outer
    cx = w / 2.0
    cy = h / 2.0
    max_r = min(w, h) * outer_scale
    r = inner + (1.0 - ((lat + 90.0) / 180.0)) * (max_r - inner)
    # lon may be in 0..360 or -180..180 — normalize
    lon_norm = lon
    try:
        lon_norm = float(lon)
    except Exception:
        pass
    if lon_norm > 180:
        lon_norm -= 360
    angle = math.radians(lon_norm)
    return cx, cy, r, angle


def wind_to_brightness(wind, scale=1.0):
    return min(1.0, max(0.0, (wind / 150.0) * scale))


def make_glow_surface(radius, color, intensity=1.0):
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
    ap.add_argument('--csv', default='gen_typhoon/sample_typhoons_small.csv')
    ap.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    ap.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--brightness-scale', type=float, default=1.0)
    ap.add_argument('--rotation-speed', type=float, default=0.2, help='global rotation speed multiplier')
    ap.add_argument('--shimmer-scale', type=float, default=1.0, help='amplitude of shimmer/twinkle')
    args = ap.parse_args(argv)

    random.seed(args.seed)
    np.random.seed(args.seed)

    data = load_typhoon_csv(args.csv)

    pygame.init()
    screen = pygame.display.set_mode((args.width, args.height))
    clock = pygame.time.Clock()

    # Build particles mapped to polar coordinates (so they revolve like a sky shell)
    particles = []
    for _, row in data.iterrows():
        try:
            lat = float(row['lat'])
            lon = float(row['lon'])
            wind = float(row['wind'])
        except Exception:
            continue
        cx, cy, base_r, base_angle = latlon_to_polar(lat, lon, args.width, args.height)
        # per-particle attributes
        phase = random.random() * math.tau
        rot_speed = (0.02 + (wind / 300.0)) * (0.5 + random.random() * 1.5)
        shimmer_freq = 1.0 + (random.random() * 3.0)
        size = max(1.5, min(28.0, wind / 3.0))
        brightness = wind_to_brightness(wind, scale=args.brightness_scale)
        particles.append({
            'cx': cx,
            'cy': cy,
            'base_r': base_r,
            'base_angle': base_angle,
            'wind': wind,
            'phase': phase,
            'rot_speed': rot_speed,
            'shimmer_freq': shimmer_freq,
            'size': size,
            'brightness': brightness,
        })

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

        screen.fill((6, 8, 15))

        now = time.time() - t0

        # subtle background stars (deterministic pattern)
        for i in range(120):
            rx = (i * 97 + 13) % args.width
            ry = (i * 53 + 29) % args.height
            screen.fill((5, 6, 10), rect=(rx, ry, 1, 1))

        # draw revolving particles with shimmer
        for p in particles:
            angle = p['base_angle'] + now * (args.rotation_speed * p['rot_speed'])
            # small radial breathing
            r = p['base_r'] * (1.0 + 0.02 * math.sin(now * 0.6 + p['phase']))
            x = p['cx'] + math.cos(angle) * r
            y = p['cy'] + math.sin(angle) * r

            # shimmer: sin-based twinkle plus a small random noise component
            shimmer = (0.6 + 0.4 * math.sin(now * p['shimmer_freq'] + p['phase'] * 0.7))
            shimmer *= (1.0 + 0.05 * math.sin(now * 7.3 + p['phase']))
            intensity = p['brightness'] * shimmer * args.shimmer_scale

            radius = max(1.0, p['size'] * (0.5 + intensity))
            color = (200, 220, 255)
            key = (int(radius), int(max(1, min(255, intensity * 255))))
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
