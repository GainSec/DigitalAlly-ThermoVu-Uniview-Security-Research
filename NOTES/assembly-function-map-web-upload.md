# Assembly Function Map: Web GUI Photo Upload Flow

**Device:** Digital Ally DTM-600 ThermoVu
**Analysis Date:** 2026-01-12
**Status:** In Progress - Static analysis from strings/symbols

---

## Pipeline Summary

```
Web Browser → HTTP POST → main.cgi → IPC → mwareserver → OpenCV decode →
NNIE inference → libFaceAnalyzeSystemAPI.so → Template storage
```

---

## 1. Entry Point: Web GUI JavaScript

**File:** `/www/script/PTS/pts_faceStaffEdit.2b91ffc3.js`

### Upload Flow (from JS analysis)
```javascript
// Key LAPI endpoints
LAPI_URL.PeopleLibsAddPerson.replace("ID", libId)
// Resolves to: /LAPI/PeopleLibraries/{LibID}/People

// Image data sent as base64 in JSON:
{
  PersonInfoList: [{
    ImageList: [{
      FaceID: 0,
      Data: "<base64 encoded JPEG>",
      Size: <bytes>,
      Type: 1
    }]
  }]
}

// Result codes checked:
FaceImportStatus.Success
FaceImportStatus.FaceDetectionFail
FaceImportStatus.FaceNotDetected
FaceImportStatus.DecodingFail
FaceImportStatus.InsufficientQuality
```

---

## 2. CGI Handler: main.cgi

**Binary:** `/program/www/cgi-bin/main.cgi`
**Type:** ELF 32-bit LSB executable, ARM, EABI5
**Size:** Small (CGI wrapper)

### Known Strings (for function location)
- `"PeopleLibraries"`
- `"PersonInfoList"`
- `"ImageList"`
- `"FaceList"`
- `"LAPI"`

### Expected Functions (to locate via strings)
```
main()                    → CGI entry point
LAPI_RouteRequest()       → URL routing
LAPI_HandlePeopleLibs()   → /PeopleLibraries handler
ParseJSON_PersonInfo()    → JSON parsing
Base64Decode()            → Image decoding
IPC_SendToMwareserver()   → Forward to main process
```

**TODO:** Disassemble main.cgi to find exact function addresses

---

## 3. IPC Layer: BP_PACS_* Functions

**Binary:** `/program/bin/mwareserver` (6.3 MB)
**Type:** ELF 32-bit LSB executable, ARM, EABI5

### Identified Functions (from strings)
| Function Name | Purpose | Location |
|---------------|---------|----------|
| `BP_PACS_ParseImage` | Parse uploaded image data | TBD |
| `BP_PACS_SetLAPIWritePipe` | Setup IPC pipe to LAPI | TBD |
| `BP_PACS_GetLAPIWritePipe` | Get IPC pipe handle | TBD |
| `BP_PACS_GetLAPISem` | Get LAPI semaphore | TBD |
| `BP_ACS_IsJpegFile` | Validate JPEG magic bytes | TBD |
| `BP_ACS_SpaceDecode` | Decode spaces in URLs | TBD |

### Related Strings (for cross-reference)
```
"BP_PACS_SetLAPIWritePipe"
"BP_PACS_GetLAPIWritePipe"
"BP_PACS_GetLAPISem"
"BP_ACS_IsJpegFile"
"GetFaceLibCfg Fail"
"pstFaceLibCfg is null"
"/data/WorkLibFile"
"MWare/ACS/PeopleLibraries/DatabaseInfo/DatabaseList/FaceLibInfo%lu"
```

### IPC Message Types
```
MW_CMD_PACS_IOCONTROL        → ACS control commands
MW_CMD_LAPI_CAP_INFO         → Capability info
MW_CMD_LAPI_PTZ_CFG          → PTZ configuration
```

### IPC Send/Receive Functions
```
BP_SendAsyncMsg()            → Async message send
BP_SendSyncGetMsg()          → Sync request/response
BP_RecvMsg()                 → Message reception
BP_SendResponseMsg()         → Response to requests
BP_SendCmdProcRes()          → Command result
```

---

## 4. Image Decode: OpenCV 3.4

