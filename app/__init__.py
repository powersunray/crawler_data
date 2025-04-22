from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import Swagger

db = SQLAlchemy()
migrate = Migrate()
swagger = Swagger()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)

    # Import models for Alembic recognition
    from app.models.attributes import Attribute
    from app.models.sources import Source
    from app.models.results import Result
    
    # Register blueprints
    from app.api.attributes import attributes_bp
    from app.api.sources import sources_bp
    from app.api.crawl import crawler_bp
    # from app.api.web import web_bp
    app.register_blueprint(attributes_bp, url_prefix="/api")
    app.register_blueprint(sources_bp, url_prefix="/api")
    app.register_blueprint(crawler_bp, url_prefix="/api")
    # app.register_blueprint(web_bp)

    return app