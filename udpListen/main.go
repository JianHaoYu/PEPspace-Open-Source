package main

import (
	"PEPSpace/udpListen/pacer"
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
	"syscall"
	"time"
	"unsafe"
)

type ReceivedUDPPacket struct {
	originalSrc *net.UDPAddr
	originalDst *net.UDPAddr
	data        []byte
}

func main() {
	// 监听的本地地址
	fmt.Println("Starting GoLang TProxy example")
	localAddr, err := net.ResolveUDPAddr("udp", ":8080")
	if err != nil {
		fmt.Println("解析本地地址出错:", err)
		return
	}

	// 创建UDP监听套接字
	listener, err := net.ListenUDP("udp", localAddr)
	if err != nil {
		fmt.Println("创建UDP监听出错:", err)
		return
	}
	defer listener.Close()
	fmt.Printf("listener %v To %v \n", listener.LocalAddr(), listener.RemoteAddr())

	fileDescriptorSource, err := listener.File()
	if err != nil {
		fmt.Println("Error fileDescriptorSource, err := listener.File()")
		return
	}
	fileDescriptor := int(fileDescriptorSource.Fd())
	err = syscall.SetsockoptInt(fileDescriptor, syscall.SOL_IP, syscall.IP_TRANSPARENT, 1)
	if err != nil {
		fmt.Println("Error syscall.SetsockoptInt(fileDescriptor, syscall.SOL_IP, syscall.IP_TRANSPARENT, 1)")
		return
	}
	err = syscall.SetsockoptInt(fileDescriptor, syscall.SOL_IP, syscall.IP_RECVORIGDSTADDR, 1)
	if err != nil {
		fmt.Println("Error syscall.SetsockoptInt(fileDescriptor, syscall.SOL_IP, syscall.IP_RECVORIGDSTADDR, 1)")
		return
	}
	fmt.Printf("Binding UDP TProxy listener to %s, Successfully \n", listener.LocalAddr().String())

	UDPPacketChan := make(chan *ReceivedUDPPacket, 200000)
	pacer := pacer.NewPacer()
	packetCount := 0
	go handleUDPChan(UDPPacketChan, pacer)
	buffer := make([]byte, 2048)
	oob := make([]byte, 1024)
	for {
		// 接收UDP数据包
		n, oobn, _, originalSrc, err := listener.ReadMsgUDP(buffer, oob)
		if err != nil {
			fmt.Println("Error listener.ReadMsgUDP(buffer, oob)")
			return
		}
		msgs, err := syscall.ParseSocketControlMessage(oob[:oobn])
		if err != nil {
			fmt.Println("Error syscall.ParseSocketControlMessage(oob[:oobn])")
			return
		}
		var originalDst *net.UDPAddr

		for _, msg := range msgs {
			if msg.Header.Level == syscall.SOL_IP && msg.Header.Type == syscall.IP_RECVORIGDSTADDR {
				originalDstRaw := &syscall.RawSockaddrInet4{}
				if err = binary.Read(bytes.NewReader(msg.Data), binary.LittleEndian, originalDstRaw); err != nil {
					fmt.Println("Error binary.Read(bytes.NewReader(msg.Data), binary.LittleEndian, originalDstRaw)")
					return
				}

				switch originalDstRaw.Family {
				case syscall.AF_INET:
					pp := (*syscall.RawSockaddrInet4)(unsafe.Pointer(originalDstRaw))
					p := (*[2]byte)(unsafe.Pointer(&pp.Port))
					originalDst = &net.UDPAddr{
						IP:   net.IPv4(pp.Addr[0], pp.Addr[1], pp.Addr[2], pp.Addr[3]),
						Port: int(p[0])<<8 + int(p[1]),
					}

				case syscall.AF_INET6:
					pp := (*syscall.RawSockaddrInet6)(unsafe.Pointer(originalDstRaw))
					p := (*[2]byte)(unsafe.Pointer(&pp.Port))
					originalDst = &net.UDPAddr{
						IP:   net.IP(pp.Addr[:]),
						Port: int(p[0])<<8 + int(p[1]),
						Zone: strconv.Itoa(int(pp.Scope_id)),
					}

				default:
					fmt.Println("Error for _, msg := range msgs { default")
					return
				}
			}
		}
		if originalDst == nil {
			fmt.Println("Error originalDst == nil")
			return
		}
		packetCount++
		fmt.Printf("Received data from %v To %v Length %d Total number of packets:% d \n", originalSrc, originalDst, n, packetCount)
		// handleUDPConn(buffer[:n], originalSrc, originalDst)
		data := make([]byte, n)
		copy(data, buffer[:n])
		packet := &ReceivedUDPPacket{
			originalDst: originalDst,
			originalSrc: originalSrc,
			data:        data,
		}
		UDPPacketChan <- packet
	}
}

