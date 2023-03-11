package event

import (
	"time"

	"gotest.tools/v3/assert"

	"testing"
)

func TestParseCSV(t *testing.T) {
	csv := [][]string{}
	csv = append(csv, []string{"1/3/2006 16:00", "event 1", "1/3/2006 17:00", "location 1"})
	// csv = append(csv, []string{"1/3/2006 16:00", "event 1", "17:00", "location 1"})

	var events Events
	err := events.ParseCSV(csv)
	assert.NilError(t, err)

	assert.Equal(t, events[0].location, "location 1")
	assert.Equal(t, events[0].title, "event 1")
	assert.Check(t, events[0].startDate.Equal(time.Date(2006, 1, 3, 16, 0, 0, 0, events[0].startDate.Location())))
}
