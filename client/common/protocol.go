package common

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
)

const maxBatchSize = 8192
const dniLength = 8
const winnersListLength = 2

const (
	MSG_NEW_BET uint8 = iota
	MSG_ACK
	MSG_NEW_BETS_BATCH
	MSG_NACK
	MSG_BETS_FINISHED
	MSG_ASK_WINNERS
	MSG_WAIT_WINNERS
	MSG_WINNERS_READY
	MSG_EOF
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

func (p *Protocol) SendBet(bet Bet, agencyId uint8) error {
	msg := make([]byte, 0)
	msg = append(msg, MSG_NEW_BET)
	msg = append(msg, agencyId)

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

func (p *Protocol) SendBets(betReader IBetReader, agencyId uint8) error {
	msg := make([]byte, 0)
	msg = append(msg, MSG_NEW_BETS_BATCH)
	msg = append(msg, agencyId)

	for betReader.hasNext() {
		bets, err := betReader.ReadBatchBets()
		if err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return fmt.Errorf("error reading bets: %w", err)
		}

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

		msg = make([]byte, 0)
		msg = append(msg, MSG_NEW_BETS_BATCH)
	}

	if err := p.sendAll([]byte{MSG_EOF}); err != nil {
		return fmt.Errorf("error sending EOF message: %w", err)
	}

	return nil
}

func (p *Protocol) sendMsgWithAgencyId(msgType uint8, agencyId uint8) error {
	msg := make([]byte, 0)
	msg = append(msg, msgType)
	msg = append(msg, agencyId)

	if err := p.sendAll(msg); err != nil {
		return fmt.Errorf("error sending message through socket: %w", err)
	}
	return nil
}

func (p *Protocol) NotifyAllBetsSent(agencyId uint8) error {
	if err := p.sendMsgWithAgencyId(MSG_BETS_FINISHED, agencyId); err != nil {
		return fmt.Errorf("error sending message: %w", err)
	}
	return nil
}

func (p *Protocol) SendWinnersRequest(agencyId uint8) error {
	if err := p.sendMsgWithAgencyId(MSG_ASK_WINNERS, agencyId); err != nil {
		return fmt.Errorf("error sending message: %w", err)
	}
	return nil
}

func (p *Protocol) RecvWinners() ([]string, error) {
	amountBytes, err := p.recvAll(winnersListLength)
	if err != nil {
		return nil, fmt.Errorf("error reading amount of winners: %w", err)
	}

	amount := binary.BigEndian.Uint16(amountBytes)
	winners := make([]string, 0)
	for i := 0; i < int(amount); i++ {
		winnerBytes, err := p.recvAll(dniLength)
		if err != nil {
			return nil, fmt.Errorf("error reading winner: %w", err)
		}
		winners = append(winners, string(winnerBytes))
	}

	return winners, nil
}

func (p *Protocol) RecvWinnersAnswer() (uint8, error) {
	answer, err := p.recvAll(1)
	if err != nil {
		return 0, fmt.Errorf("error reading answer: %w", err)
	}

	switch answer[0] {
	case MSG_WAIT_WINNERS:
		return MSG_WAIT_WINNERS, nil
	case MSG_WINNERS_READY:
		return MSG_WINNERS_READY, nil
	default:
		return 0, fmt.Errorf("unexpected message type: %d", answer[0])
	}
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
