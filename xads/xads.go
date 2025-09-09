package xads

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"io"
	"time"

	"github.com/quic-go/quic-go"
	"golang.org/x/crypto/hkdf"
)

// deriveSecret 使用 TLS 1.3 的 HKDF-Expand-Label 语义派生密钥
func DeriveSecret(secret []byte, label string, length int) ([]byte, error) {
	hkdfLabel := make([]byte, 2+1+len("tls13 ")+len(label)+1)
	// 填充长度
	hkdfLabel[0] = byte(length >> 8)
	hkdfLabel[1] = byte(length)
	// 填充标签
	hkdfLabel[2] = byte(len("tls13 ") + len(label))
	copy(hkdfLabel[3:], "tls13 ")
	copy(hkdfLabel[3+len("tls13 "):], label)
	// context 长度 = 0
	hkdfLabel[len(hkdfLabel)-1] = 0

	hk := hkdf.New(sha256.New, secret, nil, hkdfLabel)
	derived := make([]byte, length)
	if _, err := io.ReadFull(hk, derived); err != nil {
		return nil, fmt.Errorf("_, err := io.ReadFull(hk, derived);: %w", err)
	}
	return derived, nil
}

// NewAESGCM 根据给定 key 创建 AES-GCM AEAD 实例
func NewAESGCM(key []byte) (cipher.AEAD, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("block, err := aes.NewCipher(key): %w", err)
	}
	return cipher.NewGCM(block)
}

// exportKeyingMaterial demonstrates how QUIC obtains keying material from TLS
func ExportKeyingMaterial(connection quic.Connection, label string, context []byte, length int) ([]byte, error) {
	// Under the hood, quic-go uses the TLS 1.3 exporter interface
	cs := connection.ConnectionState()
	material, err := cs.TLS.ExportKeyingMaterial(label, context, length)
	if err != nil {
		return nil, fmt.Errorf("material, err := cs.TLS.ExportKeyingMaterial(label, context, length): %w", err)
	}
	return material, nil
}

func DecryptStream(src io.Reader, dst io.Writer, key []byte) error {
	block, err := aes.NewCipher(key)
	if err != nil {
		return err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return err
	}
	nonceSize := aead.NonceSize()

	// helper to read exactly len bytes or return error
	readFull := func(r io.Reader, buf []byte) error {
		_, err := io.ReadFull(r, buf)
		return err
	}
	SumDecryptBytes := 0
	for {
		hdr := make([]byte, 2+nonceSize)
		// read 2-byte length + nonce
		if err := readFull(src, hdr); err != nil {
			if err == io.EOF || err == io.ErrUnexpectedEOF {
				return nil
			}
			return fmt.Errorf("[ApplicationEncryption] read header: %w", err)
		}
		// parse length
		clen := int(binary.BigEndian.Uint16(hdr[:2]))
		nonce := hdr[2:]

		// read ciphertext+tag
		ct := make([]byte, clen)
		if err := readFull(src, ct); err != nil {
			return fmt.Errorf("[ApplicationEncryption] read ciphertext: %w", err)
		}

		plaintext, err := aead.Open(nil, nonce, ct, nil)
		if err != nil {
			return fmt.Errorf("[ApplicationEncryption] decrypt chunk: %w", err)
		}
		n, err := dst.Write(plaintext)
		if err != nil {
			return fmt.Errorf("[ApplicationEncryption] write plaintext: %w", err)
		}
		SumDecryptBytes += n
		fmt.Printf("[DecryptStream] bytesRead %d AtTime: %f \n", SumDecryptBytes, float64(time.Now().UnixNano()/1e3)/1e6)

	}
}

func EncryptStream(src io.Reader, dst io.Writer, key []byte) error {
	block, err := aes.NewCipher(key)
	if err != nil {
		return err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return err
	}
	noncesize := aead.NonceSize()
	buf := make([]byte, 1024*10)
	// write: [nonceLen][ciphertextLen][nonce|ciphertext]
	// 2 bytes for ciphertext length, adjust if your chunks can exceed 65535
	header := make([]byte, 2+noncesize)
	SumEncryptBytes := 0
	for {
		n, err := src.Read(buf)
		if err != nil && err != io.EOF {
			return fmt.Errorf("[ApplicationEncryption] read src: %w", err)
		}
		if n == 0 {
			break
		}
		nonce := header[2:]
		// generate a fresh nonce for each chunk
		if _, err := rand.Read(nonce); err != nil {
			return fmt.Errorf("[ApplicationEncryption] rand.Read nonce: %w", err)
		}
		// seal attaches authentication tag automatically
		ciphertext := aead.Seal(nil, nonce, buf[:n], nil)

		// big-endian uint16 length
		binary.BigEndian.PutUint16(header[:2], uint16(len(ciphertext)))
		EncryptionSegment := append(header, ciphertext...)
		realwrite, err := dst.Write(EncryptionSegment)
		if err != nil {
			return fmt.Errorf("[ApplicationEncryption] dst.Write(EncryptionSegment): %w", err)
		}
		SumEncryptBytes += n
		fmt.Printf("[EncryptStream] bytesWrite %d AtTime: %f RealWrite: %d \n", SumEncryptBytes, float64(time.Now().UnixNano()/1e3)/1e6, realwrite)
		if err == io.EOF {
			break
		}
	}
	return nil
}
