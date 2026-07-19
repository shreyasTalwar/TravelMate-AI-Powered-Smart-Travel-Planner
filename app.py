import os
from flask import Flask, render_template
from config import Config
from extensions import db, migrate, csrf, limiter
from routes.auth import auth_bp
from routes.trips import trips_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure Upload Folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(trips_bp)

    # Global Home route
    @app.route('/')
    def landing():
        return render_template('landing.html')

    # Custom Error Pages
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html', description=e.description), 429

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
