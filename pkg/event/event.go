package event

import (
	"fmt"
	"sort"
	"time"

	"github.com/araddon/dateparse"
	ics "github.com/arran4/golang-ical"
	"github.com/google/uuid"
	"github.com/jinzhu/now"
	"github.com/jung-kurt/gofpdf"
)

type Event struct {
	startDate time.Time
	title     string
	endDate   time.Time
	location  string
}
type Events []Event

func (e *Events) Print() {
	// Print dumps the parsed information to a tab-separated list of event details
	for _, event := range *e {
		fmt.Printf("%v\t%v\t%s\t%s\n", event.startDate, event.endDate, event.title, event.location)
	}
}

func (e *Events) Parse(records [][]string) {
	// Parse takes a slice of slices, where the inner slice is of
	// the format: startTime, title, endTime, location, and sets
	// `e` to a list of Event structs
	for _, record := range records {
		var event Event
		var err error
		event.startDate, err = dateparse.ParseLocal(record[0])
		if err != nil {
			panic(err)
		}
		event.title = record[1]
		var endTime time.Time
		if record[2] != "" {
			endTime, err = time.Parse("15:04", record[2])
			if err != nil {
				panic(err)
			}
		} else {
			endTime, _ = time.Parse("15:04", "23:59")
		}

		end := time.Date(event.startDate.Year(), event.startDate.Month(), event.startDate.Day(),
			endTime.Hour(), endTime.Minute(), 0, 0, event.startDate.Location())
		event.endDate = end
		if err != nil {
			panic(err)
		}
		event.location = record[3]
		*e = append(*e, event)
	}
}

func (e Events) MakeICS() string {
	// MakeICS returns a string representation of an ICS file that
	// can be imported into a calendar program
	cal := ics.NewCalendar()
	cal.SetMethod(ics.MethodAdd)
	for _, evt := range e {
		uuid := uuid.NewString()
		event := cal.AddEvent(uuid)
		event.SetCreatedTime(time.Now())
		event.SetDtStampTime(time.Now())
		event.SetModifiedAt(time.Now())
		event.SetStartAt(evt.startDate)
		event.SetEndAt(evt.endDate)
		event.SetSummary(evt.title)
		event.SetLocation(evt.location)
	}
	return cal.Serialize()
}

func (e Events) Months() []time.Time {
	// Months returns a sorted list of year/month data
	eventMonths := make(map[time.Time]bool)
	for _, evt := range e {
		eventMonths[time.Date(evt.endDate.Year(), evt.endDate.Month(), 1, 0, 0, 0, 0, evt.endDate.Location())] = true
		eventMonths[time.Date(evt.startDate.Year(), evt.startDate.Month(), 1, 0, 0, 0, 0, evt.startDate.Location())] = true
	}
	var months []time.Time
	for month := range eventMonths {
		months = append(months, month)
	}
	sort.Slice(months, func(i, j int) bool {
		return months[i].Before(months[j])
	})
	return months
}

func (e Events) PdfCal() {
	type Pos struct {
		x float64
		y float64
	}
	dateSize := 8
	eventSize := 7
	locationSize := 6
	// make a pdf calendar page
	weekdays := []string{"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}
	pdf := gofpdf.New("L", "mm", "letter", "")
	pageWidth, pageHeight := pdf.GetPageSize()
	startX, startY := 10.0, 30.0
	maxX, maxY := pageWidth-startX, pageHeight-startY
	sizeX := (maxX - startX) / 7.0
	for _, calMonth := range e.Months() {
		pdf.AddPage()
		// write the header
		pdf.SetFont("Arial", "B", 16)
		pdf.Cell(40, 10, fmt.Sprintf("%s %d", calMonth.Month(), calMonth.Year()))
		pdf.SetLineWidth(0.3)
		pdf.SetDrawColor(190, 190, 190) // gray
		// make the right number of rows in the calendar
		monthStart := now.With(calMonth).BeginningOfMonth()
		monthEnd := now.With(calMonth).EndOfMonth()
		_, endWeek := monthEnd.ISOWeek()
		_, startWeek := monthStart.ISOWeek()
		weeksInMonth := float64(endWeek - startWeek + 1)
		if weeksInMonth < 0 {
			weeksInMonth = 52 + weeksInMonth - 1
		}
		sizeY := (maxY - startY) / weeksInMonth
		// make the grid with the weekday headings
		for i := 0.0; i <= weeksInMonth; i++ {
			pdf.Line(startX, startY+(i*sizeY), maxX, startY+(i*sizeY))
		}
		pdf.SetFont("Arial", "", float64(dateSize))
		for i := 0.0; i <= 7.0; i++ {
			if i < 7.0 {
				pdf.Text(startX+(i*sizeX)+2.0, startY-2.0, weekdays[int(i)])
			}
			pdf.Line(startX+(i*sizeX), startY, startX+(i*sizeX), maxY)
		}
		// write in the dates and save note locations for later
		xPos := startX + float64(int(monthStart.Weekday()))*sizeX
		yPos := startY + 5.0
		dateCoords := make(map[int]Pos)
		for day := 1; day <= monthEnd.Day(); day++ {
			dateCoords[day] = Pos{
				x: xPos,
				y: yPos,
			}
			pdf.Text(xPos+2, yPos, fmt.Sprintf("%d", day)) // put the date in the box
			xPos += sizeX
			if xPos > 0.9*maxX {
				xPos = startX
				yPos += sizeY
			}
		}
		// write the events into the boxes
		pdf.SetFont("Arial", "", float64(eventSize))
		for _, ee := range e {
			if !ee.InMonth(calMonth) {
				continue
			}
			d := ee.startDate.Day()
			textX := dateCoords[d].x + 3
			textY := dateCoords[d].y + 5
			for _, line := range pdf.SplitText(fmt.Sprintf("%s %s",
				ee.startDate.Format("3:04 PM"), ee.title),
				0.95*sizeX) {
				pdf.Text(textX, textY, line)
				textY += float64(eventSize) - 3.5
			}
			pdf.SetFont("Arial", "I", float64(locationSize))
			for _, line := range pdf.SplitText(ee.location, 0.95*sizeX) {
				pdf.Text(textX, textY, line)
				textY += float64(locationSize) - 2.0
			}
			pdf.SetFont("Arial", "", float64(eventSize))
		}
		// draw a cool border at the top and bottom
		pdf.SetLineWidth(10)
		pdf.Line(0, 0, pageWidth, 0)                   // draw across the "top" of the landscape page
		pdf.Line(0, pageHeight, pageWidth, pageHeight) // draw across the "bottom" of the landscape page
		// write the file
	}
	err := pdf.OutputFileAndClose("hello.pdf")
	if err != nil {
		panic(err)
	}
}

func (e Event) InMonth(month time.Time) bool {
	return month.Month() == e.startDate.Month()
}
