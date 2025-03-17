package common

import (
	"bufio"
	"fmt"
	"net"
)

func writeAll(conn net.Conn, msg []byte) error {
	writer := bufio.NewWriter(conn)

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
