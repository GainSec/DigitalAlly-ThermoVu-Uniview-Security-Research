# DTM-600 Factory Directory Analysis

**Source:** `/program/factory/` from device 192.168.30.178
**Extracted To:** `dtm-600/program_factory/factory/`
**Date:** 2026-01-12
**Total Size:** 99 MB (109 files)

---

## 1. Directory Structure

```
factory/
├── models/                    # Neural network models for NNIE
│   ├── model/                 # Compiled model files
│   ├── Configs/               # Runtime configuration
│   └── TensorEngineEnv/       # Inference engine libraries
├── PcmSource/                 # Audio prompts
│   ├── 01_English/            # English voice prompts
│   └── 36_Korean/             # Korean voice prompts
├── faceTemplate/              # Face enrollment templates
│   ├── CH/                    # Chinese
│   └── EN/                    # English
├── ptztemplate/               # PTZ protocol templates
├── zoneinfo/                  # Timezone data
├── default_cfg_*.xml          # Default configs per device variant
├── device_cap_*.xml           # Device capability definitions
├── preset_scene_*.xml         # Scene presets per variant
├── Lens-*.csv                 # Lens calibration tables
├── Ratio*.csv                 # Sensor ratio calibration
└── [other calibration files]
```

---

## 2. Neural Network Models (HiSilicon NNIE)

Located in `factory/models/model/` - compiled for Hi3516DV300 NNIE accelerator:

| Model | Size | Purpose |
|-------|------|---------|
| `faceRec_4110_fc256_Model_r37_3516x` | 65.3 MB | Face recognition (256-dim embedding) |
| `Yolo_0808_512_r37_3516x` | 3.6 MB | YOLO object detection |
| `faceDetect_yolo_h512_w288_r37_3516x` | 3.1 MB | Face detection (YOLO-based) |
| `safeHelmet_Model_v0104_hign_r37_3516x` | 2.8 MB | Safety helmet detection |
| `FaceAttr_dv300_int8_ry41_4504` | 1.7 MB | Face attributes (age, gender, etc.) |
| `STM_liveness_Model_spe_r37_3516x` | 1.5 MB | Spatio-temporal liveness detection |
| `Liveness_1frame_Model_1004_33w_merge_specify_r37_3516x` | 787 KB | Single-frame liveness |
| `Quality_Angle_71000_005_r37_3516x` | 429 KB | Face quality/angle assessment |
| `faceAlign5_Model_r37_3516x` | 421 KB | 5-point face alignment |

### TensorEngine Libraries
- `libTensorEngineModuleHisi.so` (4.7 MB) - HiSilicon inference engine
- `libplugin_proposal.so` (42 KB) - Region proposal plugin

### VNP Firmware
- `VNP.mvcmd` (7.3 MB) - Neural processor microcode/firmware

---

## 3. OEM Device Variants

Default configurations exist for multiple Uniview OEM products:

| Model | Type | Notes |
|-------|------|-------|
| **OET-213H-NB-WH** | Thermal + Face | Digital Ally ThermoVu DTM-600 |
| **OET-213H-WH** | Thermal + Face | With network backup |
| **OET-223L-NB-WH** | Thermal | No network backup variant |
| **OET-223L-WH** | Thermal | Standard variant |
| **ET-B31H-M-WH** | Access Control | Face terminal |
| **ET-B31H-WH** | Access Control | Face terminal |
| **ET-B31H-M@B** | Access Control | Variant B |
| **ET-B32F-D@W** | Access Control | Door variant |
| **ET-B32L** | Access Control | L-series |
| **ET-B32L-WH@W-NB** | Access Control | White, no backup |
| **DET-231H-M-WH** | Detection | M variant |
| **DET-532L-WH** | Detection | L variant |
| **DET-B31F-M-WH@TWD** | Detection | TWD variant |
| **KTP-ET-B32L-WH@W** | Access Control | KTP branded |
| **UNIPC-C** | Unknown | Uniview PC integration |

---

## 4. Audio Prompts

### English (`PcmSource/01_English/`) - 42 files
Access control voice prompts including:
- `Access.pcm` - Access granted
- `Fail.pcm` - Access denied
- `NoMask.pcm` - Mask required
- `FacePosition.pcm` - Position face
- `Tmp_Abnormal.pcm` - Temperature abnormal
- `GreenCode.pcm` / `RedCode.pcm` / `YellowCode.pcm` - Health code status
- `NoLiveness.pcm` - Liveness check failed
- `CollectSuccess.pcm` / `CollectFail.pcm` - Enrollment status

### Korean (`PcmSource/36_Korean/`) - 41 files
Same prompts localized to Korean.

---

## 5. Lens Calibration Data

Calibration tables for various lens modules:

| Lens Model | Size | Notes |
|------------|------|-------|
| Lens-4801C020 | 94 KB | |
| Lens-4801C02M | 116 KB | |
| Lens-4801C03V | 121 KB | |
| Lens-4801C03W | 27 KB | |
| Lens-4807C001 | 23 KB | |
| Lens-4807C002 | 97 KB | |
| Lens-4807C003 | 92 KB | |
| Lens-4807C004 | 162 KB | |
| Lens-4807C00C | 161 KB | |
| Lens-4807C00E | 211 KB | |
| Lens-4807C00F | 57 KB | |
| Lens-4807C00G | 167 KB | |
| Lens-4807C00H | 40 KB | |

---

## 6. PTZ Protocol Templates

Pelco and other PTZ protocols in `ptztemplate/`:
- `PELCO-D.ini` - Pelco D protocol
- `PELCO-P.ini` - Pelco P protocol
- `VISCA.ini` - Sony VISCA
- `ALEC.ini` / `ALEC_PELCO-D.ini` / `ALEC_PELCO-P.ini`
- `MINKING_PELCO-D.ini` / `MINKING_PELCO-P.ini`
- `YAAN.ini`

---

## 7. Other Calibration Files

| File | Description |
|------|-------------|
| `BestFace.bin` (162 KB) | Reference face data |
| `ADN-CTRL-THR.csv` | ADN control thresholds |
| `LED-CTRL-THR.csv` | LED control thresholds |
| `IrCtrl.csv` | IR illuminator control |
| `DEFAULT-IRCTB.csv` | Default IR cut table |
| `DayNightSense.txt` | Day/night switching params |
| `ParamTable.csv` | General parameters |
| `RatioB*.csv` | Sensor ratio calibration (multiple variants) |
| `cali_node_table.csv` | Calibration node mapping |
| `isp_param.zip` | ISP parameters (compressed) |
| `default_pic.zip` | Default UI pictures |

---

## 8. Version Information

```
factory/version: (29 bytes)
factory/interversion: (29 bytes)
factory/publishdate: (20 bytes)
```

---

## 9. Security Implications

1. **Model Extraction** - Neural network models can be analyzed for:
   - Architecture reverse engineering
   - Adversarial attack development
   - Model cloning/theft

2. **Default Configurations** - All OEM variants share same credential defaults:
   - Same weak passwords across product line
   - Same SSL certificates/keys
   - Same WiFi keys

3. **Calibration Data** - Lens/sensor calibration reveals:
   - Supported hardware variants
   - Manufacturing tolerances
   - Potential sensor fingerprinting

4. **Audio Prompts** - Voice files can be:
   - Used for social engineering
   - Modified for spoofing access events
