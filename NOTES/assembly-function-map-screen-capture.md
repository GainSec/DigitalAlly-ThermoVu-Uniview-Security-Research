# Assembly Function Map: Device Screen Face Capture Flow

**Device:** Digital Ally DTM-600 ThermoVu
**Analysis Date:** 2026-01-12
**Status:** In Progress - Static analysis from strings/symbols

---

## Pipeline Summary

```
Touchscreen → mmi_client → IPC → mwareserver → VI capture →
NNIE inference → libFaceAnalyzeSystemAPI.so → Template storage
```

---

## 1. Entry Point: mmi_client Touch Handler

**Binary:** `/program/bin/mmi_client` (5.9 MB)
**Type:** ELF 32-bit LSB executable, ARM, EABI5

### GUI Framework (from strings)
```
DGUI_RegisterTouchMsgHook    → Register touch event handler
DGUI_RegisterKeyMsgHook      → Register key event handler
DGUI_RegisterMouseMsgHook    → Register mouse handler
DGUI_RegisterWindowClass     → Window class registration
DGUI_RegisterIMEWindow       → IME window registration
DGUI_DskRegisterTouchHook    → Desktop touch hook
```

### Message Types
```
MSG_REGISTERTOUCHHOOK        → Touch hook registration message
MSG_REGISTERKEYHOOK          → Key hook registration message
MSG_REGISTERMOUSEHOOK        → Mouse hook registration message
MSG_REGISTERWNDCLASS         → Window class registration
MSG_UNREGISTERWNDCLASS       → Window class unregistration
MSG_IME_REGISTER             → IME registration
MSG_IME_UNREGISTER           → IME unregistration
```

### Expected Enrollment Flow
```
1. User touches "Enroll" button on screen
2. Touch handler receives MSG_TOUCH event
3. Handler constructs IPC message to mwareserver
4. mwareserver triggers camera capture
5. Face detection/enrollment proceeds
6. Result displayed on screen
```

---

## 2. IPC Communication: mmi_client → mwareserver

### IPC Functions (from strings)
```
// In mmi_client
SendMsgToMwareserver()       → Send command to mwareserver
RecvMsgFromMwareserver()     → Receive response

// Message construction
MW_CMD_* message types       → Same as web upload
```

### Expected Message Types for Enrollment
```
MW_CMD_PACS_IOCONTROL        → ACS control (likely enrollment trigger)
MW_CMD_ACS_*                 → ACS-specific commands
```

---

## 3. Camera Capture: VI Subsystem

### Kernel Module
**File:** `/program/lib/modules/4.9.37/extra/hi3516cv500_vi.ko`

### User-space Interface (from mwareserver strings)
```
// VI-related strings in mwareserver
"vi_cap"
"VI_CreateChn"
"VI_GetFrame"
```

### Expected Functions in mwareserver
```
VI_Init()                    → Initialize VI subsystem
VI_CreateChn()               → Create capture channel
VI_StartChn()                → Start capture
VI_GetFrame()                → Get frame buffer
VI_ReleaseFrame()            → Release frame buffer
```

### Frame Buffer Path
```
/dev/mmz_userdev             → Memory mapped zone for frame buffers
```

---

## 4. Device Files (from mwareserver_maps.log)

### Memory-Mapped Devices
```
/dev/mmz_userdev             → Frame buffers, inference buffers
/dev/venc                    → Video encoder
/dev/mem                     → Physical memory access
/dev/sys                     → System interface
/tmp/threadRunStutas         → Thread status (shared memory)
```

---

## 5. Frame Processing (Same as Web Upload)

Once frame is captured from VI, the processing is identical:

```
[VI Frame Capture]
    │
    ▼
[Image Preprocessing]
    │ libTensorEnginePreprocess.so
    │ libopencv_imgproc.so.3.4 → cv::resize()
    │
    ▼
[NNIE Inference Pipeline]
    │ libTensorEngineModuleHisi.so
    │ hi3516cv500_nnie.ko
    │
    ├─► faceDetect_yolo_h512_w288_r37_3516x
    ├─► faceAlign5_Model_r37_3516x
    ├─► Quality_Angle_71000_005_r37_3516x
    └─► faceRec_4110_fc256_Model_r37_3516x
    │
    ▼
[Feature Extraction]
    │ 256-dimensional float vector
    │
    ▼
[Template Storage]
    │ ISF_UVFACE_Modify_Feature_Library()
    │ /data/WorkLibFile/<LibID>/PersonID_*/FaceID_*.bin
    │
    ▼
[Response to mmi_client]
    │ Display result on screen
    └─► Audio prompt (PcmSource/*.pcm)
```

