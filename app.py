import os
from flask import Flask, render_template
from config import Config
from extensions import db, migrate, csrf, limiter
from routes.auth import auth_bp
from routes.trips import trips_bp

import json
import requests

def get_unsplash_urls():
    cache_path = os.path.join('static', 'unsplash_cache.json')
    ACCESS_KEY = "zLdCcMhv5O2I8AB-Ntnvmfq-vqNGWCmEEQTKjWwEPGU"
    
    queries = {
        "goa": "goa beach sunset",
        "jaipur": "jaipur hawa mahal",
        "kerala": "kerala backwaters houseboat",
        "agra": "taj mahal agra",
        "kashmir": "dal lake kashmir",
        "ladakh": "pangong lake ladakh",
        "hampi": "hampi ruins",
        "rishikesh": "rishikesh rafting",
        "darjeeling": "darjeeling tea garden"
    }

    fallback = {
        "goa": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
        "jaipur": "https://images.unsplash.com/photo-1477587458883-47135fb7a0be?auto=format&fit=crop&w=900&q=80",
        "kerala": "https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=900&q=80",
        "agra": "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=900&q=80",
        "kashmir": "https://images.unsplash.com/photo-1598091383021-15ddea10925d?auto=format&fit=crop&w=900&q=80",
        "ladakh": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=900&q=80",
        "hampi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=900&q=80",
        "rishikesh": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=900&q=80",
        "darjeeling": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=900&q=80"
    }

    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    updated = False
    for key, query in queries.items():
        if key not in cache or not cache[key]:
            try:
                resp = requests.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": query, "per_page": 1, "orientation": "landscape"},
                    headers={"Authorization": f"Client-ID {ACCESS_KEY}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("results"):
                        cache[key] = data["results"][0]["urls"]["regular"]
                        updated = True
                    else:
                        cache[key] = fallback[key]
                else:
                    cache[key] = fallback[key]
            except Exception:
                cache[key] = fallback[key]

    if updated:
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(cache, f, indent=4)
        except Exception:
            pass

    return cache

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

    # Global Home route (Immersive Cover Page)
    @app.route('/')
    def cover():
        return render_template('cover.html')

    # Main Product & Features Explore page
    @app.route('/explore')
    def explore():
        urls = get_unsplash_urls()
        return render_template('landing.html', unsplash_urls=urls)

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
