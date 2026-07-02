#!/usr/bin/env python3
"""
Landmark-aligned face morphing for DTM-600 testing.
Uses MediaPipe tasks API (0.10+) for face landmark detection.
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Download MediaPipe face landmarker model if needed
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = Path(__file__).parent / "face_landmarker.task"

def download_model():
    """Download MediaPipe face landmarker model."""
    if MODEL_PATH.exists():
        return True
    print(f"Downloading face landmarker model...")
    import urllib.request
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"Downloaded to {MODEL_PATH}")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False

def get_landmarks(image_path):
    """Extract 468 face landmarks using MediaPipe tasks API."""
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    # Create face landmarker
    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1
    )

    detector = vision.FaceLandmarker.create_from_options(options)

    # Load and process image
    image = mp.Image.create_from_file(image_path)
    result = detector.detect(image)

    if not result.face_landmarks:
        print(f"No face detected in {image_path}")
        return None

    # Convert to numpy array of (x, y) pixel coordinates
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    landmarks = []
    for lm in result.face_landmarks[0]:
        x = int(lm.x * w)
        y = int(lm.y * h)
        landmarks.append((x, y))

    return np.array(landmarks, dtype=np.float32)

def get_delaunay_triangles(landmarks, img_shape):
    """Compute Delaunay triangulation for landmarks."""
    h, w = img_shape[:2]
    rect = (0, 0, w, h)
    subdiv = cv2.Subdiv2D(rect)

    # Add landmarks to subdivision
    for pt in landmarks:
        if 0 <= pt[0] < w and 0 <= pt[1] < h:
            subdiv.insert((float(pt[0]), float(pt[1])))

    # Get triangles
    triangles = subdiv.getTriangleList()

    # Convert to indices
    tri_indices = []
    for t in triangles:
        pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        indices = []
        for px, py in pts:
            for i, (lx, ly) in enumerate(landmarks):
                if abs(px - lx) < 1 and abs(py - ly) < 1:
                    indices.append(i)
                    break
        if len(indices) == 3:
            tri_indices.append(indices)

    return tri_indices

def warp_triangle(img1, img2, t1, t2):
    """Warp triangle from img1 to img2."""
    # Bounding rectangles
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))

    # Offset points
    t1_rect = [(t1[i][0] - r1[0], t1[i][1] - r1[1]) for i in range(3)]
    t2_rect = [(t2[i][0] - r2[0], t2[i][1] - r2[1]) for i in range(3)]

    # Get mask
    mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2_rect), (1.0, 1.0, 1.0))

    # Warp triangle
    img1_rect = img1[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
    if img1_rect.size == 0:
        return

    warp_mat = cv2.getAffineTransform(np.float32(t1_rect), np.float32(t2_rect))
    img2_rect = cv2.warpAffine(img1_rect, warp_mat, (r2[2], r2[3]),
                                borderMode=cv2.BORDER_REFLECT_101)

    # Apply to output
    img2_rect = img2_rect * mask

    # Blend into output
    y1, y2 = r2[1], r2[1] + r2[3]
    x1, x2 = r2[0], r2[0] + r2[2]
    if y2 <= img2.shape[0] and x2 <= img2.shape[1]:
        img2[y1:y2, x1:x2] = img2[y1:y2, x1:x2] * (1 - mask) + img2_rect

def morph_faces(img1_path, img2_path, alpha, output_path):
    """
    Create morphed face between two images.

    alpha = 0.0 -> img1 (user face)
    alpha = 1.0 -> img2 (cover face)
    alpha = 0.5 -> 50/50 geometric blend

    For bypass: we want mostly cover appearance (high alpha)
    but some user face features blended in (low user weight in geometry)
    """
    # Load images
    img1 = cv2.imread(img1_path).astype(np.float32)
    img2 = cv2.imread(img2_path).astype(np.float32)

    # Resize to match if needed
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Get landmarks
    lm1 = get_landmarks(img1_path)
    lm2 = get_landmarks(img2_path)

    if lm1 is None or lm2 is None:
        print("Failed to detect landmarks")
        return False

    # Compute morphed landmarks (weighted average)
    lm_morphed = (1 - alpha) * lm1 + alpha * lm2

    # Get triangulation from morphed landmarks
    triangles = get_delaunay_triangles(lm_morphed, img1.shape)

    # Create output image
    output = np.zeros_like(img1)

    # Warp both images to morphed landmarks and blend
    img1_warped = np.zeros_like(img1)
    img2_warped = np.zeros_like(img2)

    for tri in triangles:
        i, j, k = tri

        # Triangle vertices in each image
        t1 = [lm1[i], lm1[j], lm1[k]]
        t2 = [lm2[i], lm2[j], lm2[k]]
        t_morph = [lm_morphed[i], lm_morphed[j], lm_morphed[k]]

        # Warp triangles to morphed position
        warp_triangle(img1, img1_warped, t1, t_morph)
        warp_triangle(img2, img2_warped, t2, t_morph)

    # Blend warped images (same alpha for pixel blend)
    output = (1 - alpha) * img1_warped + alpha * img2_warped

    # Save result
    cv2.imwrite(output_path, output.astype(np.uint8))
    print(f"Created morph at alpha={alpha}: {output_path}")
    return True

def generate_morph_series(user_face, cover_face, output_dir, alphas=None):
    """Generate series of morphs at different alpha values."""
    if alphas is None:
        # For bypass testing: we want mostly cover face appearance
        # but maybe user geometry influences the embedding
        alphas = [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    results = []
    for alpha in alphas:
        pct = int(alpha * 100)
        output_path = output_dir / f"morph_cover{pct:02d}pct.jpg"
        if morph_faces(user_face, cover_face, alpha, str(output_path)):
            results.append((alpha, output_path))

    return results

def create_import_csv(morph_dir, csv_path, start_id=91001):
    """Create batch import CSV for morphed faces."""
    morph_dir = Path(morph_dir)
    csv_path = Path(csv_path)

    # Get all morph images
    morphs = sorted(morph_dir.glob("morph_*.jpg"))

    lines = [
        '"Required Fields","Required Fields","Picture Path","Card Type","Card No.","Card Type","Card No.","Effective Time","Expiration Time","Template Name","Comment"',
        '*No.,*Name,Face Picture,Card Type 1,Card No. 1,Card Type 2,Card No. 2,Effective Time,Expiration Time,Time Template Name,Comment'
    ]

    for i, morph in enumerate(morphs):
        person_id = start_id + i
        name = morph.stem  # morph_cover95pct etc
        lines.append(f'{person_id},{name},{morph.absolute()},,,,,,,,landmark_morph')

    csv_path.write_text('\n'.join(lines) + '\n')
    print(f"Created {csv_path} with {len(morphs)} entries")

if __name__ == "__main__":
    # Ensure model is downloaded
    if not download_model():
        print("Cannot proceed without face landmarker model")
        sys.exit(1)

    # Paths
    project_dir = Path(__file__).parent.parent
    user_face = project_dir / "my_face_from_device.jpg"
    cover_face = project_dir / "man-cover.jpg"
    output_dir = project_dir / "LANDMARK_MORPH"
    csv_path = project_dir / "landmark_morph_import.csv"

    if not user_face.exists():
        print(f"User face not found: {user_face}")
        sys.exit(1)
    if not cover_face.exists():
        print(f"Cover face not found: {cover_face}")
        sys.exit(1)

    print(f"User face: {user_face}")
    print(f"Cover face: {cover_face}")
    print(f"Output dir: {output_dir}")

    # Generate morphs
    results = generate_morph_series(str(user_face), str(cover_face), str(output_dir))

    if results:
        # Create import CSV
        create_import_csv(output_dir, csv_path)
        print(f"\nGenerated {len(results)} morph images")
        print(f"Import CSV: {csv_path}")
    else:
        print("No morphs generated - check face detection")
