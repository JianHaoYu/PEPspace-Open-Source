package proxy

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"math/big"

	quicspace "github.com/quic-go/quic-go-space"
)

func PEP(PEPLocalAddr string, PEPRemoteAddr string, PEPLoaclTCPAddr string, PEPLoaclQUICAddr string, perspective int, flowControlSize uint64) {
	spaceconfig := &quicspace.Config{
		HandshakeIdleTimeout:           100000000000,
		MaxIdleTimeout:                 100000000000,
		DisablePathMTUDiscovery:        true,
		InitialStreamReceiveWindow:     flowControlSize * (1 << 20),
		MaxStreamReceiveWindow:         flowControlSize * (1 << 20),
		InitialConnectionReceiveWindow: flowControlSize * (1 << 20) * 2,
		MaxConnectionReceiveWindow:     flowControlSize * (1 << 20) * 2,
		InitialPacketSize:              1436,
	}
	fmt.Printf("[PEP] Start QUIC-Space Listening in %s Remoteadress %s FlowControlSize %d \n", PEPLocalAddr, PEPRemoteAddr, flowControlSize)
	SpaceListener, err := quicspace.ListenAddrEarly(PEPLocalAddr, generateTLSConfig(), spaceconfig)
	if err != nil {
		panic(fmt.Errorf("[PEP] quic.ListenAddrEarly(ip, generateTLSConfig(), config): %w", err))
	}
	defer SpaceListener.Close()
	var PEPSpaceConn quicspace.Connection
	if perspective == 0 { // 客户端PEP，向对端PEP建立连接
		tlsConf := &tls.Config{
			InsecureSkipVerify: true,
			NextProtos:         []string{"quic-echo-example"},
		}
		fmt.Printf("[PEP] QUIC-Space Connect to %s \n", PEPRemoteAddr)

		PEPSpaceConn, err = quicspace.DialAddr(context.Background(), PEPRemoteAddr, tlsConf, spaceconfig)
		if err != nil {
			panic(fmt.Errorf("[PEP] quic.DialAddr(context.Background(), ip, tlsConf, config): %w", err))
		}
		fmt.Printf("[PEP] QUIC-Space Connect to %s Successfuly.\n", PEPRemoteAddr)
	} else if perspective == 1 { // 服务端PEP，等待对端PEP建立连接
		fmt.Println("[PEP] QUIC-Space Wating for Connection")
		PEPSpaceConn, err = SpaceListener.Accept(context.Background())
		if err != nil {
			panic(fmt.Errorf("[PEP] listener.Accept(context.Background()): %w", err))
		}
		fmt.Printf("[PEP] QUIC-Space Remoteadress %s Connected Successfuly.\n", PEPRemoteAddr)
	}

	go HandlePEPReceiverConnection(PEPSpaceConn)

	HandlePEPSenderConnection(PEPSpaceConn, PEPLoaclTCPAddr, PEPLoaclQUICAddr)
}

func generateTLSConfig() *tls.Config {
	key, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		panic(err)
	}
	template := x509.Certificate{SerialNumber: big.NewInt(1)}
	certDER, err := x509.CreateCertificate(rand.Reader, &template, &template, &key.PublicKey, key)
	if err != nil {
		panic(err)
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(key)})
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})

	tlsCert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		panic(err)
	}
	return &tls.Config{
		Certificates: []tls.Certificate{tlsCert},
		NextProtos:   []string{"quic-echo-example"},
	}
}
