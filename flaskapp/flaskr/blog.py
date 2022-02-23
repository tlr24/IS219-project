from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT v.id, title, body, created, author_id, username"
        " FROM vendor v JOIN user u ON v.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT v.id, title, body, created, author_id, username"
            " FROM vendor v JOIN user u ON v.author_id = u.id"
            " WHERE v.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("POST",))
@login_required
def create_process():
    """Create a new post for the current user."""
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
            "INSERT INTO vendor (title, body, author_id) VALUES (?, ?, ?)",
            (title, body, g.user["id"]),
        )
        db.commit()
        return redirect(url_for("blog.index"))

    return render_template("blog/create.html")

@bp.route("/create", methods=["GET"])
@login_required
def create():
    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("POST",))
@login_required
def update_process(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

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
            "UPDATE vendor SET title = ?, body = ? WHERE id = ?", (title, body, id)
        )
        db.commit()
        return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/update", methods=("GET",))
@login_required
def update(id):
    post = get_post(id)
    return render_template("blog/update.html", post=post)



@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM vendor WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
