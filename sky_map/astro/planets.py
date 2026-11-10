"""Положения Солнца, Луны и планет для заданного момента/точки."""
from functools import lru_cache

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_body, solar_system_ephemeris

from ..config import PLANET_KEYS, PLANET_NAMES_RU
from ..viz import style
from .coordinates import radec_to_altaz


@lru_cache(maxsize=64)
def _location(lat: float, lon: float) -> EarthLocation:
    return EarthLocation.from_geodetic(lon * u.deg, lat * u.deg)


def compute_planets(dt, lat: float, lon: float) -> list[dict]:
    """
    Возвращает список словарей:
      {"key", "name", "alt", "az", "color", "size"}
    Плутон может быть недоступен без внешних эфемерид — тогда просто
    пропускается (см. README, раздел «Плутон»).
    """
    t   = Time(dt)
    loc = _location(lat, lon)
    out: list[dict] = []
    with solar_system_ephemeris.set("builtin"):
        for key in PLANET_KEYS:
            try:
                try:
                    body = get_body(key, t, loc)
                except Exception:
                    body = get_body(key, t)
            except Exception:
                continue                       # нет в builtin → пропускаем
            alt, az = radec_to_altaz(body.ra.deg, body.dec.deg, dt, lat, lon)
            name = PLANET_NAMES_RU[key]
            out.append({
                "key":   key,
                "name":  name,
                "alt":   float(alt[0]),
                "az":    float(az[0]),
                "color": style.PLANET_COLORS[name],
                "size":  style.PLANET_SIZES[name],
            })
    return out