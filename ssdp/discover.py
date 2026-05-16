# 匯入 socket 模組，用於建立 UDP 網路連線
import socket

# SSDP 使用的多播群組位址與連接埠（UPnP 標準規範）
MCAST_GRP = "239.255.255.250"
MCAST_PORT = 1900


def build_msearch_msg(mcast_grp: str = MCAST_GRP, mcast_port: int = MCAST_PORT, mx: int = 2, st: str = "ssdp:all") -> str:
    """建構符合 SSDP 規範的 M-SEARCH 請求訊息。

    Args:
        mcast_grp: 多播群組位址
        mcast_port: 多播連接埠
        mx: 裝置回應前最大等待秒數
        st: 搜尋目標（Search Target）

    Returns:
        SSDP M-SEARCH 請求字串
    """
    return "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        f'HOST: {mcast_grp}:{mcast_port}',
        'MAN: "ssdp:discover"',
        f'MX: {mx}',
        f'ST: {st}',
        '',
        ''
    ])


def discover(timeout: int = 5, mcast_grp: str = MCAST_GRP, mcast_port: int = MCAST_PORT) -> list[dict]:
    """送出 SSDP M-SEARCH 並收集裝置回應。

    Args:
        timeout: 等待回應的逾時秒數
        mcast_grp: 多播群組位址
        mcast_port: 多播連接埠

    Returns:
        list of dict，每個元素包含 'addr' (來源位址 tuple) 與 'data' (回應內容字串)
    """
    msg = build_msearch_msg(mcast_grp, mcast_port)

    # 建立 UDP socket（SSDP 使用 UDP 進行多播通訊）
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    responses = []
    try:
        # 將 M-SEARCH 請求送往多播群組位址
        sock.sendto(msg.encode(), (mcast_grp, mcast_port))

        while True:
            # 持續接收來自各 UPnP 裝置的回應（最大封包大小 65507 bytes）
            data, addr = sock.recvfrom(65507)
            responses.append({"addr": addr, "data": data.decode(errors="ignore")})
    except socket.timeout:
        pass
    finally:
        sock.close()

    return responses


def print_responses(responses: list[dict]) -> None:
    """將裝置回應列印至標準輸出。

    Args:
        responses: discover() 回傳的回應清單
    """
    for resp in responses:
        print(f"=== Response from {resp['addr']} ===")
        print(resp["data"])
        print()


if __name__ == "__main__":
    print("Searching UPnP devices...\n")
    results = discover()
    print_responses(results)
    print("Done.")