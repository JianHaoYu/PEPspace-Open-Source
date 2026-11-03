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

# # G-E参数1：GE-Original，对应现有 PEPesc 设置
LossType = "G_E_Type_Random"
Loss = 1.7


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


def ModifyLinkParameters(net, node1, node2, up_BW, down_BW, up_delay, down_delay, loss, max_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay,loss=loss, latency_ms=100, max_queue_size=max_queue_size, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay,loss=0, latency_ms=100, max_queue_size=max_queue_size, smooth_change = True) #Modify downlink

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
    ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, SPACE_DELAY, SPACE_DELAY, Loss, 50000)

    info('*** Running pingall ***\n')
    # CLI(net)
    net.pingAll()
    net.pingAll()
    net.pingAll()
    h = net.get('nodeA')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0.3:4242 -remoteaddr 10.0.0.4:4242 -TCPaddr 10.0.0.3:4243 -QUICaddr 10.0.0.3:4244 -perspective 0 -fcs "+str(flowControlSize)+" > PEP1_QUIC_"+str(LossType)+"_FN_"+filename+"_N_1"+logg+".log 2>&1 &")
    sleep(1)
    h = net.get('nodeB')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0.4:4242 -remoteaddr 10.0.0.3:4242 -TCPaddr 10.0.0.4:4243 -QUICaddr 10.0.0.4:4244 -perspective 1 -fcs "+str(flowControlSize)+" > PEP2_QUIC_"+str(LossType)+"_FN_"+filename+"_N_1"+logg+".log 2>&1 &")
    sleep(12)

    h = net.get( 'h1' )
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0.1:4242 -xadsaddr 10.0.0.1:4243 -testsize "+filename+" > s_QUIC_"+str(LossType)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_1"+"_"+str(i)+logg+".log 2>&1 &")
    h = net.get( 'h2' )    
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0.1:4242 -xadsaddr 10.0.0.1:4243 -pepaddr 10.0.0.4:4244 -fcs "+str(flowControlSize)+" > c_QUIC_"+str(LossType)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_1"+"_"+str(i)+logg+".log 2>&1")

    sleep(5)
    net.stop()
    os.system("sudo mn -c")

if __name__ == '__main__':
    setLogLevel( 'info' )

    flowControlSize = 50
    for i in range(18,50):
        run(0,'200',flowControlSize,"_"+str(i))



