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
import sys


class MyTopo( Topo  ):
    "Simple topology example."
    def __init__(self, n=1, **opts):
        super(MyTopo, self).__init__(**opts)
        self._build_topology(n)

    def _build_topology( self, n ):
        "Create custom topo."
        # Add two PEP hosts
        PEPnode1 = self.addHost( 'nodeA' )
        PEPnode2 = self.addHost( 'nodeB' )
        # Add switches
        Switch1 = self.addSwitch('s1')
        Switch2 = self.addSwitch('s2')
        # Add hosts on side 1
        for i in range(1,n+1):
            h = self.addHost( 'h'+str(i))
            self.addLink( h, Switch1, bw=10, delay='5ms')

        for i in range(1+n,n+n+1):
            h = self.addHost( 'h'+str(i))
            self.addLink( h, Switch2, bw=10, delay='5ms')

        self.addLink( PEPnode1, Switch1, bw=200, delay='5ms', max_queue_size=50000)
        self.addLink( Switch2, PEPnode2, bw=200, delay='5ms', max_queue_size=50000)
        self.addLink( Switch1, Switch2, bw=10, delay='100ms', loss= 0, max_queue_size=50000)            


def ModifyLinkParameters(net, node1, node2, up_BW, down_BW, up_delay,down_delay, loss):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay, loss=loss, max_queue_size=50000, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay, loss=0, max_queue_size=50000, smooth_change = True) #Modify downlink

