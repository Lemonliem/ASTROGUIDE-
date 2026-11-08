from dash import Input, Output, State
import dash_bootstrap_components as dbc


def register_callbacks(app):

    @app.callback(
        Output("output-data","children",),
        Input("submit-val","n_clicks",),
        State("input-data","value",),
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