from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from llm_webapp.auth import login_required
from llm_webapp.db import get_db

bp = Blueprint('user_settings', __name__)

@bp.route('/user_settings')
@login_required
def user_settings():
    # Redirect to the OpenAI settings by default
    return redirect(url_for('user_settings.openai_settings'))

@bp.route('/user_settings/openai_settings',  methods=['GET', 'POST'])
@login_required
def openai_settings():
    saved_key = False
    if request.method == 'POST':
        api_key = request.form['openai_key']
        error = None

        if not api_key or api_key=="":
            error = 'API Key is invalid'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE user_settings SET openai_key = ?'
                ' WHERE id = ?',
                (api_key, g.user['id'])
            )
            db.commit()
            saved_key = True
    return render_template('user_settings/openai_settings.html', saved_key=saved_key)

@bp.route('/user_settings/custom_model_settings')
@login_required
def custom_model_settings():
    return render_template('user_settings/custom_model_settings.html')

