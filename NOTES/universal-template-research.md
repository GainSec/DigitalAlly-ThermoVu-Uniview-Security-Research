# Universal Template Research - DTM-600

## Goal
Find a face feature template that matches any enrolled face, bypassing authentication.

## Face Recognition Architecture

### Libraries
- **libFaceAnalyzeSystemAPI.so** (2.6MB) - Main face analysis SDK
- **libnnie.so** (39KB) - HiSilicon NNIE interface
- **BestFace.bin** (166KB) - CNN model file

### Key Functions
```
ISF_UVFACE_FeatureCompare(feature1, feature2, length, score_ptr)
ISF_UVFACE_FeatureCompare2(name1, feature1, name2, length, score_ptr)
ISF_UVFACE_Get_topK_feature(name, feature, length, results)
ISF_UVFACE_Modify_Feature_Library(...)
```

### Feature Vector
- Type: Float array (FL*)
- Size: Variable - uses `GetRecModelFeatureSizeEv`
- Likely 256 or 512 dimensions (common for face recognition)
- Stored in `/data/WorkLibFile/{libID}/` directories

### Similarity Threshold
- `MultipleValue=82` in config (82% similarity required)
- `IDFaceThreshold=60` for ID verification

---

## Attack Vectors for Universal Template

### 1. Mathematical Bypass Attempts

#### Zero Vector
```python
template = [0.0] * 256
```
- May bypass normalization (division by zero)
- May return undefined similarity score

#### All-Ones Vector
```python
template = [1.0] * 256
```
- High magnitude, may cause overflow in dot product

#### Uniform Distribution
```python
template = [1.0/sqrt(256)] * 256  # Unit vector with equal components
```
- Normalized unit vector pointing equally in all directions
- Expected cosine similarity with random unit vector: ~0

#### High Variance Extremes
```python
template = [float('inf')] * 256  # or very large values
template = [float('nan')] * 256  # NaN injection
```
- May cause comparison function to return unexpected results

### 2. Implementation Bug Exploitation

#### Length Mismatch
- Pass different length than actual vector
- May cause buffer over-read and arbitrary comparison

#### Null/Empty Checks
- Send null pointer or zero-length feature
- May bypass comparison entirely

#### Score Overflow
- If score is uint8/uint16, values > 100 may wrap to valid range

### 3. Database Poisoning

#### Enroll Universal Template
If we can enroll a face with a crafted template:
1. Create template that's "central" to feature space
2. Or create template that causes comparison bugs
3. All future comparisons may match

---

## Safe Testing Approach

### Prerequisites
1. Enable face comparison: Set `CompareEn=1` in config
2. Create test face library
3. Enroll one legitimate test face
4. Monitor for crashes during testing

### Test Procedure (Non-Destructive)

```bash
# 1. Backup config
cp /config/config_a.xml /config/config_a.xml.bak

# 2. Enable face comparison (edit config)
# Change: <CompareEn>0</CompareEn>
# To:     <CompareEn>1</CompareEn>

# 3. Restart mwareserver
killall mwareserver
/program/bin/mwareserver &

# 4. Test via LAPI (if supported) or IPC
# Try to match candidate templates against enrolled faces
```

### Candidate Template Generator

```python
import struct
import math

def generate_candidates():
    candidates = []

    # Zero vector
    candidates.append(('zero', [0.0] * 256))

    # Ones vector
    candidates.append(('ones', [1.0] * 256))

    # Normalized uniform
    val = 1.0 / math.sqrt(256)
    candidates.append(('uniform', [val] * 256))

    # Max float values
    candidates.append(('max_float', [3.4e38] * 256))

    # Negative ones
    candidates.append(('neg_ones', [-1.0] * 256))

    # Alternating
    candidates.append(('alternating', [(-1)**i for i in range(256)]))

    # NaN (careful - may crash)
    # candidates.append(('nan', [float('nan')] * 256))

    return candidates

def template_to_bytes(template):
    """Convert float list to bytes (little-endian floats)"""
    return struct.pack(f'<{len(template)}f', *template)
```

---

## Offline Analysis Approach (Safest)

### 1. Extract and Analyze Locally
```bash
# Copy library for analysis
scp root@192.168.30.178:/program/lib/libFaceAnalyzeSystemAPI.so .

# Analyze with Ghidra/IDA
# Find ISF_UVFACE_FeatureCompare implementation
# Understand normalization and comparison logic
```

### 2. QEMU Emulation
```bash
# Run comparison function in QEMU user mode
qemu-arm -L /path/to/rootfs ./test_harness candidate.bin enrolled.bin
```

### 3. Symbolic Execution
Use angr/Triton to find inputs that maximize comparison score.

---

## Risk Assessment

| Action | Risk Level | Potential Impact |
|--------|------------|------------------|
| API testing with candidates | LOW | May cause mwareserver errors |
| Config modification | LOW | Reversible, backup available |
| Template database modification | MEDIUM | May corrupt face database |
| Model file modification | HIGH | System crash (proven) |
| Library modification | HIGH | System brick |

---

## Next Steps

1. **Enable face comparison in config** (safe, reversible)
2. **Enroll test face via web UI** (if available)
3. **Test candidate templates via API**
4. **Monitor logs for score values**
5. **Extract library for offline reverse engineering**

---

## Files to Extract for Offline Analysis

```
/program/lib/libFaceAnalyzeSystemAPI.so
/program/lib/libnnie.so
/program/factory/BestFace.bin
/data/WorkLibFile/AllLibInfo.bin
/data/WorkLibFile/*/LibKeyInfo.bin
```
