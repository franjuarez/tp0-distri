package common

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
)

type Protocol struct {
	conn  *net.Conn
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

	err := binary.Write(&buf, binary.BigEndian, MSG_NEW_BET)
	if err != nil {
		return nil, fmt.Errorf("error writing message type: %s", err.Error())
	}

	err = binary.Write(&buf, binary.BigEndian, uint16(len(bet.Name)))
	if err != nil {
		return nil, fmt.Errorf("error converting name len to uint16: %s", err.Error())
	}
	buf.Write([]byte(bet.Name))

	err = binary.Write(&buf, binary.BigEndian, uint16(len(bet.LastName)))
	if err != nil {
		return nil, fmt.Errorf("error converting last name len to uint16: %s", err.Error())
	}
	buf.Write([]byte(bet.LastName))

	err = binary.Write(&buf, binary.BigEndian, uint16(len(bet.Document)))
	if err != nil {
		return nil, fmt.Errorf("error converting document len to uint16: %s", err.Error())
	}
	buf.Write([]byte(bet.Document))

	birthDayStr := bet.BirthDay.Format("2006-01-02")
	err = binary.Write(&buf, binary.BigEndian, uint16(len(birthDayStr)))
	if err != nil {
		return nil, fmt.Errorf("error converting birthDay len to uint16: %s", err.Error())
	}
	buf.Write([]byte(birthDayStr))

	err = binary.Write(&buf, binary.BigEndian, uint16(len(bet.Number)))
	if err != nil {
		return nil, fmt.Errorf("error converting number len to uint16: %s", err.Error())
	}
	buf.Write([]byte(bet.Number))

	return buf.Bytes(), nil
}

func (p *Protocol) SendNewBet(bet Bet) error {
	msg, err := p.createBetMessage(bet)
	if err != nil {
		return fmt.Errorf("error crating bet message: %s", err.Error())
	}

	err = p.writeAll(msg)
	if err != nil {
		return fmt.Errorf("error sending message: %s", err.Error())
	}

	return nil
}

func (p *Protocol) ReceiveAck() error {
	msg, err := bufio.NewReader(*p.conn).ReadByte()
	if err != nil {
		return fmt.Errorf("error receiving message: %s", err.Error())
	}

	if msg != MSG_ACK {
		return fmt.Errorf("error receiving ack message: unexpected message type: %v", msg)
	}

	return nil
}

func (p *Protocol) Close() error {
	err := (*p.conn).Close()
	if err != nil {
		return fmt.Errorf("error closing connection: %s", err.Error())
	}

	return nil
}