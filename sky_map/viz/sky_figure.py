"""Сборка go.Figure из состояния, подготовленного sky_state. Всё — только Plotly."""
import numpy as np
import plotly.graph_objects as go

from . import style
from ..astro.coordinates import altaz_to_xyz


# ── утилиты ─────────────────────────────────────────────────────────────
def _line(x, y, z, color, width, name="", dash=None):
    line = dict(color=color, width=width)
    if dash:
        line["dash"] = dash
    return go.Scatter3d(x=x, y=y, z=z, mode="lines",
                        line=line, hoverinfo="skip", name=name)


def _empty_fig(bg=style.SKY_BG):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=bg, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False, uirevision="sky3d",
    )
    return fig


# ── слои ────────────────────────────────────────────────────────────────
def _ground():
    n = 90
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    # Опускаем землю чуть ниже нуля, чтобы камера не проходила ровно по ее плоскости
    z_offset = -0.1

    mesh = go.Mesh3d(
        x=np.r_[0, np.sin(a)], y=np.r_[0, np.cos(a)], z=np.full(n + 1, z_offset),
        i=np.zeros(n, dtype=int), j=np.arange(1, n + 1),
        k=np.r_[np.arange(2, n + 1), 1],
        color=style.GROUND_COLOR, opacity=style.GROUND_OPACITY,
        flatshading=True,
        lighting=dict(ambient=1, diffuse=0, specular=0),
        hoverinfo="skip", name="Земля",
    )
    az = np.linspace(0, 360, 181)
    hx, hy, hz = altaz_to_xyz(np.zeros_like(az), az)
    # Кромку горизонта тоже опускаем
    rim = _line(hx, hy, np.full_like(hz, z_offset), style.HORIZON_COLOR, style.HORIZON_WIDTH, "Горизонт")
    return [mesh, rim]


def _cardinal_labels():
    dirs = {"С": 0, "СВ": 45, "В": 90, "ЮВ": 135,
            "Ю": 180, "ЮЗ": 225, "З": 270, "СЗ": 315}
    x, y, z = altaz_to_xyz(np.full(len(dirs), 4.0),
                            np.array(list(dirs.values()), dtype=float))
    return go.Scatter3d(
        x=x, y=y, z=z, mode="text", text=list(dirs),
        textfont=dict(color=style.CARDINAL_COLOR, size=style.CARDINAL_SIZE),
        hoverinfo="skip", name="Стороны света",
    )


def _altitude_labels():
    alts = style.DEGREE_ALT_LABELS
    az  = np.array([0.0, 180.0] * len(alts))
    al  = np.array(list(alts) * 2)
    x, y, z = altaz_to_xyz(al, az)
    txt = [f"{a}°" for a in al]
    return go.Scatter3d(
        x=x, y=y, z=z, mode="text", text=txt,
        textfont=dict(color=style.DEGREE_COLOR, size=style.DEGREE_SIZE),
        hoverinfo="skip", name="Высота",
    )


def _grid():
    xs, ys, zs = [], [], []
    az = np.linspace(0, 360, 181)
    for alt in (-60, -30, 30, 60):
        x, y, z = altaz_to_xyz(np.full_like(az, alt), az)
        xs += list(x) + [None]; ys += list(y) + [None]; zs += list(z) + [None]
    alts = np.linspace(-90, 90, 61)
    for a in range(0, 360, style.GRID_AZ_STEP):
        x, y, z = altaz_to_xyz(alts, np.full_like(alts, a))
        xs += list(x) + [None]; ys += list(y) + [None]; zs += list(z) + [None]
    return _line(xs, ys, zs, style.GRID_COLOR, style.GRID_WIDTH, "Сетка")


def _ecliptic(state):
    from astropy.coordinates import SkyCoord, BarycentricMeanEcliptic
    import astropy.units as u
    from ..astro.coordinates import radec_to_altaz

    lam = np.linspace(0, 360, 361) * u.deg
    icrs = SkyCoord(lon=lam, lat=0 * u.deg,
                    frame=BarycentricMeanEcliptic).icrs
    alt, az = radec_to_altaz(icrs.ra.deg, icrs.dec.deg,
                             state["dt"], state["lat"], state["lon"])
    x, y, z = altaz_to_xyz(alt, az)
    return _line(x, y, z, style.ECLIPTIC_COLOR, style.ECLIPTIC_WIDTH, "Эклиптика")


def _stars(state):
    s = state["stars"]
    alt, mag = s["alt"], s["mag"]
    size = np.clip(style.STAR_SIZE_BASE - style.STAR_SIZE_K * mag,
                   style.STAR_SIZE_MIN, style.STAR_SIZE_MAX)
    out = []
    above = alt >= 0
    below = ~above
    for mask, color, op, name in (
        (above, style.STAR_COLOR,           style.STAR_OPACITY,       "Звёзды"),
        (below, style.STAR_COLOR_BELOW_HOR, style.STAR_OPACITY_BELOW, "Звёзды ниже горизонта"),
    ):
        if not mask.any():
            continue
        out.append(go.Scatter3d(
            x=s["x"][mask], y=s["y"][mask], z=s["z"][mask],
            mode="markers",
            marker=dict(size=size[mask], color=color, opacity=op,
                        line=dict(width=0)),
            hoverinfo="skip", name=name,
        ))
    return out


