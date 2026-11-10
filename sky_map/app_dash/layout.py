"""Layout приложения: минимальный и понятный, всё оформление — из viz/style."""
import dash_bootstrap_components as dbc
from dash import dcc, html

from .. import config
from ..viz import style


def _card(children):
    return dbc.Card(
        dbc.CardBody(children),
        style={
            "backgroundColor": style.PAPER_COLOR,
            "borderColor":     style.BORDER_COLOR,
            "color":           style.TEXT_COLOR,
            "borderRadius":    "12px",
        },
    )


def _time_controls():
    return html.Div([
        html.Div("Сдвиг времени (вперёд от момента загрузки)",
                 className="small mb-2",
                 style={"color": style.MUTED_COLOR}),
        dbc.ButtonGroup([
            dbc.Button("+30 мин", id="btn-add-30",  color="primary", outline=True, size="sm"),
            dbc.Button("+1 час",  id="btn-add-60",  color="primary", outline=True, size="sm"),
            dbc.Button("+4 часа", id="btn-set-max", color="primary", outline=True, size="sm"),
            dbc.Button("Сбросить", id="btn-reset",   color="warning", outline=True, size="sm"),
        ], className="mb-2"),
        html.Div(id="offset-indicator",
                 children="Смещение: +0 мин",
                 className="fw-bold",
                 style={"color": style.ACCENT_COLOR}),
    ])


def _coords_controls():
    return html.Div([
        html.Div("Координаты наблюдателя",
                 className="small mb-2",
                 style={"color": style.MUTED_COLOR}),
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Широта"),
                    dbc.Input(id="inp-lat", type="number",
                              value=config.DEFAULT_LAT, step=0.01, min=-90, max=90,
                              style={"backgroundColor": style.BG_COLOR,
                                     "color":           style.TEXT_COLOR,
                                     "borderColor":     style.BORDER_COLOR}),
                ], size="sm"),
            ], width=6),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Долгота"),
                    dbc.Input(id="inp-lon", type="number",
                              value=config.DEFAULT_LON, step=0.01, min=-180, max=180,
                              style={"backgroundColor": style.BG_COLOR,
                                     "color":           style.TEXT_COLOR,
                                     "borderColor":     style.BORDER_COLOR}),
                ], size="sm"),
            ], width=6),
        ], className="g-2"),
        html.Div(id="coords-error", className="small mt-1",
                 style={"color": "#FF8080"}),
        html.Div(id="coords-info",  className="small mt-1",
                 style={"color": style.MUTED_COLOR}),
    ])


def _layer_switches():
    options = [
        {"label": "Планеты",            "value": "planets"},
        {"label": "Звёзды",             "value": "stars"},
        {"label": "Созвездия",          "value": "const"},
        {"label": "Подписи созвездий",  "value": "const_names"},
        {"label": "Сетка",              "value": "grid"},
        {"label": "Эклиптика",          "value": "ecliptic"},
    ]
    return dbc.Checklist(
        id="layers", options=options,
        value=["planets", "stars", "const", "const_names", "grid", "ecliptic"],
        inline=True, switch=True, className="mb-3",
    )


def build_layout() -> html.Div:
    header = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("🔭 AstroGuide · Небесная карта",
                            style={"color": style.TEXT_COLOR,
                                   "fontWeight": "bold"}),
        ]),
        color=style.PAPER_COLOR, dark=True, sticky="top",
        style={"borderBottom": f"1px solid {style.BORDER_COLOR}"},
    )

    return html.Div([
        header,
        dbc.Container([
            dcc.Store(id="t0"),        # ISO-строка UTC: фиксируем при загрузке/сбросе
            dcc.Store(id="offset-min"),# целое: текущий сдвиг в минутах
            dbc.Row([
                dbc.Col([
                    html.H3("Карта звёздного неба", className="mt-4 mb-3"),
                    _card([
                        _layer_switches(),
                        dbc.Row([
                            dbc.Col(_time_controls(),  lg=6, md=12),
                            dbc.Col(_coords_controls(), lg=6, md=12),
                        ], className="g-3"),
                        dcc.Loading(
                            dcc.Graph(
                                id="sky-map",
                                figure=_empty_placeholder(),
                                style={"height": "640px"},
                                config={
                                    "displayModeBar": False,
                                    "scrollZoom":     False,   # зум отключён (ТЗ)
                                    "doubleClick":    False,
                                },
                            ),
                            type="circle", color=style.ACCENT_COLOR,
                        ),
                        html.Small(id="sky-info", className="mt-2 d-block",
                                   style={"color": style.MUTED_COLOR}),
                    ]),
                ], width=12),
            ]),
            html.Footer(
                html.Small("© 2026 AstroGuide · MVP «Небесная карта»",
                           style={"color": style.MUTED_COLOR}),
                className="text-center py-4 mt-4",
                style={"borderTop": f"1px solid {style.BORDER_COLOR}"},
            ),
        ], fluid="lg"),
    ], style={"backgroundColor": style.BG_COLOR,
              "color":           style.TEXT_COLOR,
              "minHeight":       "100vh",
              "fontFamily":      "system-ui, -apple-system, 'Segoe UI', sans-serif"})


def _empty_placeholder():
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=style.SKY_BG, plot_bgcolor=style.SKY_BG,
        margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text="Загрузка карты…", showarrow=False,
                          font=dict(size=18, color=style.MUTED_COLOR))],
    )
    return fig