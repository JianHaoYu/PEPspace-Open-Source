package proxy

import (
	"fmt"
	"io"
	"time"

	quic "github.com/quic-go/quic-go"
	quicspace "github.com/quic-go/quic-go-space"
)

// PEP <----- QUIC
func HandleQUICOutPutStreams(PEPstream quicspace.Stream, IncomingStream quic.Stream) {
	buf := make([]byte, 1e6)
	if err := PEPstream.SetDeadline(time.Now().Add(2000 * time.Second)); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams PEPstream.SetWriteDeadline 20s: %w", err))
	}
	if err := IncomingStream.SetDeadline(time.Now().Add(2000 * time.Second)); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams IncomingStream.SetReadDeadline 20s: %w", err))
	}
	n, err := io.CopyBuffer(PEPstream, IncomingStream, buf)
	if err != nil && err != io.EOF {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams io.Copy(PEPstream, IncomingStream) %w", err))
	}
	fmt.Printf("[PEP] HandleStreams Read %d bytes Write %d bytes \n", n, n)

	err = PEPstream.Close()
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams PEPstream.Close()"))
	}
}

// PEP -----> QUIC
func HandleQUICInPutStreams(PEPstream quicspace.Stream, IncomingStream quic.Stream) {
	buf := make([]byte, 1e6)
	if err := PEPstream.SetDeadline(time.Now().Add(2000 * time.Second)); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICInPutStreams PEPstream.SetWriteDeadline 20s: %w", err))
	}
	if err := IncomingStream.SetDeadline(time.Now().Add(2000 * time.Second)); err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICInPutStreams IncomingStream.SetReadDeadline 20s: %w", err))
	}
	n, err := io.CopyBuffer(IncomingStream, PEPstream, buf)
	if err != nil && err != io.EOF {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams io.Copy(PEPstream, IncomingStream) %w", err))
	}
	fmt.Printf("[PEP] HandleStreams Read %d bytes Write %d bytes \n", n, n)

	err = IncomingStream.Close()
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandleQUICOutPutStreams PEPstream.Close()"))
	}
}
