#!/bin/bash

# Curl 명령어로 IP 리스트 가져오기
ip_list=$(curl -s --max-time 3 -d '{"jsonrpc": "2.0", "method": "icx_call", "id": 1234, "params": {"from": "hx0000000000000000000000000000000000000000", "to": "cx0000000000000000000000000000000000000000", "dataType": "call", "data": {"method": "getPRepTerm"}}}' https://preps.net.solidwallet.io/api/v3 | jq -r '.result.preps[].p2pEndpoint | split(":")[0]')

# 테이블 헤더 출력
printf "%-24s %-14s %-12s\n" "IP Address" "Port 7100" "Port 9000"
printf "%-24s %-14s %-12s\n" "------------------" "------------" "------------"

# 포트 상태 확인 함수
check_port_status() {
    ip=$1
    port=$2
    timeout 3 bash -c "</dev/tcp/$ip/$port" >/dev/null 2>&1
    status=$?
    if [ $status -eq 0 ]; then
        echo -e "\e[32mOpen\e[0m"
    else
        echo -e "\e[31mClosed\e[0m"
    fi
}

# IP 리스트를 순회하며 포트 상태 출력
for ip in $ip_list; do
    (
        port_7100_status=$(check_port_status "$ip" 7100)
        port_9000_status=$(check_port_status "$ip" 9000)
        printf "%-24s %-23s %-22s\n" "$ip" "$port_7100_status" "$port_9000_status"
    ) &
done

# 모든 백그라운드 프로세스 완료 대기
wait
