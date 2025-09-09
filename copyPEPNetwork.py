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


class MyTopo( Topo ):
    "Simple topology example."
    def build( self,n=1):
        "Create custom topo."
        nodeA = self.addHost( 'nodeA')
        nodeB = self.addHost( 'nodeB')
        nodeC = self.addHost( 'nodeC')
        nodeD = self.addHost( 'nodeD')

        Switch1 = self.addSwitch('s1')
        Switch2 = self.addSwitch('s2')
        Switch3 = self.addSwitch('s3')
        Switch4 = self.addSwitch('s4')

        self.addLink( nodeA, Switch1, bw=10, delay='5ms', max_queue_size=50000)
        self.addLink( nodeB, Switch2, bw=10, max_queue_size=50000)
        self.addLink( nodeC, Switch3, bw=10, max_queue_size=50000)
        self.addLink( nodeD, Switch4, bw=10, delay='5ms', max_queue_size=50000)

        self.addLink( Switch1, Switch2, bw=10, delay='5ms', max_queue_size=50000)
        self.addLink( Switch3, Switch4, bw=10, delay='5ms', max_queue_size=50000)

        self.addLink( Switch2, Switch3, bw=10, delay='2000ms', loss= God_loss, max_queue_size=50000)


def ModifyLinkParameters(net, node1, node2, up_BW, down_BW, up_delay,down_delay, loss,max_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = up_BW, delay = up_delay,loss=loss, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify uplink
    dst_intf.config(bw = down_BW, delay = down_delay,loss=0, latency_ms=100,max_queue_size=max_queue_size, smooth_change = True) #Modify downlink


def update_state(Current_State, p_GG, p_EG):
  """
  生成G-E丢包模型的状态序列
  
  参数:
      p_GG: 从良好状态转移到良好状态的概率
      p_EG: 从错误状态转移到良好状态的概率
      num_packets: 要生成的状态序列的长度（即数据包数量）
  
  返回:
      states: 状态序列（0表示良好状态，1表示错误状态）
  """
    
  # 根据当前状态和转移概率决定下一个状态
  if Current_State == 0:  # 当前状态是良好状态
      if np.random.rand() < p_GG:
          next_state = 0  # 保持在良好状态
      else:
          next_state = 1  # 转移到错误状态
  else:  # 当前状态是错误状态
      if np.random.rand() < p_EG:
          next_state = 0  # 转移到良好状态
      else:
          next_state = 1  # 保持在错误状态
  
  return next_state


def run(i , filename, flowControlSize):
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
    # CLI(net)

    # Current_State = 0
    # if np.random.rand() < 0.25:
    #     Current_State = 1
    #     ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, Bad_loss,50000)
    # else:
    #     ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, God_loss,50000)
    ModifyLinkParameters(net,'s2','s3',up_BW, down_BW, up_delay, down_delay, God_loss, 50000)

    info('*** Running pingall ***\n')
    net.pingAll()
    net.pingAll()
    # net.pingAll()
    # net.pingAll()
    # net.pingAll()
    CLI(net)

    # h = net.get('h1')
    # h.cmd('cd /home/mininet/go/src/quic-go-space/example/minserver/;./minserver -ip 10.0.0.1:4242 -testdata test_'+filename+'.txt -fcs '+str(flowControlSize)+' >TestDate/s_QUIC_loss_'+str(God_loss)+'_FW_'+str(flowControlSize)+'_FN_'+filename+'_'+str(i)+'.log &')
    # sleep(1)
    # h = net.get('h2')    
    # h.cmd('cd /home/mininet/go/src/quic-go-space/example/minclient/;./minclient -ip 10.0.0.1:4242 -fcs '+str(flowControlSize)+' >TestDate/c_QUIC_loss_'+str(God_loss)+'_FW_'+str(flowControlSize)+'_FN_'+filename+'_'+str(i)+'.log &')

    # for i in range(0,20):
    #     sleep(5*4)
        # Current_State = update_state(Current_State, 0.95, 0.15)

        # if Current_State == 0:
        #     ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, God_loss, 90000)
        #     print("ModifyLinkParameters loss 5%")
        # else:
        #     ModifyLinkParameters(net,'s1','s2',up_BW, down_BW, up_delay, down_delay, Bad_loss, 90000)
        #     print("ModifyLinkParameters loss 25%")    
    net.stop()
    os.system("sudo mn -c")


def run2(i , filename, flowControlSize):
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
    ModifyLinkParameters(net,'s2','s3',up_BW, down_BW, up_delay, down_delay, God_loss, 50000)

    info('*** Running pingall ***\n')
    net.pingAll()
    net.pingAll()
    net.pingAll()
    net.pingAll()
    net.pingAll()
    # CLI(net)

    h = net.get('nodeA')
    h.cmd('cd /home/mininet/go/src/quic-go-space/example/minserver/;./minserver -ip 10.0.0.1:4242 -testdata test_'+filename+'.txt -fcs '+str(flowControlSize)+' >TestDate/s_QUIC_loss_'+str(God_loss)+'_FW_'+str(flowControlSize)+'_FN_'+filename+'_'+str(i)+'.log &')
    sleep(1)
    h = net.get('nodeD')    
    h.cmd('cd /home/mininet/go/src/quic-go-space/example/minclient/;./minclient -ip 10.0.0.1:4242 -fcs '+str(flowControlSize)+' >TestDate/c_QUIC_loss_'+str(God_loss)+'_FW_'+str(flowControlSize)+'_FN_'+filename+'_'+str(i)+'.log ')

    net.stop()
    os.system("sudo mn -c")

if __name__ == '__main__':
    setLogLevel( 'info' )

    flowControlSize = 50
    run(0,'25000',flowControlSize)



