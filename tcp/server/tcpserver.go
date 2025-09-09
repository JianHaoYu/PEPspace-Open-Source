package main

import (
	"PEPSpace/xads"
	"bytes"
	"context"
	"crypto/md5"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"encoding/pem"
	"flag"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
	"time"

	"github.com/quic-go/quic-go"
)

const addr = "10.0.0.1:4242"
const defaultXADSAddr = "10.0.0.1:4243"
const testdatasize = 35
const hashLength = 16

func main() {
	serveraddr := flag.String("serveraddr", addr, "IP:Port Address")
	XADSaddr := flag.String("xadsaddr", defaultXADSAddr, "IP:Port Address")
	sendfilesize := flag.Int("testsize", testdatasize, "dataforsend")
	flag.Parse()
	exporterchan := make(chan []byte, 10)

	go XADSServer(*XADSaddr, exporterchan)
	TCPServer(*serveraddr, *sendfilesize, exporterchan)
}

func XADSServer(XADSaddr string, exporterchan chan []byte) {
	config := &quic.Config{
		HandshakeIdleTimeout:    100000000000,
		MaxIdleTimeout:          100000000000,
		DisablePathMTUDiscovery: true,
		EnableDatagrams:         true,
		InitialPacketSize:       1436,
	}
	fmt.Printf("[APP-Server-XADS] Start Listening in %s \n", XADSaddr)
	listener, err := quic.ListenAddrEarly(XADSaddr, generateTLSConfig(), config)
	if err != nil {
		panic(fmt.Errorf("[APP-Server-XADS] XADS quic.ListenAddrEarly: %w", err))
	}
	defer listener.Close()
	for {
		conn, err := listener.Accept(context.Background())
		if err != nil {
			panic(fmt.Errorf("[APP-Server-XADS] XADS listener.Accept: %w", err))
		}
		fmt.Printf("[APP-Server-XADS] XADS GET Connection from %s, Export security Key. \n", conn.RemoteAddr().String())
		exporter, err := xads.ExportKeyingMaterial(conn, "EXPORTER-security", nil, 32)
		if err != nil {
			panic(fmt.Errorf("[APP-Server-XADS] xads.ExportKeyingMaterial: %w", err))
		}
		exporterchan <- exporter
	}
}

func TCPServer(serveraddr string, sendfilesize int, exporterchan chan []byte) {
	sendfilebytesList := PrepareTestData(sendfilesize)

	listener, err := net.Listen("tcp", serveraddr)
	if err != nil {
		log.Fatalf("Listening error: %v", err)
	}
	defer listener.Close()
	fmt.Println("The server has started and is waiting to connect ..")
	conn, err := listener.Accept()
	if err != nil {
		log.Fatalf("Accept failed: %v", err)
	}
	fmt.Println("Connection from:", conn.RemoteAddr().String())
	conn.SetDeadline(time.Time{})

	receivedbytes := make([]byte, hashLength)
	_, err = io.ReadFull(conn, receivedbytes)
	if err != nil {
		panic(fmt.Errorf("[PEPReceiver] Read Address error: %w", err))
	}
	fmt.Printf("[APP-Server] GET KEY Hash %s \n", hex.EncodeToString(receivedbytes))
	exporter := <-exporterchan
	xadsMaster, err := xads.DeriveSecret(exporter, "xads master", 32) // 派生 XADS 主密钥
	if err != nil {
		log.Fatal(err)
	}
	CalculateMD5value(exporter, "[APP-Server] Gets the XADS key \n")

	var plainBuf bytes.Buffer
	plainBuf.Write(sendfilebytesList)
	if err := xads.EncryptStream(&plainBuf, conn, xadsMaster); err != nil {
		log.Fatalf("[APP-Server] encrypt failed: %v", err)
	}
	CalculateMD5value(sendfilebytesList, "[APP-Server] Send Over")
	conn.Close()

	time.Sleep(2000 * time.Second)

}

func PrepareTestData(sizeMB int) []byte {
	bytes := make([]byte, sizeMB*1e6)
	if _, err := rand.Read(bytes); err != nil {
		log.Fatalf("生成数据失败: %v", err)
	}
	CalculateMD5value(bytes, "服务器生成测试数据")
	return bytes
}

func CalculateMD5value(data []byte, desc string) []byte {
	hash := md5.Sum(data)
	md5Str := hex.EncodeToString(hash[:])
	if desc != "" {
		fmt.Printf("%s Calculate MD5 value as %d Bytes MD5 (hex): %s\n", desc, len(data), md5Str)
	}
	return hash[:]
}

// Setup a bare-bones TLS config for the server
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
