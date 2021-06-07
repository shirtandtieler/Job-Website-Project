import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, Blueprint, request
from werkzeug.urls import url_encode
from wtforms import HiddenField

from app.form_renderer import render_form
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from geopy.geocoders import Nominatim


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
geolocator = Nominatim(user_agent="senior_software_proj_commitme")


def init_bootstrap(app):
    blueprint = Blueprint(
        'bootstrap',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path=app.static_url_path + '/bootstrap')

    # add the form rendering template filter
    blueprint.add_app_template_filter(render_form)

    app.register_blueprint(blueprint)
    app.jinja_env.globals['bootstrap_is_hidden_field'] = \
        lambda field: isinstance(field, HiddenField)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    init_bootstrap(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/website.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Website startup')

    @app.template_global()
    def modify_query(**new_values):
        """
        Keeps the current URL scheme with the specified modifications.
        Is placed here to give Jinja global access it.
        A Python variant is accessible from `api.query`.
        """
        args = request.args.copy()
        for key, val in new_values.items():
            args[key] = val
        return f"{request.path}?{url_encode(args)}"

    @app.template_global()
    def bitwise_and(lhs, rhs) -> bool:
        """ Checks if the LHS & RHS > 0 """
        return lhs & rhs > 0

    @app.template_global()
    def _print(*content):
        for item in content:
            print(item, end=" ")
        print()
        return ""

    return app


# at the end to avoid circular dependencies
from app import models
