package common

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Create the connection the server in every loop iteration. Send an
		c.createClientSocket()

		msg := fmt.Sprintf("[CLIENT %v] Message N°%v\n", c.config.ID, msgID)
		err := writeAll(c.conn, []byte(msg))
		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		msg, err = bufio.NewReader(c.conn).ReadString('\n')
		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		err = c.conn.Close()
		if err != nil {
			log.Errorf("action: close_connection | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) createBetMessage(bet Bet) ([]byte, error) {
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

func (c *Client) SendBet(bet Bet) error {
	err := bet.Validate()
	if err != nil {
		return fmt.Errorf("error validating bet: %s", err.Error())
	}

	c.createClientSocket()

	msg, err := c.createBetMessage(bet)
	if err != nil {
		return fmt.Errorf("error crating bet message: %s", err.Error())
	}

	err = writeAll(c.conn, msg)
	if err != nil {
		log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	response, err := bufio.NewReader(c.conn).ReadByte()
	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	if response != MSG_ACK {
		err := fmt.Errorf("error: unexpected response from server, expected ACK, got: %v", response)
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	err = c.conn.Close()
	if err != nil {
		log.Errorf("action: close_connection | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s",
		bet.Document,
		bet.Number,
	)

	return nil
}

// closeClientSocket Closes the client socket
func (c *Client) CloseClient() {
	c.conn.Close()
}
