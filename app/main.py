from flask import Flask, request, Response, render_template
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import csv
import calendar
import logging
import os
import xlrd
from datetime import datetime
from dateutil.parser import parse
from icalendar import Calendar, Event
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
from zipfile import ZipFile


LOG_FORMAT = "%(levelname)s: %(asctime)s %(message)s"

app = Flask(__name__)
Bootstrap(app)


@app.route("/")
def upload():
    return render_template("upload_page.html")


@app.route("/uploader", methods=["GET", "POST"])
def upload_file():
    can_process = [".csv", ".xlsx"]
    if request.method == "POST":
        if "file" not in request.files:
            return (
                "Please press your browser's Back "
                "button and specify a file to upload."
            )
        f = request.files["file"]
        sfname = secure_filename(f.filename)
        f.save(sfname)

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
            if ret is None:
                return "The .csv file was badly formatted, check it again try again."
        if fileext == ".xlsx":
            ret = parse_xlsx(sfname)
            if ret is None:
                return "The .xlsx file was badly formatted, check it again try again."

        # Why do I hate myself.  Why couldn't this have been sensible
        # like: evtdict[evt[0]] = {"title": evt[1], "location":
        # evt[2], "notes": evt[3]} also why couldn't this have been
        # all in one place so it wasn't scattered hither and yon.  fuck
        evtdict = {}
        for evt in ret:
            evtdict[evt[0]] = evt[1]

        memory_file = BytesIO()
        zip_file = ZipFile(memory_file, "w")

        pdfcals = make_pdf_cals(evtdict)
        zip_file.writestr("calendar.pdf", pdfcals)

        ics = make_ics(evtdict)
        zip_file.writestr("calendar.ics", ics.decode("ascii"))

        zip_file.close()
        resp = Response(memory_file.getvalue())
        resp.headers["Content-Disposition"] = "attachment; filename={}".format(
            "cals.zip"
        )
        resp.headers["Content-Type"] = "application/zip"
        return resp


def parse_csv(filename):
    csv_line = []
    with open(filename, "r") as f:
        try:
            reader = csv.reader(f)
            for line in reader:
                line[0] = parse(line[0])  # dateutil.parser
                csv_line.append(line)
        except ValueError:
            return None
    logging.debug(csv_line)
    return csv_line


def parse_xlsx(filename):
    try:
        workbook = xlrd.open_workbook(filename)
    except xlrd.biffh.XLRDError:
        return None

    sheet = workbook.sheet_by_index(0)

    xls_line = []

    for rowx in range(sheet.nrows):
        cols = sheet.row_values(rowx)
        cols[0] = datetime(*xlrd.xldate_as_tuple(cols[0], workbook.datemode))

        xls_line.append(cols)

    return xls_line


def make_pdf_cals(events):
    buf = BytesIO()
    stylesheet = getSampleStyleSheet()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    doc.pagesize = landscape(letter)
    elements = []
    months = set([d.month for d in events])
    years = set([d.year for d in events])
    logging.debug(f"make_pdf_cals: Events: {events}")
    logging.debug(f"make_pdf_cals: Months: {months}")
    logging.debug(f"make_pdf_cals: Years: {years}")

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

    pdf = buf.getvalue()

    return pdf


def evt_to_lists(events):
    evt = {}
    for e in events:
        date = datetime.strptime(
            datetime.strftime(e, "%Y-%m-%d 00:00"), "%Y-%m-%d %H:%M"
        )
        if date not in evt:
            evt[date] = []

        time = datetime.strftime(e, "%H:%M")
        if time == "00:00":
            time = ""
        evt[date].append("{} {}".format(time, events[e]))

    return evt


def fill_cal(cal, mon, yr, events):
    evts = evt_to_lists(events)
    logging.debug("Evts: {}".format(evts))
    for row, _ in enumerate(cal):
        for day, _ in enumerate(cal[row]):
            if not isinstance(cal[row][day], int) or int(cal[row][day]) < 1:
                if cal[row][day] == 0:
                    cal[row][day] = ""
                continue
            date = "{}/{}/{}".format(mon, cal[row][day], yr)
            date = datetime.strptime(date, "%m/%d/%Y")
            # this doesn't work because `date` is no longer just
            # m/d/y, but also has time now; I need to remove the time
            # part in the events dict before trying to reference it, I
            # think
            if date in evts:
                for evt in evts[date]:
                    cal[row][day] = str(cal[row][day]) + "\n{}".format(evt)
                    logging.debug(f"fill_cal : evt : {evt}")
            else:
                logging.debug(f"No event on {date}")

    return cal


def make_ics(events):
    ical = Calendar()

    for m in sorted(events):
        event = Event()
        event.add("summary", events[m])
        logging.debug("Date: {}  Time: {}".format(m.date(), m.time()))
        logging.debug(f"All: {m}")
        # if the time is midnight, assume it's an all day event
        if m.time() == "00:00:00":
            event.add("dtstart", m.date())
        else:
            event.add("dtstart", m)

        ical.add_component(event)

    return ical.to_ical(ical)


def _get_env_val(env_var, default=None):
    """Utility to popular variables from os environment variables

    Try to get the environment variable, otherwise return a default
    """
    env_val = os.getenv(env_var)
    if env_val:
        return env_val
    else:
        return default


if __name__ == "__main__":
    # Only for debugging while developing
    PORT = 8080
    if "PORT" in os.environ:
        PORT = os.environ["PORT"]

    LOG_LEVEL = _get_env_val("LOG_LEVEL", "DEBUG")
    numeric_log_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(numeric_log_level, int):
        numeric_log_level = logging.DEBUG
        logging.basicConfig(level=numeric_log_level, format=LOG_FORMAT)
        logging.debug(
            '"{}" is not a valid loglevel; defaulting to DEBUG'.format(LOG_LEVEL)
        )

    logging.basicConfig(level=numeric_log_level, format=LOG_FORMAT)

    app.run(host="0.0.0.0", debug=True, port=PORT)
