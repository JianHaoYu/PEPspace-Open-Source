package address

import (
	"crypto/rand"
	"fmt"
	"log"
	"testing"
)

func TestNewSCEncoder(t *testing.T) {
	Bytes := AppendTargetAddress("10.0.0.30:4242", "tcp")

	fmt.Println(Length())
	fmt.Println(len(Bytes))
	fmt.Println(ParseTargetAddress(Bytes))

	filesize := 1
	bytes := make([]byte, filesize*1e6)
	if _, err := rand.Read(bytes); err != nil {
		log.Fatalf("data gen failed: %v", err)
	}
	buf := calculateMD5value(bytes, "1")
	fmt.Println(len(buf))
}

func TestNewParseTargetAddress(t *testing.T) {
	Bytes := AppendTargetAddress("10.0.0.1:4242", "tcp")
	fmt.Println(Length())
	fmt.Println(len(Bytes))
	TargetAddress, conntype := ParseTargetAddress(Bytes)
	fmt.Println(TargetAddress)
	fmt.Println(conntype, len(conntype))
	fmt.Println(conntype[0])
	fmt.Println(conntype[1])
	fmt.Println(conntype[2])
	fmt.Println(conntype[3])
	if conntype[:] == "tcp\x00" {
		fmt.Println("Check2")
	}
}
