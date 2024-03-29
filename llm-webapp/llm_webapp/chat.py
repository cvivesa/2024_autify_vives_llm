from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
)
from werkzeug.exceptions import abort

from llm_webapp.auth import login_required
from llm_webapp.db import get_db
from llm_webapp.openai import generate_openai_response

bp = Blueprint("chat", __name__)
import time


@bp.route("/")
@login_required
def index():
    db = get_db()
    chats = db.execute(
        "SELECT chat.chat_id, chat.model, chat.created, chat_entry.type, chat_entry.body"
        " FROM chat"
        " LEFT JOIN chat_entry ON chat.chat_id = chat_entry.chat_id"
        " WHERE chat.author_id = ?"
        " ORDER BY chat.chat_id DESC, chat_entry.chat_entry_id ASC",
        (g.user["id"],),
    ).fetchall()
    # Group chat entries under their respective chats
    chat_data = {}
    for row in chats:
        chat_id, model, created, entry_type, body = row
        if chat_id not in chat_data:
            chat_data[chat_id] = {"model": model, "created": created, "entries": []}
        chat_data[chat_id]["entries"].append({"type": entry_type, "body": body})
    # reverse the chats so that they are in correct order
    return render_template("chat/index.html", chats=chat_data)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    user_models = (
        get_db()
        .execute(
            "SELECT model_name" " FROM user_models" " WHERE id = ?", (g.user["id"],)
        )
        .fetchall()
    )
    if request.method == "POST":
        selected_model = request.form["model"]  # Access the selected model
        body = request.form["body"]  # Access the body of the form
        if selected_model == "gpt-3.5":
            # check if API key exists, if not redirect to settings page to input
            api_key = (
                get_db()
                .execute(
                    "SELECT openai_key" " FROM user_settings" " WHERE id = ?",
                    (g.user["id"],),
                )
                .fetchone()
            )
            if (
                api_key is None
                or api_key["openai_key"] == ""
                or api_key["openai_key"] is None
            ):
                flash("Please input your OpenAI API key in the settings.", "warning")
                return redirect(url_for("user_settings.openai_settings"))

            else:
                try:
                    api_key = api_key["openai_key"]
                    output = generate_openai_response(api_key=api_key, user_prompt=body)
                except Exception as e:
                    flash(e, "error")
                    return render_template("chat/create.html", models=user_models)
                else:
                    if not output["valid"]:
                        flash(output["invalid_message"], "error")
                        return render_template("chat/create.html", models=user_models)
                    else:
                        # if correct, register the chat and individual chat entries
                        chat_id = register_chat(selected_model, body, output["output"])
                        # fetch chat data for this newly inserted chat id
                        return redirect(url_for("chat.load_chat", id=chat_id))

    # current_app.logger.info(user_models["model_name"])
    return render_template("chat/create.html", models=user_models)


def register_chat(model_name, user_message, system_message, provided_chat_id=None):
    db = get_db()
    cursor = db.cursor()
    # if chat_id is not provided, then we need to create a new chat
    if provided_chat_id is None:
        cursor.execute(
            "INSERT INTO chat (author_id, model) VALUES (?, ?)",
            (g.user["id"], model_name),
        )
        # commit so that it exists in the db
        db.commit()
        time.sleep(1)
        # grab the unique ID belonging to this chat
        chat_id = cursor.lastrowid
    else:
        chat_id = provided_chat_id
    cursor.execute(
        "INSERT INTO chat_entry (chat_id, type, body) VALUES (?, ?, ?)",
        (chat_id, "user", user_message),
    )
    cursor.execute(
        "INSERT INTO chat_entry (chat_id, type, body) VALUES (?, ?, ?)",
        (chat_id, "system", system_message),
    )
    db.commit()
    cursor.close()

    return chat_id


def get_chat(chat_id):
    chats = (
        get_db()
        .execute(
            "SELECT chat.chat_id, chat.author_id, chat.model, chat.created, chat_entry.type, chat_entry.body, chat_entry.chat_entry_id"
            " FROM chat"
            " LEFT JOIN chat_entry ON chat.chat_id = chat_entry.chat_id"
            " WHERE chat.chat_id = ?"
            " ORDER BY chat.created, chat.chat_id DESC,  chat_entry.chat_entry_id ASC",
            (chat_id,),
        )
        .fetchall()
    )
    if chats is None or chats == []:
        abort(404, f"Chat id {chat_id} doesn't exist.")
    # Group chat entries under their respective chats
    chat_data = {}
    for row in chats:
        chat_id, author_id, model, created, entry_type, body, chat_entry_id = row
        if chat_data == {}:
            chat_data = {
                "chat_id": chat_id,
                "author_id": author_id,
                "model": model,
                "created": created,
                "entries": [],
            }
        chat_data["entries"].append(
            {"type": entry_type, "body": body, "chat_entry_id": chat_entry_id}
        )

    if chat_data["author_id"] != g.user["id"]:
        abort(403)
    current_app.logger.info(chat_data)
    return chat_data


