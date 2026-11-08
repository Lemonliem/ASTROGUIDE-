from app.app import create_app


# Создаём приложение
app = create_app()

# Сервер для развёртывания (деплоя)
server = app.server


# Запуск приложения
if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=8050,
    )
