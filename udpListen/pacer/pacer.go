package pacer

import (
	"time"
)

const maxDatagramSize = 1500
const maxBurstSizePackets = 1
const MaxByteCount = int64(1<<62 - 1)
const MinPacingDelay = time.Millisecond
const TimerGranularity = time.Millisecond
const FixedBandwidth = 1200000 //  字节每秒(Byte/Second)

// The Pacer implements a token bucket pacing algorithm.
type Pacer struct {
	budgetAtLastSent  int64
	lastSentTime      time.Time
	adjustedBandwidth uint64 // in bytes/s
}

func NewPacer() *Pacer {
	p := &Pacer{
		adjustedBandwidth: FixedBandwidth, // Bandwidth is in bits/s. We need the value in bytes/s.
	}
	p.budgetAtLastSent = p.maxBurstSize()
	return p
}

func (p *Pacer) SentPacket(sendTime time.Time, size int64) {
	budget := p.Budget(sendTime)
	if size >= budget {
		p.budgetAtLastSent = 0
	} else {
		p.budgetAtLastSent = budget - size
	}
	p.lastSentTime = sendTime
}

func (p *Pacer) Budget(now time.Time) int64 {
	if p.lastSentTime.IsZero() {
		return p.maxBurstSize()
	}
	budget := p.budgetAtLastSent + (int64(p.adjustedBandwidth)*int64(now.Sub(p.lastSentTime).Nanoseconds()))/1e9
	if budget < 0 { // protect against overflows
		budget = MaxByteCount
	}
	return min(p.maxBurstSize(), budget)
}

func (p *Pacer) maxBurstSize() int64 {
	return max(
		int64(uint64((MinPacingDelay+TimerGranularity).Nanoseconds())*p.adjustedBandwidth)/1e9,
		maxBurstSizePackets*maxDatagramSize,
	)
}

// TimeUntilSend returns when the next packet should be sent.
// It returns the zero value of time.Time if a packet can be sent immediately.
func (p *Pacer) TimeUntilSend(packetsize int64) time.Time {
	if p.budgetAtLastSent >= packetsize {
		return time.Time{}
	}
	diff := 1e9 * uint64(packetsize-p.budgetAtLastSent)
	bw := p.adjustedBandwidth
	// We might need to round up this value.
	// Otherwise, we might have a budget (slightly) smaller than the datagram size when the timer expires.
	d := diff / bw
	// this is effectively a math.Ceil, but using only integer math
	if diff%bw > 0 {
		d++
	}
	return p.lastSentTime.Add(max(MinPacingDelay, time.Duration(d)*time.Nanosecond))
}
