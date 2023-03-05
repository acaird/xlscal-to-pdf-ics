package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"time"

	"github.com/jinzhu/now"
	"github.com/jung-kurt/gofpdf"

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
	pdfCal()
}

func pdfCal() {
	type Pos struct {
		x float64
		y float64
	}
	// can we make a pdf calendar page?
	weekdays := []string{"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}
	pdf := gofpdf.New("L", "mm", "letter", "")
	pageWidth, pageHeight := pdf.GetPageSize()
	pdf.AddPage()
	// write the header
	pdf.SetFont("Arial", "B", 16)
	n := time.Now()
	n = n.AddDate(0, -1, 0)
	pdf.Cell(40, 10, fmt.Sprintf("%s %d", n.Month(), n.Year()))
	// make the grid
	pdf.SetLineWidth(0.3)
	pdf.Line(40, 10, 41, 10)
	startX := 10.0
	startY := 30.0
	maxX := pageWidth - startX
	maxY := pageHeight - startY
	sizeX := (maxX - startX) / 7.0
	sizeY := (maxY - startY) / 5.0
	pdf.SetDrawColor(190, 190, 190) // gray
	for i := 0.0; i <= 5.0; i++ {
		pdf.Line(startX, startY+(i*sizeY), maxX, startY+(i*sizeY))
	}
	pdf.SetFont("Arial", "", 8)
	for i := 0.0; i <= 7.0; i++ {
		if i < 7.0 {
			pdf.Text(startX+(i*sizeX)+2.0, startY-2.0, fmt.Sprintf("%s", weekdays[int(i)]))
		}
		pdf.Line(startX+(i*sizeX), startY, startX+(i*sizeX), maxY)
	}
	// write in the dates
	monthStart := now.With(n).BeginningOfMonth()
	monthEnd := now.With(n).EndOfMonth()
	xPos := startX + float64(int(monthStart.Weekday()))*sizeX
	yPos := startY + 5
	x := make(map[int]Pos)
	for day := 1; day <= monthEnd.Day(); day++ {
		x[day] = Pos{
			x: xPos,
			y: yPos,
		}
		pdf.Text(xPos+2, yPos, fmt.Sprintf("%d", day))
		xPos += sizeX
		if xPos > maxX {
			xPos = startX
			yPos += sizeY
		}
	}
	// draw a cool border at the top and bottom
	pdf.SetLineWidth(10)
	pdf.Line(0, 0, pageWidth, 0)                   // draw across the "top" of the landscape page
	pdf.Line(0, pageHeight, pageWidth, pageHeight) // draw across the "bottom" of the landscape page
	// write the file
	err := pdf.OutputFileAndClose("hello.pdf")
	if err != nil {
		panic(err)
	}

}