---

## 6. Differences from Web Upload Flow

| Aspect | Web Upload | Screen Capture |
|--------|------------|----------------|
| Entry Point | main.cgi | mmi_client touch handler |
| Image Source | Base64 JPEG in JSON | Live VI frame |
| Image Format | Compressed JPEG | Raw YUV/RGB frame |
| Decode Step | cv::imdecode() | Direct from VI buffer |
| Trigger | HTTP POST | Touch event |
| Response | HTTP JSON | Screen update + audio |

---

## 7. mmi_client Binary Analysis

### Key Strings to Search
```
"Enroll"
"Capture"
"Face"
"Registration"
"MW_CMD_"
"SendMsg"
"RecvMsg"
```

### Expected Function Flow
```c
// Pseudo-code based on string analysis

void OnEnrollButtonPress() {
    // Construct IPC message
    MW_CMD_MSG msg;
    msg.cmd = MW_CMD_PACS_ENROLL;  // or similar

    // Send to mwareserver
    BP_SendAsyncMsg(&msg);

    // Wait for response
    // Update UI
}
```

---

## 8. Audio Prompts (from filesystem)

**Location:** `/program/PcmSource/`

### Enrollment-related audio files
```
Access.pcm                   → Access granted
Fail.pcm                     → Operation failed
Welcome.pcm                  → Welcome message
NoLiveness.pcm               → Liveness check failed
Tmp_Abnormal.pcm             → Temperature abnormal
```

---

## 9. Complete Call Flow (Expected)

```
[User Touch Screen]
    │
    ▼ Touch event
[mmi_client]
    │
    ├─► OnEnrollTouchHandler()
    │       └─► Parse touch coordinates
    │       └─► Identify "Enroll" button
    │
    ├─► ConstructEnrollMessage()
    │       └─► Create MW_CMD_PACS_* message
    │
    ▼ IPC (pipe/socket)
[mwareserver]
    │
    ├─► ReceiveIPCMessage()
    │       └─► Dispatch to handler
    │
    ├─► StartFaceCapture()
    │       └─► VI_GetFrame()
    │       └─► Copy frame to processing buffer
    │
    ├─► ProcessFaceFrame()
    │       └─► TensorEngine preprocessing
    │       └─► NNIE inference pipeline
    │       └─► Extract 256-dim feature vector
    │
    ├─► ISF_UVFACE_Modify_Feature_Library()
    │       └─► Validate feature vector
    │       └─► Write template to /data/WorkLibFile/
    │
    ├─► SendEnrollResult()
    │       └─► BP_SendResponseMsg()
    │
    ▼ IPC response
[mmi_client]
    │
    ├─► OnEnrollComplete()
    │       └─► Update display (success/fail)
    │       └─► Play audio prompt
    │
    └─► Return to idle state
```

---

## 10. Required for Full Disassembly

### Specific Analysis Tasks
1. **mmi_client touch handler**
   - Find DGUI_RegisterTouchMsgHook registration
   - Locate enrollment button handler
   - Trace IPC message construction

2. **mwareserver VI interface**
   - Find VI_GetFrame calls
   - Trace frame buffer handling
   - Map transition to face processing

3. **Live tracing**
   - Trigger enrollment via screen
   - Capture syscalls/library calls
   - Map to static analysis

### Tools Needed
- Cross-compiled strace for ARM
- gdbserver for live debugging
- Ghidra for static analysis

### Missing Information
- [ ] Exact touch handler function address
- [ ] IPC message format for enrollment
- [ ] VI capture function addresses
- [ ] Frame buffer format (YUV420? RGB?)
- [ ] Live trace output from actual capture

---

## 11. Key Differences from Recognition Flow

Note: This document covers **enrollment** (adding a new face).
The **recognition** flow (matching against enrolled faces) is different:

### Recognition Flow (for comparison)
```
Live VI frames → Face detection → Feature extraction →
ISF_UVFACE_FeatureCompare() → Access decision
```

The recognition flow continuously processes frames and compares against enrolled templates, while enrollment only runs when triggered and stores a new template.

---

*Document Status: Partial - Awaiting mmi_client analysis and live tracing*
