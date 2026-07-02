# Digital Ally DTM-600 Face Recognition Pipeline - Complete Binary Mapping

**Device:** Digital Ally DTM-600 ThermoVu
**SoC:** HiSilicon Hi3516DV300 (ARM Cortex-A7)
**Platform:** Linux 4.9.37
**Date:** 2026-01-12

---

## Pipeline Overview

```
Camera Frame (VI) → Face Detection → Alignment → Quality Check → Liveness Check → Feature Extraction → Template Comparison → Access Decision
      ↓                    ↓              ↓            ↓               ↓                  ↓                    ↓                 ↓
 hi3516cv500_vi.ko    YOLO Model    Align Model   Quality Model  Liveness Models   faceRec Model     libFaceAnalyzeSystemAPI.so   Wiegand OUT
```

---

## 1. Main Executables

### mwareserver
| Attribute | Value |
|-----------|-------|
| **Purpose** | Main server process - orchestrates all face recognition, video, and access control |
| **Device Path** | `/program/bin/mwareserver` |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/program_factory/bin/mwareserver` |
| **Size** | 6,623,012 bytes (6.3 MB) |
| **MD5** | `504c0e0248c8c5aab11ea67182efc9d8` |
| **Type** | ELF 32-bit LSB executable, ARM, EABI5 |
| **Language** | C/C++ |

### mmi_client
| Attribute | Value |
|-----------|-------|
| **Purpose** | GUI/Display client - touchscreen UI, face detection overlay, access result display |
| **Device Path** | `/program/bin/mmi_client` |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/program_factory/bin/mmi_client` |
| **Size** | 6,169,672 bytes (5.9 MB) |
| **MD5** | `4088fb5e884aa9ec910ecda85563536a` |
| **Type** | ELF 32-bit LSB executable, ARM, EABI5 |
| **Language** | C/C++ (Qt-based) |

---

## 2. Core Face Recognition Libraries

### libFaceAnalyzeSystemAPI.so
| Attribute | Value |
|-----------|-------|
| **Purpose** | **CRITICAL** - Main face analysis API. Contains `ISF_UVFACE_FeatureCompare()` (vulnerable to zero-template bypass) |
| **Device Path** | `/program/lib/libFaceAnalyzeSystemAPI.so` |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/extracted_face_libs/libFaceAnalyzeSystemAPI.so` |
| **Size** | 2,536,901 bytes (2.4 MB) |
| **MD5** | `fe7c28db509fb17fced6e6a77d9bcd88` |
| **Type** | ELF 32-bit LSB shared object, ARM, EABI5 |
| **Language** | C++ |
| **Key Functions** | `ISF_UVFACE_FeatureCompare()`, `ISF_UVFACE_ExtractFeature()`, `ISF_UVFACE_Detect()` |

### libnnie.so
| Attribute | Value |
|-----------|-------|
| **Purpose** | NNIE (Neural Network Inference Engine) userspace interface |
| **Device Path** | `/program/lib/libnnie.so` |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/extracted_face_libs/libnnie.so` |
| **Size** | 39,220 bytes (38 KB) |
| **MD5** | `148993dbe680e38724c93bce780d900b` |
| **Type** | ELF 32-bit LSB shared object, ARM, EABI5 |
| **Language** | C |

---

## 3. TensorEngine Libraries (Neural Network Inference Stack)

