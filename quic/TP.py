import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 
# [DecryptStream] bytesRead 35000000 AtTime: 1749045079.308827 
# [APP-Client-PEP] Receive and decode Calculate MD5 value as 35000000 Bytes MD5 (hex): d421031933bd2006a627b5671e5694d4


Bottom_List = np.zeros(10)
for i in range(1,11):
    GoodPut_List =[]
    X_List =[]
    for n in range(i,11):
        CheckFinsh = False

        Receivebytes_List = []
        ReceiveTimes_List = []
        
        filename = "/home/mininet/go/src/PEPSpace/quic/date/c_QUIC_1_FW_50_FN_35_N_"+str(n)+"_"+str(i)+".log"
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

        if not CheckFinsh:
            print(filename)


        file_object.close()
        goodput = (Receivebytes_List[-1]*8/1000/1000)/(ReceiveTimes_List[-1]-ReceiveTimes_List[0])
        GoodPut_List.append(goodput)
        X_List.append(n)
    ax.bar(X_List,GoodPut_List, bottom=Bottom_List)
    Bottom_List = np.array(GoodPut_List[1:])+np.array(Bottom_List[1:])


ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.grid(True)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>





























