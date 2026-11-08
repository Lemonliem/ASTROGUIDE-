from app.app import create_app

# Создание приложения
app = create_app()

# Сервер для деплоя
server = app.server


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=8050,
    )