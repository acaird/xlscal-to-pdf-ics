from flask import Flask, render_template, request
from werkzeug import secure_filename

app = Flask(__name__)


@app.route("/")
def upload():
    page = """<html>
   <body>
      <form action = "/uploader" method = "POST" 
         enctype = "multipart/form-data">
         <input type = "file" name = "file" />
         <input type = "submit"/>
      </form>
   </body>
</html>"""
    return page


@app.route("/uploader", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        f = request.files["file"]
        f.save(secure_filename(f.filename))
        return 'file "{}" uploaded successfully'.format(f.filename)


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=8080)
