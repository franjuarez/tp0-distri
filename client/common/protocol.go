package common

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
)

type Protocol struct {
	conn *net.Conn
}

func NewProtocol(conn *net.Conn) *Protocol {
	return &Protocol{
		conn: conn,
	}
}

func (p *Protocol) writeAll(msg []byte) error {
	writer := bufio.NewWriter(*p.conn)

	_, err := writer.Write(msg)
	if err != nil {
		return fmt.Errorf("error writing to connection: %v", err)
	}

	err = writer.Flush()
	if err != nil {
		return fmt.Errorf("error flushing connection: %v", err)
	}

	return nil
}

func (p *Protocol) createBetMessage(bet Bet) ([]byte, error) {
	var buf bytes.Buffer

	if err := binary.Write(&buf, binary.BigEndian, uint16(len(bet.Name))); err != nil {
		return nil, fmt.Errorf("error converting name len to uint16: %w", err)
	}
	buf.Write([]byte(bet.Name))

	if err := binary.Write(&buf, binary.BigEndian, uint16(len(bet.LastName))); err != nil {
		return nil, fmt.Errorf("error converting last name len to uint16: %w", err)
	}
	buf.Write([]byte(bet.LastName))

	if err := binary.Write(&buf, binary.BigEndian, uint16(len(bet.Document))); err != nil {
		return nil, fmt.Errorf("error converting document len to uint16: %w", err)
	}
	buf.Write([]byte(bet.Document))

	birthDayStr := bet.BirthDay.Format("2006-01-02")
	if err := binary.Write(&buf, binary.BigEndian, uint16(len(birthDayStr))); err != nil {
		return nil, fmt.Errorf("error converting birthDay len to uint16: %w", err)
	}
	buf.Write([]byte(birthDayStr))

	if err := binary.Write(&buf, binary.BigEndian, uint16(len(bet.Number))); err != nil {
		return nil, fmt.Errorf("error converting number len to uint16: %w", err)
	}
	buf.Write([]byte(bet.Number))

	return buf.Bytes(), nil
}

func (p *Protocol) SendNewBetMessage(agencyId string, bet Bet) error {
	if len(agencyId) != 1 {
		return fmt.Errorf("error writing agency id: invalid length")
	}

	var buf bytes.Buffer

	if err := binary.Write(&buf, binary.BigEndian, MSG_NEW_BET); err != nil {
		return fmt.Errorf("error writing message type: %w", err)
	}

	if err := buf.WriteByte(agencyId[0]); err != nil {
		return fmt.Errorf("error writing agency id: %w", err)
	}

	msg, err := p.createBetMessage(bet)
	if err != nil {
		return fmt.Errorf("error crating bet message: %w", err)
	}

	buf.Write(msg)

	if err := p.writeAll(buf.Bytes()); err != nil {
		return fmt.Errorf("error sending message: %w", err)
	}

	return nil
}

func (p *Protocol) ReceiveAck() error {
	msg, err := bufio.NewReader(*p.conn).ReadByte()
	if err != nil {
		return fmt.Errorf("error receiving message: %w", err)
	}

	if msg != MSG_ACK {
		return fmt.Errorf("error receiving ack message: unexpected message type: %v", msg)
	}

	return nil
}

func (p *Protocol) Close() error {
	if err := (*p.conn).Close(); err != nil {
		return fmt.Errorf("error closing connection: %s", err.Error())
	}
	return nil
}
