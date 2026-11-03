package proxy

import (
	"context"
	"fmt"
	"net"

	"github.com/quic-go/quic-go"
	quicspace "github.com/quic-go/quic-go-space"
)

// QUIC----->
//            \
//		       -PEP------->
//            /
// QUIC----->

func HandlePEPSenderConnection(PEPConn quicspace.Connection, PEPLoaclTCPAddr string, PEPLoaclQUICAddr string) {
	go PEPTCPListener(PEPConn, PEPLoaclTCPAddr)

	config := &quic.Config{
		// HandshakeIdleTimeout:           100000000000,
		MaxIdleTimeout:                 300000000000,
		InitialStreamReceiveWindow:     40 * (1 << 20),
		MaxStreamReceiveWindow:         40 * (1 << 20),
		InitialConnectionReceiveWindow: 40 * (1 << 20) * 2,
		MaxConnectionReceiveWindow:     40 * (1 << 20) * 2,
		// InitialStreamReceiveWindow:     2250,
		// MaxStreamReceiveWindow:         2250,
		// InitialConnectionReceiveWindow: 2250 * 7,
		// MaxConnectionReceiveWindow:     2250 * 7,
	}
	QUICListener, err := quic.ListenAddrEarly(PEPLoaclQUICAddr, generateTLSConfig(), config)
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandlePEPSenderConnection quic.ListenAddrEarly: %w", err))
	}
	defer QUICListener.Close()
	fmt.Printf("[PEPSender] QUIC Server listening on %s\n", PEPLoaclQUICAddr)

	for {
		QUICConn, err := QUICListener.Accept(context.Background())
		if err != nil {
			panic(fmt.Errorf("[PEPSender] HandlePEPSenderConnection QUICListener.Accept: %w", err))
		}

		go HandleIncomingQUICConnection(PEPConn, QUICConn)
	}
}

func HandleIncomingQUICConnection(PEPConn quicspace.Connection, QUICConn quic.Connection) { //处理端点输入连接，开启新Stream
	//开启新的Stream，并根据新的连接通知PEP对端如何转发到对应的Address
	for {
		IncomingStream, err := QUICConn.AcceptStream(context.Background())
		if err != nil {
			panic(fmt.Errorf("[PEPSender] HandleIncomingQUICConnection QUICConn.AcceptStream: %w", err))
		}
		PEPstream, err := PEPConn.OpenStreamSync(context.Background())
		if err != nil {
			panic(fmt.Errorf("[PEPSender] HandleIncomingQUICConnection PEPConn.OpenStreamSync: %w", err))
		}
		fmt.Println("[PEPSender] HandleIncomingQUICConnection QUICStream and PEPstream Open new Stream Successfully")
		go HandleQUICOutPutStreams(PEPstream, IncomingStream)
		go HandleQUICInPutStreams(PEPstream, IncomingStream)
	}
}

func PEPTCPListener(PEPConn quicspace.Connection, PEPLoaclTCPAddr string) {
	listener, err := net.Listen("tcp", PEPLoaclTCPAddr)
	if err != nil {
		panic(fmt.Errorf("[PEPSender] PEPTCPListener net.Listen: %w", err))
	}
	defer listener.Close()
	fmt.Printf("[PEPSender] TCP Server listening on %s\n", PEPLoaclTCPAddr)

	for {
		TCPconn, err := listener.Accept()
		if err != nil {
			fmt.Println("[PEPSender] PEPTCPListener listener.Accept:", err)
			continue
		}
		fmt.Printf("[PEPSender] TCP Server %s connected successfully \n", TCPconn.RemoteAddr())

		go HandleIncomingTCPConnection(PEPConn, TCPconn)
	}
}

func HandleIncomingTCPConnection(PEPConn quicspace.Connection, TCPconn net.Conn) {
	PEPstream, err := PEPConn.OpenStreamSync(context.Background())
	if err != nil {
		panic(fmt.Errorf("[PEPSender] HandleIncomingTCPConnection PEPConn.OpenStreamSync: %w", err))
	}
	fmt.Println("[PEPSender] PEPstream Open new Stream Successfully")

	go HandleTCPOutPutStreams(PEPstream, TCPconn)
	go HandleTCPInPutStreams(PEPstream, TCPconn)
}
