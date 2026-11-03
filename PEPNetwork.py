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

up_delay='2000ms'
down_delay='2000ms'
God_loss =1
# Bad_loss =25
up_BW=10
down_BW=1
n=1


class MyTopo( Topo ):
    "Simple topology example."
    def build( self ):
        "Create custom topo."
        PEPnode1 = self.addHost( 'nodeA' )
        PEPnode2 = self.addHost( 'nodeB' )

        Switch1 = self.addSwitch('s1')
        Switch2 = self.addSwitch('s2')
        for i in range(1,n+1):
            h = self.addHost( 'h'+str(i))
            self.addLink( h, Switch1, bw=10, delay='5ms', max_queue_size=50000)

        for i in range(1+n,n+n+1):
            h = self.addHost( 'h'+str(i))
            self.addLink( h, Switch2, bw=10, delay='5ms', max_queue_size=50000)

        self.addLink( PEPnode1, Switch1, bw=10, delay='5ms', max_queue_size=50000)
        self.addLink( Switch2, PEPnode2, bw=10, delay='5ms', max_queue_size=50000)
        self.addLink( Switch1, Switch2, bw=10, delay='1990ms', loss= God_loss, max_queue_size=50000)            


def ModifyLinkParameters(net, node1, node2, up_BW, down_BW, up_delay,down_delay, loss,max_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay,loss=loss, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay,loss=0, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify downlink


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
    ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, God_loss, 50000)

    info('*** Running pingall ***\n')
    net.pingAll()
    net.pingAll()
    net.pingAll()
    # CLI(net)
    h = net.get('nodeA')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+1)+":4242 -remoteaddr 10.0.0."+str(n+n+2)+":4242 -TCPaddr 10.0.0."+str(n+n+1)+":4243 -QUICaddr 10.0.0."+str(n+n+1)+":4244 -perspective 0 -fcs "+str(flowControlSize)+" > PEP1_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(1)
    h = net.get('nodeB')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+2)+":4242 -remoteaddr 10.0.0."+str(n+n+1)+":4242 -TCPaddr 10.0.0."+str(n+n+2)+":4243 -QUICaddr 10.0.0."+str(n+n+2)+":4244 -perspective 1 -fcs "+str(flowControlSize)+" > PEP2_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(8)

    for i in range(1,n+1):
        h = net.get( 'h'+str(i))
        print("h"+str(i)+" cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > s_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > s_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    for i in range(1,n+1):
        h = net.get( 'h'+str(i+n))    
        print("h"+str(i+n)+" cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    sleep(int(33*n*1.5))

    net.stop()
    os.system("sudo mn -c")

if __name__ == '__main__':
    setLogLevel( 'info' )

    flowControlSize = 50
    n=1
    for j in range(0,1):
        run(0,'35',flowControlSize,"_"+str(j))
    # for i in range(6,11):
    #     n=i
    #     for j in range(1,6):
    #         run(0,'35',flowControlSize,"_"+str(j))
    
    # n=1
    # run(0,'35',flowControlSize,"_2")
    # run(0,'35',flowControlSize,"_3")
    # run(0,'35',flowControlSize,"_5")
    # run(0,'35',flowControlSize,"_3")
