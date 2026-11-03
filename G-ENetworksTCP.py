#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from time import sleep
import os
import numpy as np
import shlex
import re

up_BW=10
down_BW=1
SPACE_DELAY = '2000ms'          # Each bottleneck direction, not the RTT.
QUEUE_LIMIT = 50000             # Packets, unchanged from the supplied script.


# # G-E参数1
# LossType = "G_E_Type_1"
# MEAN_LOSS = 0.02
# MEAN_BURST = 10.0               # Geometric mean, NOT a fixed burst length.
# GE_Q = 1.0 / MEAN_BURST         # P(G | B) = 0.1.
# GE_P = MEAN_LOSS * GE_Q / (1.0 - MEAN_LOSS)  # P(B | G).
# GE_LOSS_GOOD = 0.0
# GE_LOSS_BAD = 1.0


# # # # G-E参数2：采用PEPesc论文中的设置
# LossType = "G_E_Type_2"
# GE_P = 0.017                    # P(B | G)
# GE_Q = 0.935                    # P(G | B)
# GE_LOSS_GOOD = 0.0              # 好状态不丢包
# GE_LOSS_BAD = 0.952             # 坏状态丢包概率95.2%
# MEAN_LOSS = (
#     GE_Q * GE_LOSS_GOOD + GE_P * GE_LOSS_BAD
# ) / (GE_P + GE_Q)               # 平均丢包率1.7%
# MEAN_BAD_STATE = 1.0 / GE_Q     # 平均坏状态长度，约1.070个分组
# # 在GE_LOSS_GOOD=0时，平均连续丢包长度：
# MEAN_BURST = 1.0 / (
#     1.0 - (1.0 - GE_Q) * GE_LOSS_BAD
# )                              # 约1.066个分组


# # G-E参数1：GE-Original，对应现有 PEPesc 设置
# LossType = "G_E_Type_PEPesc"
# GE_P = 0.017                    # P(B | G)
# GE_Q = 0.935                    # P(G | B)
# GE_LOSS_GOOD = 0.0              # 好状态不丢包
# GE_LOSS_BAD = 0.952             # 坏状态丢包概率 95.2%


# G-E参数2：GE-Longer-Burst，增强时间相关性
LossType = "G_E_Type_PEPesc_Longer_Burst"
GE_P = 0.00182                  # P(B | G)，由平均 PER=0.017、GE_Q=0.1 反算
GE_Q = 0.1                      # P(G | B) = 1 / 平均坏状态长度
GE_LOSS_GOOD = 0.0              # 好状态不丢包
GE_LOSS_BAD = 0.952             # 坏状态丢包概率 95.2%




class MyTopo( Topo ):
    "Simple topology example."
    def build( self ):
        "Create custom topo."
        PEPnode1 = self.addHost( 'nodeA' )
        PEPnode2 = self.addHost( 'nodeB' )

        Switch1 = self.addSwitch('s1')
        Switch2 = self.addSwitch('s2')
        h = self.addHost( 'h1')
        self.addLink( h, Switch1, bw=100, delay='5ms', max_queue_size=50000)

        h = self.addHost( 'h2')
        self.addLink( h, Switch2, bw=100, delay='5ms', max_queue_size=50000)

        self.addLink( PEPnode1, Switch1, bw=100, delay='5ms', max_queue_size=50000)
        self.addLink( Switch2, PEPnode2, bw=100, delay='5ms', max_queue_size=50000)
        self.addLink( Switch1, Switch2, bw=10, delay='1990ms', max_queue_size=50000)            


