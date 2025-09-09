import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 
# [DecryptStream] bytesRead 35000000 AtTime: 1749045079.308827 
# [APP-Client-PEP] Receive and decode Calculate MD5 value as 35000000 Bytes MD5 (hex): f71b20747864a53fe5334ab49bbc692d

Receivebytes_List = []
ReceiveTimes_List = []
checkfinish = False
# filename = "/home/mininet/go/src/PEPSpace/quic/c_QUIC_1_FW_50_FN_35_N_1_1_2.log"
filename = "/home/mininet/go/src/PEPSpace/tcp/c_TCP_1_FW_50_FN_35_N_1_1.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>0 and  information[0]=="[DecryptStream]" and information[1]=="bytesRead":
            Sendbytes = float(information[2])
            Time = float(information[4])
            Receivebytes_List.append(Sendbytes)
            ReceiveTimes_List.append(Time)
        if len(information)>0 and information[0]=="[APP-Client-PEP]" and information[1]=="Receive" and information[2]=="and" :
            CheckFinsh = True
file_object.close()
if not CheckFinsh:
    print(filename)

GoodPut_List=[]
Time_List=[]
for i in range(1,len(ReceiveTimes_List)):
    goodput = (Receivebytes_List[i]*8/1000/1000)/(ReceiveTimes_List[i]-ReceiveTimes_List[0])
    GoodPut_List.append(goodput)
    Time_List.append((ReceiveTimes_List[i]-ReceiveTimes_List[0]))

StratTime = ReceiveTimes_List[0]
StartBytes=Receivebytes_List[0]
PerGoodPut_List=[]
PerTime_List=[]
for i in range(1,len(ReceiveTimes_List)):
    if StratTime+1 < ReceiveTimes_List[i]:
        perSecondBytes = Receivebytes_List[i]-StartBytes

        PerGoodPut_List.append((perSecondBytes*8/1000/1000)/(ReceiveTimes_List[i]-StratTime))
        PerTime_List.append(ReceiveTimes_List[i]-ReceiveTimes_List[0])
        StartBytes = Receivebytes_List[i]
        StratTime = ReceiveTimes_List[i]
        
ax.plot(Time_List,GoodPut_List)
print(PerTime_List[0])
print(PerTime_List[1])
# ax.plot(PerTime_List,PerGoodPut_List)

ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.grid(True)
ax.set_ylim(0,10)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>





























