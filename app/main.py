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


class EventList:
    def __init__(self, file_, filename, http_request):
        self.file_ = file_
        self.filename = filename
        self.request = http_request
        self.can_process = [".csv", ".xlsx"]
        self.fileroot, self.fileext = os.path.splitext(self.filename)
        self.events = None
        self.headers = ["time", "description", "endtime", "location"]

    def _validate(self):
        """Validate a file based on its extension

        Returns
        -------
        None
            if the file is valid
        str
            containing the error if the file is invalid

        """
        if self.fileext not in self.can_process:
            message = (
                'Files of type "{}" cannot be processed, please '
                "upload a file of one of these types: {}".format(
                    fileext, ", ".join(self.can_process)
                )
            )
            return message

        return None

    def _parse_csv(self):
        """Parse an uploaded CSV file

        Returns
        -------
        list
            datetime.datetime, str, ...
        """
        csv_lines = []
        with open(self.filename, "r") as f:
            try:
                reader = csv.reader(f)
                for line in reader:
                    logging.debug(line)
                    line[0] = parse(line[0])  # dateutil.parser

                    if len(line) > 2:
                        if line[2] is not None and line[2] != " " and line[2] != "":
                            line[2] = parse(line[2])
                    csv_lines.append(line)
            except ValueError as e:
                logging.debug(e)
                csv_lines = None

        logging.debug(csv_lines)
        return csv_lines

    def _parse_xlsx(self):
        """Parse an uploaded XLSX file

        Returns
        -------
        list
            datetime.datetime, str, ...
        """
        try:
            workbook = xlrd.open_workbook(self.filename)
        except xlrd.biffh.XLRDError as e:
            logging.debug(e)
            return None

        sheet = workbook.sheet_by_index(0)

        xls_line = []

        for rowx in range(sheet.nrows):
            cols = sheet.row_values(rowx)
            cols[0] = datetime(*xlrd.xldate_as_tuple(cols[0], workbook.datemode))
            cols[2] = datetime(*xlrd.xldate_as_tuple(cols[0], workbook.datemode))

            xls_line.append(cols)

        return xls_line

    def _structure_events(self, events):
        """Take events in lists and return them with some structure

        The structure is a list of objects that look like: {"time":
        datetime.datetime, "description": str, "endtime":
        datetime.datetime, "location": str}

        Parameters
        ----------
        events: list
           list of lists, each sub-list is the ordered list of details
           assuming the order: time, description, endtime, location

        Returns
        -------
        list
           list of objects describing each event using the format
           described above

        """
        events.sort()
        events_list = []

        for event in events:
            event_obj = dict.fromkeys(self.headers)
            logging.debug(f"[_structure_events] event: {event}")
            for index, field in enumerate(event):
                if self.headers[index] == "endtime" and isinstance(field, datetime):
                    logging.debug(
                        "Field: {} event_obj[time]: {}".format(field, event_obj["time"])
                    )
                    if field < event_obj["time"]:
                        field = field.replace(
                            year=event_obj["time"].year,
                            month=event_obj["time"].month,
                            day=event_obj["time"].day,
                        )
                if isinstance(field, str):
                    field.strip()
                event_obj[self.headers[index]] = field
            logging.debug(event_obj)
            events_list.append(event_obj)

        return events_list

    def _fill_cal(self, cal, mon, yr):
        for row, _ in enumerate(cal):
            for day, _ in enumerate(cal[row]):
                if not isinstance(cal[row][day], int) or int(cal[row][day]) < 1:
                    if cal[row][day] == 0:
                        cal[row][day] = ""
                    continue
                date = "{}/{}/{}".format(mon, cal[row][day], yr)
                date = datetime.strptime(date, "%m/%d/%Y")
                for event in self.events:
                    cal_entry = ""
                    if event["time"].date() == date.date():
                        if event["time"].time() != "00:00:00":
                            cal_entry += "\n{}".format(
                                datetime.strftime(event["time"], "%H:%M"),
                            )
                            if (
                                "endtime" in event
                                and event["endtime"] is not None
                                and isinstance(event["endtime"], datetime)
                            ):
                                cal_entry += "-{}".format(
                                    datetime.strftime(event["endtime"], "%H:%M"),
                                )

                        cal_entry += "\n{}".format(event["description"])
                        if "location" in event and event["location"] is not None:
                            cal_entry += "\n{}".format(event["location"])

                        cal[row][day] = str(cal[row][day]) + cal_entry

                        logging.debug(f"fill_cal : event : {cal_entry}")
                    else:
                        logging.debug(f"No event on {date}")

        return cal

    def loadfile(self):
        """Loads data into the EventList object

        """
        ret = self._validate()
        if ret:
            return ret

        if self.fileext == ".csv":
            events = self._parse_csv()
            if events is None:
                return "The .csv file was badly formatted, check it again try again."
        if self.fileext == ".xlsx":
            events = self._parse_xlsx(sfname)
            if events is None:
                return "The .xlsx file was badly formatted, check it again try again."

        self.events = self._structure_events(events)

        return None

    def make_pdf_cals(self, return_flask_resp=False):
        logging.debug(f"make_pdf_cals: Events: {self.events}")
        buf = BytesIO()
        stylesheet = getSampleStyleSheet()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        doc.pagesize = landscape(letter)
        elements = []
        months = set([d["time"].month for d in self.events])
        years = set([d["time"].year for d in self.events])
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
                cal = self._fill_cal(cal, month, year)
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

        return buf.getvalue()

    def make_ics(self):
        ical = Calendar()

        for e in self.events:
            event = Event()
            event.add("summary", e["description"])
            logging.debug(
                "Date: {}  Time: {}".format(e["time"].date(), e["time"].time())
            )
            logging.debug(f"All: {e}")
            # if the time is midnight, assume it's an all day event
            if e["time"].time() == "00:00:00":
                event.add("dtstart", e["time"].date())
            else:
                event.add("dtstart", e["time"])
            if (
                "endtime" in e
                and e["endtime"] is not None
                and isinstance(e["endtime"], datetime)
            ):
                event.add("dtend", e["endtime"])
            if "location" in e and e["location"] is not None:
                event.add("location", e["location"])

            ical.add_component(event)

        return ical.to_ical(ical)

    def make_zipfile(self):
        """Make a zip file with the PDF and ICS files in it

        Returns
        -------
        flask.Response
        """
        memory_file = BytesIO()
        zip_file = ZipFile(memory_file, "w")

        pdfcals = self.make_pdf_cals()
        if pdfcals:
            zip_file.writestr(f"calendar-{self.fileroot}.pdf", pdfcals)

        ics = self.make_ics()
        zip_file.writestr(f"calendar-{self.fileroot}.ics", ics.decode("ascii"))

        zip_file.close()
        resp = Response(memory_file.getvalue())
        resp.headers["Content-Disposition"] = "attachment; filename={}".format(
            f"cals-{self.fileroot}.zip"
        )
        resp.headers["Content-Type"] = "application/zip"
        return resp


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

        events = EventList(f, sfname, request)
        load_status = events.loadfile()
        if load_status:
            return load_status, 400
        return events.make_zipfile()


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
