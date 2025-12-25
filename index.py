try:
    from app import create_app
    app = create_app()
    application = app
except Exception as e:
    import traceback
    error_info = traceback.format_exc()
    print(error_info)
    
    from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    @app.route('/<path:path>')
    def error_page(path=None):
        return f"<h1>App Startup Error</h1><pre>{error_info}</pre>", 500
    application = app
