# DTM-600 Face Recognition Pipeline Analysis

**Device:** Digital Ally ThermoVu DTM-600 (OET-213H-NB)
**Date:** 2026-01-12
**Source:** Static analysis of extracted firmware + runtime logs

---

## 1. Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAMERA INPUT (1920x1080)                            │
│                              VI_CAP0 IRQ                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: FACE DETECTION                                                    │
│  Model: faceDetect_yolo_h512_w288_r37_3516x (3.1 MB)                        │
│  Output: Bounding boxes, confidence scores                                  │
│  Min face: 45px, Max faces: 300, Alarm size: 55px                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: FACE ALIGNMENT                                                    │
│  Model: faceAlign5_Model_r37_3516x (421 KB)                                 │
│  Output: 5-point landmarks (eyes, nose, mouth corners)                      │
│  Pupil distance range: 185-6018 pixels                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: QUALITY ASSESSMENT                                                │
│  Model: Quality_Angle_71000_005_r37_3516x (429 KB)                          │
│  Config: QualityEn=1, QEMode=2, Threshold=0.5                               │
│  Checks: Face angle, blur, occlusion, lighting                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: LIVENESS DETECTION (if enabled)                                   │
│  Models:                                                                    │
│    - Liveness_1frame_Model_1004_33w_merge_specify_r37_3516x (787 KB)        │
│    - STM_liveness_Model_spe_r37_3516x (1.5 MB)                              │
│  Config: FaceLivingAnalysis Enable=0, Threshold=50, Grade=0-2               │
│  Anti-spoofing: Single-frame + spatio-temporal analysis                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: FACE ATTRIBUTES (optional)                                        │
│  Model: FaceAttr_dv300_int8_ry41_4504 (1.7 MB)                              │
│  Outputs: Age, Gender, Glasses, Mask detection                              │
│  Config: AttrEn=0, MaskEnable=1, SafetyCapEnable=0                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 6: FEATURE EXTRACTION                                                │
│  Model: faceRec_4110_fc256_Model_r37_3516x (65.3 MB)                        │
│  Output: 256-dimensional feature vector                                     │
│  Feature version: 10041000                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 7: TEMPLATE MATCHING (1:N Search)                                    │
│  Libraries:                                                                 │
│    - DefaultEmployeeLib (ID=3, Type=3)                                      │
│    - DefaultVisitorLib (ID=4, Type=4)                                       │
│  Storage: /data/WorkLibFile/{LibID}/                                        │
│  Thresholds:                                                                │
│    - IDFaceThreshold: 60 (ID verification)                                  │
│    - wzr_threshold: 0.95 (whitelist recognition)                            │
│    - MultipleValue: 82 (per-library similarity threshold)                   │
│  Capacity: 10,000 people, 10,000 faces, 20,000 cards                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 8: ATTRIBUTE VERIFICATION                                            │
│  Thermal Check (if enabled):                                                │
│    - Normal range: 35.5°C - 42.0°C                                          │
│    - Alarm threshold: 37.3°C                                                │
│    - Environment compensation: -1°C to +5°C based on ambient temp           │
│  Mask Check: Mode=2, Enable=1                                               │
│  Safety Helmet: Mode=1, Enable=0                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 9: ACCESS DECISION                                                   │
│  OpenDoorMode: 1 (face recognition mode)                                    │
│  DevWorkMode: 1=Normal, 2=Enrollment, 5=Intercom, 8=Attendance              │
│                                                                             │
│  MATCH SUCCESS (Type=1):                     MATCH FAIL (Type=2):           │
│    - IsDoorOpen: 1                             - IsDoorOpen: 0              │
│    - IsLightRemind: 1                          - IsLightRemind: 1           │
│    - IsVoiceRemind: 1                          - IsVoiceRemind: 1           │
│    - IsGUIRemind: 1                            - IsGUIRemind: 1             │
│    - IsWiegandOut: 0 (configurable)            - IsWiegandOut: 0            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│  STAGE 10A: ACCESS GRANTED    │   │  STAGE 10B: ACCESS DENIED     │
│                               │   │                               │
│  Door Control:                │   │  Audio Prompts:               │
│    - DRV_DoorControl()        │   │    - Fail.pcm                 │
│    - Relay output (FPort0)    │   │    - NoLiveness.pcm           │
│    - Duration: 10 seconds     │   │    - Tmp_Abnormal.pcm         │
│                               │   │    - NoMask.pcm               │
│  Wiegand Output:              │   │    - NoAccess.pcm             │
│    - Format: 26-bit or 34-bit │   │                               │
│    - Ports: 1, 21             │   │  Display:                     │
│                               │   │    - Red indicator            │
│  Audio Prompts:               │   │    - Denial reason            │
│    - Success.pcm              │   │                               │
│    - Access.pcm               │   │                               │
│    - Access_Tmp.pcm           │   │                               │
│                               │   │                               │
│  Display:                     │   │                               │
│    - Green indicator          │   │                               │
│    - Person name              │   │                               │
│    - Temperature (if taken)   │   │                               │
└───────────────────────────────┘   └───────────────────────────────┘
```

---

## 2. Key Software Components

### 2.1 Main Binaries

| Binary | Size | Function |
|--------|------|----------|
| `mwareserver` | 14.8 MB | Main firmware orchestrator |
| `mmi_client` | N/A | GUI/display interface |
| `libFaceAnalyzeSystemAPI.so` | N/A | Face analysis API library |
| `libTensorEngineModuleHisi.so` | 4.7 MB | NNIE inference engine |

### 2.2 Source Files (from logs)

| File | Function |
|------|----------|
| `iw_acs_face.c` | ACS face processing |
| `iw_acs_msgpro.c` | ACS message processing |
| `iw_acs_peripheral.c` | Peripheral device control |
| `iw_facecommon.c` | Common face recognition functions |
| `mw_ctrl_acs_func.c` | ACS control functions |
| `mw_audio.c` | Audio playback (PCM prompts) |
| `mw_conf.c` | Configuration management |

### 2.3 NNIE Runtime APIs

```c
HI_SVPRT_RUNTIME_Init()           // Initialize NNIE runtime
HI_SVPRT_RUNTIME_LoadModelGroup() // Load compiled model (.wk file)
HI_SVPRT_RUNTIME_ForwardGroupSync() // Synchronous inference
HI_SVPRT_RUNTIME_ForwardGroupASync() // Async inference
HI_SVPRT_RUNTIME_UnloadModelGroup() // Unload model
HI_SVPRT_RUNTIME_DeInit()         // Deinitialize runtime
```

---

## 3. Configuration Parameters

### 3.1 Face Detection

```xml
<!-- /config/config_a.xml -->
<Face>
    <SensitivityCompat>56</SensitivityCompat>
    <FaceLivingAnalysis>
        <Enable>0</Enable>
        <Threshold>50</Threshold>
        <Grade>0</Grade>  <!-- 0=Low, 1=Medium, 2=High -->
    </FaceLivingAnalysis>
    <FaceRecog>
        <AttrEn>0</AttrEn>
        <CompareEn>0</CompareEn>
        <IDFaceThreshold>60</IDFaceThreshold>
    </FaceRecog>
    <FaceAttribute>
        <MaskEnable>1</MaskEnable>
        <SafetyCapEnable>0</SafetyCapEnable>
    </FaceAttribute>
