package main

import (
	"context"
	"crypto/md5"
	"crypto/tls"
	"encoding/hex"
	"flag"
	"fmt"
	"time"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/example/XADSExample/xads"
)

const ServerAddr = "10.0.0.1:4242"
const XADSaddr = "10.0.0.1:4243"

// We start a server echoing data on the first stream the client opens,
// then connect with a client, send the message, and wait for its receipt.
func main() {
	ServerAddr := flag.String("serveraddr", ServerAddr, "IP:Port Address")
	XADSaddr := flag.String("xadsaddr", XADSaddr, "IP:Port Address")
	flowControlSize := flag.Uint64("fcs", 40, "dataforsend")
	flag.Parse()
	exporterchan := make(chan []byte)
	go GenerateXADSKey(*XADSaddr, *flowControlSize, exporterchan)

	err := clientToPEP(*ServerAddr, exporterchan)
	if err != nil {
		panic(err)
	}
	time.Sleep(2 * time.Second)

}

func GenerateXADSKey(ip string, flowControlSize uint64, exporterchan chan []byte) {
	tlsConf := &tls.Config{
		InsecureSkipVerify: true,
		NextProtos:         []string{"quic-echo-example"},
	}
	config := &quic.Config{
		HandshakeIdleTimeout:    100000000000,
		MaxIdleTimeout:          100000000000,
		DisablePathMTUDiscovery: true,
		EnableDatagrams:         true,
	}
	fmt.Printf("[APP-Client-XADS] Start connecting to in %s AtTime %f \n", ip, float64(time.Now().UnixNano()/1e3)/1e6)
	XADSconn, err := quic.DialAddr(context.Background(), ip, tlsConf, config)
	if err != nil {
		panic(fmt.Errorf("[APP-Client-XADS] XADS quic.DialAddr(): %w", err))
	}
	fmt.Printf("[APP-Client-XADS] XADS Connection %s successful. Export security Key. AtTime %f \n", XADSconn.RemoteAddr().String(), float64(time.Now().UnixNano()/1e3)/1e6)
	exporter, err := xads.ExportKeyingMaterial(XADSconn, "EXPORTER-security", nil, 32)
	if err != nil {
		panic(fmt.Errorf("[APP-Client-XADS] XADS exporter, err := xads.ExportKeyingMaterial(): %w", err))
	}
	exporterchan <- exporter
	XADSconn.CloseWithError(0, "")
}

func clientToPEP(ServerAddr string, exporterchan chan []byte) error {
	tlsConf := &tls.Config{
		InsecureSkipVerify: true,
		NextProtos:         []string{"quic-echo-example"},
	}
	config := &quic.Config{
		HandshakeIdleTimeout:    100000000000,
		MaxIdleTimeout:          100000000000,
		DisablePathMTUDiscovery: true,
		EnableDatagrams:         true,
		InitialPacketSize:       1436,
	}
	fmt.Printf("[APP-Client-PEP] Start connecting to in %s \n", ServerAddr)
	conn, err := quic.DialAddr(context.Background(), ServerAddr, tlsConf, config)
	if err != nil {
		return fmt.Errorf("[APP-Client-PEP] quic.DialAddr(): %w", err)
	}
	defer conn.CloseWithError(0, "")
	fmt.Printf("[APP-Client-PEP] Connection successful.\n")
	// stream, err := conn.OpenStreamSync(context.Background())
	// if err != nil {
	// 	return fmt.Errorf("[APP-Client-PEP] conn.OpenStreamSync(): %w", err)
	// }
	// defer stream.Close()
	// fmt.Printf("[APP-Client-PEP] Open Stream Successful...\n")
	// stream.Write(address.AppendTargetAddress(ServerAddr, "quic"))

	// exporter := <-exporterchan
	// if len(exporter) != 32 {
	// 	return fmt.Errorf("[APP-Client-PEP] exporter Length %d ", len(exporter))
	// }
	// CalculateMD5value(exporter, "[APP-Client-PEP] Gets the XADS key \n")
	// // 派生 XADS 主密钥
	// xadsMaster, err := xads.DeriveSecret(exporter, "xads master", 32)
	// if err != nil {
	// 	log.Fatal(err)
	// }
	// stream.Write(CalculateMD5value(exporter, ""))

	// var inputBuf bytes.Buffer
	// if err := xads.DecryptStream(stream, &inputBuf, xadsMaster); err != nil {
	// 	log.Fatalf("decrypt failed: %v", err)
	// }
	// CalculateMD5value(inputBuf.Bytes(), "[APP-Client-PEP] Receive and decode ")
	time.Sleep(10 * time.Second)
	return nil
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
