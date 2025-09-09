package proxy

import (
	"fmt"
	"io"
	"net"
	"time"

	quicspace "github.com/quic-go/quic-go-space"
)

// PEP <----- TCP
func HandleTCPOutPutStreams(PEPstream quicspace.Stream, TCPconn net.Conn) {
	buf := make([]byte, 1e6)
	if err := PEPstream.SetReadDeadline(time.Time{}); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICInPutStreams PEPstream.SetReadDeadline 20s: %w", err))
	}
	if err := TCPconn.SetWriteDeadline(time.Time{}); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICInPutStreams TCPconn.SetWriteDeadline 20s: %w", err))
	}
	n, err := io.CopyBuffer(TCPconn, PEPstream, buf)
	if err != nil && err != io.EOF {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams io.Copy(PEPstream, IncomingStream) %w", err))
	}
	fmt.Printf("[PEP] HandleTCPOutPutStreams Read %d bytes Write %d bytes \n", n, n)

	err = TCPconn.(*net.TCPConn).CloseWrite()
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams PEPstream.Close()"))
	}
}

// PEP -----> TCP
func HandleTCPInPutStreams(PEPstream quicspace.Stream, TCPconn net.Conn) {
	buf := make([]byte, 1e6)
	if err := TCPconn.SetReadDeadline(time.Time{}); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleTCPInPutStreams TCPconn.SetReadDeadline 20s: %w", err))
	}
	if err := PEPstream.SetWriteDeadline(time.Time{}); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleTCPInPutStreams PEPstream.SetWriteDeadline 20s: %w", err))
	}
	n, err := io.CopyBuffer(PEPstream, TCPconn, buf)
	if err != nil && err != io.EOF {
		panic(fmt.Errorf("[PEPSender] HandleTCPInPutStreams io.Copy(PEPstream, TCPconn) %w", err))
	}
	fmt.Printf("[PEP] HandleTCPInPutStreams Read %d bytes Write %d bytes \n", n, n)

	err = PEPstream.Close()
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandleTCPInPutStreams PEPstream.Close()"))
	}

}