def ModifyLinkParameters(net, node1, node2, up_BW, down_BW, up_delay,down_delay, max_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify downlink

def checked(node, argv):
    out, err, code = node.pexec(argv)
    if code:
        raise RuntimeError('{}: {}\n{}{}'.format(
            node.name, ' '.join(map(shlex.quote, argv)), out, err))
    return out

def find_netem(qdisc_output):
    """Find the existing netem handle/parent; do not guess port numbers."""
    found = []
    for line in qdisc_output.splitlines():
        match = re.match(r'^qdisc\s+netem\s+([0-9a-fA-F]+:)\s+(.*)$', line)
        if match:
            handle, fields = match.groups()
            parent = re.search(r'\bparent\s+(\S+)', fields)
            if parent:
                found.append((handle, ['parent', parent.group(1)]))
            elif re.search(r'\broot\b', fields):
                found.append((handle, ['root']))
    if len(found) != 1:
        raise RuntimeError('Expected one netem qdisc, found {}:\n{}'.format(
            len(found), qdisc_output))
    return found[0]


def setup_ge_loss(node, intf):
    before = checked(node, ['tc', 'qdisc', 'show', 'dev', str(intf)])
    handle, parent = find_netem(before)
    # Keep the HTB bandwidth limiter and explicitly retain netem delay/limit.
    command = ['tc', 'qdisc', 'change', 'dev', str(intf)] + parent + [
        'handle', handle, 'netem', 'delay', SPACE_DELAY,
        'limit', str(QUEUE_LIMIT), 'loss', 'gemodel',
        '{:.10f}%'.format(100 * GE_P), '{:.10f}%'.format(100 * GE_Q),
        '{:.10f}%'.format(100 * GE_LOSS_BAD),'{:.10f}%'.format(100 * GE_LOSS_GOOD)]
    checked(node, command)  # Unsupported GE/seed syntax is an error, not a fallback.
    after = checked(node, ['tc', 'qdisc', 'show', 'dev', str(intf)])
    info('*** GE on {}:{}: mean loss 2%, mean burst 10 packets\n'.format(
        node.name, intf))
    print({'argv': command, 'before': before, 'after': after})
    return 


def run(i , filename, flowControlSize, logg):
    "Create network and run simple performance test"
    #topo = SingleSwitchTopo( n=4, lossy=lossy )
    topo = MyTopo()
    net = Mininet( topo=topo,
                   link=TCLink,
                   autoStaticArp=True )
    
    net.start()
    print ("Testing network connectivity")
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    dumpNodeConnections(net.switches)
    ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, SPACE_DELAY, SPACE_DELAY, 50000)
    s1, s2 = net.get('s1', 's2')
    links = s1.connectionsTo(s2)
    forward, reverse = links[0]
    setup_ge_loss(s1, forward)

    info('*** Running pingall ***\n')
    # CLI(net)
    net.pingAll()
    net.pingAll()
    net.pingAll()
    net.pingAll()
    net.pingAll()
    h = net.get('nodeA')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0.3:4242 -remoteaddr 10.0.0.4:4242 -TCPaddr 10.0.0.3:4243 -QUICaddr 10.0.0.3:4244 -perspective 0 -fcs "+str(flowControlSize)+" > PEP1_TCP_"+str(LossType)+"_FN_"+filename+"_N_1"+logg+".log 2>&1 &")
    sleep(1)
    h = net.get('nodeB')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0.4:4242 -remoteaddr 10.0.0.3:4242 -TCPaddr 10.0.0.4:4243 -QUICaddr 10.0.0.4:4244 -perspective 1 -fcs "+str(flowControlSize)+" > PEP2_TCP_"+str(LossType)+"_FN_"+filename+"_N_1"+logg+".log 2>&1 &")
    sleep(12)

    h = net.get( 'h1' )
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpserver -serveraddr 10.0.0.1:4242 -xadsaddr 10.0.0.1:4243 -testsize "+filename+" > s_TCP_"+str(LossType)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_1"+"_"+str(i)+logg+".log 2>&1 &")
    h = net.get( 'h2' )    
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpclient -serveraddr 10.0.0.1:4242 -xadsaddr 10.0.0.1:4243 -pepaddr 10.0.0.4:4243 -fcs "+str(flowControlSize)+" > c_TCP_"+str(LossType)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_1"+"_"+str(i)+logg+".log 2>&1")

    sleep(5)
    net.stop()
    os.system("sudo mn -c")

if __name__ == '__main__':
    setLogLevel( 'info' )

    flowControlSize = 50
    for i in range(30,50):
        run(0,'200',flowControlSize,"_"+str(i))



