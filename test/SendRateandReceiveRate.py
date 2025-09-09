import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()


Sendbytes=0
Sendbytes_List = []
SendTimes_List = []

Receivebytes_List = []
ReceiveTimes_List = []

filename = "/home/mininet/go/src/PEPSpace/nodeA.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>0 and  information[0]=="[SendStream]" and information[1]=="writeOffset":
            Sendbytes = float(information[2])
            Time = float(information[4])
            Sendbytes_List.append(Sendbytes)
            SendTimes_List.append(Time)

file_object.close()

SendRate_List = []
SendRateTime_List = []

for Index in range(1,len(Sendbytes_List)):
    rate = Sendbytes_List[Index]*8/1024/1024/(SendTimes_List[Index]-SendTimes_List[0])
    SendRate_List.append(rate)
    SendRateTime_List.append(SendTimes_List[Index]-SendTimes_List[0])

ax.plot(SendRateTime_List,Sendbytes_List[1:],alpha=0.8,linewidth=3)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 

Sendbytes=0
SendmaxwriteOffset_List = []
Sendbytes_List = []
SendTimes_List = []

Receivebytes_List = []
ReceiveTimes_List = []

filename = "/home/mininet/go/src/PEPSpace/b.log"
with open(filename,'r') as file_object:
    for line in file_object:
        linecopy = line
        information = linecopy.split( )
        if len(information)>5 and  information[0]=="[SendStream]" and information[1]=="writeOffset":
            Sendbytes = float(information[2])
            Time = float(information[4])
            SendmaxwriteOffset = float(information[6])
            SendmaxwriteOffset_List.append(SendmaxwriteOffset)
            Sendbytes_List.append(Sendbytes)
            SendTimes_List.append(Time)

        if len(information)>0 and  information[0]=="[ReceiveStream]" and information[1]=="bytesRead":
            Sendbytes = float(information[2])
            Time = float(information[4])
            Receivebytes_List.append(Sendbytes)
            ReceiveTimes_List.append(Time)

file_object.close()

SendRate_List = []
maxwriteOffsetRate_List = []
SendRateTime_List = []

for Index in range(1,len(Sendbytes_List)):
    rate = Sendbytes_List[Index]*8/1024/1024/(SendTimes_List[Index]-SendTimes_List[0])
    SendRate_List.append(rate)
    maxwriteOffsetRate_List.append(SendmaxwriteOffset_List[Index]*8/1024/1024/(SendTimes_List[Index]-SendTimes_List[0]))
    SendRateTime_List.append(SendTimes_List[Index]-SendTimes_List[0])

ReceiveRateTime_List = []
for Index in range(1,len(ReceiveTimes_List)):
    ReceiveRateTime_List.append(ReceiveTimes_List[Index]-SendTimes_List[0])



ax.plot(SendRateTime_List,Sendbytes_List[1:],alpha=0.8,linewidth=3)
ax.plot(SendRateTime_List,SendmaxwriteOffset_List[1:],alpha=0.8,linewidth=3)
ax.plot(ReceiveRateTime_List,Receivebytes_List[1:],alpha=0.8,linewidth=3)


ax.set_ylabel('Packet/s',fontsize = 30)
ax.set_xlabel('Time(s)',fontsize = 30)
ax.grid(True)
ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

































# # #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# # [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# # [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 

# Sendbytes=0
# Sendbytes_List = []
# SendTimes_List = []

# Receivebytes_List = []
# ReceiveTimes_List = []

# filename = "/home/mininet/go/src/PEPSpace/quic/server/nodeA.log"
# with open(filename,'r') as file_object:
#     for line in file_object:
#         linecopy = line
#         information = linecopy.split( )
#         if len(information)>0 and  information[0]=="[SendStream]" and information[1]=="writeOffset":
#             Sendbytes = float(information[2])
#             Time = float(information[4])
#             Sendbytes_List.append(Sendbytes)
#             SendTimes_List.append(Time)

#         if len(information)>0 and  information[0]=="[ReceiveStream]" and information[1]=="bytesRead":
#             Sendbytes = float(information[2])
#             Time = float(information[4])
#             Receivebytes_List.append(Sendbytes)
#             ReceiveTimes_List.append(Time)
# file_object.close()

# ReceiveRate_List = []
# ReceiveRateTime_List = []
# SendRate_List = []
# SendRateTime_List = []

# StartTime = 0
# for Index in range(100,len(Receivebytes_List)):
#     if StartTime == 0:
#         StartTime = ReceiveTimes_List[Index]
#         continue
#     rate = Receivebytes_List[Index]*8/1024/1024/(ReceiveTimes_List[Index]-StartTime)

#     ReceiveRate_List.append(rate)
#     ReceiveRateTime_List.append(ReceiveTimes_List[Index]-StartTime)

# for Index in range(100,len(Sendbytes_List)):
#     if SendTimes_List[Index] < StartTime:
#         continue

#     rate = Sendbytes_List[Index]*8/1024/1024/(SendTimes_List[Index]-StartTime)
#     SendRate_List.append(rate)
#     SendRateTime_List.append(SendTimes_List[Index]-StartTime)

# ax.plot(SendRateTime_List,SendRate_List,alpha=0.8,linewidth=3)
# ax.plot(ReceiveRateTime_List,ReceiveRate_List,alpha=0.8,linewidth=3)


# ax.set_ylabel('Packet/s',fontsize = 30)
# ax.set_xlabel('Time(s)',fontsize = 30)
# ax.grid(True)
# ax.legend(fontsize=30)
# plt.tick_params(labelsize=23)
# plt.show()
# # #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>