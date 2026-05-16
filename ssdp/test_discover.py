"""ssdp/discover.py 的單元測試"""

import socket
import unittest
from unittest.mock import MagicMock, call, patch

from discover import (
    MCAST_GRP,
    MCAST_PORT,
    build_msearch_msg,
    discover,
    print_responses,
)


class TestConstants(unittest.TestCase):
    """驗證 SSDP 常數符合 UPnP 規範"""

    def test_mcast_grp(self):
        self.assertEqual(MCAST_GRP, "239.255.255.250")

    def test_mcast_port(self):
        self.assertEqual(MCAST_PORT, 1900)


class TestBuildMsearchMsg(unittest.TestCase):
    """驗證 M-SEARCH 訊息格式"""

    def test_default_message_starts_with_msearch(self):
        msg = build_msearch_msg()
        self.assertTrue(msg.startswith("M-SEARCH * HTTP/1.1"))

    def test_default_host_header(self):
        msg = build_msearch_msg()
        self.assertIn(f"HOST: {MCAST_GRP}:{MCAST_PORT}", msg)

    def test_man_header_fixed_value(self):
        msg = build_msearch_msg()
        self.assertIn('MAN: "ssdp:discover"', msg)

    def test_default_mx_value(self):
        msg = build_msearch_msg()
        self.assertIn("MX: 2", msg)

    def test_default_st_value(self):
        msg = build_msearch_msg()
        self.assertIn("ST: ssdp:all", msg)

    def test_message_uses_crlf_line_endings(self):
        msg = build_msearch_msg()
        self.assertIn("\r\n", msg)

    def test_message_ends_with_double_crlf(self):
        """HTTP 標頭結尾必須以 CRLF CRLF 結束"""
        msg = build_msearch_msg()
        self.assertTrue(msg.endswith("\r\n\r\n"))

    def test_custom_mx(self):
        msg = build_msearch_msg(mx=5)
        self.assertIn("MX: 5", msg)

    def test_custom_st(self):
        msg = build_msearch_msg(st="urn:schemas-upnp-org:device:MediaRenderer:1")
        self.assertIn("ST: urn:schemas-upnp-org:device:MediaRenderer:1", msg)

    def test_custom_host(self):
        msg = build_msearch_msg(mcast_grp="192.168.1.1", mcast_port=9999)
        self.assertIn("HOST: 192.168.1.1:9999", msg)

    def test_message_line_order(self):
        """驗證標頭順序：請求行 → HOST → MAN → MX → ST"""
        lines = build_msearch_msg().split("\r\n")
        self.assertEqual(lines[0], "M-SEARCH * HTTP/1.1")
        self.assertIn("HOST:", lines[1])
        self.assertIn("MAN:", lines[2])
        self.assertIn("MX:", lines[3])
        self.assertIn("ST:", lines[4])


