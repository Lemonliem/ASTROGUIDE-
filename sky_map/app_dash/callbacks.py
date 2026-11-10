"""Callback'и Dash: связывают astro.sky_state и viz.sky_figure."""
from datetime import datetime, timedelta, timezone

from dash import Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate

from .. import config
from ..astro.sky_state import compute_sky_state
from ..viz.sky_figure import build_sky_figure


def register_callbacks(app):

    # ── базовое время: фиксируется при загрузке и по «Сбросить» ──
    @app.callback(
        Output("t0", "data"),
        Output("offset-min", "data", allow_duplicate=True),
        Output("offset-indicator", "children", allow_duplicate=True),
        Input("t0", "id"),            # триггер «при загрузке»
        prevent_initial_call="initial_duplicate",
    )
    def _init(_):
        return datetime.now(timezone.utc).isoformat(), 0, "Смещение: +0 мин"

    # ── кнопки управления временем ──
    @app.callback(
        Output("offset-min", "data", allow_duplicate=True),
        Output("offset-indicator", "children", allow_duplicate=True),
        Input("btn-add-30",  "n_clicks"),
        Input("btn-add-60",  "n_clicks"),
        Input("btn-set-max", "n_clicks"),
        Input("btn-reset",   "n_clicks"),
        State("offset-min", "data"),
        prevent_initial_call=True,
    )
    def _change_offset(_a, _b, _c, _d, current):
        cur = int(current or 0)
        trig = ctx.triggered_id
        if trig == "btn-add-30":
            cur += config.TIME_STEP_MIN
        elif trig == "btn-add-60":
            cur += 60
        elif trig == "btn-set-max":
            cur = config.TIME_MAX_MIN
        elif trig == "btn-reset":
            cur = 0
        cur = max(0, min(config.TIME_MAX_MIN, cur))
        label = "Смещение: " + _format_offset(cur)
        return cur, label

    # ── координаты ──
    @app.callback(
        Output("coords-error", "children"),
        Input("inp-lat", "value"),
        Input("inp-lon", "value"),
    )
    def _validate_coords(lat, lon):
        try:
            lat_f = float(lat); lon_f = float(lon)
        except (TypeError, ValueError):
            return "Введите числовые значения широты и долготы."
        if not (config.LAT_RANGE[0] <= lat_f <= config.LAT_RANGE[1]):
            return f"Широта должна быть в диапазоне {config.LAT_RANGE}."
        if not (config.LON_RANGE[0] <= lon_f <= config.LON_RANGE[1]):
            return f"Долгота должна быть в диапазоне {config.LON_RANGE}."
        return ""

    # ── главный callback: пересборка карты ──
    @app.callback(
        Output("sky-map",  "figure"),
        Output("sky-info", "children"),
        Output("coords-info", "children"),
        Input("layers",     "value"),
        Input("offset-min", "data"),
        Input("t0",         "data"),
        Input("inp-lat",    "value"),
        Input("inp-lon",    "value"),
        Input("coords-error","children"),
    )
    def _update_sky(layers, offset, t0, lat, lon, coord_err):
        if not t0 or coord_err:
            raise PreventUpdate
        try:
            lat_f = float(lat); lon_f = float(lon)
        except (TypeError, ValueError):
            raise PreventUpdate
        if not (config.LAT_RANGE[0] <= lat_f <= config.LAT_RANGE[1]
                and config.LON_RANGE[0] <= lon_f <= config.LON_RANGE[1]):
            raise PreventUpdate

        dt = datetime.fromisoformat(t0) + timedelta(minutes=int(offset or 0))
        import time as _t
        t_start = _t.perf_counter()
        state = compute_sky_state(dt, lat_f, lon_f)

        # Если триггером был именно t0 (первичная инициализация),
        # сбрасываем камеру на дефолт. Иначе — сохраняем текущий ракурс.
        is_initial = (ctx.triggered_id == "t0")
        #fig = build_sky_figure(state, set(layers or []), is_initial=is_initial)
        fig = build_sky_figure(state, set(layers or []))

        elapsed_ms = (_t.perf_counter() - t_start) * 1000

        sun = next((p for p in state["planets"] if p["key"] == "sun"),  None)
        moon = next((p for p in state["planets"] if p["key"] == "moon"), None)
        info = f"UTC {dt.strftime('%Y-%m-%d %H:%M')} · сдвиг {_format_offset(offset or 0)}"
        if sun:
            info += f" · Солнце: выс {sun['alt']:+.1f}°"
        if moon:
            info += f" · Луна: выс {moon['alt']:+.1f}°"
        info += f" · пересчёт {elapsed_ms:.0f} мс"

        coords_info = f"Наблюдатель: {lat_f:.2f}°, {lon_f:.2f}°"
        return fig, info, coords_info


def _format_offset(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    if h == 0:
        return f"+{m} мин"
    if m == 0:
        return f"+{h} ч"
    return f"+{h} ч {m} мин"