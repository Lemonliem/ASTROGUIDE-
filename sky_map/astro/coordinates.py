"""Преобразования координат — только numpy / astropy, без Plotly."""
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.utils import iers

try:                                    # работаем без интернета
    iers.conf.auto_download = False
except Exception:
    pass


def local_sidereal_deg(t: Time, lon_deg: float) -> float:
    try:
        return float(t.sidereal_time("mean", longitude=lon_deg * u.deg).deg)
    except Exception:
        d = t.jd - 2451545.0
        return float((280.46061837 + 360.98564736629 * d + lon_deg) % 360.0)


def radec_to_altaz(ra_deg, dec_deg, dt, lat, lon):
    """RA/Dec (J2000) → высота/азимут (градусы). Векторизовано."""
    ra  = np.radians(np.atleast_1d(np.asarray(ra_deg,  dtype=float)))
    dec = np.radians(np.atleast_1d(np.asarray(dec_deg, dtype=float)))
    phi = np.radians(lat)
    h   = np.radians(local_sidereal_deg(Time(dt), lon)) - ra
    east  = -np.cos(dec) * np.sin(h)
    north =  np.sin(dec) * np.cos(phi) - np.cos(dec) * np.cos(h) * np.sin(phi)
    up    =  np.sin(dec) * np.sin(phi) + np.cos(dec) * np.cos(h) * np.cos(phi)
    alt   =  np.degrees(np.arcsin(np.clip(up, -1.0, 1.0)))
    az    =  np.degrees(np.arctan2(east, north)) % 360.0
    return alt, az


def altaz_to_xyz(alt_deg, az_deg, r=1.0):
    """Высота/азимут → (x=Восток, y=Север, z=Зенит) на сфере радиуса r."""
    alt = np.radians(np.asarray(alt_deg, dtype=float))
    az  = np.radians(np.asarray(az_deg,  dtype=float))
    return (r * np.cos(alt) * np.sin(az),
            r * np.cos(alt) * np.cos(az),
            r * np.sin(alt))