package common

import (
	"errors"
	"io"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

const betFilePath = "/data.csv"

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchSize     int
}

// Client Entity that encapsulates how
type Client struct {
	config   ClientConfig
	protocol *Protocol
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
		return err
	}

	protocol := NewProtocol(&conn)
	c.protocol = protocol
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	betsReader, err := NewBetReader(betFilePath, c.config.BatchSize)
	if err != nil {
		log.Errorf("action: read_bets | result: fail | error: %v", err)
		return
	}
	defer betsReader.Close()

	for betsReader.hasNext() {
		if err := c.createClientSocket(); err != nil { //TODO: change to 1 connection
			log.Error("action: connect | result: fail | error: %v", err)
			return
		}

		bets, err := betsReader.ReadBatchBets()
		if err != nil {
			c.Close()
			if !errors.Is(err, io.EOF) {
				log.Errorf("action: read_bets | result: fail | error: %v", err)
				return
			}
		}

		err = c.protocol.SendBets(bets, c.config.ID)
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			c.Close()
			return
		}

		answer, err := c.protocol.RecvAnswer()
		if err != nil {
			log.Errorf("action: respuesta_recibida | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			c.Close()
			return
		}

		if answer == MSG_ACK {
			log.Infof("action: apuesta_enviada | result: success | cantidad: %v", len(bets))
		} else {
			log.Infof("action: apuesta_enviada | result: fail | cantidad: %v", len(bets))
		}

		c.Close()
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

// closeClientSocket Closes the client socket
func (c *Client) Close() {
	c.protocol.Close()
}
