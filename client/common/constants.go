package common

// iota for the different types of messages
const (
	MSG_NEW_BET uint8 = iota
	MSG_ACK
	MSG_NEW_BETS_BATCH
	MSG_NACK
)
