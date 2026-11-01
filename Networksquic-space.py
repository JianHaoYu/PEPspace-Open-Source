import os

from mininet.net import Mininet
from mininet.node import Node, Controller, RemoteController
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mininet.util import dumpNodeConnections
from time import sleep
from ast import literal_eval



nodeA_eth1 = '10.0.0.1/24'
nodeB_eth1 = '10.0.0.2/24'

nodeB_eth2 = '10.0.1.2/24'
nodeC_eth1 = '10.0.1.3/24'


up_BW=10
down_BW=1
initial_delay='20ms'
up_delay='1010ms'
down_delay='1010ms'
initial_loss =1

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ): 
        nodeA = self.addNode( 'nodeA', cls=LinuxRouter, ip=nodeA_eth1 )
        nodeB = self.addNode( 'nodeB', cls=LinuxRouter, ip=nodeB_eth1 )
        nodeC = self.addNode( 'nodeC', cls=LinuxRouter, ip=nodeC_eth1 )
        print("AddLink nodeA-eth1 nodeB-eth1")
        self.addLink(nodeA, nodeB, intfName1='nodeA-eth1', params1={'ip':nodeA_eth1}, intfName2='nodeB-eth1', params2={'ip':nodeB_eth1}, bw=50, delay=initial_delay, loss= initial_loss,max_queue_size=50000)
        print("AddLink nodeC-eth1 nodeB-eth2")
        self.addLink(nodeC, nodeB, intfName1='nodeC-eth1', params1={'ip':nodeC_eth1}, intfName2='nodeB-eth2', params2={'ip':nodeB_eth2}, bw=50, delay=initial_delay, loss= initial_loss,max_queue_size=50000)


class TestMininet(Mininet):
    def __init__(self,controller,topo):
        Mininet.__init__(self,controller=controller,topo=topo,link=TCLink)  


def ModifyLinkParameters(net, node1, node2,up_BW, down_BW, up_delay,down_delay, initial_loss,max_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay,loss=initial_loss,max_queue_size=max_queue_size, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay,loss=initial_loss,max_queue_size=max_queue_size, smooth_change = True) #Modify downlink


def run(n , filename,flowControlSize, logg, God_loss):
    "Test linux router"
    topo = NetworkTopo()
    net = TestMininet(controller=RemoteController,topo=topo)
    net.start()

    ModifyLinkParameters(net,'nodeA','nodeB',up_BW, down_BW, up_delay, down_delay, God_loss,50000)
    print()
    ModifyLinkParameters(net,'nodeB','nodeC',up_BW, down_BW, up_delay, down_delay, 0 ,50000)
    print()

    dumpNodeConnections(net.hosts)
    
    print(" Testing network connectivity ")
    info( '*** Routing Table on Router:\n' )

    nodeA = net.getNodeByName('nodeA')
    nodeB = net.getNodeByName('nodeB')
    nodeC = net.getNodeByName('nodeC')

    nodeA.cmd('ip route add 10.0.1.0/24 via 10.0.0.2')
    nodeC.cmd('ip route add 10.0.0.0/24 via 10.0.1.2')

    net.pingAll()
    net.pingAll()
    net.pingAll()

    # nodeA.cmd('cd /home/mininet/go/src/quic-go/example/minserver/;./minserver -testdata test_'+filename+'.txt -fcs '+str(flowControlSize)+' >s_break_3RTT_'+str(initial_loss)+'_'+str(flowControlSize)+'_'+filename+'_SC_'+str(i)+'.log &')
    # nodeB.cmd('cd /home/mininet/go/src/quic-go/example/Interrupt_proxy/udpListen/;sh deploy-proxy-on-node-b.sh; ./main >m.log &')
    # nodeC.cmd('cd /home/mininet/go/src/quic-go/example/minclient;./minclient -fcs '+str(flowControlSize)+' >c_break_3RTT_'+str(initial_loss)+'_'+str(flowControlSize)+'_'+filename+'_SC_'+str(i)+'.log')


    nodeA.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.0.1:4242 -remoteaddr 10.0.1.3:4242 -TCPaddr 10.0.0.1:4243 -QUICaddr 10.0.0.1:4244 -perspective 1 -fcs "+str(flowControlSize)+" > date/PEP1_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(1)
    nodeC.cmd("cd /home/mininet/go/src/PEPSpace/;./PEP -localaddr 10.0.1.3:4242 -remoteaddr 10.0.0.1:4242 -TCPaddr 10.0.1.3:4243 -QUICaddr 10.0.1.3:4244 -perspective 0 -fcs "+str(flowControlSize)+" > date/PEP2_QUIC_"+str(God_loss)+"_FN_"+filename+"_N_"+str(n)+logg+".log &")
    sleep(8)

    nodeA.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/server/quicserver -serveraddr 10.0.0.1:5242 -xadsaddr 10.0.0.1:5243 -testsize "+filename+" > date/s_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_1"+logg+".log &")
    # CLI(net)
    nodeB.cmd('cd /home/mininet/go/src/PEPSpace/udpListen/;sh deploy-proxy-on-node-b.sh; ./main >m.log &')
    sleep(1)
    nodeC.cmd("cd /home/mininet/go/src/PEPSpace/;./quic/client/quicclient -serveraddr 10.0.0.1:5242 -xadsaddr 10.0.0.1:5243 -pepaddr 10.0.1.3:4244 -fcs "+str(flowControlSize)+" > date/c_QUIC_"+str(God_loss)+"_FW_"+str(flowControlSize)+"_FN_"+filename+"_N_"+str(n)+"_1"+logg+".log")

    net.stop()
    os.system("sudo mn -c")

if __name__ == '__main__':
    setLogLevel( 'info' )
    initial_loss = 1

    flowControlSize = 50
    # for j in range(0,10):
    #     run(1,'35',flowControlSize,"_"+str(j),1)
    # for j in range(0,10):
    #     run(1,'35',flowControlSize,"_"+str(j),2)
    # for j in range(0,10):
    #     run(1,'35',flowControlSize,"_"+str(j),3)


    for j in range(0,20):
        run(1,'35',flowControlSize,"_"+str(j),10)
    # for i in range(0,10):
    #     run(i,'2500',flowControlSize)

    # for j in range(1,11):
    #     run(1,'35',flowControlSize,"_"+str(j),0.1)
    # for j in range(1,11):
    #     runquic(1,'35',flowControlSize,"_Loss_"+str(j),1)
    # for j in range(1,11):
    #     run(1,'35',flowControlSize,"_"+str(j),0)
    # for j in range(1,11):
    #     run(1,'35',flowControlSize,"_"+str(j),2)
    # for j in range(1,11):
    #     run(1,'35',flowControlSize,"_"+str(j),3)
    # for j in range(0,10):
    #     run(1,'35',flowControlSize,"_"+str(j),4)
    # flowControlSize = 40
    # for i in range(0,10):
    #     run(i,'25000',flowControlSize)

    # for i in range(5,45,5):
    #     for j in range(0,10):
    #         run(j,'25000',i)

