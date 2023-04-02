package event

import (
	"reflect"
	"testing"
	"time"

	"gotest.tools/v3/assert"
)

func TestEvents_ParseCSV(t *testing.T) {
	csv := [][]string{}
	csv = append(csv, []string{"1/3/2006 16:00", "event 1", "1/3/2006 17:00", "location 1"})
	csv = append(csv, []string{"1/3/2006 16:00", "event 1", "17:00", "location 1"})

	var events Events
	err := events.ParseCSV(csv)
	assert.NilError(t, err)

	assert.Equal(t, events[0].location, "location 1")
	assert.Equal(t, events[0].title, "event 1")
	assert.Check(t, events[0].startDate.Equal(time.Date(2006, 1, 3, 16, 0, 0, 0, events[0].startDate.Location())))
	assert.Check(t, events[1].endDate.Equal(time.Date(2006, 1, 3, 17, 0, 0, 0, events[1].endDate.Location())))
}

func TestEvents_Print(t *testing.T) {
	tests := []struct {
		name string
		e    *Events
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.e.Print()
		})
	}
}

// func TestEvents_ParseCSV(t *testing.T) {
// 	type args struct {
// 		records [][]string
// 	}
// 	tests := []struct {
// 		name    string
// 		e       *Events
// 		args    args
// 		wantErr bool
// 	}{
// 		// TODO: Add test cases.
// 	}
// 	for _, tt := range tests {
// 		t.Run(tt.name, func(t *testing.T) {
// 			if err := tt.e.ParseCSV(tt.args.records); (err != nil) != tt.wantErr {
// 				t.Errorf("Events.ParseCSV() error = %v, wantErr %v", err, tt.wantErr)
// 			}
// 		})
// 	}
// }

func TestEvents_MakeICS(t *testing.T) {
	tests := []struct {
		name string
		e    Events
		want string
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.e.MakeICS(); got != tt.want {
				t.Errorf("Events.MakeICS() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestEvents_Months(t *testing.T) {
	time_one, _ := time.Parse("2006-01-02T15:00", "2023-02-05T14:00")
	month_one, _ := time.Parse("2006-01-02T15:00", "2023-02-01T00:00")
	time_two, _ := time.Parse("2006-01-02T15:00", "2023-03-05T14:00")
	month_two, _ := time.Parse("2006-01-02T15:00", "2023-03-01T00:00")
	month_three, _ := time.Parse("2006-01-02T15:00", "2023-04-01T00:00")

	tests := []struct {
		name string
		e    Events
		want []time.Time
	}{
		{
			name: "months1",
			e: []Event{
				{
					startDate: time_one,
					title:     "event 2/5/23 2pm",
					endDate:   time_one.Add(48 * time.Hour),
					location:  "loc of 2/5/23 2pm",
				},
				{
					startDate: time_two,
					title:     "event 2/5/23 2pm",
					endDate:   time_two.Add(48 * time.Hour),
					location:  "loc of 2/5/23 2pm",
				},
				{
					startDate: time_one.Add(1 * time.Second),
					title:     "event 2/5/23 2:00:01pm",
					endDate:   time_one.Add(48 * time.Hour),
					location:  "loc of 2/5/23 2:00:01pm",
				},
				{
					startDate: time_one.Add(-48 * time.Hour),
					title:     "event 2/5/21 2pm",
					endDate:   time_one.Add(24 * time.Hour),
					location:  "loc of 2/5/21 2pm",
				},
			},
			want: []time.Time{
				month_one,
				month_two,
			},
		},
		{
			name: "months2",
			e: []Event{
				{
					startDate: time_one,
					title:     "event 2/5/23 2pm",
					endDate:   time_one.Add(48 * time.Hour),
					location:  "loc of 2/5/23 2pm",
				},
				{
					startDate: time_two.Add(24 * 32 * time.Hour),
					title:     "event 2/5/23 2pm",
					endDate:   time_two.Add(25 * 32 * time.Hour),
					location:  "loc of 2/5/23 2pm",
				},
				{
					startDate: time_one.Add(1 * time.Second),
					title:     "event 2/5/23 2:00:01pm",
					endDate:   time_one.Add(48 * time.Hour),
					location:  "loc of 2/5/23 2:00:01pm",
				},
				{
					startDate: time_one.Add(-48 * time.Hour),
					title:     "event 2/5/21 2pm",
					endDate:   time_one.Add(24 * time.Hour),
					location:  "loc of 2/5/21 2pm",
				},
			},
			want: []time.Time{
				month_one,
				month_three,
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.e.Months(); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("Events.Months() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestEvents_PdfCal(t *testing.T) {
	type args struct {
		filename string
	}
	tests := []struct {
		name    string
		e       Events
		args    args
		wantErr bool
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if err := tt.e.PdfCal(tt.args.filename); (err != nil) != tt.wantErr {
				t.Errorf("Events.PdfCal() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestEvent_InMonth(t *testing.T) {
	type fields struct {
		startDate time.Time
		title     string
		endDate   time.Time
		location  string
	}
	type args struct {
		month time.Time
	}
	time_one, _ := time.Parse("2006-01-02T15:00", "2023-02-05T14:00")
	time_two, _ := time.Parse("2006-01-02T05:00", "2023-02-25T14:00")
	time_three, _ := time.Parse("2006-01-02T15:00", "2023-03-05T14:00")

	tests := []struct {
		name   string
		fields fields
		args   args
		want   bool
	}{
		{
			name: "in month",
			fields: fields{
				startDate: time_one,
			},
			args: args{
				time_two,
			},
			want: true,
		},
		{
			name: "not in month",
			fields: fields{
				startDate: time_one,
			},
			args: args{
				time_three,
			},
			want: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			e := Event{
				startDate: tt.fields.startDate,
				title:     tt.fields.title,
				endDate:   tt.fields.endDate,
				location:  tt.fields.location,
			}
			if got := e.InMonth(tt.args.month); got != tt.want {
				t.Errorf("Event.InMonth() = %v, want %v", got, tt.want)
			}
		})
	}
}
