# """AstroGuide — точка входа. Запуск: python app.py"""
# from sky_map.app_dash import create_app
#
# app = create_app()
# server = app.server
#
# if __name__ == "__main__":
#     app.run(debug=True, host="127.0.0.1", port=8050)

"""
Небесная карта
Запуск:  python app.py   ->  http://127.0.0.1:8050
"""
from datetime import datetime, timedelta, timezone

from dash import Dash, html, dcc, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Импортируем логику карты из нашего модуля
from sky_map import config
from sky_map.astro.sky_state import compute_sky_state
from sky_map.viz.sky_figure import build_sky_figure
from sky_map.viz import style as sky_style

# Базовая сетка и компоненты Bootstrap
BOOTSTRAP_THEME = dbc.themes.DARKLY

COLORS = {
    "bg": "#E4F2FF",  # Основной фон всей страницы
    "paper": "#C6E7FF",  # Фон карточек, шапки и блоков
    "accent": "#82D2FF",  # Акцентный цвет: кнопки, линии, загрузка
    "text": "#1E2525",  # Основной цвет текста
    "muted": "#2C2F32",  # Приглушенный текст: подсказки, подвал
    "border": "#3A506B",  # Цвет рамок и разделителей
}

LAYOUT_STYLES = {
    "border_radius": "12px",
    "map_height": "550px",  # Увеличил высоту для удобства
    "font_family": "system-ui, -apple-system, 'Segoe UI', Montserrat, sans-serif",
}

CARD_STYLE = {
    "backgroundColor": COLORS["paper"],
    "borderColor": COLORS["border"],
    "color": COLORS["text"],
    "borderRadius": LAYOUT_STYLES["border_radius"],
}

INPUT_STYLE = {
    "backgroundColor": COLORS["bg"],
    "borderColor": COLORS["border"],
    "color": COLORS["text"],
}

app = Dash(
    __name__,
    external_stylesheets=[BOOTSTRAP_THEME],
    title="AstroGuide",
    update_title=None,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)


def make_empty_fig(text="Заглушка"):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["paper"],
        font=dict(color=COLORS["muted"], size=16, family=LAYOUT_STYLES["font_family"]),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.add_annotation(
        text=text,
        showarrow=False,
        font=dict(size=20, color=COLORS["muted"]),
    )
    return fig


def section_title(text, id_):
    return html.H2(
        text,
        id=id_,
        className="mb-4 pb-2 fw-bold",
        style={
            "color": COLORS["text"],
            "borderBottom": f"2px solid {COLORS['border']}",
        },
    )


# --- 1. Шапка ---------------------------------------------------------------
header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            "🔭 AstroGuide",
            href="#top",
            style={"color": COLORS["text"], "fontWeight": "bold"},
        ),
        dbc.Nav([
            dbc.NavLink("Карта", href="#map", style={"color": COLORS["text"]}),
            dbc.NavLink("Нейросеть", href="#nn", style={"color": COLORS["text"]}),
            dbc.NavLink("О проекте", href="#about", style={"color": COLORS["text"]}),
        ], navbar=True),
    ]),
    color=COLORS["paper"],
    dark=True,
    className="mb-4 shadow-sm",
    style={"borderBottom": f"1px solid {COLORS['border']}"}, id="top",
    sticky="top",
)

# --- 2. Карта ---------------------------------------------------------------
# Добавляем элементы управления картой в map_section
time_controls = html.Div([
    html.Div("Сдвиг времени", className="small mb-1", style={"color": COLORS["muted"]}),
    dbc.ButtonGroup([
        dbc.Button("+30 мин", id="btn-add-30", color="primary", outline=True, size="sm"),
        dbc.Button("+1 час", id="btn-add-60", color="primary", outline=True, size="sm"),
        dbc.Button("+4 часа", id="btn-set-max", color="primary", outline=True, size="sm"),
        dbc.Button("Сбросить", id="btn-reset", color="warning", outline=True, size="sm"),
    ], className="mb-2 w-100"),
    html.Div("Смещение: +0 мин", id="offset-indicator", className="fw-bold small", style={"color": COLORS["accent"]}),
])

coords_controls = html.Div([
    html.Div("Координаты", className="small mb-1", style={"color": COLORS["muted"]}),
    dbc.InputGroup([
        dbc.InputGroupText("Шир."),
        dbc.Input(id="inp-lat", type="number", value=config.DEFAULT_LAT, step=0.01, style=INPUT_STYLE, size="sm"),
        dbc.InputGroupText("Долг."),
        dbc.Input(id="inp-lon", type="number", value=config.DEFAULT_LON, step=0.01, style=INPUT_STYLE, size="sm"),
    ], size="sm", className="mb-1"),
    html.Div(id="coords-error", className="small text-danger"),
])

map_section = dbc.Row(
    dbc.Col([
        section_title("Карта звёздного неба", "map"),
        # Хранилища для времени и координат
        dcc.Store(id="t0"),
        dcc.Store(id="offset-min"),

        dbc.Card(
            dbc.CardBody([
                # Панель управления картой
                dbc.Row([
                    dbc.Col(time_controls, md=6, className="mb-2"),
                    dbc.Col(coords_controls, md=6, className="mb-2"),
                ]),

                dcc.Loading(
                    dcc.Graph(
                        id="sky_map",
                        figure=make_empty_fig("Загрузка карты..."),
                        style={"height": LAYOUT_STYLES["map_height"]},
                        config={"displayModeBar": False, "scrollZoom": False},
                    ),
                    type="circle",
                    color=COLORS["accent"],
                ),
                html.Small(id="sky-info", className="mt-2 d-block", style={"color": COLORS["muted"]}),
            ], className="p-3"),
            style=CARD_STYLE,
        ),
    ], width=12),
    className="mb-5",
)

