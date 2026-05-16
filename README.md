# python-scapy-upnp

使用 Python 進行 UPnP 探索、SOAP 控制及網路封包分析的實驗性專案，結合 Scapy 與 socket/requests 等標準工具。

---

## 專案結構

```
python_scapy_upnp/
├── requirements.txt        # 相依套件清單
├── test_scapy.py           # Scapy 基本測試：送出 ICMP Ping 並印出回應
├── captures/               # 封包擷取檔存放目錄（.pcap 等）
├── ssdp/
│   ├── discover.py         # SSDP M-SEARCH：掃描區域網路內的 UPnP 裝置
│   └── parser.py           # ARP 封包監聽：使用 Scapy 偵測 ARP Spoofing
└── soap/
    └── winip.py            # SOAP 請求：向路由器查詢 WAN 外部 IP 位址
```

---

## 功能說明

### `test_scapy.py` — Scapy ICMP 測試
使用 Scapy 建構 IP/ICMP 封包並送往 `8.8.8.8`，印出回應摘要，用於確認 Scapy 環境是否正常運作。

### `ssdp/discover.py` — UPnP 裝置探索
透過 SSDP（Simple Service Discovery Protocol）向多播位址 `239.255.255.250:1900` 發送 `M-SEARCH` 請求，列出區域網路內所有回應的 UPnP 裝置。

### `ssdp/parser.py` — ARP Spoofing 偵測
使用 Scapy 監聽網路上的 ARP 回應封包（`op == 2`），維護一份 IP→MAC 對應表，當同一 IP 出現不同 MAC 時發出警告，用於偵測潛在的 ARP 欺騙攻擊。

### `soap/winip.py` — SOAP 查詢外部 IP
對路由器（預設 `192.168.1.1:49000`）發送 UPnP SOAP 請求，呼叫 `WANIPConnection:1#GetExternalIPAddress` 取得 WAN 外部 IP 位址。

---

## 環境需求

- Python 3.8+
- 建議使用虛擬環境（`.venv`）

### 安裝相依套件

```bash
pip install -r requirements.txt
```

主要套件：

| 套件 | 版本 | 用途 |
|------|------|------|
| scapy | 2.7.0 | 封包建構與擷取 |
| requests | 2.34.2 | SOAP HTTP 請求 |
| miniupnpc | 2.3.3 | UPnP 客戶端工具庫 |
| lxml | 6.1.0 | XML 解析 |

---

## 使用方式

> **注意：** Scapy 及 ARP 監聽相關功能需要系統管理員（Administrator / root）權限。

### 測試 Scapy 封包傳送

```bash
python test_scapy.py
```

### 掃描 UPnP 裝置

```bash
python ssdp/discover.py
```

### 啟動 ARP Spoofing 偵測

```bash
# 需要管理員權限
python ssdp/parser.py
```

### 查詢路由器外部 IP

編輯 `soap/winip.py` 中的 `control_url`，將其改為你的路由器實際 UPnP 控制端點，然後執行：

```bash
python soap/winip.py
```

---

## 注意事項

- ARP 監聽及原始封包操作需要**管理員/root 權限**。
- `soap/winip.py` 中的 `control_url` 預設為 `192.168.1.1`，請依實際環境修改。
- `captures/` 目錄可用於存放以 Scapy `wrpcap()` 儲存的 `.pcap` 擷取檔，供後續離線分析。
- 本專案僅供學習與實驗用途，請勿用於未授權的網路環境。
