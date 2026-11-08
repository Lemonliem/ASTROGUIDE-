"""
sky_map.py — «Сфера» звёздного неба для AstroGuide.

Небесная сфера рисуется через go.Scattergeo в ортографической проекции:
прямое восхождение (RA) играет роль долготы, склонение (Dec) — широты.
Сферу можно вращать мышкой, колесо — масштаб.

Astropy используется для:
  * времени и звёздного времени (Time.sidereal_time);
  * положения Солнца, Луны и планет (get_body, встроенные эфемериды);
  * линий эклиптики и плоскости Млечного Пути (SkyCoord + преобразование в ICRS).
"""
import numpy as np
import plotly.graph_objects as go
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import (
    SkyCoord,
    BarycentricMeanEcliptic,
    get_body,
    solar_system_ephemeris,
)
from astropy.utils import iers

# Работаем без интернета: не пытаемся скачивать таблицы IERS
try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "warn"
except Exception:  # другая версия astropy — не критично
    pass

# Точка наблюдения по умолчанию (меняется в интерфейсе)
DEFAULT_LAT = 55.75   # широта, °
DEFAULT_LON = 37.62   # долгота, °

# ---------------------------------------------------------------- цвета
SPHERE_COLOR = "#0A1128"
GRID_COLOR = "rgba(130,210,255,0.28)"
FRAME_COLOR = "#82D2FF"
STAR_COLOR = "#F4F8FF"
LABEL_COLOR = "#CFE8FF"
CONST_COLOR = "rgba(130,210,255,0.55)"
ECLIPTIC_COLOR = "#FFD166"
HORIZON_COLOR = "#7BE495"
MILKY_COLOR = "rgba(190,170,255,0.16)"

# ---------------------------------------------------------------- каталог
# ключ: (название, RA°, Dec°, звёздная величина)  — эпоха J2000
STARS = {
    "sirius":     ("Сириус",            101.287, -16.716, -1.46),
    "canopus":    ("Канопус",            95.988, -52.696, -0.74),
    "arcturus":   ("Арктур",            213.915,  19.182, -0.05),
    "rigil":      ("Ригиль Кентавр",    219.900, -60.834, -0.01),
    "vega":       ("Вега",              279.235,  38.784,  0.03),
    "capella":    ("Капелла",            79.172,  45.998,  0.08),
    "rigel":      ("Ригель",             78.634,  -8.202,  0.13),
    "procyon":    ("Процион",           114.825,   5.225,  0.34),
    "betelgeuse": ("Бетельгейзе",        88.793,   7.407,  0.50),
    "achernar":   ("Ахернар",            24.429, -57.237,  0.46),
    "hadar":      ("Хадар",             210.956, -60.373,  0.61),
    "altair":     ("Альтаир",           297.696,   8.868,  0.76),
    "acrux":      ("Акрукс",            186.650, -63.099,  0.76),
    "aldebaran":  ("Альдебаран",         68.980,  16.509,  0.85),
    "spica":      ("Спика",             201.298, -11.161,  0.97),
    "antares":    ("Антарес",           247.352, -26.432,  1.06),
    "pollux":     ("Поллукс",           116.329,  28.026,  1.14),
    "fomalhaut":  ("Фомальгаут",        344.413, -29.622,  1.16),
    "deneb":      ("Денеб",             310.358,  45.280,  1.25),
    "mimosa":     ("Бекрукс",           191.930, -59.689,  1.25),
    "regulus":    ("Регул",             152.093,  11.967,  1.35),
    "castor":     ("Кастор",            113.650,  31.888,  1.58),
    "gacrux":     ("Гакрукс",           187.791, -57.113,  1.64),
    "bellatrix":  ("Беллатрикс",         81.283,   6.350,  1.64),
    "elnath":     ("Эльнат",             81.573,  28.608,  1.65),
    "alnilam":    ("Альнилам",           84.053,  -1.202,  1.69),
    "alnitak":    ("Альнитак",           85.190,  -1.943,  1.77),
    "shaula":     ("Шаула",             263.402, -37.104,  1.62),
    "dubhe":      ("Дубхе",             165.932,  61.751,  1.79),
    "alioth":     ("Алиот",             193.507,  55.960,  1.77),
    "mirfak":     ("Мирфак",             51.081,  49.861,  1.80),
    "alkaid":     ("Алькаид",           206.885,  49.313,  1.86),
    "polaris":    ("Полярная",           37.955,  89.264,  1.98),
    "mizar":      ("Мицар",             200.981,  54.925,  2.04),
    "saiph":      ("Саиф",               86.939,  -9.670,  2.06),
    "algieba":    ("Альгиеба",          154.993,  19.842,  2.01),
    "denebola":   ("Денебола",          177.265,  14.572,  2.14),
    "sadr":       ("Садр",              305.557,  40.257,  2.20),
    "mintaka":    ("Минтака",            83.002,  -0.299,  2.23),
    "schedar":    ("Шедар",              10.127,  56.537,  2.24),
    "caph":       ("Каф",                 2.295,  59.150,  2.27),
    "merak":      ("Мерак",             165.460,  56.382,  2.37),
    "phecda":     ("Фекда",             178.458,  53.695,  2.44),
    "gienah":     ("Гиенах",            311.553,  33.970,  2.50),
    "gamma_cas":  ("γ Кассиопеи",        14.177,  60.717,  2.47),
    "ruchbah":    ("Рукбах",             21.454,  60.235,  2.68),
    "delta_cru":  ("δ Южного Креста",   183.786, -58.749,  2.80),
    "delta_cyg":  ("δ Лебедя",          296.244,  45.131,  2.87),
    "albireo":    ("Альбирео",          292.680,  27.960,  3.10),
    "megrez":     ("Мегрец",            183.857,  57.033,  3.31),
    "segin":      ("Сегин",              28.599,  63.670,  3.38),
}

