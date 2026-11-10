"""
Оркестратор: собирает всё состояние неба для момента (dt, lat, lon).
Возвращает обычный dict — без Plotly, без Dash.
"""
import numpy as np

from .catalog import load_stars, load_constellations
from .coordinates import radec_to_altaz, altaz_to_xyz
from .planets import compute_planets


def compute_sky_state(dt, lat: float, lon: float) -> dict:
    stars = load_stars()
    const = load_constellations()

    # ── звёзды ──
    alt_s, az_s = radec_to_altaz(stars["ra"], stars["dec"], dt, lat, lon)
    xs, ys, zs = altaz_to_xyz(alt_s, az_s)

    # ── планеты ──
    planets = compute_planets(dt, lat, lon)

    # ── сегменты созвездий (дуги большого круга по координатам) ──
    segs = []
    for ra_a, dec_a, ra_b, dec_b, name in const["segments"]:
        segs.append((ra_a, dec_a, ra_b, dec_b, name))
    alt_a = np.array([radec_to_altaz(ra_a, dec_a, dt, lat, lon)[0][0] for ra_a, dec_a, _, _, _ in segs])
    az_a  = np.array([radec_to_altaz(ra_a, dec_a, dt, lat, lon)[1][0] for ra_a, dec_a, _, _, _ in segs])
    alt_b = np.array([radec_to_altaz(ra_b, dec_b, dt, lat, lon)[0][0] for _, _, ra_b, dec_b, _ in segs])
    az_b  = np.array([radec_to_altaz(ra_b, dec_b, dt, lat, lon)[1][0] for _, _, ra_b, dec_b, _ in segs])
    xa, ya, za = altaz_to_xyz(alt_a, az_a)
    xb, yb, zb = altaz_to_xyz(alt_b, az_b)

    # ── центроиды подписей ──
    centroids = []
    for cname, (ra_c, dec_c) in const["centroids"].items():
        alt_c, az_c = radec_to_altaz(ra_c, dec_c, dt, lat, lon)
        xc, yc, zc = altaz_to_xyz(alt_c, az_c)
        centroids.append({
            "name": cname,
            "alt":  float(alt_c[0]),
            "xyz":  (float(xc[0]), float(yc[0]), float(zc[0])),
            "major": cname in const["major"],
        })

    return {
        "dt": dt,
        "lat": lat,
        "lon": lon,
        "stars": {
            "x": xs, "y": ys, "z": zs,
            "alt": alt_s, "mag": stars["mag"],
        },
        "planets": planets,
        "constellation_segments": {
            "xa": xa, "ya": ya, "za": za,
            "xb": xb, "yb": yb, "zb": zb,
            "names": [s[4] for s in segs],
        },
        "constellation_centroids": centroids,
    }