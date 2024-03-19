from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from llm_webapp.auth import login_required
from llm_webapp.db import get_db

bp = Blueprint('chat', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    print(g.user['id'])
    chats = db.execute(
    'SELECT chat.chat_id, chat.model, chat.created, chat_entry.type, chat_entry.body'
    ' FROM chat'
    ' LEFT JOIN chat_entry ON chat.chat_id = chat_entry.chat_id'
    ' WHERE chat.author_id = ?'
    ' ORDER BY chat.created, chat.chat_id DESC,  chat_entry.chat_entry_id ASC', (g.user['id'], )
    ).fetchall()
    # Group chat entries under their respective chats
    chat_data = {}
    for row in chats:
        chat_id, model, created, entry_type, body = row
        if chat_id not in chat_data:
            chat_data[chat_id] = {
                'model': model,
                'created': created,
                'entries': []
            }
        chat_data[chat_id]['entries'].append({'type': entry_type, 'body': body})
    # reverse the chats so that they are in correct order
    return render_template('chat/index.html', chats=chat_data)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('chat.index'))

    return render_template('chat/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('chat.index'))

    return render_template('chat/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('chat.index'))