</Face>
```

### 3.2 Algorithm Runtime (fs_runtime_params.config)

```yaml
wzr_threshold: 0.95      # Whitelist recognition threshold
minface: 45              # Minimum face size (pixels)
maxface: 300             # Maximum faces per frame
alarm_facesize: 55       # Alert if face smaller than this
pre_upload_face_quality: 0.5
lower_limit_face_quality: 0.1
```

### 3.3 Temperature Verification

```xml
<ThermometryInfo>
    <Lower>34.0000</Lower>
    <Upper>37.3000</Upper>
</ThermometryInfo>
<EnvironmentAdjustInfos>
    <Enable>1</Enable>
    <!-- Ambient temp → Adjustment -->
    <!-- 5°C → +5.0°C -->
    <!-- 10°C → +4.0°C -->
    <!-- 16°C → +2.0°C -->
    <!-- 25°C → 0.0°C -->
    <!-- 32°C → -0.5°C -->
    <!-- 38°C → -1.0°C -->
</EnvironmentAdjustInfos>
```

### 3.4 Access Control Linkage

```xml
<PermissionList>
    <Permission3>  <!-- Employee Library -->
        <Basic>
            <LibID>3</LibID>
            <MultipleValue>82</MultipleValue>  <!-- 82% similarity threshold -->
        </Basic>
        <LinkageStrategy0>  <!-- On Match -->
            <Type>1</Type>
            <IsDoorOpen>1</IsDoorOpen>
            <IsLightRemind>1</IsLightRemind>
            <IsVoiceRemind>1</IsVoiceRemind>
            <IsGUIRemind>1</IsGUIRemind>
            <IsWiegandOut>0</IsWiegandOut>
        </LinkageStrategy0>
        <LinkageStrategy1>  <!-- On No Match -->
            <Type>2</Type>
            <IsDoorOpen>0</IsDoorOpen>
            <IsLightRemind>1</IsLightRemind>
            <IsVoiceRemind>1</IsVoiceRemind>
            <IsGUIRemind>1</IsGUIRemind>
        </LinkageStrategy1>
    </Permission3>
