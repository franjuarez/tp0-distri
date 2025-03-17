package common

import (
	"fmt"
	"time"
)

type Bet struct {
	Name     string
	LastName string
	Document string
	BirthDay time.Time
	Number   string
}

func (b *Bet) Validate() error {
	if len(b.Name) < 2 {
		return fmt.Errorf("validation error: first name should be 2 or more characters long")
	}
	if len(b.LastName) < 2 {
		return fmt.Errorf("validation error: last name should be 2 or more characters long")
	}
	if len(b.Document) < 4 {
		return fmt.Errorf("validation error: document should be 4 or more characters long")
	}
	if b.BirthDay.IsZero() {
		return fmt.Errorf("validation error: birth day should be valid")
	}
	if len(b.Number) < 2 {
		return fmt.Errorf("validation error: bet number should be 2 or more characters long")
	}

	return nil
}