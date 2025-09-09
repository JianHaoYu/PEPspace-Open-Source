package main

import (
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
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/example/XADSExample/xads"
)

const addr = "10.0.0.1:4242"
const defaultXADSAddr = "10.0.0.1:4243"
const testdatasize = 35
const hashLength = 16

// We start a server echoing data on the first stream the client opens,
// then connect with a client, send the message, and wait for its receipt.
func main() {
	serveraddr := flag.String("ip", addr, "IP:Port Address")
	XADSaddr := flag.String("xadsaddr", defaultXADSAddr, "IP:Port Address")
	sendfilesize := flag.Int("testsize", testdatasize, "dataforsend")
	flag.Parse()
	exporterchan := make(chan []byte, 10)
	go XADSServer(*XADSaddr, exporterchan)
	err := QUICServer(*serveraddr, *sendfilesize, exporterchan)
	if err != nil {
		panic(err)
	}
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
		panic(fmt.Errorf("[APP-Server-XADS] XADS quic.ListenAddr: %w", err))
	}
	defer listener.Close()
	for {
		conn, err := listener.Accept(context.Background())
		if err != nil {
			panic(fmt.Errorf("[APP-Server-XADS] XADS listener.Accept: %w", err))
		}
		fmt.Printf("[APP-Server-XADS] XADS GET Connection from %s, Export security Key. AtTime %f \n", conn.RemoteAddr().String(), float64(time.Now().UnixNano()/1e3)/1e6)
		exporter, err := xads.ExportKeyingMaterial(conn, "EXPORTER-security", nil, 32)
		if err != nil {
			panic(fmt.Errorf("[APP-Server-XADS] xads.ExportKeyingMaterial: %w", err))
		}
		exporterchan <- exporter
	}
}

func QUICServer(serveraddr string, sendfilesize int, exporterchan chan []byte) error {
	sendfilebytesList := PrepareTestDate(sendfilesize)
	config := &quic.Config{
		HandshakeIdleTimeout:    100000000000,
		MaxIdleTimeout:          100000000000,
		DisablePathMTUDiscovery: true,
		EnableDatagrams:         true,
	}
	fmt.Printf("[APP-Server] Start Listening in %s \n", serveraddr)
	listener, err := quic.ListenAddr(serveraddr, generateTLSConfig(), config)
	if err != nil {
		return err
	}
	defer listener.Close()
	for {
		conn, err := listener.Accept(context.Background())
		if err != nil {
			return err
		}
		fmt.Printf("[APP-Server] GET Connection from %s \n", conn.RemoteAddr().String())
		go handleconnections(conn, sendfilebytesList, exporterchan)
	}
}

func handleconnections(conn quic.Connection, data []byte, exporterchan chan []byte) {
	stream, err := conn.AcceptStream(context.Background())
	if err != nil {
		return
	}
	receivedbytes := make([]byte, hashLength)
	_, err = io.ReadFull(stream, receivedbytes)
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
	plainBuf.Write(data)
	if err := xads.EncryptStream(&plainBuf, stream, xadsMaster); err != nil {
		log.Fatalf("[APP-Server] encrypt failed: %v", err)
	}
	CalculateMD5value(data, "[APP-Server] Send Over")
	stream.Close()

	time.Sleep(2000 * time.Second)
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

func PrepareTestDate(filesize int) []byte {
	bytes := make([]byte, filesize*1e6)
	if _, err := rand.Read(bytes); err != nil {
		log.Fatalf("data gen failed: %v", err)
	}
	CalculateMD5value(bytes, "Server Generates Test Data")
	return bytes
}

func CalculateMD5value(filebytes []byte, log string) []byte {
	hash := md5.New()
	// 将字符串写入哈希对象
	hash.Write([]byte(filebytes))
	// 获取哈希值的字节切片
	sum := hash.Sum(nil)
	// 将字节切片转换为十六进制字符串
	md5String := hex.EncodeToString(sum)
	if log != "" {
		fmt.Printf(log+"Calculate MD5 value as %d Bytes MD5 (hex): %s\n", len(filebytes), md5String)
	}
	return sum
}