**Library:** `/program/lib/libopencv_imgcodecs.so.3.4`

### Key Functions (from imports)
```cpp
cv::imdecode()              // Main JPEG decode - buffer to cv::Mat
cv::imread()                // File-based read
```

### Expected Call Sequence
```
1. BP_ACS_IsJpegFile(buffer, len)    // Check JPEG magic
2. malloc(sizeof(cv::Mat))            // Allocate output
3. cv::imdecode(buffer, IMREAD_COLOR) // Decode JPEG → BGR Mat
4. Check Mat.data != NULL             // Verify decode success
```

**Image Format:**
- Input: Raw JPEG (from base64 decoded)
- Output: cv::Mat (BGR, CV_8UC3)
- Dimensions: From JPEG header

---

## 5. Face Analysis: libFaceAnalyzeSystemAPI.so

**Binary:** `/program/lib/libFaceAnalyzeSystemAPI.so` (2.4 MB)
**Type:** ELF 32-bit LSB shared object, ARM, EABI5
**Note:** Section headers corrupted at offset 2637580

### Exported Functions (from strings at offsets)

| Function | String Offset | Log Messages |
|----------|---------------|--------------|
| `ISF_UVFACE_GlobalInit` | 0x835d | - |
| `ISF_UVFACE_GlobalRelease` | 0x8643 | - |
| `ISF_UVFACE_ParamInit` | 0x8e69 | - |
| `ISF_UVFACE_GetCapInit` | 0x892e | "Params is NULL!" @ 0x1e9bc3 |
| `ISF_UVFACE_GetVersion` | 0x8997 | - |
| `ISF_UVFACE_PushFrame2` | 0x865c | "start." @ 0x1e95b7, "end." @ 0x1e9b57 |
| `ISF_UVFACE_FeatureCompare` | 0x8a1a | "is start." @ 0x1ea117, "is end." @ 0x1ea1c3 |
| `ISF_UVFACE_FeatureCompare2` | 0x8a34 | "is start." @ 0x1ea1e7 |
| `ISF_UVFACE_Modify_Feature_Library` | 0x89c0 | "start." @ 0x1e9f1f, "end." @ 0x1ea00b |
| `ISF_UVFACE_Get_topK_feature` | 0x89fe | "is start." @ 0x1ea0c3 |
| `ISF_UVFACE_Destroy` | 0x89ad | "Start." @ 0x1e9ec7 |

### Function Signatures (from strings)
```c
// From log message strings
L32 ISF_UVFACE_FeatureCompare(pV, pV, UL32, FL*)     // @ 0x1e927f
L32 ISF_UVFACE_FeatureCompare2(S8*, FL*, S8*, UL32, FL*)  // @ 0x1e92b7

// Interpreted as:
int32_t ISF_UVFACE_FeatureCompare(
    void* pVec1,        // First feature vector
    void* pVec2,        // Second feature vector
    uint32_t dimension, // Vector dimension (256)
    float* pScore       // Output similarity score
);
```

### Error Strings (for call tracing)
```
"ISF_UVFACE_PushFrame params.pstInputImage is NULL!" @ 0x1e95d7
"ISF_UVFACE_PushFrame params.pvHandle is NULL!" @ 0x1e960b
"ISF_UVFACE_PushFrame() failed: Does not support eWorkType: ISF_UVFACE_WT_RG_COMPLEX" @ 0x1e9a7f
"ISF_UVFACE_FeatureCompare params is NULL!" @ 0x1ea13b
"ISF_UVFACE_FeatureCompare failed..." @ 0x1ea18f
"feature check value:" @ 0x1e9f47
"feature data exception!" @ 0x1e9f87
"feature damaged:" @ 0x1e9f9f
```

### C++ Mangled Symbols (internal)
```
_ZN3isf3HPC2FS14FeatureCompareEPKvS3_iRf  @ 0x5b68
// Demangles to: isf::HPC2FS::FeatureCompare(void const*, void const*, int, float&)

_ZN3isf3HPC2FS22GetRecModelFeatureSizeEv
// Demangles to: isf::HPC2FS::GetRecModelFeatureSize()
```

---

## 6. Template Storage

