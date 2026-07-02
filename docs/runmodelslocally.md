Title: Running ThermoVu/Uniview NNIE Models Locally

Context
- Device: Digital Ally ThermoVu DTM-600 (Uniview OET-213H-NB).
- Model binaries live at `/program/factory/models/model` on the device (HiSilicon NNIE format).
- `/data/WorkLibFile/*` only has metadata (FeatureVersion, LibKeyInfo), not the actual models.

Model bundle to extract
- FaceAttr_dv300_int8_ry41_4504
- Liveness_1frame_Model_1004_33w_merge_specify_r37_3516x
- Quality_Angle_71000_005_r37_3516x
- STM_liveness_Model_spe_r37_3516x
- Yolo_0808_512_r37_3516x
- faceAlign5_Model_r37_3516x
- faceDetect_yolo_h512_w288_r37_3516x
- faceRec_4110_fc256_Model_r37_3516x
- safeHelmet_Model_v0104_hign_r37_3516x

Exfil the models
On device (telnet root shell):
```
tar czf /tmp/models.tgz /program/factory/models/model
```
Send to host (example with nc; replace HOST):
```
# host
nc -l 9000 > models.tgz
# device
nc HOST 9000 < /tmp/models.tgz
```

Local use path (webcam)
These blobs are HiSilicon NNIE offline models; they are not directly usable with OpenCV/ONNX until converted.

1) Convert NNIE → Caffe → ONNX (or direct NNIE → ONNX if you have tooling):
   - Use HiSilicon NNIE SDK tools (e.g., nnie_mapper/nnie2caffe) to produce Caffe models.
   - Convert to ONNX (e.g., caffe2onnx).
   - Validate shapes/quantization; adjust preprocessing to match the device (likely NV12/BGR, specific scales).
2) Run via ONNX Runtime + OpenCV webcam:
```python
import cv2, onnxruntime as ort
sess = ort.InferenceSession("faceDetect_yolo_h512_w288_r37_3516x.onnx", providers=["CPUExecutionProvider"])
cap = cv2.VideoCapture(0)
while True:
    ok, frame = cap.read()
    if not ok: break
    # TODO: preprocess to model input (resize, normalize), sess.run, postprocess boxes
    cv2.imshow("cam", frame)
    if cv2.waitKey(1) == 27: break
```

Alternative: run on-device
- If you keep the models on the device, you’d need an NNIE sample app to bind V4L/RTSP input to these blobs; the shipped firmware already does this. For local experimentation, conversion to ONNX on your workstation is simpler.  
