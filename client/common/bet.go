package common

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"strconv"
	"time"
)

type Bet struct {
	FirstName string
	LastName  string
	Document  string
	BirthDate time.Time
	Number    string
}

type BetReader struct {
	fileName  string
	file      *os.File
	reader    *csv.Reader
	done      bool
	batchSize int
}

func (b *Bet) Validate() error {
	if len(b.FirstName) == 0 {
		return fmt.Errorf("validation error: first name should be 1 or more characters long")
	}
	if len(b.LastName) == 0 {
		return fmt.Errorf("validation error: last name should be 1 or more characters long")
	}
	if len(b.Document) != 8 {
		return fmt.Errorf("validation error: document should be 8 characters long")
	}
	if _, err := time.Parse("2006-01-02", b.BirthDate.Format("2006-01-02")); err != nil {
		return fmt.Errorf("validation error: birth day should be in the format YYYY-MM-DD")
	}
	if b.BirthDate.IsZero() {
		return fmt.Errorf("validation error: birth day should be valid")
	}
	if len(b.Number) == 0 {
		return fmt.Errorf("validation error: bet number should be 1 or more characters long")
	}
	if _, err := strconv.Atoi(b.Number); err != nil {
		return fmt.Errorf("validation error: bet number should be a number")
	}

	return nil
}

func NewBetReader(fileName string, batchSize int) (*BetReader, error) {
	file, err := os.Open(fileName)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}

	reader := csv.NewReader(file)
	return &BetReader{
		fileName:  fileName,
		file:      file,
		reader:    reader,
		done:      false,
		batchSize: batchSize,
	}, nil
}

func (br *BetReader) ReadBatchBets() ([]Bet, error) {
	var bets []Bet

	for i := 0; i < br.batchSize; i++ {
		record, err := br.reader.Read()
		if err != nil {
			if err == io.EOF {
				br.done = true
				break
			}
			return nil, fmt.Errorf("error reading file: %w", err)
		}

		birthDay, err := time.Parse("2006-01-02", record[3])
		if err != nil {
			return nil, fmt.Errorf("error parsing birth day: %w", err)
		}

		bet := Bet{
			FirstName: record[0],
			LastName:  record[1],
			Document:  record[2],
			BirthDate: birthDay,
			Number:    record[4],
		}

		if err := bet.Validate(); err != nil {
			log.Infof("error validating bet: %w", err)
			continue
		}

		bets = append(bets, bet)
	}
	
	if len(bets) == 0 {
		return nil, io.EOF
	}

	return bets, nil
}

func (br *BetReader) hasNext() bool {
	return !br.done
}

func (br *BetReader) Close() error {
	if err := br.file.Close(); err != nil {
		return fmt.Errorf("error closing file: %w", err)
	}
	return nil
}