def _constellation_lines(state):
    seg = state["constellation_segments"]
    n_pts = style.CONSTELLATION_ARC_POINTS
    t = np.linspace(0, 1, n_pts)[None, :]
    xa, ya, za = seg["xa"][:, None], seg["ya"][:, None], seg["za"][:, None]
    xb, yb, zb = seg["xb"][:, None], seg["yb"][:, None], seg["zb"][:, None]
    x = (1 - t) * xa + t * xb
    y = (1 - t) * ya + t * yb
    z = (1 - t) * za + t * zb
    norm = np.sqrt(x*x + y*y + z*z)
    with np.errstate(invalid="ignore", divide="ignore"):
        x = x / norm; y = y / norm; z = z / norm
    gap = np.full((x.shape[0], 1), np.nan)
    x = np.hstack([x, gap]).ravel()
    y = np.hstack([y, gap]).ravel()
    z = np.hstack([z, gap]).ravel()
    return _line(x, y, z,
                 style.CONSTELLATION_LINE_COLOR,
                 style.CONSTELLATION_LINE_WIDTH,
                 "Созвездия")


def _constellation_labels(state):
    items = [c for c in state["constellation_centroids"]
             if c["major"] and c["alt"] >= style.CONSTELLATION_LABEL_ALT_MIN]
    if not items:
        return None
    x = [c["xyz"][0] for c in items]
    y = [c["xyz"][1] for c in items]
    z = [c["xyz"][2] for c in items]
    return go.Scatter3d(
        x=x, y=y, z=z, mode="text",
        text=[c["name"] for c in items],
        textfont=dict(color=style.CONSTELLATION_LABEL_COLOR,
                      size=style.CONSTELLATION_LABEL_SIZE),
        hoverinfo="skip", name="Созвездия",
    )


def _planets(state):
    out = []
    for p in state["planets"]:
        x, y, z = altaz_to_xyz(p["alt"], p["az"])
        x, y, z = float(x), float(y), float(z)

        if p["key"] == "sun":
            out.append(go.Scatter3d(
                x=[x], y=[y], z=[z], mode="markers",
                marker=dict(size=p["size"] * style.SUN_GLOW_SCALE,
                            color=p["color"],
                            opacity=style.SUN_GLOW_OPACITY),
                hoverinfo="skip", name="Свечение Солнца",
            ))
        out.append(go.Scatter3d(
            x=[x], y=[y], z=[z], mode="markers+text",
            marker=dict(size=p["size"], color=p["color"],
                        line=dict(color=style.PLANET_OUTLINE_COLOR, width=1),
                        opacity=1.0 if p["alt"] >= 0 else 0.55),
            text=[p["name"]], textposition="bottom center",
            textfont=dict(color=style.PLANET_LABEL_COLOR,
                          size=style.PLANET_LABEL_SIZE),
            hovertext=[f"{p['name']}: выс {p['alt']:+.1f}°, аз {p['az']:.1f}°"],
            hoverinfo="text", name=p["name"],
        ))
    return out


# ── сборка ──────────────────────────────────────────────────────────────
def build_sky_figure(state: dict, layers: set[str]) -> go.Figure:
    fig = _empty_fig()
    for tr in _ground():
        fig.add_trace(tr)
    fig.add_trace(_cardinal_labels())
    fig.add_trace(_altitude_labels())
    if "grid" in layers:
        fig.add_trace(_grid())
    if "ecliptic" in layers:
        fig.add_trace(_ecliptic(state))
    if "const" in layers:
        fig.add_trace(_constellation_lines(state))
    if "const_names" in layers:
        lab = _constellation_labels(state)
        if lab is not None:
            fig.add_trace(lab)
    if "stars" in layers:
        for tr in _stars(state):
            fig.add_trace(tr)
    if "planets" in layers:
        for tr in _planets(state):
            fig.add_trace(tr)

    axis = dict(visible=False, range=[-1.45, 1.45], showbackground=False)

    # Всегда передаем стартовую камеру
    eye = -style.EYE_DIST * np.array(style.DEFAULT_LOOK)
    scene_dict = dict(
        xaxis=axis, yaxis=axis, zaxis=axis,
        aspectmode="cube", bgcolor=style.SKY_BG,
        camera=dict(
            eye=dict(x=float(eye[0]), y=float(eye[1]), z=float(eye[2])),
            center=dict(x=0, y=0, z=0),
            up=dict(x=style.UP_VECTOR[0], y=style.UP_VECTOR[1], z=style.UP_VECTOR[2]),
            projection=dict(type="perspective"),
        )
    )

    fig.update_layout(
        scene=scene_dict,
        paper_bgcolor=style.SKY_BG,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        uirevision="sky3d",  # <--- Эта строка заставляет Plotly запоминать ваш ракурс
    )
    return fig