# --- 3. Нейросеть -----------------------------------------------------------
nn_form_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            dbc.Input(
                id="input-data",
                type="text",
                placeholder="Введите название или координаты...",
                className="mb-3",
                style=INPUT_STYLE,
            ),
            dbc.Button(
                "Отправить",
                id="submit-val",
                className="mb-3 border-0 fw-semibold",
                style={"backgroundColor": COLORS["accent"], "color": "#000"},
            ),
            html.Hr(style={"borderColor": COLORS["border"]}),
            html.Div(
                "Здесь появится результат обработки...",
                id="output-data",
                style={"color": COLORS["muted"]},
            ),
        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=7, md=12,
)

nn_side_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            html.H5("💡 Подсказка", className="card-title", style={"color": COLORS["accent"]}),
            html.P(
                "Введите имя объекта — например, «Сириус» или координаты прямого восхождения и склонения.",
                className="mb-0",
                style={"color": COLORS["muted"]},
            ),
        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=5, md=12,
)

nn_section = html.Div([
    section_title("Нейросеть", "nn"),
    dbc.Alert("Здесь будет нейросеть:).", color="info", className="mb-4"),
    dbc.Row([nn_form_col, nn_side_col], className="g-4"),
], className="mb-5")

# --- 4. О проекте -----------------------------------------------------------
ABOUT_MD = """
**AstroGuide** — учебный проект на *Plotly Dash*.
- Интерактивная карта звёздного неба
Документация: [Dash Plotly](https://dash.plotly.com)
"""

about_section = dbc.Row(
    dbc.Col([
        section_title("О проекте", "about"),
        dbc.Card(
            dbc.CardBody(dcc.Markdown(ABOUT_MD, link_target="_blank", className="mb-0")),
            style=CARD_STYLE,
        ),
    ], lg=8, md=12),
    className="mb-5",
)

# --- 5. Подвал --------------------------------------------------------------
footer = dbc.Row(
    dbc.Col(
        html.Small("© 2026 AstroGuide · учебный проект", style={"color": COLORS["muted"]}),
        className="text-center py-4",
        style={"borderTop": f"1px solid {COLORS['border']}"},
    ),
)

app.layout = html.Div(
    [
        header,
        dbc.Container([map_section, nn_section, about_section, footer]),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "color": COLORS["text"],
        "minHeight": "100vh",
        "fontFamily": LAYOUT_STYLES["font_family"],
    },
)


# ============================================================================
# CALLBACKS
# ============================================================================

# --- Callbacks для нейросети (заглушка) ---
@callback(
    Output("output-data", "children"),
    Input("submit-val", "n_clicks"),
    State("input-data", "value"),
    prevent_initial_call=True,
)
def process_input(n_clicks, value):
    if not value or not value.strip():
        return dbc.Alert("Введите что-нибудь перед отправкой", color="warning", className="mb-0")
    return dbc.Alert(f"Вы ввели: {value}", color="success", className="mb-0")


# --- Callbacks для КАРТЫ ---

# 1. Инициализация времени
@callback(
    Output("t0", "data"),
    Output("offset-min", "data", allow_duplicate=True),
    Output("offset-indicator", "children", allow_duplicate=True),
    Input("t0", "id"),
    prevent_initial_call="initial_duplicate",
)
def _init_time(_):
    return datetime.now(timezone.utc).isoformat(), 0, "Смещение: +0 мин"


# 2. Кнопки сдвига времени
@callback(
    Output("offset-min", "data", allow_duplicate=True),
    Output("offset-indicator", "children", allow_duplicate=True),
    Input("btn-add-30", "n_clicks"),
    Input("btn-add-60", "n_clicks"),
    Input("btn-set-max", "n_clicks"),
    Input("btn-reset", "n_clicks"),
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
    h, m = divmod(cur, 60)
    label = f"Смещение: +{h} ч {m} мин" if h else f"Смещение: +{m} мин"
    return cur, label


# 3. Валидация координат
@callback(
    Output("coords-error", "children"),
    Input("inp-lat", "value"),
    Input("inp-lon", "value"),
)
def _validate_coords(lat, lon):
    try:
        lat_f = float(lat);
        lon_f = float(lon)
    except (TypeError, ValueError):
        return "Введите числа."
    if not (-90 <= lat_f <= 90):
        return "Широта от -90 до 90."
    if not (-180 <= lon_f <= 180):
        return "Долгота от -180 до 180."
    return ""


# 4. Главный callback: перерисовка карты
@callback(
    Output("sky_map", "figure"),
    Output("sky-info", "children"),
    Input("offset-min", "data"),
    Input("t0", "data"),
    Input("inp-lat", "value"),
    Input("inp-lon", "value"),
    Input("coords-error", "children"),
)
def _update_sky_map(offset, t0, lat, lon, coord_err):
    if not t0 or coord_err:
        raise PreventUpdate
    try:
        lat_f = float(lat);
        lon_f = float(lon)
    except (TypeError, ValueError):
        raise PreventUpdate
    if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
        raise PreventUpdate

    # Считаем время и состояние неба
    dt = datetime.fromisoformat(t0) + timedelta(minutes=int(offset or 0))
    state = compute_sky_state(dt, lat_f, lon_f)

    # Собираем график
    fig = build_sky_figure(state, {"planets", "stars", "const", "const_names", "grid", "ecliptic"})

    # Формируем текст с информацией
    info = f"UTC {dt.strftime('%H:%M')} · Шир: {lat_f:.1f}°, Долг: {lon_f:.1f}°"
    return fig, info


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)