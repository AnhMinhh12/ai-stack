#!/usr/bin/env bash
set -e

echo "=== Đang khôi phục DNS mặc định từ Router ==="
nmcli connection modify "Wired connection 3" ipv4.dns ""
nmcli connection modify "Wired connection 3" ipv4.ignore-auto-dns no
nmcli connection up "Wired connection 3"

echo ""
echo "=== Kiểm tra lại cấu hình DNS hiện tại ==="
resolvectl dns enP7s7
echo "=== ĐÃ HOÀN TẤT KHÔI PHỤC ==="
