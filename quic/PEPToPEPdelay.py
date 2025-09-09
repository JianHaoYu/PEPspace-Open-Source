import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 1415 AtTime: 1732785023.364786 
# [Client] GetPacketNumber: 319 ,AtTime: 1731496762.336309  
# [SendStream] writeOffset 37664 AtTime: 1732796510.881531 
# [ReceiveStream] bytesRead 6940 AtTime: 1749451665.276872 maxOffset 6940 SumOffset 6940 QUICSpaceStreamID: 1 
# [SendStream] writeOffset 1804360 AtTime: 1749451667.601155 maxwriteOffset: 1807520 QUICSpaceStreamID: 1 
		# fmt.Printf("[ReceiveStream2] maxOffset %d AtTime: %f \n", s.maxOffset, float64(time.Now().UnixNano()/1e3)/1e6)


ReceiveByte=0
APPReceivebytesTime_List=[]
APPReceivebytes_List=[]
filename = "/home/mininet/go/src/PEPSpace/quic/PEP2_QUIC_1_FN_35_N_1_2.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>9 and information[0]=="[ReceiveStream]" and information[1]=="bytesRead" and information[10]=="1":
            Time = float(information[4])
            APPReceivebytesTime_List.append(Time)
            ReceiveByte=float(information[2])
            APPReceivebytes_List.append(ReceiveByte)

file_object.close()

APPSendbytesTime_List=[]
APPSendbytes_List=[]
filename = "/home/mininet/go/src/PEPSpace/quic/PEP1_QUIC_1_FN_35_N_1_2.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>7 and information[0]=="[SendStream]" and information[1]=="writeOffset" and information[8]=="1":
            Time = float(information[4])
            APPSendbytesTime_List.append(Time)
            APPSendbytes_List.append(float(information[2]))
file_object.close()
i=0
j=0
x = 0
endtoendTime=[]
byetsList=[]
stratTime = APPReceivebytesTime_List[0]
while(i <len(APPReceivebytes_List) and j <len(APPSendbytes_List)):
    if APPReceivebytes_List[i]>=APPSendbytes_List[j]:
        endtoendTime.append(APPReceivebytesTime_List[i]-APPSendbytesTime_List[j])
        # if endtoendTime[-1]>2.3:
        #     print(APPReceivebytesTime_List[i],APPSendbytesTime_List[j])
        byetsList.append(APPReceivebytesTime_List[i]-stratTime)
        x+=1
        j+=1
    else:
        i+=1
print(f"丢包率5% 平均值是: {sum(endtoendTime)/len(endtoendTime)} 最大值: {max(endtoendTime)}")


ax.plot(byetsList,endtoendTime)

ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.set_ylim(1,4)
ax.grid(True)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()