#!/usr/bin/env bash
set -e

echo "=== Đang đổi DNS sang Google DNS (8.8.8.8) và Cloudflare (1.1.1.1) ==="
nmcli connection modify "Wired connection 3" ipv4.dns "8.8.8.8 1.1.1.1"
nmcli connection modify "Wired connection 3" ipv4.ignore-auto-dns yes
nmcli connection modify "Wired connection 3" ipv4.dns-priority -10
nmcli connection up "Wired connection 3"

echo ""
echo "=== Kiểm tra lại cấu hình DNS hiện tại ==="
resolvectl dns enP7s7
echo "=== ĐÃ HOÀN TẤT ==="
