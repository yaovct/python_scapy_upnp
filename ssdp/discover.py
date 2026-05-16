# 匯入 socket 模組，用於建立 UDP 網路連線
import socket

# SSDP 使用的多播群組位址與連接埠（UPnP 標準規範）
MCAST_GRP = "239.255.255.250"
MCAST_PORT = 1900

# 建構符合 SSDP 規範的 M-SEARCH 請求訊息
# MAN: 必填標頭，固定值 "ssdp:discover"
# MX: 裝置回應前最大等待秒數（避免同時湧入大量回應）
# ST: 搜尋目標，ssdp:all 表示搜尋所有 UPnP 裝置
msg = "\r\n".join([
    'M-SEARCH * HTTP/1.1',
    f'HOST: {MCAST_GRP}:{MCAST_PORT}',
    'MAN: "ssdp:discover"',
    'MX: 2',
    'ST: ssdp:all',
    '',
    ''
])

# 建立 UDP socket（SSDP 使用 UDP 進行多播通訊）
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 設定接收逾時為 5 秒，超時後視為搜尋結束
sock.settimeout(5)

# 將 M-SEARCH 請求送往多播群組位址
sock.sendto(msg.encode(), (MCAST_GRP, MCAST_PORT))

print("Searching UPnP devices...\n")

try:
    while True:
        # 持續接收來自各 UPnP 裝置的回應（最大封包大小 65507 bytes）
        data, addr = sock.recvfrom(65507)
        print(f"=== Response from {addr} ===")
        # 解碼回應內容並印出（忽略無法解碼的字元）
        print(data.decode(errors="ignore"))
        print()
except socket.timeout:
    # 超過等待時間，搜尋結束
    print("Done.")