</PermissionList>
```

---

## 4. Face Database Structure

```
/data/WorkLibFile/
├── AllLibInfo.bin          # Library metadata
├── AllLibInfo_B.bin        # Backup
├── 3/                      # Employee Library (Type=3)
│   ├── LibKeyInfo.bin      # Library key info (44 bytes)
│   └── FeatureVersion      # "10041000"
└── 4/                      # Visitor Library (Type=4)
    ├── LibKeyInfo.bin
    └── FeatureVersion
```

### LibKeyInfo.bin Format

```
Offset  Size  Field
0x00    8     Magic "FeatFile"
0x08    4     File size (36 bytes struct)
0x0C    4     Library ID
0x10    4     Library Type
0x14    4     Entry count
0x18    4     Reserved
0x1C    4     Timestamp
0x20    4     Reserved
```

---

## 5. Audio Prompt Index

| Index | File | Trigger Condition |
|-------|------|-------------------|
| 0 | Success.pcm | Recognition success |
| 1 | TimeFail.pcm | Time schedule violation |
| 2 | Fail.pcm | Recognition failure |
| 3 | IDfail.pcm | ID verification fail |
| 4 | Invalidcard.pcm | Invalid card |
| 5 | IDprompt.pcm | ID prompt |
| 6 | NoLiveness.pcm | Liveness check failed |
| 7 | CollectSuccess.pcm | Enrollment success |
| 8 | CollectFail.pcm | Enrollment failure |
| 12 | Refuse.pcm | Access refused |
| 14 | OpenSucceed.pcm | Door opened |
| 16 | FacePosition.pcm | Position face correctly |
| 17 | NoMask.pcm | Mask required |
| 19 | Tmp_Abnormal.pcm | Temperature abnormal |
| 23 | NoAccess.pcm | No access permission |
| 24 | Access.pcm | Access granted |

---

## 6. Wiegand Output Configuration

```xml
<WiegandInfos>
    <WiegandNum>2</WiegandNum>
    <WiegandInfo0>
        <Mode>2</Mode>        <!-- 2=Output mode -->
        <AccessPort>1</AccessPort>
        <Format>1</Format>    <!-- 1=26-bit, 2=34-bit -->
    </WiegandInfo0>
    <WiegandInfo1>
        <Mode>2</Mode>
        <AccessPort>21</AccessPort>
        <Format>1</Format>
    </WiegandInfo1>
</WiegandInfos>
```

---

## 7. IPC Message Flow

```
mwareserver (main process)
    │
    ├──► BP_SendAsyncMsg()      → Async notification to mmi_client
    │    └── Display update, audio playback
    │
    ├──► BP_SendSyncGetMsg()    → Synchronous config fetch
    │    └── MsgCmd: 3141, 4045, 4246, etc.
    │
    ├──► DRV_DoorControl()      → Door relay control
    │
    └──► DRV_SetParam(4246)     → Hardware parameter setting
```

---

## 8. Security Observations

1. **Liveness Disabled by Default**: `FaceLivingAnalysis.Enable=0` - vulnerable to photo/video attacks

2. **Low Similarity Threshold**: `MultipleValue=82` (82%) may allow false positives

3. **Temperature Compensation**: Environment adjustment could be exploited to bypass thermal checks

4. **Wiegand Output Disabled**: `IsWiegandOut=0` - door opens directly without external controller validation

5. **Hardcoded Thresholds**: All thresholds in plaintext XML configuration

---

## 9. Neural Network Models Summary

| Stage | Model | Size | Purpose |
|-------|-------|------|---------|
| 1 | faceDetect_yolo_h512_w288 | 3.1 MB | YOLO face detection |
| 2 | faceAlign5_Model | 421 KB | 5-point landmark alignment |
| 3 | Quality_Angle_71000_005 | 429 KB | Quality/angle assessment |
| 4a | Liveness_1frame_Model | 787 KB | Single-frame liveness |
| 4b | STM_liveness_Model | 1.5 MB | Spatio-temporal liveness |
| 5 | FaceAttr_dv300_int8 | 1.7 MB | Face attributes |
| 6 | faceRec_4110_fc256_Model | 65.3 MB | 256-dim feature extraction |

**Total model size:** ~73 MB
**Runtime engine:** libTensorEngineModuleHisi.so (4.7 MB)
**Platform:** HiSilicon Hi3516DV300 NNIE accelerator

---

## 10. Verification Modes

| Mode | Description | Inputs |
|------|-------------|--------|
| 1 | ID Verification | Face + ID card |
| 2 | Number Whitelist | Card number |
| 3 | Face Whitelist | Face only |
| 4 | Password | PIN code |
| 5 | ID + Number | Face + ID + Card |
| 6 | Number + Face | Card + Face |

Current config: Staff=[2,3,4,6], Visitor=[2,3,4,6]
