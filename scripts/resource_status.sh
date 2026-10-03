#!/usr/bin/env bash
# Quick, dependency-free resource overview for this host and its Docker stack.
# It is intentionally read-only and is safe to run as the normal server user.
set -euo pipefail

WATCH_INTERVAL=""

usage() {
	cat <<'EOF'
Usage: scripts/resource_status.sh [--watch SECONDS]

Shows a compact host, GPU, Docker and web-connection resource snapshot.
Exit status is 0 (normal), 1 (warning) or 2 (critical).
EOF
}

while (($#)); do
	case "$1" in
		--watch)
			[[ ${2:-} =~ ^[1-9][0-9]*$ ]] || { echo "--watch requires a positive number of seconds" >&2; exit 64; }
			WATCH_INTERVAL="$2"
			shift 2
			;;
		-h|--help) usage; exit 0 ;;
		*) echo "Unknown option: $1" >&2; usage >&2; exit 64 ;;
	esac
done

if [[ -n "$WATCH_INTERVAL" ]]; then
	while true; do
		clear 2>/dev/null || true
		if "$0"; then
			status=0
		else
			status=$?
		fi
		echo
		echo "Refreshing every ${WATCH_INTERVAL}s — Ctrl+C to stop"
		sleep "$WATCH_INTERVAL"
	done
fi

severity=0
label() {
	local value="$1" warn="$2" critical="$3"
	if (( value >= critical )); then
		severity=2; printf 'CRITICAL'
	elif (( value >= warn )); then
		(( severity < 1 )) && severity=1
		printf 'WARNING'
	else
		printf 'OK'
	fi
}

cpu_snapshot() {
	awk '/^cpu / { print $2+$3+$4+$5+$6+$7+$8, $5, $6 }' /proc/stat
}
read -r cpu_total_1 cpu_idle_1 cpu_iowait_1 < <(cpu_snapshot)
sleep 0.2
read -r cpu_total_2 cpu_idle_2 cpu_iowait_2 < <(cpu_snapshot)
cpu_delta=$((cpu_total_2 - cpu_total_1))
idle_delta=$((cpu_idle_2 - cpu_idle_1))
iowait_delta=$((cpu_iowait_2 - cpu_iowait_1))
cpu_used=$(( (100 * (cpu_delta - idle_delta)) / cpu_delta ))
iowait=$(( (100 * iowait_delta) / cpu_delta ))

read -r mem_total mem_available swap_total swap_free < <(
	awk '/MemTotal:/ {m=$2} /MemAvailable:/ {a=$2} /SwapTotal:/ {s=$2} /SwapFree:/ {f=$2} END {print m, a, s, f}' /proc/meminfo
)
mem_used=$(( (100 * (mem_total - mem_available)) / mem_total ))
swap_used=0
if (( swap_total > 0 )); then swap_used=$(( (100 * (swap_total - swap_free)) / swap_total )); fi

read -r disk_used disk_free < <(df -P / | awk 'NR == 2 {gsub(/%/, "", $5); print $5, $4}')
read -r load1 load5 load15 _ < /proc/loadavg
cores=$(getconf _NPROCESSORS_ONLN)
load_percent=$(awk -v load_1="$load1" -v cores="$cores" 'BEGIN { printf "%d", (load_1 * 100) / cores }')

cpu_state=$(label "$cpu_used" 75 90)
mem_state=$(label "$mem_used" 80 90)
disk_state=$(label "$disk_used" 80 90)
load_state=$(label "$load_percent" 80 100)
swap_state=$(label "$swap_used" 20 50)
iowait_state=$(label "$iowait" 10 20)

echo "Resource status — $(date -Is)"
echo "Thresholds: warning / critical = CPU 75/90%, RAM 80/90%, disk 80/90%, load 80/100% per CPU"
printf 'Host    CPU %3s%% %-8s | load %s / %s / %s (%s cores, %s%%) %-8s | iowait %2s%% %-8s\n' \
	"$cpu_used" "$cpu_state" "$load1" "$load5" "$load15" "$cores" "$load_percent" "$load_state" "$iowait" "$iowait_state"
printf 'Memory  RAM %3s%% %-8s | available %.1f GiB | swap %3s%% %-8s\n' \
	"$mem_used" "$mem_state" "$(awk -v k="$mem_available" 'BEGIN {print k/1048576}')" "$swap_used" "$swap_state"
printf 'Disk    /   %3s%% %-8s | free %.1f GiB\n' \
	"$disk_used" "$disk_state" "$(awk -v k="$disk_free" 'BEGIN {print k/1048576}')"

if command -v nvidia-smi >/dev/null 2>&1 && gpu_lines=$(nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null); then
	echo "GPU"
	while IFS=, read -r id name gpu mem_used_gpu mem_total_gpu temp; do
		gpu=$(echo "$gpu" | xargs); mem_used_gpu=$(echo "$mem_used_gpu" | xargs); mem_total_gpu=$(echo "$mem_total_gpu" | xargs); temp=$(echo "$temp" | xargs)
		[[ "$gpu" =~ ^[0-9]+$ && "$mem_used_gpu" =~ ^[0-9]+$ && "$mem_total_gpu" =~ ^[1-9][0-9]*$ ]] || continue
		gpu_mem_pct=$(( 100 * mem_used_gpu / mem_total_gpu ))
		gpu_state=$(label "$gpu" 85 95)
		gpu_mem_state=$(label "$gpu_mem_pct" 85 95)
		printf '  GPU %s: %s%% %-8s | VRAM %s/%s MiB (%s%%) %-8s | %s°C\n' "$id" "$gpu" "$gpu_state" "$mem_used_gpu" "$mem_total_gpu" "$gpu_mem_pct" "$gpu_mem_state" "$temp"
	done <<< "$gpu_lines"
else
	echo "GPU     nvidia-smi is unavailable or the NVIDIA driver is not reachable"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
	echo "Containers"
	docker stats --no-stream --format '  {{.Name}}: CPU {{.CPUPerc}} | RAM {{.MemUsage}} ({{.MemPerc}}) | NET {{.NetIO}} | restarts unavailable here' 2>/dev/null || true
else
	echo "Containers  Docker is unavailable or this user cannot access its socket"
fi

if command -v ss >/dev/null 2>&1; then
	web_connections=$(ss -Htan '( sport = :80 or sport = :443 )' 2>/dev/null | wc -l | tr -d ' ')
	printf 'Web     active TCP connections on ports 80/443: %s\n' "$web_connections"
fi

case "$severity" in
	0) echo "Overall: OK" ;;
	1) echo "Overall: WARNING — investigate if this persists for 5 minutes." ;;
	2) echo "Overall: CRITICAL — reduce load or scale/repair the constrained component." ;;
esac
exit "$severity"
