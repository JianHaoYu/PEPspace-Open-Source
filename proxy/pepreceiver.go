package proxy

import (
	"PEPSpace/address"
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"net"

	quic "github.com/quic-go/quic-go"
	quicspace "github.com/quic-go/quic-go-space"
)

//               -----> QUIC
//             /
//-------> PEP
//             \
//               -----> QUIC

func HandlePEPReceiverConnection(PEPConn quicspace.Connection) { //处理PEP连接，循环等待开启新Stream，每个新Stream代表对端开启了一个新连接
	for { //等待对端开启新Stream，并根据新Stream与本地叶子建立连接
		newstream, err := PEPConn.AcceptStream(context.Background())
		if err != nil {
			fmt.Println("[PEPReceiver] PEPConn.AcceptStream: %w", err)
			panic(fmt.Errorf("[PEPReceiver] PEPConn.AcceptStream: %w", err))
		}
		fmt.Println("Open a new Stream on the other end and start connecting to leaf nodes")
		go HandlePEPNewStream(newstream)
	}
}

func HandlePEPNewStream(PEPstream quicspace.Stream) {
	receivedbytes := make([]byte, address.Length()) // [Length(2 byte) | HASH(32 byte) | Address (16 bytes) | Type (3 bytes)]
	_, err := io.ReadFull(PEPstream, receivedbytes)
	if err != nil {
		panic(fmt.Errorf("[PEPReceiver] Read Address error: %w", err))
	}
	TargetAddress, conntype := address.ParseTargetAddress(receivedbytes)

	if conntype == "tcp\x00" {
		OpenNewTCPConn(TargetAddress, PEPstream)
	} else {
		OpenNewQUICConn(TargetAddress, PEPstream)
	}
}

func OpenNewTCPConn(addr string, PEPstream quicspace.Stream) {
	TCPconn, err := net.Dial("tcp", addr)
	if err != nil {
		panic(fmt.Errorf("[PEPReceiver] OpenNewTCPConn net.Dial(tcp, addr): %w", err))
	}

	go HandleTCPOutPutStreams(PEPstream, TCPconn)
	go HandleTCPInPutStreams(PEPstream, TCPconn)
}

// Yu TODO: Check if it is a new stream from an existing connection
func OpenNewQUICConn(addr string, PEPstream quicspace.Stream) {
	tlsConf := &tls.Config{
		InsecureSkipVerify: true,
		NextProtos:         []string{"quic-echo-example"},
	}
	config := &quic.Config{
		// HandshakeIdleTimeout:           100000000000,
		// MaxIdleTimeout:                 300000000000,
		InitialStreamReceiveWindow:     30 * (1 << 10),
		MaxStreamReceiveWindow:         30 * (1 << 10),
		InitialConnectionReceiveWindow: 30 * (1 << 10) * 2,
		MaxConnectionReceiveWindow:     30 * (1 << 10) * 2,
		// InitialStreamReceiveWindow:     3000,
		// MaxStreamReceiveWindow:         3000,
		// InitialConnectionReceiveWindow: 3000 * 7,
		// MaxConnectionReceiveWindow:     3000 * 7,
	}
	OutPutConn, err := quic.DialAddr(context.Background(), addr, tlsConf, config)
	if err != nil {
		panic(fmt.Errorf("[PEPSender] OpenNewQUICConn quic.DialAddr: %w", err))
	}
	OutPutstream, err := OutPutConn.OpenStreamSync(context.Background())
	if err != nil {
		panic(fmt.Errorf("[PEPSender] OpenNewQUICConn OpenStreamSync: %w", err))
	}

	go HandleQUICInPutStreams(PEPstream, OutPutstream)
	go HandleQUICOutPutStreams(PEPstream, OutPutstream)

}