@bp.route("/<int:id>/load_chat", methods=("GET", "POST"))
@login_required
def load_chat(id):
    chat_data = get_chat(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ?" " WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("chat.index"))

    return render_template("chat/chat_view.html", chat_data=chat_data)


@bp.route("/<int:id>/continue_chat", methods=["POST"])
@login_required
def continue_chat(id):

    # first load the chat information
    chat_data = get_chat(id)
    body = request.form["body"]
    # format past messages so that openai can view them
    past_messages = [
        {"role": sub_dict["type"], "content": sub_dict["body"]}
        for sub_dict in chat_data["entries"]
    ]
    if chat_data["model"] == "gpt-3.5":
        api_key = (
            get_db()
            .execute(
                "SELECT openai_key" " FROM user_settings" " WHERE id = ?",
                (g.user["id"],),
            )
            .fetchone()
        )
        if (
            api_key is None
            or api_key["openai_key"] == ""
            or api_key["openai_key"] is None
        ):
            flash("Please input your OpenAI API key in the settings.", "warning")
            return redirect(url_for("user_settings.openai_settings"))

        else:
            try:
                api_key = api_key["openai_key"]
                output = generate_openai_response(
                    api_key=api_key, user_prompt=body, past_messages=past_messages
                )
            except Exception as e:
                flash(e, "error")
                return render_template("chat/chat_view.html", chat_data=chat_data)
            else:
                if not output["valid"]:
                    flash(output["invalid_message"], "error")
                    return render_template("chat/chat_view.html", chat_data=chat_data)
                else:
                    # if correct, register the chat and individual chat entries
                    chat_id = register_chat(
                        chat_data["model"], body, output["output"], provided_chat_id=id
                    )
                    # fetch chat data for this newly inserted chat id
                    return redirect(url_for("chat.load_chat", id=chat_id))


@bp.route("/<int:id>/regenerate_chat", methods=["POST"])
@login_required
def regenerate_chat(id):

    # is the same as the function `continue_chat` but updates the values
    # first load the chat information
    chat_data = get_chat(id)
    # format past messages so that openai can view them
    past_messages = [
        {"role": sub_dict["type"], "content": sub_dict["body"]}
        for sub_dict in chat_data["entries"]
    ]
    # we pop the system message since we want to regenerate it
    user_message = past_messages[-2]["content"]
    past_messages = past_messages[:-2]
    # only grab the chat_entry id for the latest message (the system message that is being regenerated)
    latest_system_chat_id = [
        sub_dict["chat_entry_id"] for sub_dict in chat_data["entries"]
    ][-1]
    if chat_data["model"] == "gpt-3.5":
        api_key = (
            get_db()
            .execute(
                "SELECT openai_key" " FROM user_settings" " WHERE id = ?",
                (g.user["id"],),
            )
            .fetchone()
        )
        if (
            api_key is None
            or api_key["openai_key"] == ""
            or api_key["openai_key"] is None
        ):
            flash("Please input your OpenAI API key in the settings.", "warning")
            return redirect(url_for("user_settings.openai_settings"))

        else:
            try:
                api_key = api_key["openai_key"]
                output = generate_openai_response(
                    api_key=api_key,
                    user_prompt=user_message,
                    past_messages=past_messages,
                )
            except Exception as e:
                flash(e, "error")
                return render_template("chat/chat_view.html", chat_data=chat_data)
            else:
                if not output["valid"]:
                    flash(output["invalid_message"], "error")
                    return render_template("chat/chat_view.html", chat_data=chat_data)
                else:
                    # if correct, we update the latest system message
                    db = get_db()
                    db.execute(
                        "UPDATE chat_entry SET body = ?" " WHERE chat_entry_id = ?",
                        (output["output"], latest_system_chat_id),
                    )
                    db.commit()
                    time.sleep(1)
                    # fetch chat data for this newly inserted chat id
                    return redirect(url_for("chat.load_chat", id=id))


@bp.route("/<int:id>/delete_chat", methods=("POST",))
@login_required
def delete_chat(id):
    # run for validation and to grab chat_entry_ids
    chat_data = get_chat(id)
    chat_entry_ids = [sub_dict["chat_entry_id"] for sub_dict in chat_data["entries"]]
    db = get_db()
    db.execute("DELETE FROM chat WHERE chat_id = ?", (id,))
    for chat_entry_id in chat_entry_ids:
        db.execute("DELETE FROM chat_entry WHERE chat_entry_id = ?", (chat_entry_id,))
    db.commit()
    return redirect(url_for("chat.index"))
