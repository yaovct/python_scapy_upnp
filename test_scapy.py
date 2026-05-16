# 匯入 Scapy 所有模組（封包建構、傳送、擷取等功能）
from scapy.all import *

# 建構一個目的地為 8.8.8.8（Google DNS）的 IP/ICMP 封包
pkt = IP(dst="8.8.8.8")/ICMP()

# 送出封包並等待回應，timeout=2 表示最多等待 2 秒
reply = sr1(pkt, timeout=2)

# 印出回應封包的摘要資訊（來源 IP、協定、TTL 等）
print(reply.summary())
