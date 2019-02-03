from flask import Flask, render_template, request
from werkzeug import secure_filename
import os
import csv
import json
import xlrd
from dateutil.parser import parse
from datetime import datetime

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
    can_process = [".csv", ".xlsx"]
    if request.method == "POST":
        f = request.files["file"]
        sfname = secure_filename(f.filename)
        a = f.save(sfname)

        filename, fileext = os.path.splitext(sfname)
        if fileext not in can_process:
            message = (
                'Files of type "{}" cannot be processed, please '
                "upload a file of one of these types: {}".format(
                    fileext, ", ".join(can_process)
                )
            )
            return message

        if fileext == ".csv":
            ret = parse_csv(sfname)
        if fileext == ".xlsx":
            ret = parse_xlsx(sfname)

        return "<pre>{}</pre>".format(json.dumps(ret, indent=4))


def parse_csv(filename):
    l = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        for line in reader:
            line[0] = "{}".format(parse(line[0]))
            l.append(line)

    return l


def parse_xlsx(filename):
    workbook = xlrd.open_workbook(filename)
    sheet = workbook.sheet_by_index(0)

    l = []

    for rowx in range(sheet.nrows):
        cols = sheet.row_values(rowx)
        cols[0] = "{}".format(
            datetime(*xlrd.xldate_as_tuple(cols[0], workbook.datemode))
        )
        l.append(cols)

    return l


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=8080)
