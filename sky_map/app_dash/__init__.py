# sky_map/app_dash/__init__.py — собирает приложение из layout + callbacks
import dash
import dash_bootstrap_components as dbc

from .layout import build_layout
from .callbacks import register_callbacks


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        title="AstroGuide · Небесная карта",
        update_title=None,
        meta_tags=[{"name": "viewport",
                    "content": "width=device-width, initial-scale=1"}],
    )
    app.layout = build_layout()
    register_callbacks(app)
    return app