### File Paths (from strings)
```
/data/WorkLibFile/%lu/bmp
/data/WorkLibFile/%lu/bmp/Bmp.binary
/data/tmp/LibFile/%lu/MemberLib.bin
/data/tmp/LibFile/%lu/FeatureLib.bin
/data/tmp/Feature/%lu/FeatureLib.bin
/data/tmp/Feature/%lu/MemberLib.bin
/data/tmp/Feature/%lu/bmp/Bmp.binary
/data/PassRecord/PassRecordIndex.bin
```

### Template Format
```
Path: /data/WorkLibFile/<LibID>/PersonID_*/FaceID_*.bin
Size: 1044 bytes
Structure:
  [0x00-0x13] Header (20 bytes): 03 00 00 00 02 00 00 f0 00 00 00 00 01 00 00 f0 00 00 00 00
  [0x14-0x413] Feature vector (1024 bytes): 256 little-endian floats, unit-normalized
```

---

## 7. NNIE Inference Pipeline

### Model Sequence for Face Enrollment
```
1. faceDetect_yolo_h512_w288_r37_3516x  → Detect face bbox
2. faceAlign5_Model_r37_3516x           → 5-point alignment
3. Quality_Angle_71000_005_r37_3516x    → Quality check
4. faceRec_4110_fc256_Model_r37_3516x   → Extract 256-dim feature
```

### TensorEngine Libraries
- `libTensorEngine.so` - Main interface
- `libTensorEngineModuleHisi.so` - HiSilicon NNIE backend
- `libTensorEnginePreprocess.so` - Image preprocessing
- `libTensorEngineCore.so` - Core inference

---

## 8. Complete Call Flow (Expected)

```
[Browser]
    │
    ▼ HTTP POST /LAPI/PeopleLibraries/{ID}/People
[main.cgi]
    │ Parse JSON
    │ Base64 decode image
    │
    ▼ IPC message (BP_SendAsyncMsg)
[mwareserver]
    │
    ├─► BP_PACS_ParseImage(buffer, len)
    │       └─► BP_ACS_IsJpegFile(buffer, len)
    │
    ├─► cv::imdecode(buffer, IMREAD_COLOR)
    │
    ├─► TensorEngine preprocessing
    │       └─► cv::resize() to model input size
    │
    ├─► NNIE inference (libTensorEngineModuleHisi.so)
    │       ├─► faceDetect_yolo
    │       ├─► faceAlign5
    │       ├─► Quality_Angle
    │       └─► faceRec_4110_fc256 → 256-dim vector
    │
    ├─► ISF_UVFACE_Modify_Feature_Library()
    │       └─► Write /data/WorkLibFile/<LibID>/PersonID_*/FaceID_*.bin
    │
    └─► Send response (BP_SendResponseMsg)
[main.cgi]
    │
    ▼ HTTP Response (JSON with result code)
[Browser]
```

---

## 9. Required for Full Disassembly

### Tools Needed
1. **Ghidra** with ARM support - Import binaries
2. **Cross-compiled strace** - Upload to device for live tracing
3. **gdbserver** - For breakpoint debugging

### Analysis Steps
1. Import mwareserver into Ghidra
2. Search for strings: "BP_PACS_ParseImage", "BP_ACS_IsJpegFile"
3. Find cross-references to locate functions
4. Document full disassembly for each function
5. Upload strace to device, trace actual enrollment
6. Correlate live trace with static analysis

### Missing Information
- [ ] Exact function addresses in mwareserver
- [ ] Complete disassembly of BP_PACS_ParseImage
- [ ] IPC message format between main.cgi and mwareserver
- [ ] cv::imdecode call site in mwareserver
- [ ] Live strace output from actual upload

---

## 10. Known Vulnerabilities in This Pipeline

### Zero Template Bypass (CVE Pending)
- **Location:** `ISF_UVFACE_FeatureCompare()` in libFaceAnalyzeSystemAPI.so
- **Issue:** Zero-magnitude vector causes division by zero → returns high match score
- **Impact:** Any face matches enrolled person with 93-99% confidence
- **Details:** See `/NOTES/CVE-zero-template-bypass.md`

---

*Document Status: Partial - Awaiting full Ghidra analysis and live tracing*
