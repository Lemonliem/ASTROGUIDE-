from dash import Dash
from .layout import (create_layout, BOOTSTRAP_THEME)
from .callbacks import register_callbacks


def create_app():   # Инициализация приложения
    app = Dash(
        __name__,
        external_stylesheets=[BOOTSTRAP_THEME],
        title="AstroGuide",
        update_title=None,
        meta_tags=[
            {
                "name": "viewport",
                "content": ("width=device-width, ""initial-scale=1"),
            }
        ],

    )

    # Подключение макета
    app.layout = create_layout()

    # Регистрация обработчиков
    register_callbacks(app)

    return app