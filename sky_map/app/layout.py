from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


# Базовая сетка и компоненты Bootstrap
BOOTSTRAP_THEME = dbc.themes.DARKLY


COLORS = {
    "bg": "#E4F2FF",
    "paper": "#C6E7FF",
    "accent": "#82D2FF",
    "text": "#1E2525",
    "muted": "#2C2F32",
    "border": "#3A506B",
}


# Общие настройки геометрии и отступов
LAYOUT_STYLES = {
    "border_radius": "12px",
    "map_height": "420px",
    "font_family": (
        "system-ui, -apple-system, "
        "'Segoe UI', Montserrat, sans-serif"
    ),
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


# --------------------------------------------------
# УТИЛИТЫ И ШАБЛОНЫ КОМПОНЕНТОВ
# --------------------------------------------------

def make_empty_fig(text="Заглушка"):
    fig = go.Figure()

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["paper"],
        font=dict(
            color=COLORS["muted"],
            size=16,
            family=LAYOUT_STYLES["font_family"],
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    fig.add_annotation(
        text=text,
        showarrow=False,
        font=dict(
            size=20,
            color=COLORS["muted"],
        ),
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


# --------------------------------------------------
# 1. ШАПКА
# --------------------------------------------------

header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            "🔭 AstroGuide",
            href="#top",
            style={
                "color": COLORS["text"],
                "fontWeight": "bold",
            },
        ),

        dbc.Nav([
            dbc.NavLink(
                "Карта",
                href="#map",
                style={"color": COLORS["text"]},
            ),

            dbc.NavLink(
                "Нейросеть",
                href="#nn",
                style={"color": COLORS["text"]},
            ),

            dbc.NavLink(
                "О проекте",
                href="#about",
                style={"color": COLORS["text"]},
            ),

        ], navbar=True),

    ]),

    color=COLORS["paper"],
    dark=True,
    className="mb-4 shadow-sm",
    style={
        "borderBottom": f"1px solid {COLORS['border']}"
    },
    id="top",
    sticky="top",
)


# --------------------------------------------------
# 2. КАРТА
# --------------------------------------------------

map_section = dbc.Row(
    dbc.Col([
        section_title(
            "Карта звёздного неба",
            "map",
        ),
        dbc.Card(
            dbc.CardBody(
                dcc.Loading(
                    dcc.Graph(
                        id="sky_map",
                        figure=make_empty_fig(
                            "Здесь будет карта"
                        ),
                        style={
                            "height": LAYOUT_STYLES["map_height"]
                        },
                        config={
                            "displayModeBar": False
                        },
                    ),
                    type="circle",
                    color=COLORS["accent"],
                ),
                className="p-2",
            ),
            style=CARD_STYLE,
        ),
    ], width=12),
    className="mb-5",
)


# --------------------------------------------------
# 3. НЕЙРОСЕТЬ
# --------------------------------------------------

nn_form_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            dbc.Input(
                id="input-data",
                type="text",
                placeholder=(
                    "Введите название или координаты..."
                ),
                className="mb-3",
                style=INPUT_STYLE,
            ),
            dbc.Button(
                "Отправить",
                id="submit-val",
                className="mb-3 border-0 fw-semibold",
                style={
                    "backgroundColor": COLORS["accent"],
                    "color": "#000",
                },
            ),
            html.Hr(
                style={
                    "borderColor": COLORS["border"]
                }
            ),
            html.Div(
                "Здесь появится результат обработки...",
                id="output-data",
                style={
                    "color": COLORS["muted"]
                },
            ),

        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=7,
    md=12,
)


nn_side_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            html.H5(
                "💡 Подсказка",
                className="card-title",
                style={
                    "color": COLORS["accent"]
                },
            ),
            html.P(
                "Введите имя объекта — например, "
                "«Сириус» или координаты прямого "
                "восхождения и склонения.",
                className="mb-0",
                style={
                    "color": COLORS["muted"]
                },
            ),
        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=5,
    md=12,
)


nn_section = html.Div([
    section_title("Нейросеть", "nn"),
    dbc.Alert("Здесь будет нейросеть:).", color="info", className="mb-4"),
    dbc.Row([nn_form_col, nn_side_col], className="g-4"),
], className="mb-5")


# --------------------------------------------------
# 4. О ПРОЕКТЕ
# --------------------------------------------------

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
                dcc.Markdown(
                    ABOUT_MD,
                    link_target="_blank",
                    className="mb-0",
                ),
            ),
            style=CARD_STYLE,
        ),
    ], lg=8, md=12),
    className="mb-5"
)


# --------------------------------------------------
# 5. ПОДВАЛ
# --------------------------------------------------

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


# --------------------------------------------------
# СОЗДАНИЕ МАКЕТА САЙТА
# --------------------------------------------------

def create_layout():
    return html.Div(
        [header, dbc.Container([map_section, nn_section, about_section, footer,])],
        style={
            "backgroundColor": COLORS["bg"],
            "color": COLORS["text"],
            "minHeight": "100vh",
            "fontFamily": LAYOUT_STYLES["font_family"],
        },
    )