import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

goodputs_for_n = []
receive_times_buf = []
receive_bytes_buf = []
n=10
for i in range(1, n + 1):
    filename = "/home/mininet/go/src/PEPSpace/date/c_QUIC_1_FW_50_FN_35_N_"+str(n)+"_"+str(i)+"_"+str(1)+".log"
    # read and collect until we hit 35 000 000 bytes
    times = []
    bytes_read = []
    finished = False

    with open(filename, 'r') as f:
        for line in f:
            parts = line.split()
        
            if len(parts) > 1 and parts[0] == "[DecryptStream]" and parts[1] == "bytesRead":
                b = float(parts[2])
                t = float(parts[4]) # convert ms to seconds
                bytes_read.append(b)
                times.append(t)
                # if b >= 35_000_000:
                #     finished = True
                #     break

    # if not finished:
    #     print(filename,bytes_read[-1])
        # raise RuntimeError(f"Did not reach 35 000 000 bytes in {filename}")

    receive_bytes_buf.append(bytes_read)
    receive_times_buf.append(times)

# find the earliest completion time across runs
end_time = min(times_list[-1] for times_list in receive_times_buf)

# compute goodput for each run at its completion
for times, bytes_list in zip(receive_times_buf, receive_bytes_buf):
    # find the index where time >= end_time
    for idx in range(1, len(times)):
        if times[idx] >= end_time:
            duration = times[idx] - times[0]
            # bits per second → megabits per second
            gp = (bytes_list[idx] * 8 / 1e6) / duration
            goodputs_for_n.append(gp)
            break
print(goodputs_for_n)
print(sum(goodputs_for_n))





# # #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# # [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# # [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 
# # [DecryptStream] bytesRead 35000000 AtTime: 1749045079.308827
# for j in range(1,11): 
#     n=10
#     goodputsum=0.0
#     for i in range(1,n+1):
#         Receivebytes_List = []
#         ReceiveTimes_List = []
#         filename = "/home/mininet/go/src/PEPSpace/date/c_QUIC_1_FW_50_FN_35_N_"+str(n)+"_"+str(i)+"_"+str(j)+".log"
#         # print(filename)
#         with open(filename,'r') as file_object:
#             for line in file_object:
#                 linecopy = line
#                 information = linecopy.split( )
#                 if len(information)>0 and  information[0]=="[DecryptStream]" and information[1]=="bytesRead":
#                     Sendbytes = float(information[2])
#                     Time = float(information[4])
#                     Receivebytes_List.append(Sendbytes)
#                     ReceiveTimes_List.append(Time)
#         goodput = (Receivebytes_List[-1]*8/1000/1000)/(ReceiveTimes_List[-1]-ReceiveTimes_List[0])
#         # print(goodput)
#         goodputsum+=goodput

#     print("n %d j %d goodputsum %f " %(n,1,goodputsum))
#     print("********************************************************")



# for i in range(1,11):
#     GoodPut_List =[]
#     X_List =[]
#     for n in range(i,11):
#         Receivebytes_List = []
#         ReceiveTimes_List = []
#         filename = "/home/mininet/go/src/PEPSpace/c_QUIC_1_FW_50_FN_35_N_"+str(n)+"_"+str(i)+".log"
#         print(filename)
#         with open(filename,'r') as file_object:
#             for line in file_object:
#                 linecopy = line
#                 information = linecopy.split( )
#                 if len(information)>0 and  information[0]=="[DecryptStream]" and information[1]=="bytesRead":
#                     Sendbytes = float(information[2])
#                     Time = float(information[4])
#                     Receivebytes_List.append(Sendbytes)
#                     ReceiveTimes_List.append(Time)

#         file_object.close()
#         goodput = (Receivebytes_List[-1]*8/1000/1000)/(ReceiveTimes_List[-1]-ReceiveTimes_List[0])
#         GoodPut_List.append(goodput)
#         X_List.append(n)
#     ax.bar(X_List,GoodPut_List, bottom=Bottom_List)
#     Bottom_List = np.array(GoodPut_List[1:])+np.array(Bottom_List[1:])


# ax.set_ylabel('Mbps',fontsize = 30)
# ax.set_xlabel('Number of flows',fontsize = 30)
# ax.grid(True)
# # ax.legend(fontsize=30)
# plt.tick_params(labelsize=23)
# plt.show()
# # #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>





























