#!/bin/bash
# 포트 7892에 HTTP 서버 실행
kill $(lsof -ti:7892) 2>/dev/null || true
cd "/Users/choi_ai/Library/CloudStorage/Dropbox/02-프로젝트렌트RENT/02_Project-ING/2026/글로벌K존_유니원"
python3 -m http.server 7892 &
echo $! > /tmp/playwright-server.pid
sleep 2
echo "Server started on port 7892"
