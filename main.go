package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"

	"github.com/acaird/xlscal-to-pdf-ics/pkg/event"
)

func main() {
	// options:
	//   -f <csv file of events>
	//   -i [produce an ICS file with the same basename as the CSV file, or provide a new basename]
	//   -p [produce a PDF file with the same basename as the CSV file, or provide a new basename]

	fileName := flag.String("f", "", "name of CSV file to read")
	printEvents := flag.Bool("P", false, "print out the parsed events")
	makeIcs := flag.Bool("i", false, "make an ICS file")
	makePdf := flag.Bool("p", false, "make an PDF file")
	flag.Parse()

	if *fileName == "" {
		fmt.Fprintf(os.Stderr, "Usage:\n")
		os.Exit(1)
	}

	file, err := os.Open(*fileName)
	if err != nil {
		panic(err)
	}
	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	var events event.Events
	err = events.ParseCSV(records)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	if *printEvents {
		events.Print()
	}
	if *makeIcs {
		ics := events.MakeICS()
		fmt.Println(ics)
	}
	if *makePdf {
		err = events.PdfCal(*fileName)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}
}
