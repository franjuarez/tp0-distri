package common

import (
	"encoding/binary"
	"fmt"
	"net"
	"strconv"
)

const maxBatchSize = 8192

// iota for the different types of messages
const (
	MSG_NEW_BET uint8 = iota
	MSG_ACK
	MSG_NEW_BETS_BATCH
	MSG_NACK
)

type Protocol struct {
	conn *net.Conn
}

func NewProtocol(conn *net.Conn) *Protocol {
	return &Protocol{conn: conn}
}

func (p *Protocol) recvAll(size int) ([]byte, error) {
	buf := make([]byte, size)
	total := 0

	for total < size {
		n, err := (*p.conn).Read(buf[total:])
		if err != nil || n == 0 {
			return nil, err
		}
		total += n
	}
	return buf, nil
}

func (p *Protocol) sendAll(msg []byte) error {
	written := 0
	for written < len(msg) {
		n, err := (*p.conn).Write(msg[written:])
		if err != nil {
			return fmt.Errorf("error writing message: %w", err)
		}
		if n == 0 {
			return fmt.Errorf("error writing message: wrote 0 bytes")
		}
		written += n
	}
	return nil
}

func encodeStringWithOneByteLength(s string, buf []byte) ([]byte, error) {
	if len(s) > 255 {
		return nil, fmt.Errorf("string too long")
	}
	buf = append(buf, byte(len(s)))
	buf = append(buf, []byte(s)...)
	return buf, nil
}

func (p *Protocol) createBetMessage(bet Bet) ([]byte, error) {
	msg := make([]byte, 0)

	msg, err := encodeStringWithOneByteLength(bet.FirstName, msg)
	if err != nil {
		return nil, fmt.Errorf("error serializing name: %w", err)
	}

	msg, err = encodeStringWithOneByteLength(bet.LastName, msg)
	if err != nil {
		return nil, fmt.Errorf("error serializing last name: %w", err)
	}

	msg, err = encodeStringWithOneByteLength(bet.Document, msg)
	if err != nil {
		return nil, fmt.Errorf("error serializing document: %w", err)
	}

	birthDayStr := bet.BirthDate.Format("2006-01-02")
	msg, err = encodeStringWithOneByteLength(birthDayStr, msg)
	if err != nil {
		return nil, fmt.Errorf("error serializing birth day: %w", err)
	}

	msg, err = encodeStringWithOneByteLength(bet.Number, msg)
	if err != nil {
		return nil, fmt.Errorf("error serializing number: %w", err)
	}

	return msg, nil
}

func (p *Protocol) SendBet(bet Bet, agencyId string) error {
	agencyInt, err := strconv.ParseUint(agencyId, 10, 8)
	if err != nil {
		return fmt.Errorf("error converting agency id to uint8: %w", err)
	}

	msg := make([]byte, 0)
	msg = append(msg, MSG_NEW_BET)
	msg = append(msg, byte(agencyInt))

	betMsg, err := p.createBetMessage(bet)
	if err != nil {
		return err
	}

	msg = append(msg, betMsg...)

	err = p.sendAll(msg)
	if err != nil {
		return err
	}
	return nil
}


func (p *Protocol) SendBets(bets []Bet, agencyId string) error {
	agencyInt, err := strconv.ParseUint(agencyId, 10, 8)
	if err != nil {
		return fmt.Errorf("error converting agency id to uint8: %w", err)
	}

	msg := make([]byte, 0)
	msg = append(msg, MSG_NEW_BETS_BATCH)
	msg = append(msg, byte(agencyInt))
	
	amountBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(amountBytes, uint16(len(bets)))
	msg = append(msg, amountBytes...)
	
	if err := p.sendAll(msg); err != nil {
		return fmt.Errorf("error sending message: %w", err)
	}

	var batch []byte
	for _, bet := range bets {
		betMsg, err := p.createBetMessage(bet)
		if err != nil {
			return fmt.Errorf("error creating bet message: %w", err)
		}

		if len(batch)+len(betMsg) > maxBatchSize {
			if err := p.sendAll(batch); err != nil {
				return fmt.Errorf("error sending batch message: %w", err)
			}
			batch = make([]byte, 0)
		}

		batch = append(batch, betMsg...)
	}


	if len(batch) > 0 {
		if err := p.sendAll(batch); err != nil {
			return fmt.Errorf("error sending batch message: %w", err)
		}
	}

	return nil
}

func (p *Protocol) RecvAnswer() (uint8, error) {
	answer, err := p.recvAll(1)
	if err != nil {
		return 0, fmt.Errorf("error reading answer: %w", err)
	}
	return uint8(answer[0]), nil
}

func (p *Protocol) Close() error {
	if err := (*p.conn).Close(); err != nil {
		return fmt.Errorf("error closing connection: %s", err.Error())
	}
	return nil
}