class TestDiscover(unittest.TestCase):
    """驗證 discover() 的 socket 互動與回傳值"""

    def _make_mock_sock(self, responses):
        """建立模擬 socket，依序回傳 responses 後拋出 socket.timeout。

        Args:
            responses: list of (bytes, addr_tuple)
        """
        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = responses + [socket.timeout]
        return mock_sock

    @patch("discover.socket.socket")
    def test_returns_empty_list_on_immediate_timeout(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        result = discover(timeout=1)

        self.assertEqual(result, [])

    @patch("discover.socket.socket")
    def test_single_response_parsed(self, mock_socket_cls):
        raw = b"HTTP/1.1 200 OK\r\nST: ssdp:all\r\n\r\n"
        addr = ("192.168.1.10", 1900)
        mock_sock = self._make_mock_sock([(raw, addr)])
        mock_socket_cls.return_value = mock_sock

        result = discover()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["addr"], addr)
        self.assertEqual(result[0]["data"], raw.decode())

    @patch("discover.socket.socket")
    def test_multiple_responses_collected(self, mock_socket_cls):
        responses = [
            (b"HTTP/1.1 200 OK\r\n\r\n", ("192.168.1.10", 1900)),
            (b"HTTP/1.1 200 OK\r\n\r\n", ("192.168.1.11", 1900)),
            (b"HTTP/1.1 200 OK\r\n\r\n", ("192.168.1.12", 1900)),
        ]
        mock_sock = self._make_mock_sock(responses)
        mock_socket_cls.return_value = mock_sock

        result = discover()

        self.assertEqual(len(result), 3)
        addrs = [r["addr"] for r in result]
        self.assertIn(("192.168.1.10", 1900), addrs)
        self.assertIn(("192.168.1.12", 1900), addrs)

    @patch("discover.socket.socket")
    def test_socket_timeout_set_correctly(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        discover(timeout=7)

        mock_sock.settimeout.assert_called_once_with(7)

    @patch("discover.socket.socket")
    def test_msearch_sent_to_correct_address(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        discover()

        sent_data, sent_addr = mock_sock.sendto.call_args[0]
        self.assertEqual(sent_addr, (MCAST_GRP, MCAST_PORT))
        self.assertIn(b"M-SEARCH", sent_data)

    @patch("discover.socket.socket")
    def test_socket_closed_after_timeout(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        discover()

        mock_sock.close.assert_called_once()

    @patch("discover.socket.socket")
    def test_socket_closed_even_if_error_during_recv(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.recvfrom.side_effect = OSError("network error")
        mock_socket_cls.return_value = mock_sock

        with self.assertRaises(OSError):
            discover()

        mock_sock.close.assert_called_once()

    @patch("discover.socket.socket")
    def test_invalid_bytes_decoded_with_replace(self, mock_socket_cls):
        """含無效 UTF-8 字元的回應應仍被收錄（errors='ignore'）"""
        raw = b"HTTP/1.1 200 OK\r\n\xff\xfe\r\n"
        mock_sock = self._make_mock_sock([(raw, ("10.0.0.1", 1900))])
        mock_socket_cls.return_value = mock_sock

        result = discover()

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0]["data"], str)

    @patch("discover.socket.socket")
    def test_custom_mcast_grp_and_port(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        discover(mcast_grp="239.255.255.251", mcast_port=9999)

        _, sent_addr = mock_sock.sendto.call_args[0]
        self.assertEqual(sent_addr, ("239.255.255.251", 9999))

    @patch("discover.socket.socket")
    def test_udp_socket_created(self, mock_socket_cls):
        mock_sock = self._make_mock_sock([])
        mock_socket_cls.return_value = mock_sock

        discover()

        mock_socket_cls.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)


class TestPrintResponses(unittest.TestCase):
    """驗證 print_responses() 的輸出格式"""

    def test_empty_responses_prints_nothing(self):
        with patch("builtins.print") as mock_print:
            print_responses([])
            mock_print.assert_not_called()

    def test_response_addr_appears_in_output(self):
        responses = [{"addr": ("192.168.1.1", 1900), "data": "HTTP/1.1 200 OK\r\n"}]
        with patch("builtins.print") as mock_print:
            print_responses(responses)
            printed = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("192.168.1.1", printed)

    def test_response_data_appears_in_output(self):
        responses = [{"addr": ("10.0.0.1", 1900), "data": "USN: uuid:device-001"}]
        with patch("builtins.print") as mock_print:
            print_responses(responses)
            printed = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("USN: uuid:device-001", printed)

    def test_multiple_responses_all_printed(self):
        responses = [
            {"addr": ("10.0.0.1", 1900), "data": "device-A"},
            {"addr": ("10.0.0.2", 1900), "data": "device-B"},
        ]
        with patch("builtins.print") as mock_print:
            print_responses(responses)
            printed = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("device-A", printed)
            self.assertIn("device-B", printed)


if __name__ == "__main__":
    unittest.main()
