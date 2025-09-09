package main

import (
	"PEPSpace/proxy"
	"flag"
	"fmt"
)

var PEPlocalAddr = "10.0.0.1:4242"
var PEPremoteAddr = "10.0.0.2:4242"
var PEPLoaclTCPAddr = "10.0.0.1:4243"
var PEPLoaclQUICAddr = "10.0.0.1:4244"

func main() {
	PEPLocalAddr := flag.String("localaddr", PEPlocalAddr, "LocalAddr:Port Address")
	PEPRemoteAddr := flag.String("remoteaddr", PEPremoteAddr, "RemoteAddr:Port Address")
	PEPLoaclTCPAddr := flag.String("TCPaddr", PEPLoaclTCPAddr, "RemoteAddr:Port Address")
	PEPLoaclQUICAddr := flag.String("QUICaddr", PEPLoaclQUICAddr, "RemoteAddr:Port Address")
	perspective := flag.Int("perspective", 0, " Perspective determines if we're acting as a server or a client. 0 for Client 1 for Server")
	flowControlSize := flag.Uint64("fcs", 40, "flowControlSize")
	flag.Parse()

	fmt.Printf("[PEPMain] InputParameter PEPLocalAddr: %s PEPRemoteAddr: %s PEPLoaclTCPAddr: %s PEPLoaclQUICAddr: %s perspective: %d FlowControlSize %d \n\n",
		*PEPLocalAddr, *PEPRemoteAddr, *PEPLoaclTCPAddr, *PEPLoaclQUICAddr, *perspective, *flowControlSize)

	proxy.PEP(*PEPLocalAddr, *PEPRemoteAddr, *PEPLoaclTCPAddr, *PEPLoaclQUICAddr, *perspective, *flowControlSize)

}