func handleUDPChan(UDPPacketChan chan *ReceivedUDPPacket, pacer *pacer.Pacer) {

	Pacingdeadline := time.Time{}
	startTime := time.Now()
	SendByets := 0
	SendPacketCount := 0
	DisruptionEventTime := startTime.Add(18 * time.Second)
	NotDisruptionEvent := true

	var UDPPacket *ReceivedUDPPacket

	for {
		now := time.Now()
		//检查是否中断
		if now.After(DisruptionEventTime) && NotDisruptionEvent {
			NetwrokDisruptionEvent(12 * time.Second)
			NotDisruptionEvent = false
			startTime = time.Now()
			continue
		}

		if now.Before(Pacingdeadline) {
			continue
		}

		if UDPPacket == nil {
			fmt.Printf("len(UDPPacketChan) %d \n", len(UDPPacketChan))
			UDPPacket = <-UDPPacketChan
		}
		originalDst := UDPPacket.originalDst
		originalSrc := UDPPacket.originalSrc
		data := UDPPacket.data

		dataLength := int64(len(data))
		if pacer.Budget(now) < dataLength {
			Pacingdeadline = pacer.TimeUntilSend(dataLength)
			continue
		}
		handleUDPConn(data, originalSrc, originalDst)
		pacer.SentPacket(now, dataLength)
		UDPPacket = nil

		duration := time.Since(startTime).Microseconds()
		SendPacketCount++
		SendByets += int(dataLength)
		throughput := float64(SendByets) * 8 / (float64(duration))
		fmt.Printf("Send rate: %.2f Mbps from %v to %v SendPacketCount: %d AtTime: %f \n", throughput, originalSrc, originalDst, SendPacketCount, float64(time.Now().UnixNano()/1e3)/1e6)
	}
}

func NetwrokDisruptionEvent(Disruptioninterval time.Duration) {
	fmt.Printf("Network Disrupt for %v \n", Disruptioninterval)
	time.Sleep(Disruptioninterval)
}

func handleUDPConn(data []byte, srcAddr, dstAddr *net.UDPAddr) {
	// log.Printf("Accepting UDP connection from %s with destination of %s", srcAddr, dstAddr)

	remoteConn, err := DialUDP("udp", srcAddr, dstAddr)
	if err != nil {
		log.Printf("Failed to connect to original UDP destination [%s]: %s", dstAddr.String(), err)
		return
	}
	defer remoteConn.Close()

	bytesWritten, err := remoteConn.Write(data)
	if err != nil {
		log.Printf("Encountered error while writing to remote [%s]: %s", remoteConn.RemoteAddr(), err)
		return
	} else if bytesWritten < len(data) {
		log.Printf("Not all bytes [%d < %d] in buffer written to remote [%s]", bytesWritten, len(data), remoteConn.RemoteAddr())
		return
	}

}

// DialUDP connects to the remote address raddr on the network net,
// which must be "udp", "udp4", or "udp6".  If laddr is not nil, it is
// used as the local address for the connection.
func DialUDP(network string, laddr *net.UDPAddr, raddr *net.UDPAddr) (*net.UDPConn, error) {
	remoteSocketAddress, err := udpAddrToSocketAddr(raddr)
	if err != nil {
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("build destination socket address: %s", err)}
	}

	localSocketAddress, err := udpAddrToSocketAddr(laddr)
	if err != nil {
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("build local socket address: %s", err)}
	}

	fileDescriptor, err := syscall.Socket(udpAddrFamily(network, laddr, raddr), syscall.SOCK_DGRAM, 0)
	if err != nil {
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("socket open: %s", err)}
	}

	// if err = syscall.SetsockoptInt(fileDescriptor, syscall.SOL_SOCKET, syscall.SO_REUSEADDR, 1); err != nil {
	// 	syscall.Close(fileDescriptor)
	// 	return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("set socket option: SO_REUSEADDR: %s", err)}
	// }

	if err = syscall.SetsockoptInt(fileDescriptor, syscall.SOL_IP, syscall.IP_TRANSPARENT, 1); err != nil {
		syscall.Close(fileDescriptor)
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("set socket option: IP_TRANSPARENT: %s", err)}
	}

	if err = syscall.Bind(fileDescriptor, localSocketAddress); err != nil {
		syscall.Close(fileDescriptor)
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("socket bind: %s", err)}
	}

	if err = syscall.Connect(fileDescriptor, remoteSocketAddress); err != nil {
		syscall.Close(fileDescriptor)
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("socket connect: %s", err)}
	}

	fdFile := os.NewFile(uintptr(fileDescriptor), fmt.Sprintf("net-udp-dial-%s", raddr.String()))
	defer fdFile.Close()

	remoteConn, err := net.FileConn(fdFile)
	if err != nil {
		syscall.Close(fileDescriptor)
		return nil, &net.OpError{Op: "dial", Err: fmt.Errorf("convert file descriptor to connection: %s", err)}
	}

	return remoteConn.(*net.UDPConn), nil
}

// udpAddToSockerAddr will convert a UDPAddr
// into a Sockaddr that may be used when
// connecting and binding sockets
func udpAddrToSocketAddr(addr *net.UDPAddr) (syscall.Sockaddr, error) {
	switch {
	case addr.IP.To4() != nil:
		ip := [4]byte{}
		copy(ip[:], addr.IP.To4())

		return &syscall.SockaddrInet4{Addr: ip, Port: addr.Port}, nil

	default:
		ip := [16]byte{}
		copy(ip[:], addr.IP.To16())

		zoneID, err := strconv.ParseUint(addr.Zone, 10, 32)
		if err != nil {
			return nil, err
		}

		return &syscall.SockaddrInet6{Addr: ip, Port: addr.Port, ZoneId: uint32(zoneID)}, nil
	}
}

// udpAddrFamily will attempt to work
// out the address family based on the
// network and UDP addresses
func udpAddrFamily(net string, laddr, raddr *net.UDPAddr) int {
	switch net[len(net)-1] {
	case '4':
		return syscall.AF_INET
	case '6':
		return syscall.AF_INET6
	}

	if (laddr == nil || laddr.IP.To4() != nil) &&
		(raddr == nil || laddr.IP.To4() != nil) {
		return syscall.AF_INET
	}
	return syscall.AF_INET6
}
