from app import crear_app


app = crear_app()


if __name__ == "__main__":
    host = app.config.get("APP_HOST", "127.0.0.1")
    port = int(app.config.get("APP_PORT", 5000))
    debug = app.config.get("APP_DEBUG", False)
    app.run(host=host, port=port, debug=debug)
