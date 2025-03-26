package common

import (
	"fmt"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

const betFilePath = "/data.csv"

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            uint8
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
		return fmt.Errorf("error connecting to server: %v", err)
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

	if err := c.createClientSocket(); err != nil {
		log.Error("action: connect | result: fail | error: %v", err)
		return
	}

	err = c.protocol.SendBets(betsReader, c.config.ID)
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
		log.Infof("action: apuesta_enviada | result: success")
	} else {
		log.Errorf("action: apuesta_enviada | result: fail | answer: %v", answer)
		return
	}
	
	if err := c.protocol.NotifyAllBetsSent(c.config.ID); err != nil {
		log.Errorf("action: apuestas_finalizadas | result: fail | client_id: %v | error: %v",
		c.config.ID,
			err,
		)
		c.Close()
		return
	}
	
	fmt.Println("Notified all bets sent")
	
	if err := c.askForWinners(); err != nil {
		log.Errorf("action: ganadores | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) askForWinners() error {
	for {
		err := c.protocol.SendWinnersRequest(c.config.ID)
		if err != nil {
			log.Errorf("action: winners_request | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			c.Close()
			return err
		}

		fmt.Println("Sent winners request")

		answer, err := c.protocol.RecvWinnersAnswer()
		if err != nil {
			log.Errorf("action: winners_received | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			c.Close()
			return err
		}

		if answer == MSG_WINNERS_READY {
			winners, err := c.protocol.RecvWinners()
			if err != nil {
				log.Errorf("action: winners_received | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				c.Close()
				return err
			}
			log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))
			break
		}

		time.Sleep(1 * time.Second)
	}

	c.Close()
	return nil
}

// closeClientSocket Closes the client socket
func (c *Client) Close() {
	if c.protocol != nil {
		c.protocol.Close()
	}
}
