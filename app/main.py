from flask import Flask, render_template, request, Response
from werkzeug import secure_filename
import os
import csv
import json
import xlrd
from base64 import b64encode
from dateutil.parser import parse
from datetime import datetime, date
from time import strptime, strftime, mktime
from io import BytesIO
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    PageBreak,
)
from reportlab.graphics.shapes import Drawing
import calendar
from icalendar import Calendar, Event

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

        evtdict = {}
        for evt in ret:
            evtdict[evt[0]] = evt[1]

        pdfcals = make_pdf_cals(evtdict)

        ics = make_ics(evtdict)

        print(ics.decode("ascii"))

        return pdfcals


def parse_csv(filename):
    l = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        for line in reader:
            line[0] = parse(line[0])
            l.append(line)

    return l


def parse_xlsx(filename):
    workbook = xlrd.open_workbook(filename)
    sheet = workbook.sheet_by_index(0)

    l = []

    for rowx in range(sheet.nrows):
        cols = sheet.row_values(rowx)
        cols[0] = datetime(*xlrd.xldate_as_tuple(cols[0], workbook.datemode))

        l.append(cols)

    return l


def make_pdf_cals(events):
    buf = BytesIO()
    stylesheet = getSampleStyleSheet()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    doc.pagesize = landscape(letter)
    elements = []

    months = set([d.month for d in events])
    years = set([d.year for d in events])

    for year in years:
        for month in months:
            elements.append(
                Paragraph(
                    "{} {}".format(calendar.month_name[month], year),
                    stylesheet["Title"],
                )
            )
            cal = [["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
            cal.extend(calendar.monthcalendar(year, month))
            cal = fill_cal(cal, month, year, events)
            table = Table(cal, 7 * [1.25 * inch], len(cal) * [0.8 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Helvetica"),
                        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.green),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )

            elements.append(table)
            elements.append(PageBreak())

    doc.build(elements)

    resp = Response(buf.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename={}".format("cals.pdf")
    resp.headers["Content-Type"] = "application/pdf"
    buf.close()

    return resp


def fill_cal(cal, mon, yr, events):
    for row, _ in enumerate(cal):
        for day, _ in enumerate(cal[row]):
            if not isinstance(cal[row][day], int) or int(cal[row][day]) < 1:
                if cal[row][day] == 0:
                    cal[row][day] = ""
                continue
            date = "{}/{}/{}".format(mon, cal[row][day], yr)
            date = datetime.strptime(date, "%m/%d/%Y")
            if date in events:
                cal[row][day] = str(cal[row][day]) + "\n{}".format(events[date])

    return cal


def make_ics(events):
    ical = Calendar()

    for m in sorted(events):
        event = Event()
        event.add("summary", events[m])
        event.add("dtstart", m.date())

        ical.add_component(event)

    return ical.to_ical(ical)


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=8080)