# Созвездия: название -> пары звёзд, соединённые линиями
CONSTELLATIONS = {
    "Орион": [
        ("betelgeuse", "bellatrix"), ("betelgeuse", "alnitak"),
        ("bellatrix", "mintaka"), ("alnitak", "alnilam"),
        ("alnilam", "mintaka"), ("alnitak", "saiph"),
        ("mintaka", "rigel"), ("rigel", "saiph"),
    ],
    "Большая Медведица": [
        ("dubhe", "merak"), ("merak", "phecda"), ("phecda", "megrez"),
        ("megrez", "dubhe"), ("megrez", "alioth"),
        ("alioth", "mizar"), ("mizar", "alkaid"),
    ],
    "Кассиопея": [
        ("caph", "schedar"), ("schedar", "gamma_cas"),
        ("gamma_cas", "ruchbah"), ("ruchbah", "segin"),
    ],
    "Южный Крест": [("acrux", "gacrux"), ("mimosa", "delta_cru")],
    "Лебедь": [
        ("deneb", "sadr"), ("sadr", "albireo"),
        ("gienah", "sadr"), ("sadr", "delta_cyg"),
    ],
    "Лев": [("regulus", "algieba"), ("algieba", "denebola")],
}

# ключ astropy, подпись, цвет, размер маркера
PLANETS = [
    ("sun",     "Солнце",   "#FFD43B", 18),
    ("moon",    "Луна",     "#E9ECEF", 15),
    ("mercury", "Меркурий", "#ADB5BD", 8),
    ("venus",   "Венера",   "#FFE8A3", 11),
    ("mars",    "Марс",     "#FF6B4A", 10),
    ("jupiter", "Юпитер",   "#F4C58A", 13),
    ("saturn",  "Сатурн",   "#E3C78A", 12),
    ("uranus",  "Уран",     "#7FE0E6", 8),
    ("neptune", "Нептун",   "#6C8CFF", 8),
]


# ---------------------------------------------------------------- вычисления
def to_lon(ra_deg):
    """RA -> долгота на карте. Знак минус: небо смотрим изнутри сферы."""
    return (-np.asarray(ra_deg, dtype=float) + 180.0) % 360.0 - 180.0


def local_sidereal_deg(t, lon_deg):
    """Местное звёздное время в градусах (RA точки над головой)."""
    try:
        return float(t.sidereal_time("mean", longitude=lon_deg * u.deg).deg)
    except Exception:
        # запасной вариант: приближённая формула GMST
        d = t.jd - 2451545.0
        return float((280.46061837 + 360.98564736629 * d + lon_deg) % 360.0)


def horizon_to_equatorial(az_deg, alt_deg, lst_deg, lat_deg):
    """Азимут/высота -> RA/Dec для данного звёздного времени и широты."""
    az, alt, lat = (np.radians(np.asarray(x, dtype=float))
                    for x in (az_deg, alt_deg, lat_deg))
    sin_dec = np.sin(alt) * np.sin(lat) + np.cos(alt) * np.cos(lat) * np.cos(az)
    dec = np.arcsin(np.clip(sin_dec, -1, 1))
    ha = np.arctan2(
        -np.cos(alt) * np.sin(az),
        np.sin(alt) * np.cos(lat) - np.cos(alt) * np.sin(lat) * np.cos(az),
    )
    ra = (lst_deg - np.degrees(ha)) % 360.0
    return ra, np.degrees(dec)


