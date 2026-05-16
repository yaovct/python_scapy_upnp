# 匯入 requests 模組，用於發送 HTTP POST 請求
import requests

# 路由器的 UPnP SOAP 控制端點 URL
# 請依實際路由器的 UPnP 描述檔（XML）調整此路徑
control_url = "http://192.168.1.1:49000/control/WANIPConn1"

# 建構 SOAP 請求主體（XML 格式）
# 呼叫 WANIPConnection:1 服務的 GetExternalIPAddress 動作
# 以取得路由器目前的 WAN 外部 IP 位址
soap_body = """<?xml version="1.0"?>
<s:Envelope
 xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
 s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">

<s:Body>
<u:GetExternalIPAddress
 xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
</u:GetExternalIPAddress>
</s:Body>

</s:Envelope>
"""

# 設定 HTTP 標頭
# SOAPAction：指定要呼叫的 UPnP 服務動作（必填）
# Content-Type：SOAP 請求固定使用 text/xml
headers = {
    "SOAPAction":
        '"urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"',
    "Content-Type": "text/xml"
}

# 發送 HTTP POST 請求至路由器控制端點
r = requests.post(
    control_url,
    data=soap_body,
    headers=headers
)

# 印出路由器回傳的 SOAP XML 回應（包含外部 IP 位址）
print(r.text)
