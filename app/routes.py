from app import app
from flask import (
    send_file,
    request,
    flash,
    redirect,
    render_template,
    send_from_directory,
)
from PIL import Image
import os
import secrets
import time
import subprocess
from werkzeug.utils import secure_filename
import sys


@app.route("/", methods=["GET"])
@app.route("/index")
def index():
    return send_file("static/form.html")


@app.route("/uploads/<path:path>", methods=["GET"])
def static_uploads(path):
    return send_from_directory(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads")), path
    )


@app.route("/static/<path:path>", methods=["GET"])
def static_files(path):
    return send_from_directory(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "static")), path
    )


@app.route("/transfer", methods=["POST"])
def transfer():
    if "content" not in request.files:
        flash("no content file")
        return redirect("/")
    if "style" not in request.files:
        flash("no style file")
        return redirect("/")

    mysecret = secrets.token_hex(16)
    mydir = os.path.join(app.config["UPLOAD_FOLDER"], mysecret)
    os.mkdir(mydir)

    contentfile = request.files["content"]
    if contentfile.filename == "":
        flash("no content file selected")
        return redirect("/")
    filename = secure_filename(contentfile.filename)
    contentfile.save(os.path.join(mydir, "content-input"))

    subprocess.check_call(
        [
            "convert",
            "content-input",
            "-resize",
            "444x444^",
            "-gravity",
            "center",
            "-extent",
            "444x444",
            "content-input.jpg",
        ],
        cwd=mydir,
    )

    stylefile = request.files["style"]
    if stylefile.filename == "":
        flash("no style file selected")
        return redirect("/")
    stylefile.save(os.path.join(mydir, "style-input"))

    subprocess.check_call(
        [
            "convert",
            "style-input",
            "-resize",
            "444x444^",
            "-gravity",
            "center",
            "-extent",
            "444x444",
            "style-input.jpg",
        ],
        cwd=mydir,
    )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    output = subprocess.check_output(
        [
            sys.executable,
            os.path.join(dir_path, "transfer.py"),
            "style-input.jpg",
            "content-input.jpg",
        ],
        cwd=mydir,
        stderr=subprocess.STDOUT,
    )
    r = render_template(
        "result.html",
        output=output.decode("ascii"),
        outputimage=f"/uploads/{mysecret}/output.jpg",
        styleimage=f"/uploads/{mysecret}/style-input.jpg",
        contentimage=f"/uploads/{mysecret}/content-input.jpg",
    )
    with open(os.path.join(mydir, 'index.html'), 'w') as f:
        f.write(r)
    return redirect(f"/uploads/{mysecret}")


def image_parse(file):
    # Cheap hack, open the image and try to turn it into a thumbnail.
    # if any of that fails, it's not parsable as jpeg
    try:
        im = Image.open(file, mode="r", formats=["jpeg"])
        im.copy().thumbnail((128, 128))
        file.seek(0)
        return im
    except:
        return None
