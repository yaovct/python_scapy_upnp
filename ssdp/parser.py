# 匯入 Scapy 所有模組，用於封包擷取與分析
from scapy.all import *

# 用於記錄已知的 IP → MAC 對應關係
arp_table = {}

def detect(pkt):
    """封包回調函式：分析每個擷取到的 ARP 封包"""
    # ARP op=2 代表 ARP Reply（回應），op=1 為 ARP Request（請求）
    if pkt.haslayer(ARP) and pkt[ARP].op == 2:
        # 取得 ARP 回應中宣告的來源 IP 與 MAC 位址
        ip = pkt[ARP].psrc
        mac = pkt[ARP].hwsrc

        if ip in arp_table:
            # 若同一 IP 出現不同 MAC，可能是 ARP Spoofing 攻擊
            if arp_table[ip] != mac:
                print(f"[WARNING] Possible ARP spoofing:")
                print(f"IP: {ip}")
                print(f"Old MAC: {arp_table[ip]}")
                print(f"New MAC: {mac}")
        else:
            # 首次出現此 IP，記錄至對應表
            arp_table[ip] = mac

# 開始監聽網路介面上的 ARP 封包
# filter="arp"：只擷取 ARP 協定封包
# prn=detect：每個封包都呼叫 detect() 函式處理
# store=0：不在記憶體中保留封包，節省記憶體
sniff(filter="arp", prn=detect, store=0)
