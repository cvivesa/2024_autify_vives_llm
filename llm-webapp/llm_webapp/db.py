import sqlite3

import click
from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
        # for testing!
        """db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("pepe", generate_password_hash("1234")),
        )
        db.execute(
            "INSERT INTO chat (chat_id, author_id, model) VALUES (?, ?, ?)",
            (1,1, "gpt-3.5"),
        )
        db.execute(
            "INSERT INTO chat (chat_id, author_id, model) VALUES (?, ?, ?)",
            (2,1, "llama-7B"),
        )
        db.execute(
            "INSERT INTO chat_entry (chat_entry_id, chat_id, type, body) VALUES (?, ?, ?, ?)",
            (1, 1, "user", "I want a tomato"),
        )
        db.execute(
            "INSERT INTO chat_entry (chat_entry_id, chat_id, type, body) VALUES (?, ?, ?, ?)",
            (2, 1, "system", "As an AI language model, blah blah"),
        )
        db.execute(
            "INSERT INTO chat_entry (chat_entry_id, chat_id, type, body) VALUES (?, ?, ?, ?)",
            (3, 2, "user", "Write me a fun piece of code!"),
        )
        db.execute(
            "INSERT INTO chat_entry (chat_entry_id, chat_id, type, body) VALUES (?, ?, ?, ?)",
            (4, 2, "system", "System.out.println('Hello World)"),
        )
        db.execute(
            "INSERT INTO user_models (model_id, id, model_name, is_custom) VALUES (?, ?, ?, ?)",
            (1, 1, "gpt-3.5", True),
        )
        db.commit()"""


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
