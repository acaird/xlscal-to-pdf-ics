from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.graphics.shapes import Drawing

import calendar

stylesheet = getSampleStyleSheet()
doc = SimpleDocTemplate('calendar.pdf', pagesize=letter)
doc.pagesize = landscape(letter)
elements = []

elements.append(Paragraph('February 2019', stylesheet['Title']))

cal = [['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']]
cal.extend(calendar.monthcalendar(2019,2))
cal[1][4] = str(cal[1][4])+"\nHI!!!!!"
for w,x in enumerate(cal):
    for v,y in enumerate(cal[w]):
        print "{},{}".format(w,v)
        if cal[w][v] == 0:
            cal[w][v] = ''
print cal


table = Table(cal, 7*[1.25 *inch], len(cal) * [0.8 * inch])

table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.green),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

elements.append(table)
#create the pdf with this
#doc.build([table])
doc.build(elements)
