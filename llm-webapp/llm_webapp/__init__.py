import os
from flask import Flask
import logging
from markupsafe import Markup


def nl2br(value):
    return Markup(value.replace('\n', '<br>\n'))
def create_app(test_config=None):

    logging.basicConfig(level=logging.DEBUG)
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'llm_webapp.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import chat
    app.register_blueprint(chat.bp)
    app.add_url_rule('/', endpoint='index')

    from . import user_settings
    app.register_blueprint(user_settings.bp)
    app.add_url_rule('/user_settings', endpoint='user_settings.openai_settings')

    app.jinja_env.filters['nl2br'] = nl2br
    return app