### libTensorEngineModuleHisi.so
| Attribute | Value |
|-----------|-------|
| **Purpose** | HiSilicon-specific TensorEngine implementation - loads and runs NNIE models |
| **Device Path** | `/program/factory/models/TensorEngineEnv/Hisi/libTensorEngineModuleHisi.so` |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/program_factory/factory/models/TensorEngineEnv/Hisi/libTensorEngineModuleHisi.so` |
| **Size** | 4,909,576 bytes (4.7 MB) |
| **MD5** | `1bef18931fd6dd16a00f425eea6198b2` |
| **Type** | ELF 32-bit LSB shared object, ARM, EABI5 |
| **Language** | C++ |

### Additional TensorEngine Components
| Library | Device Path | Purpose |
|---------|-------------|---------|
| libTensorEngine.so | `/program/lib/libTensorEngine.so` | Main TensorEngine interface |
| libTensorEngineAlgorithm.so | `/program/lib/libTensorEngineAlgorithm.so` | Algorithm implementations |
| libTensorEngineCore.so | `/program/lib/libTensorEngineCore.so` | Core inference engine |
| libTensorEngineExecutor.so | `/program/lib/libTensorEngineExecutor.so` | Model executor |
| libTensorEngineLog.so | `/program/lib/libTensorEngineLog.so` | Logging |
| libTensorEnginePreprocess.so | `/program/lib/libTensorEnginePreprocess.so` | Image preprocessing |
| libTensorEngineScheduler.so | `/program/lib/libTensorEngineScheduler.so` | Inference scheduling |

---

## 4. Neural Network Models

All models are in HiSilicon NNIE format, compiled for Hi3516CV500 SVP (Smart Vision Platform).

| Model | Size | MD5 | Purpose |
|-------|------|-----|---------|
| **faceDetect_yolo_h512_w288_r37_3516x** | 3.1 MB | `3cd3ec466967e8e324da75f155ab9e75` | YOLO-based face detection (512x288 input) |
| **faceAlign5_Model_r37_3516x** | 422 KB | `f99c0accf0a6d7a17979c8fb24e7fd92` | 5-point facial landmark alignment |
| **Quality_Angle_71000_005_r37_3516x** | 429 KB | `8305083e79b0af3b331a4f4e97833579` | Face quality/angle assessment |
| **FaceAttr_dv300_int8_ry41_4504** | 1.7 MB | `55c95bef2802d294de72307f10c6bc1f` | Face attributes (age, gender, glasses, mask) |
| **Liveness_1frame_Model_1004_33w_merge_specify_r37_3516x** | 787 KB | `275dfb957e7160c9e9a3551973dc5761` | Single-frame anti-spoofing |
| **STM_liveness_Model_spe_r37_3516x** | 1.5 MB | `32a4f47f3cdea53c8a51eded6e416f90` | Spatio-temporal multi-frame liveness |
| **faceRec_4110_fc256_Model_r37_3516x** | 65.3 MB | `6e49bc26d19d567fae463b6a96c30749` | **Feature extraction** - outputs 256-dim vector |
| **Yolo_0808_512_r37_3516x** | 3.6 MB | `ee122626c9eaa2fc5db43655d8753e34` | Generic YOLO detection |
| **safeHelmet_Model_v0104_hign_r37_3516x** | 2.8 MB | `fc9b8a3268b0ca1992f1c1e5b60d5c4f` | Safety helmet detection |

**Model Path (Device):** `/program/factory/models/model/`
**Model Path (Local):** `<RELEASE_ROOT>/dtm-600/program_factory/factory/models/model/`

---

## 5. Image Processing Libraries (JPEG/Image Pipeline)

### libopencv_imgcodecs.so.3.4
| Attribute | Value |
|-----------|-------|
| **Purpose** | **IMAGE PARSING** - JPEG/PNG encoding/decoding. Potential attack surface for malformed images |
| **Device Path** | `/program/lib/libopencv_imgcodecs.so.3.4` |
| **Size** | ~2.5 MB |
| **Type** | OpenCV 3.4 Image Codecs |
| **Language** | C++ |
| **Note** | Parses JPEG headers, EXIF could be stripped here or in preprocessing |

### libopencv_imgproc.so.3.4
| Attribute | Value |
|-----------|-------|
| **Purpose** | Image processing - resizing, color conversion, filters |
| **Device Path** | `/program/lib/libopencv_imgproc.so.3.4` |
| **Size** | ~2.5 MB |
| **Type** | OpenCV 3.4 Image Processing |
| **Language** | C++ |

### libopencv_core.so.3.4
| Attribute | Value |
|-----------|-------|
| **Purpose** | Core OpenCV - matrix operations, data structures |
| **Device Path** | `/program/lib/libopencv_core.so.3.4` |
| **Size** | ~2.5 MB |
| **Type** | OpenCV 3.4 Core |
| **Language** | C++ |

### libimg.so
| Attribute | Value |
|-----------|-------|
| **Purpose** | Custom image handling library |
| **Device Path** | `/program/lib/libimg.so` |
| **Type** | ELF 32-bit LSB shared object |
| **Language** | C |

### libdspvideomjpeg.so
| Attribute | Value |
|-----------|-------|
| **Purpose** | MJPEG DSP acceleration |
| **Device Path** | `/program/lib/libdspvideomjpeg.so` |
| **Type** | ELF 32-bit LSB shared object |
| **Language** | C |

---

## 6. Kernel Modules (Video/NNIE/JPEG)

Located at `/program/lib/modules/4.9.37/extra/`

### hi3516cv500_nnie.ko
| Attribute | Value |
|-----------|-------|
| **Purpose** | NNIE kernel driver - neural network accelerator |
| **Local Path** | `<RELEASE_ROOT>/dtm-600/program_factory/lib/modules/4.9.37/extra/hi3516cv500_nnie.ko` |
| **Type** | Kernel module |

### hi3516cv500_vi.ko
| Attribute | Value |
|-----------|-------|
| **Purpose** | Video Input - camera frame capture |
| **Note** | Entry point for all image data |

### hi3516cv500_jpege.ko
| Attribute | Value |
|-----------|-------|
| **Purpose** | Hardware JPEG encoder |

### hi3516cv500_jpegd.ko
| Attribute | Value |
|-----------|-------|
| **Purpose** | Hardware JPEG decoder |
| **Note** | Potential fuzzing target for JPEG parsing |

### Other Key Kernel Modules
| Module | Purpose |
|--------|---------|
| hi3516cv500_vpss.ko | Video processing subsystem |
| hi3516cv500_venc.ko | Video encoder |
| hi3516cv500_vdec.ko | Video decoder |
| hi3516cv500_ive.ko | Intelligent Video Engine |
| hi3516cv500_svprt.ko | Smart Vision Platform runtime |

---

## 7. Supporting Libraries

### Protocol/Network
| Library | Purpose |
|---------|---------|
| libcurl.so.4.5.0 | HTTP client (firmware updates, API) |
| libwolfssl.so.14.0.0 | TLS/SSL (WolfSSL embedded) |
| libsdkserver.so | SDK server interface |
| libstdprotocol.so | Standard protocols |

### System/Utility
| Library | Purpose |
|---------|---------|
| libiware.so | Main middleware library |
| libmpi.so | Media Processing Interface |
| libisp.so | Image Signal Processor control |
| libive.so | Intelligent Video Engine userspace |
| libmxml.so | Mini-XML parsing |
| libz.so.1.2.11 | zlib compression |
| libfreetype.so.6 | Font rendering |
| libzbar.so.0 | QR/barcode scanning |

### Audio
| Library | Purpose |
|---------|---------|
| libaacenc.so | AAC encoder |
| libaacdec.so | AAC decoder |
| libaaccomm.so | AAC common |
| libVoiceEngine.so | Voice processing |

---

## 8. Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CAMERA INPUT                                       │
│                     hi3516cv500_vi.ko → VI capture                          │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMAGE PREPROCESSING                                   │
│  libopencv_imgproc.so → resize, normalize                                   │
│  libTensorEnginePreprocess.so → prepare for NNIE                            │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FACE DETECTION                                       │
│  Model: faceDetect_yolo_h512_w288_r37_3516x                                 │
│  Engine: libTensorEngineModuleHisi.so → hi3516cv500_nnie.ko                 │
│  Output: Bounding boxes                                                      │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FACE ALIGNMENT                                        │
│  Model: faceAlign5_Model_r37_3516x                                          │
│  Output: 5-point landmarks (eyes, nose, mouth)                              │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        QUALITY CHECK                                         │
│  Model: Quality_Angle_71000_005_r37_3516x                                   │
│  Output: Quality score, pose angle                                           │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LIVENESS CHECK                                        │
│  Models: Liveness_1frame_Model + STM_liveness_Model                         │
│  Output: Liveness score (real face vs photo/video)                          │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FEATURE EXTRACTION                                      │
│  Model: faceRec_4110_fc256_Model_r37_3516x (65MB)                           │
│  Output: 256-dimensional float vector (unit normalized)                      │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEMPLATE COMPARISON                                     │
│  Library: libFaceAnalyzeSystemAPI.so                                         │
│  Function: ISF_UVFACE_FeatureCompare(pVec1, pVec2, 256, &score)             │
│  Algorithm: Cosine similarity                                                │
│  **VULNERABILITY: Zero template → 99% match for ANY face**                  │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ACCESS DECISION                                        │
│  mwareserver → Check threshold, temperature, time rules                     │
│  Output: Wiegand signal via GPIO, audio prompt, display result              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Template Storage

| Item | Path (Device) |
|------|---------------|
| Face Templates | `/data/WorkLibFile/<LibID>/PersonID_*/FaceID_*.bin` |
| Person Metadata | `/data/WorkLibFile/<LibID>/PersonID_*/Person_*.bin` |
| Enrollment Photos | `/data/WorkLibFile/<LibID>/Image/*.jpg` |
| Recognition Logs | `/data/PassRecord/records/*.xml` |
| Snapshot Photos | `/data/channel01/sub05/photo/*.jpg` |

### Template Format
- **Size:** 1044 bytes
- **Header:** 20 bytes (`03 00 00 00 02 00 00 f0 00 00 00 00 01 00 00 f0 00 00 00 00`)
- **Feature Vector:** 1024 bytes (256 little-endian floats, unit-normalized)

---

## 10. Attack Surfaces

| Component | Attack Type | Status |
|-----------|-------------|--------|
| libFaceAnalyzeSystemAPI.so | Zero-template bypass | **CONFIRMED VULNERABLE** |
| libopencv_imgcodecs.so.3.4 | JPEG/image parsing | Testing needed |
| hi3516cv500_jpegd.ko | Hardware JPEG decoder | Kernel-level fuzzing |
| libTensorEngineModuleHisi.so | Model loading | Testing needed |
| libmxml.so | XML parsing | Testing needed |
| libiware.so | IPC/command handling | Testing needed |

---

## 11. Files for Analysis

**High Priority (Face Recognition Core):**
1. `/program/lib/libFaceAnalyzeSystemAPI.so` - Template comparison
2. `/program/factory/models/TensorEngineEnv/Hisi/libTensorEngineModuleHisi.so` - Model inference
3. `/program/bin/mwareserver` - Main orchestrator

**Image Processing (Fuzzing Targets):**
1. `/program/lib/libopencv_imgcodecs.so.3.4` - JPEG parsing
2. `/program/lib/libimg.so` - Image handling
3. `/program/lib/modules/4.9.37/extra/hi3516cv500_jpegd.ko` - JPEG decode

**Models (For understanding pipeline):**
1. `faceRec_4110_fc256_Model_r37_3516x` - Feature extraction
2. `faceDetect_yolo_h512_w288_r37_3516x` - Detection

---

*Document generated from authorized security research on Digital Ally DTM-600*
