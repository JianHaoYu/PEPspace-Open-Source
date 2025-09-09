package address

import (
	"crypto/md5"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"fmt"
)

func ParseTargetAddress(data []byte) (string, string) {
	Length := int(binary.BigEndian.Uint16(data[:2]))
	receivedHash := data[2 : sha256.Size+2]
	TargetAddressBytes := data[sha256.Size+2 : sha256.Size+2+Length]
	typebytes := data[sha256.Size+2+16:]
	calculatedHash := sha256.Sum256(TargetAddressBytes)
	valid := true
	for i := 0; i < sha256.Size; i++ {
		if receivedHash[i] != calculatedHash[i] {
			valid = false
			break
		}
	}

	if valid {
		return string(TargetAddressBytes), string(typebytes)
	} else {
		panic(fmt.Errorf("[PEP] ParseTarget"))
	}
}

func Length() int {
	return 2 + sha256.Size + 16 + 4
}

func AppendTargetAddress(addr string, connType string) []byte {
	Targetbytes := make([]byte, 2+sha256.Size+16+4)
	addrbytes := []byte(addr)
	typebytes := []byte(connType)

	binary.BigEndian.PutUint16(Targetbytes[:2], uint16(len(addrbytes)))
	hash := sha256.Sum256(addrbytes)
	copy(Targetbytes[2:2+sha256.Size], hash[:])
	copy(Targetbytes[2+sha256.Size:], addrbytes)
	copy(Targetbytes[2+sha256.Size+16:], typebytes)
	return Targetbytes
}

func calculateMD5value(filebytes []byte, log string) []byte {
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
