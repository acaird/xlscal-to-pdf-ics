package main

import (
	"encoding/csv"
	"os"

	"github.com/acaird/xlscal-to-pdf-ics/pkg/event"
)

func main() {
	file, err := os.Open("22bs.csv")
	if err != nil {
		panic(err)
	}
	reader := csv.NewReader(file)
	records, _ := reader.ReadAll()

	var events event.Events
	events.Parse(records)
	// i := events.MakeICS()
	// fmt.Println(i)
	events.PdfCal()
	// fmt.Println(months)
}
