import matplotlib.pyplot as plt
import numpy as np

fig1, axs = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 1415 AtTime: 1732785023.364786 
# [Client] GetPacketNumber: 319 ,AtTime: 1731496762.336309  
# [SendStream] writeOffset 37664 AtTime: 1732796510.881531 
# [EncryptStream] bytesRead 122880 AtTime: 1749199876.210510 

ReceiveByte=0
APPReceivebytesTime_List=[]
APPReceivebytes_List=[]
# filename = "/home/mininet/go/src/PEPSpace/tcp/c_TCP_1_FW_50_FN_35_N_1_1.log"
filename = "/home/mininet/go/src/PEPSpace/quic/c_QUIC_1_FW_50_FN_35_N_1_1_2.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>0 and  information[0]=="[DecryptStream]" and information[1]=="bytesRead":
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
            Time = float(information[4])
            APPSendbytesTime_List.append(Time)
            APPSendbytes_List.append(float(information[2]))
file_object.close()
i=0
j=0
x = 0
endtoendTime=[]
while(i <len(APPReceivebytes_List) and j <len(APPSendbytes_List)):
    if APPReceivebytes_List[i]>=APPSendbytes_List[j]:
        endtoendTime.append(APPReceivebytesTime_List[i]-APPSendbytesTime_List[j])
        x+=1
        j+=1
    else:
        i+=1
print(f"丢包率1% 平均值是: {sum(endtoendTime)/len(endtoendTime)} 最大值: {max(endtoendTime)}")


