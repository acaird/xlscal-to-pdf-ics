package event

import (
	"fmt"
	"sort"
	"time"

	"github.com/araddon/dateparse"
	ics "github.com/arran4/golang-ical"
	"github.com/google/uuid"
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
		event := cal.AddEvent(fmt.Sprintf(uuid))
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