def planet_positions(t):
    """Положения Солнца, Луны и планет (RA/Dec в градусах) через astropy."""
    result = []
    with solar_system_ephemeris.set("builtin"):
        for key, name, color, size in PLANETS:
            try:
                c = get_body(key, t)
                result.append((name, color, size, float(c.ra.deg), float(c.dec.deg)))
            except Exception:
                continue  # одно тело не посчиталось — остальные рисуем
    return result


def ecliptic_line():
    lam = np.linspace(0, 360, 361) * u.deg
    c = SkyCoord(lon=lam, lat=0 * u.deg, frame=BarycentricMeanEcliptic).icrs
    return c.ra.deg, c.dec.deg


def galactic_plane_line():
    l = np.linspace(0, 360, 361) * u.deg
    c = SkyCoord(l=l, b=0 * u.deg, frame="galactic").icrs
    return c.ra.deg, c.dec.deg


def _segments(pairs):
    """Список пар звёзд -> массивы lon/lat с разрывами (None) между отрезками."""
    lons, lats = [], []
    for a, b in pairs:
        for key in (a, b):
            _, ra, dec, _ = STARS[key]
            lons.append(float(to_lon(ra)))
            lats.append(dec)
        lons.append(None)
        lats.append(None)
    return lons, lats


# ---------------------------------------------------------------- рисование
def build_sky_figure(layers, lat, lon, paper_bg="#C6E7FF"):
    """
    layers — список включённых слоёв:
        grid, const, names, ecliptic, horizon, milky, planets
    Возвращает (figure, строка_с_информацией).
    """
    layers = set(layers or [])
    t = Time.now()
    lst = local_sidereal_deg(t, lon)

    fig = go.Figure()

    # --- Млечный Путь (широкая бледная полоса) ---
    if "milky" in layers:
        ra, dec = galactic_plane_line()
        fig.add_trace(go.Scattergeo(
            lon=to_lon(ra), lat=dec, mode="lines",
            line=dict(color=MILKY_COLOR, width=26),
            hoverinfo="skip", name="Млечный Путь",
        ))

    # --- Эклиптика ---
    if "ecliptic" in layers:
        ra, dec = ecliptic_line()
        fig.add_trace(go.Scattergeo(
            lon=to_lon(ra), lat=dec, mode="lines",
            line=dict(color=ECLIPTIC_COLOR, width=1.5, dash="dash"),
            hoverinfo="skip", name="Эклиптика",
        ))

    # --- Горизонт и стороны света ---
    if "horizon" in layers:
        az = np.linspace(0, 360, 361)
        ra, dec = horizon_to_equatorial(az, 0, lst, lat)
        fig.add_trace(go.Scattergeo(
            lon=to_lon(ra), lat=dec, mode="lines",
            line=dict(color=HORIZON_COLOR, width=2),
            hoverinfo="skip", name="Горизонт",
        ))
        cards = [(0, "С"), (90, "В"), (180, "Ю"), (270, "З")]
        c_ra, c_dec = horizon_to_equatorial([a for a, _ in cards], 0, lst, lat)
        fig.add_trace(go.Scattergeo(
            lon=to_lon(c_ra), lat=c_dec, mode="text",
            text=[s for _, s in cards],
            textfont=dict(color=HORIZON_COLOR, size=16),
            hoverinfo="skip", name="Стороны света",
        ))

    # --- Подписи часов прямого восхождения вдоль экватора ---
    if "grid" in layers:
        hours = np.arange(0, 24, 2)
        fig.add_trace(go.Scattergeo(
            lon=to_lon(hours * 15.0), lat=np.zeros(len(hours)),
            mode="text", text=[f"{h}ч" for h in hours],
            textposition="top center",
            textfont=dict(color=FRAME_COLOR, size=11),
            hoverinfo="skip", name="RA",
        ))

    # --- Созвездия ---
    if "const" in layers:
        all_pairs = [p for pairs in CONSTELLATIONS.values() for p in pairs]
        lons, lats = _segments(all_pairs)
        fig.add_trace(go.Scattergeo(
            lon=lons, lat=lats, mode="lines",
            line=dict(color=CONST_COLOR, width=1.4),
            hoverinfo="skip", name="Созвездия",
        ))
        names, c_lon, c_lat = [], [], []
        for cname, pairs in CONSTELLATIONS.items():
            keys = {k for p in pairs for k in p}
            c_lon.append(float(to_lon(np.mean([STARS[k][1] for k in keys]))))
            c_lat.append(float(np.mean([STARS[k][2] for k in keys])))
            names.append(cname)
        fig.add_trace(go.Scattergeo(
            lon=c_lon, lat=c_lat, mode="text", text=names,
            textposition="bottom center",
            textfont=dict(color=CONST_COLOR, size=12),
            hoverinfo="skip", name="Названия созвездий",
        ))

    # --- Звёзды (ореол + сами звёзды) ---
    keys = list(STARS)
    s_lon = to_lon([STARS[k][1] for k in keys])
    s_lat = [STARS[k][2] for k in keys]
    mags = np.array([STARS[k][3] for k in keys])
    sizes = np.clip(11.0 - 2.4 * mags, 4, 17)
    hover = [f"{STARS[k][0]} · {STARS[k][3]:+.2f}m" for k in keys]
    labels = [STARS[k][0] if (STARS[k][3] <= 1.5 and "names" in layers) else ""
              for k in keys]

    fig.add_trace(go.Scattergeo(
        lon=s_lon, lat=s_lat, mode="markers",
        marker=dict(size=sizes * 2.2, color=STAR_COLOR, opacity=0.12),
        hoverinfo="skip", name="Ореолы",
    ))
    fig.add_trace(go.Scattergeo(
        lon=s_lon, lat=s_lat, mode="markers+text",
        marker=dict(size=sizes, color=STAR_COLOR, opacity=0.95,
                    line=dict(width=0)),
        text=labels, textposition="top right",
        textfont=dict(color=LABEL_COLOR, size=11),
        hovertext=hover, hoverinfo="text", name="Звёзды",
    ))

    # --- Солнце, Луна, планеты (astropy) ---
    if "planets" in layers:
        bodies = planet_positions(t)
        if bodies:
            fig.add_trace(go.Scattergeo(
                lon=to_lon([b[3] for b in bodies]),
                lat=[b[4] for b in bodies],
                mode="markers+text",
                marker=dict(size=[b[2] for b in bodies],
                            color=[b[1] for b in bodies],
                            line=dict(color="white", width=1)),
                text=[b[0] for b in bodies], textposition="bottom right",
                textfont=dict(color="white", size=12),
                hovertext=[f"{b[0]}: RA {b[3]/15:.2f}ч, Dec {b[4]:+.1f}°"
                           for b in bodies],
                hoverinfo="text", name="Планеты",
            ))

    # --- Зенит ---
    fig.add_trace(go.Scattergeo(
        lon=[float(to_lon(lst))], lat=[lat], mode="markers",
        marker=dict(symbol="cross", size=9, color=HORIZON_COLOR),
        hovertext=["Зенит"], hoverinfo="text", name="Зенит",
    ))

    # --- Сфера: проекция, сетка RA/Dec, фон ---
    show_grid = "grid" in layers
    fig.update_geos(
        projection=dict(type="orthographic",
                        rotation=dict(lon=float(to_lon(lst)), lat=lat, roll=0)),
        showland=False, showcoastlines=False, showcountries=False,
        showlakes=False, showrivers=False,
        showocean=True, oceancolor=SPHERE_COLOR,
        showframe=True, framecolor=FRAME_COLOR, framewidth=2,
        bgcolor="rgba(0,0,0,0)",
        lonaxis=dict(showgrid=show_grid, gridcolor=GRID_COLOR, gridwidth=0.7,
                     dtick=30, range=[-180, 180]),
        lataxis=dict(showgrid=show_grid, gridcolor=GRID_COLOR, gridwidth=0.7,
                     dtick=15, range=[-90, 90]),
    )
    fig.update_layout(
        paper_bgcolor=paper_bg,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        # одинаковое значение => вращение мышкой не сбрасывается при смене слоёв
        uirevision=f"{lat:.2f}_{lon:.2f}",
    )

    h = int(lst / 15)
    m = int((lst / 15 - h) * 60)
    info = (f"Время (UTC): {t.strftime('%Y-%m-%d %H:%M')} · "
            f"Звёздное время: {h:02d}ч {m:02d}м · "
            f"Зенит: RA {lst/15:.2f}ч, Dec {lat:+.1f}°")
    return fig, info