def run(n , filename,flowControlSize, logg, loss):
    "Create network and run simple performance test"
    #topo = SingleSwitchTopo( n=4, lossy=lossy )
    topo = MyTopo(n)
    net = Mininet( topo=topo,
                   link=TCLink,
                   autoStaticArp=True )
    setLogLevel('info')
    net.start()

    up_delay='2000ms'
    down_delay='2000ms'
    God_loss =loss
    up_BW=10
    down_BW=1
    ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, God_loss)

    print ("Testing network connectivity")
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    dumpNodeConnections(net.switches)

    info( "*** Ping all hosts***\n" )
    net.pingAll()

    # CLI(net)
    h = net.get('nodeA')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+1)+":4242 -remoteaddr 10.0.0."+str(n+n+2)+":4242 -TCPaddr 10.0.0."+str(n+n+1)+":4243 -QUICaddr 10.0.0."+str(n+n+1)+":4244 -perspective 0 -fcs "+str(flowControlSize)+" > date/PEP1_TCP_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(1)
    h = net.get('nodeB')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+2)+":4242 -remoteaddr 10.0.0."+str(n+n+1)+":4242 -TCPaddr 10.0.0."+str(n+n+2)+":4243 -QUICaddr 10.0.0."+str(n+n+2)+":4244 -perspective 1 -fcs "+str(flowControlSize)+" > date/PEP2_TCP_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(8)

    for i in range(1,n+1):
        h = net.get( 'h'+str(i))
        print("h"+str(i)+" cd cd /home/mininet/go/src/PEPSpace/;./tcp/server/tcpserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > date/s_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./tcp/server/tcpserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > date/s_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    for i in range(1,n):
        h = net.get( 'h'+str(i+n))    
        print("h"+str(i+n)+" cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4243 -fcs "+str(flowControlSize)+" > date/c_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4243 -fcs "+str(flowControlSize)+" > date/c_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    i=n
    h = net.get( 'h'+str(n+i))    
    print("h"+str(i+n)+" cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4243 -fcs "+str(flowControlSize)+" > date/c_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log ")
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./tcp/client/tcpclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4243 -fcs "+str(flowControlSize)+" >  date/c_TCP_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log ")

    sys.stdout.flush()
    print("sys.stdout.flush()")
    sleep(33)
    net.stop()
    os.system("sudo mn -c")

def runquic(n , filename,flowControlSize, logg, loss):
    "Create network and run simple performance test"
    #topo = SingleSwitchTopo( n=4, lossy=lossy )
    topo = MyTopo(n)
    net = Mininet( topo=topo,
                   link=TCLink,
                   autoStaticArp=True )
    setLogLevel('info')
    net.start()

    up_delay='2000ms'
    down_delay='2000ms'
    God_loss =loss
    up_BW=10
    down_BW=1
    ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, God_loss)

    print ("Testing network connectivity")
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    dumpNodeConnections(net.switches)

    info( "*** Ping all hosts***\n" )
    net.pingAll()

    # CLI(net)
    h = net.get('nodeA')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+1)+":4242 -remoteaddr 10.0.0."+str(n+n+2)+":4242 -TCPaddr 10.0.0."+str(n+n+1)+":4243 -QUICaddr 10.0.0."+str(n+n+1)+":4244 -perspective 1 -fcs "+str(flowControlSize)+" > date/PEP1_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    print("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+1)+":4242 -remoteaddr 10.0.0."+str(n+n+2)+":4242 -TCPaddr 10.0.0."+str(n+n+1)+":4243 -QUICaddr 10.0.0."+str(n+n+1)+":4244 -perspective 1 -fcs "+str(flowControlSize)+" > date/PEP1_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(1)
    h = net.get('nodeB')
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+2)+":4242 -remoteaddr 10.0.0."+str(n+n+1)+":4242 -TCPaddr 10.0.0."+str(n+n+2)+":4243 -QUICaddr 10.0.0."+str(n+n+2)+":4244 -perspective 0 -fcs "+str(flowControlSize)+" > date/PEP2_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    print("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0."+str(n+n+2)+":4242 -remoteaddr 10.0.0."+str(n+n+1)+":4242 -TCPaddr 10.0.0."+str(n+n+2)+":4243 -QUICaddr 10.0.0."+str(n+n+2)+":4244 -perspective 0 -fcs "+str(flowControlSize)+" > date/PEP2_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(6)

    for i in range(1,n+1):
        h = net.get( 'h'+str(i))
        print("h"+str(i)+" cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > date/s_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -testsize "+filename+" > date/s_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    for i in range(1,n):
        h = net.get( 'h'+str(i+n))    
        print("h"+str(i+n)+" cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > date/c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")
        h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > date/c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log &")

    i=n
    h = net.get( 'h'+str(i+n))    
    print("h"+str(i+n)+" cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > date/c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log ")
    h.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0."+str(i)+":4242 -xadsaddr 10.0.0."+str(i)+":4243 -pepaddr 10.0.0."+str(n+n+2)+":4244 -fcs "+str(flowControlSize)+" > date/c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_"+str(i)+logg+".log ")

    sys.stdout.flush()
    print("sys.stdout.flush()")
    sleep(33)
    net.stop()
    os.system("sudo mn -c")


if __name__ == '__main__':
    setLogLevel( 'info' )

    flowControlSize = 50
    runquic(7,'35',flowControlSize,"_"+str(1),1)
    runquic(8,'35',flowControlSize,"_"+str(1),1)
    runquic(9,'35',flowControlSize,"_"+str(1),1)

    # runquic(2,'35',flowControlSize,"_"+str(1),1)
    # runquic(7,'35',flowControlSize,"_"+str(1),1)

    # for j in range(1,11):
    #     runquic(1,'35',flowControlSize,"_Loss_"+str(j),0.1)
    # for j in range(1,11):
    #     runquic(1,'35',flowControlSize,"_Loss_"+str(j),1)
    # for j in range(1,11):
    #     runquic(1,'35',flowControlSize,"_Loss_"+str(j),5)

    # for j in range(1,11):
    #     runquic(1,'1',flowControlSize,"_SendFile_"+str(j),1)
    # for j in range(1,11):
    #     runquic(1,'10',flowControlSize,"_SendFile_"+str(j),1)
    # for j in range(2,11):
    #     runquic(1,'100',flowControlSize,"_SendFile_"+str(j),1)
    # for j in range(4,11):
    #     runquic(1,'150',flowControlSize,"_SendFile_"+str(j),1)
    # for j in range(1,11):
    #     runquic(1,'200',flowControlSize,"_SendFile_"+str(j),1)

    # for i in range(1,11):
    #     n=i
    #     for j in range(1,11):
    #         runquic(n,'35',flowControlSize,"_"+str(j),1)
