import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 1415 AtTime: 1732785023.364786 
# [Client] GetPacketNumber: 319 ,AtTime: 1731496762.336309  
# [SendStream] writeOffset 37664 AtTime: 1732796510.881531 
# [EncryptStream] bytesRead 122880 AtTime: 1749199876.210510 
# [ReceiveStream] bytesRead 14 AtTime: 1749198135.802992 maxOffset 2764 SumOffset 2764 
# [SendStream] writeOffset 6278 AtTime: 1749198133.781578 


ReceiveByte=0
APPReceivebytesTime_List=[]
APPReceivebytes_List=[]
filename = "/home/mininet/go/src/PEPSpace/quic/PEP1_QUIC_1_FN_35_N_1_2.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        # if len(information)>0 and  information[0]=="[DecryptStream]" and information[1]=="bytesRead":
        if len(information)>0 and  information[0]=="[ReceiveStream]" and information[1]=="bytesRead":
            Time = float(information[4])
            APPReceivebytesTime_List.append(Time)
            ReceiveByte=float(information[2])
            APPReceivebytes_List.append(ReceiveByte)
file_object.close()

APPSendbytesTime_List=[]
APPSendbytes_List=[]
# filename = "/home/mininet/go/src/PEPSpace/tcp/s_TCP_1_FW_50_FN_35_N_1_1.log"
filename = "/home/mininet/go/src/PEPSpace/quic/s_QUIC_1_FW_50_FN_35_N_1_1_2.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>0 and  information[0]=="[EncryptStream]" and information[1]=="bytesWrite":
        # if len(information)>0 and  information[0]=="[SendStream]" and information[1]=="writeOffset":
            Time = float(information[4])
            APPSendbytesTime_List.append(Time)
            APPSendbytes_List.append(float(information[2]))
file_object.close()
i=0
j=0
x = 0
endtoendTime=[]
byetsList=[]
while(i <len(APPReceivebytes_List) and j <len(APPSendbytes_List)):
    if APPReceivebytes_List[i]>=APPSendbytes_List[j]:
        endtoendTime.append(APPReceivebytesTime_List[i]-APPSendbytesTime_List[j])
        byetsList.append(APPReceivebytes_List[i])
        x+=1
        j+=1
    else:
        i+=1
print(f"丢包率1% 平均值是: {sum(endtoendTime)/len(endtoendTime)} 最大值: {max(endtoendTime)}")

ax.plot(byetsList,endtoendTime)

ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.grid(True)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



