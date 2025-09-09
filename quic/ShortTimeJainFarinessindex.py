import matplotlib.pyplot as plt
import numpy as np

fig1, ax = plt.subplots()

# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# [ReceiveStream] bytesRead 10270 AtTime: 1748162183.970777 maxOffset 10270 SumOffset 10270 
# [SendStream] writeOffset 10270 AtTime: 1748165254.602329 maxwriteOffset: 12784 
# [DecryptStream] bytesRead 35000000 AtTime: 1749045079.308827 
# [APP-Client-PEP] Receive and decode Calculate MD5 value as 35000000 Bytes MD5 (hex): d421031933bd2006a627b5671e5694d4

def compute_sfi_varlen(goodputs_list):
    """
    处理不同长度的流，并计算 SFI。

    参数：
        goodputs_list: list of 1D arrays，每个数组是一个流的 goodput 序列（时间序列）
        
    返回：
        SFI 值
    """
    # 获取所有流的最短长度
    min_len = min(len(gp) for gp in goodputs_list)
    
    # 截断所有流为相同长度，形状变为 (min_len, num_flows)
    truncated_goodputs = np.array([gp[:min_len] for gp in goodputs_list]).T
    
    # 调用之前的 SFI 函数
    return truncated_goodputs , min_len

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
    numerator = np.sum(goodputs, axis=1) ** 2
    denominator = L * np.sum(goodputs ** 2, axis=1)
    fairness_per_t = numerator / (denominator + 1e-12)
    return np.mean(fairness_per_t)

X_List =[]
Y_List=[]

n=10
GoodPut_List =[]
for i in range(1,n+1):
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

    StratTime = ReceiveTimes_List[0]
    StartBytes = Receivebytes_List[0]
    PerGoodPut_List=[]
    PerTime_List=[]
    for i in range(1,len(ReceiveTimes_List)):
        if StratTime+1 < ReceiveTimes_List[i]:
            perSecondBytes = Receivebytes_List[i]-StartBytes

            PerGoodPut_List.append((perSecondBytes*8/1000/1000)/(ReceiveTimes_List[i]-StratTime))
            PerTime_List.append(ReceiveTimes_List[i]-ReceiveTimes_List[0])
            StartBytes = Receivebytes_List[i]
            StratTime = ReceiveTimes_List[i]

    GoodPut_List.append(np.array(PerGoodPut_List))


GoodPut_List,min_len =compute_sfi_varlen(GoodPut_List)
for i in range(0,min_len):

    Y_List.append(compute_sfi(GoodPut_List[i:i+1, :]))
    X_List.append(i+1)

ax.plot(X_List,Y_List)


ax.set_ylabel('Mbps',fontsize = 30)
ax.set_xlabel('Number of flows',fontsize = 30)
ax.set_ylim(0,1.1)
ax.grid(True)
# ax.legend(fontsize=30)
plt.tick_params(labelsize=23)
plt.show()
# #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


