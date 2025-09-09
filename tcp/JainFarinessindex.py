import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 
# [DecryptStream] bytesRead 35000000 AtTime: 1749045079.308827 
# [APP-Client-PEP] Receive and decode Calculate MD5 value as 35000000 Bytes MD5 (hex): d421031933bd2006a627b5671e5694d4

def compute_sfi(goodputs):
    """
    计算 SFI（Slot Fairness Index）

    参数：
        goodputs: numpy.ndarray，形状为 (T, L)，
                  表示 T 个时间点、L 个流的 goodput

    返回：
        SFI 值
    """
    T, L = goodputs.shape
    numerator = np.sum(goodputs, axis=1) ** 2               # shape: (T,)
    denominator = L * np.sum(goodputs ** 2, axis=1)         # shape: (T,)
    
    fairness_per_t = numerator / (denominator + 1e-12)      # 加一个小量防止除零
    sfi = np.mean(fairness_per_t)
    return sfi

X_List =[]
Y_List=[]
for n in range(1,11):
    GoodPut_List =[]
    for i in range(1,n+1):
        CheckFinsh = False

        Receivebytes_List = []
        ReceiveTimes_List = []
        
        filename = "/home/mininet/go/src/PEPSpace/tcp/data/c_TCP_1_FW_50_FN_35_N_"+str(n)+"_"+str(i)+".log"
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
        GoodPut_List.append([goodput])
    X_List.append(n)
    Y_List.append(compute_sfi(np.array(GoodPut_List)))

print(X_List)
print(Y_List)
ax.plot(X_List,Y_List)


ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.set_ylim(0,1.1)
ax.grid(True)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


