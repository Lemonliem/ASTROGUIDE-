"""
Задание 4
Запуск:  python app.py   ->  http://127.0.0.1:8050
"""
from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from sky_map import build_sky_figure, DEFAULT_LAT, DEFAULT_LON

# Базовая сетка и компоненты Bootstrap (DARKLY / FLATLY / CYBORG / MORPH)
BOOTSTRAP_THEME = dbc.themes.DARKLY

COLORS = {
    "bg":      "#E4F2FF",  # Основной фон всей страницы 
    "paper":   "#C6E7FF",  # Фон карточек, шапки и блоков
    "accent":  "#82D2FF",  # Акцентный цвет: кнопки, линии, загрузка
    "text":    "#1E2525",  # Основной цвет текста
    "muted":   "#2C2F32",  # Приглушенный текст: подсказки, подвал
    "border":  "#3A506B",  # Цвет рамок и разделителей
}

# Общие настройки геометрии и отступов
LAYOUT_STYLES = {
    "border_radius": "12px",
    "map_height": "600px",
    "font_family": "system-ui, -apple-system, 'Segoe UI', Montserrat, sans-serif",
}

# Готовые стили для карточек
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

# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ

app = Dash(
    __name__,
    external_stylesheets=[BOOTSTRAP_THEME],
    title="AstroGuide",
    update_title=None,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)

# УТИЛИТЫ И ШАБЛОНЫ КОМПОНЕНТОВ

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
    """Единый стиль заголовков для всех секций сайта"""
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
    style={"borderBottom": f"1px solid {COLORS['border']}"},id="top",
    sticky="top",
)

# --- 2. Карта ---------------------------------------------------------------
SKY_LAYER_OPTIONS = [
    {"label": "Сетка",       "value": "grid"},
    {"label": "Созвездия",   "value": "const"},
    {"label": "Названия",    "value": "names"},
    {"label": "Планеты",     "value": "planets"},
    {"label": "Эклиптика",   "value": "ecliptic"},
    {"label": "Горизонт",    "value": "horizon"},
    {"label": "Млечный Путь", "value": "milky"},
]
SKY_LAYERS_DEFAULT = ["grid", "const", "names", "planets", "ecliptic", "horizon"]

sky_controls = dbc.Row(
    [
        dbc.Col(
            dbc.Checklist(
                id="sky-layers",
                options=SKY_LAYER_OPTIONS,
                value=SKY_LAYERS_DEFAULT,
                inline=True,
                switch=True,
            ),
            lg=8, md=12, className="mb-2",
        ),
        dbc.Col(
            dbc.InputGroup(
                [
                    dbc.InputGroupText("Шир."),
                    dbc.Input(id="sky-lat", type="number", value=DEFAULT_LAT,
                              min=-90, max=90, step=0.01, style=INPUT_STYLE),
                    dbc.InputGroupText("Долг."),
                    dbc.Input(id="sky-lon", type="number", value=DEFAULT_LON,
                              min=-180, max=180, step=0.01, style=INPUT_STYLE),
                    dbc.Button("Сейчас", id="sky-now", className="border-0",
                               style={"backgroundColor": COLORS["accent"],
                                      "color": "#000"}),
                ],
                size="sm",
            ),
            lg=4, md=12, className="mb-2",
        ),
    ],
    className="g-2 align-items-center",
)

map_section = dbc.Row(
    dbc.Col([
        section_title("Карта звёздного неба", "map"),
        dbc.Card(
            dbc.CardBody([
                sky_controls,
                dcc.Loading(
                    dcc.Graph(
                        id="sky_map",
                        figure=make_empty_fig("Загрузка карты..."),
                        style={"height": LAYOUT_STYLES["map_height"]},
                        config={"displayModeBar": False, "scrollZoom": True},
                    ),
                    type="circle",
                    color=COLORS["accent"],
                ),
                html.Small(id="sky-info", style={"color": COLORS["muted"]}),
                html.Div(
                    "Перетаскивайте сферу мышкой, колесо — масштаб.",
                    className="small", style={"color": COLORS["muted"]},
                ),
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
    dbc.Alert(
        "Здесь будет нейросеть:).",
        color="info",
        className="mb-4",
    ),
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
            dbc.CardBody(
                dcc.Markdown(ABOUT_MD, link_target="_blank", className="mb-0"),
            ),
            style=CARD_STYLE,
        ),
    ], lg=8, md=12),
    className="mb-5",
)

# --- 5. Подвал --------------------------------------------------------------
footer = dbc.Row(
    dbc.Col(
        html.Small(
            "© 2026 AstroGuide · учебный проект",
            style={"color": COLORS["muted"]},
        ),
        className="text-center py-4",
        style={"borderTop": f"1px solid {COLORS['border']}"},
    ),
)

app.layout = html.Div(
    [
        header,
        dbc.Container([
            map_section,
            nn_section,
            about_section,
            footer,
        ]),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "color": COLORS["text"],
        "minHeight": "100vh",
        "fontFamily": LAYOUT_STYLES["font_family"],
    },
)

@callback(
    Output("sky_map", "figure"),
    Output("sky-info", "children"),
    Input("sky-layers", "value"),
    Input("sky-lat", "value"),
    Input("sky-lon", "value"),
    Input("sky-now", "n_clicks"),   # кнопка «Сейчас»: пересчитать на текущий момент
)
def update_sky(layers, lat, lon, _n_clicks):
    lat = DEFAULT_LAT if lat is None else max(-90.0, min(90.0, float(lat)))
    lon = DEFAULT_LON if lon is None else max(-180.0, min(180.0, float(lon)))
    return build_sky_figure(layers, lat, lon, paper_bg=COLORS["paper"])


@callback(
     Output("output-data", "children"),
    Input("submit-val", "n_clicks"),
    State("input-data", "value"),
    prevent_initial_call=True,
)
def process_input(n_clicks, value):
    if not value or not value.strip():
        return dbc.Alert(
            "Введите что-нибудь перед отправкой",
            color="warning",
            className="mb-0",
        )
    return dbc.Alert(
        f"Вы ввели: {value}",
        color="success",
        className="mb-0",
    )

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)