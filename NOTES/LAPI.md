# LAPI REST API Reference — Uniview OET-213H-NB

**Device:** Uniview OET-213H-NB (Digital Ally ThermoVu DTM-600)
**Firmware Version:** WEB_CTRL_VERSION 1.0.407
**Base URL:** `http://<device-ip>/LAPI/...`
**ONVIF Port:** 81
**Source:** Extracted from `ComScript.d7fe61b7.js`

---

## Authentication

Most endpoints require HTTP Basic Auth or session-based authentication.
- **Default Credentials:** `admin:admin`
- **Super Password:** `87654321` (backdoor)
- **Auth Header:** `Authorization: Basic YWRtaW46YWRtaW4=`

**Auth Bypass Testing:** Endpoints marked with `[TEST]` should be tested without authentication.

---

## Table of Contents

1. [System & Device Info](#1-system--device-info)
2. [Authentication & Security](#2-authentication--security)
3. [Network Configuration](#3-network-configuration)
4. [Telnet & Debug](#4-telnet--debug)
5. [Firmware & Updates](#5-firmware--updates)
6. [PTZ Control](#6-ptz-control)
7. [Media & Streaming](#7-media--streaming)
8. [Image & Video Settings](#8-image--video-settings)
9. [Storage](#9-storage)
10. [Alarms & Events](#10-alarms--events)
11. [Smart/IVA Features](#11-smartiva-features)
12. [Face Recognition](#12-face-recognition)
13. [PACS (Access Control)](#13-pacs-access-control)
14. [I/O Control](#14-io-control)
15. [Demo/Debug Endpoints](#15-demodebug-endpoints)
16. [Intelligent Traffic](#16-intelligent-traffic)

---

## 1. System & Device Info

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/System/DeviceBasicInfo` | GET | [TEST] | Device model, serial, firmware version |
| `/LAPI/V1.0/System/DeviceRunInfo` | GET | Yes | Runtime info, uptime, memory usage |
| `/LAPI/V1.0/System/Reboot` | PUT | Yes | **CRITICAL** Reboot device |
| `/LAPI/V1.0/System/FactoryReset` | PUT | Yes | **CRITICAL** Factory reset |
| `/LAPI/V1.0/System/Language` | GET/PUT | Yes | System language setting |
| `/LAPI/V1.0/System/Logs` | GET | Yes | System logs |
| `/LAPI/V1.0/System/TimePrivate` | GET/PUT | Yes | System time configuration |
| `/LAPI/V1.0/System/TimePrivate/LocalTime` | GET/PUT | Yes | Local time |
| `/LAPI/V1.0/System/Time/DST` | GET/PUT | Yes | Daylight saving time config |
| `/LAPI/V1.0/System/Time/NTP` | GET/PUT | Yes | NTP server configuration |
| `/LAPI/System/Time/NTP/Test` | POST | Yes | Test NTP connection |
| `/LAPI/V1.0/System/Time/SyncMode` | GET/PUT | Yes | Time sync mode |
| `/LAPI/V1.0/System/KeepAlive` | POST | Yes | Session keepalive |
| `/LAPI/V1.0/System/LocationInfo` | GET/PUT | Yes | Device location info |
| `/LAPI/V1.0/System/BatteryInfo` | GET | Yes | Battery status (if applicable) |
| `/LAPI/V1.0/System/FanCtrl` | GET/PUT | Yes | Fan control settings |
| `/LAPI/V1.0/System/HideDeviceInfo` | GET/PUT | Yes | Hide device info from discovery |
| `/LAPI/V1.0/System/Diagnosis/FileURL` | GET | Yes | Diagnostic file download URL |
| `/LAPI/V1.0/System/Diagnosis/PackStatus` | GET | Yes | Diagnostic package status |
| `/LAPI/V1.0/System/ConfigurationInfoURL` | GET | Yes | Config backup URL |
| `/LAPI/V1.0/System/ConfigurationInfo/` | GET/PUT | Yes | Configuration backup/restore |
| `/LAPI/V1.0/System/DebugMessage` | GET | Yes | Debug messages |
| `/LAPI/V1.0/System/ExtraLogSwitch` | GET/PUT | Yes | Extra logging toggle |
| `/LAPI/V1.0/System/CustomizePackage` | GET/PUT | Yes | Custom package info |
| `/LAPI/V1.0/System/PearlEyeCommonCfg` | GET/PUT | Yes | PearlEye camera config |
| `/LAPI/V1.0/System/ManageServer` | GET/PUT | Yes | Management server config |
| `/LAPI/V1.0/System/BMServer` | GET/PUT | Yes | BM server config |

### Example: Get Device Info
```bash
curl -u admin:admin http://192.168.30.178/LAPI/V1.0/System/DeviceBasicInfo
```

### Example Response
```json
{
  "Response": {
    "ResponseURL": "/LAPI/V1.0/System/DeviceBasicInfo",
    "DeviceType": "IPC",
    "ProductModel": "OET-213H-NB-WH",
    "SerialNo": "210235B8GR321B000XXX",
    "FirmwareVersion": "IPC_G6103-B0011P05D1812"
  }
}
```

---

## 2. Authentication & Security

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/System/Security/Login` | POST | No | Web login endpoint |
| `/LAPI/V1.0/Channel/0/System/Login` | POST | No | Channel login |
| `/LAPI/V1.0/Channel/0/System/Users` | GET/PUT | Yes | User management |
| `/LAPI/V1.0/System/Security/RSA` | GET | [TEST] | RSA public key for encrypted login |
| `/LAPI/V1.0/System/Security/AccessPolicy` | GET/PUT | Yes | Access policy / "Friendly Password" |
| `/LAPI/V1.0/System/PrivacyPolicy/Status` | GET/PUT | Yes | Privacy policy status |
| `/LAPI/V1.0/System/CurrentPasswordInfo` | GET | Yes | Current password info |
| `/LAPI/V1.0/System/SecretKeyInfo` | GET | Yes | Secret key information |
| `/LAPI/V1.0/NetWork/HttpAuth` | GET/PUT | Yes | HTTP authentication settings |
| `/LAPI/V1.0/NetWork/RtspAuth` | GET/PUT | Yes | RTSP authentication settings |
| `/LAPI/V1.0/NetWork/SecureAccess` | GET/PUT | Yes | Secure access configuration |

### Example: Login Request
```bash
curl -X POST http://192.168.30.178/LAPI/V1.0/System/Security/Login \
  -H "Content-Type: application/json" \
  -d '{"UserName":"admin","Password":"YWRtaW4="}'
```

---

## 3. Network Configuration

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Network/Interfaces/1` | GET/PUT | Yes | Network interface config (IP, mask, gateway) |
| `/LAPI/V1.0/NetWork/DNS` | GET/PUT | Yes | DNS server configuration |
| `/LAPI/V1.0/NetWork/Port` | GET/PUT | Yes | Port configuration |
| `/LAPI/V1.0/NetWork/DDNS` | GET/PUT | Yes | DDNS configuration |
| `/LAPI/V1.0/NetWork/FTP` | GET/PUT | Yes | FTP server settings |
| `/LAPI/V1.0/NetWork/FTP/Test` | POST | Yes | Test FTP connection |
| `/LAPI/V1.0/Channel/0/NetWork/Email` | GET/PUT | Yes | Email/SMTP settings |
| `/LAPI/V1.0/NetWork/Email/Test` | POST | Yes | Test email settings |
| `/LAPI/V1.0/NetWork/SNMP` | GET/PUT | Yes | SNMP configuration |
| `/LAPI/V1.0/NetWork/HTTPS` | GET/PUT | Yes | HTTPS settings |
| `/LAPI/V1.0/Network/HTTPS_SSLCERT` | GET/PUT | Yes | SSL certificate management |
| `/LAPI/V1.0/NetWork/UNP` | GET/PUT | Yes | UPnP configuration |
| `/LAPI/V1.0/NetWork/RegistInfo` | GET/PUT | Yes | Registration info |
| `/LAPI/V1.0/NetWork/ArpBinding` | GET/PUT | Yes | ARP binding |
| `/LAPI/V1.0/NetWork/SoftAP` | GET/PUT | Yes | Soft AP configuration |
| `/LAPI/V1.0/NetWork/SoftAPWiFi` | GET/PUT | Yes | Soft AP WiFi settings |
| `/LAPI/V1.0/NetWork/Net4G` | GET/PUT | Yes | 4G network config |
| `/LAPI/V1.0/NetWork/Net4GStatus` | GET | Yes | 4G network status |
| `/LAPI/V1.0/NetWork/IEEE8021x` | GET/PUT | Yes | 802.1X authentication |
| `/LAPI/V1.0/NetWork/SSLVPN` | GET/PUT | Yes | SSL VPN configuration |
| `/LAPI/V1.0/NetWork/WiFi/Configuration` | GET/PUT | Yes | WiFi configuration |
| `/LAPI/V1.0/NetWork/WiFi/ScanInfo` | GET | Yes | WiFi scan results |
| `/LAPI/V1.0/NetWork/WiFi/LinkStatus` | GET | Yes | WiFi connection status |
| `/LAPI/V1.0/Channel/0/NetWork/IPFilter` | GET/PUT | Yes | IP filter/whitelist |
| `/LAPI/V1.0/Channel/0/NetWork/QOS` | GET/PUT | Yes | QoS settings |
| `/LAPI/V1.0/Channel/0/NetWork/PortMap` | GET/PUT | Yes | Port mapping |
| `/LAPI/V1.0/Channel/0/NetWork/CheckPort` | POST | Yes | Check port availability |
| `/LAPI/V1.0/Channel/0/NetWork/DDNSDomainCheck` | POST | Yes | DDNS domain check |
| `/LAPI/Network/Routes` | GET/PUT | Yes | Routing table |
| `/LAPI/V1.0/Network/Cloud` | GET/PUT | Yes | Cloud service config |
| `/LAPI/V1.0/Network/Cloud/Unregistration` | DELETE | Yes | Unregister from cloud |
| `/LAPI/V1.0/Network/Cloud/DeviceAdd/Mode` | GET/PUT | Yes | Cloud device add mode |
| `/LAPI/NetWork/CameraComm` | GET/PUT | Yes | Camera communication settings |

### Example: Get Network Config
```bash
curl -u admin:admin http://192.168.30.178/LAPI/V1.0/Network/Interfaces/1
```

---

## 4. Telnet & Debug

**CRITICAL SECURITY ENDPOINTS**

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/NetWork/Telnet` | GET/PUT | Yes | **Enable/disable Telnet** |
| `/LAPI/V1.0/Channel/0/Demo/OnvifDebug` | GET/PUT | Yes | ONVIF debug settings (incl. auth toggle) |
| `/LAPI/V1.0/Channel/0/Demo/NetDetect` | GET/POST | Yes | Network detection/diagnostics |
| `/LAPI/V1.0/Channel/0/Demo/WiegandDebug` | GET/PUT | Yes | Wiegand debug settings |
| `/LAPI/V1.0/Channel/0/Image/DebugSwitch` | GET/PUT | Yes | Image debug switch |
| `/LAPI/Demo/Debug/EpTgType` | GET/PUT | Yes | EP/TG debug type |
| `/LAPI/Demo/Debug/DebugEpMsg` | GET/PUT | Yes | Debug EP messages |
| `/LAPI/Demo/Debug/DebugEpTmpMsg` | GET/PUT | Yes | Debug EP temp messages |
| `/LAPI/Demo/Debug/DebugCaputrePara` | GET/PUT | Yes | Debug capture parameters |
| `/LAPI/Demo/Debug/DebugFlashExposure` | GET/PUT | Yes | Debug flash exposure |
| `/LAPI/Demo/Debug/DebugPolarizer` | GET/PUT | Yes | Debug polarizer |
| `/LAPI/Demo/Debug/Heat` | GET/PUT | Yes | Heat debug |
| `/LAPI/Demo/Debug/SaturationSwitch` | GET/PUT | Yes | Saturation debug switch |
| `/LAPI/Demo/Debug/PolarizerInverseSwitch` | GET/PUT | Yes | Polarizer inverse |
| `/LAPI/V1.0/Channel/0/Demo/Debug/IQDebugInfo` | GET | Yes | IQ debug info |
| `/LAPI/V1.0/Channel/0/Demo/Debug/AudioAGC` | GET/PUT | Yes | Audio AGC debug |
| `/LAPI/V1.0/Channel/0/Demo/Debug/EnhanceMode` | GET/PUT | Yes | Enhance mode debug |
| `/LAPI/V1.0/Channel/0/Demo/Debug/ProfileMode` | GET/PUT | Yes | Profile mode debug |
| `/LAPI/V1.0/Channel/0/Demo/Debug/SpecialLensType` | GET/PUT | Yes | Special lens type |

### Example: Enable Telnet
```bash
curl -X PUT -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"Enable": 1}' \
  http://192.168.30.178/LAPI/V1.0/Channel/0/NetWork/Telnet
```

### Example: Get Telnet Status
```bash
curl -u admin:admin http://192.168.30.178/LAPI/V1.0/Channel/0/NetWork/Telnet
```

### Example Response
```json
{
  "Response": {
    "ResponseURL": "/LAPI/V1.0/Channel/0/NetWork/Telnet",
    "Data": {
      "Enable": 1
    }
  }
}
```

---

## 5. Firmware & Updates

**CRITICAL - Can modify device firmware**

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/System/Upgrade` | POST | Yes | **Initiate firmware upgrade** |
| `/LAPI/V1.0/System/UpgradeInfo` | GET | Yes | Upgrade information |
| `/LAPI/V1.0/System/UploadFirmware` | POST | Yes | **Upload firmware file** |
| `/LAPI/V1.0/System/UpgradeUboot` | POST | Yes | **Upgrade U-Boot** |
| `/LAPI/V1.0/System/UpdateStatus` | GET | Yes | Update status |
| `/LAPI/PACS/TempModule/Upgrade` | POST | Yes | Temperature module upgrade |
| `/LAPI/PACS/TempModule/UpStatus` | GET | Yes | Temp module upgrade status |

### Example: Upload Firmware
```bash
curl -X POST -u admin:admin \
  -F "file=@firmware.bin" \
  http://192.168.30.178/LAPI/V1.0/System/UploadFirmware
```

---

## 6. PTZ Control

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/PTZ/PTZCtrl` | PUT | Yes | PTZ control commands |
| `/LAPI/V1.0/Channel/0/PTZ/PTZReset` | PUT | Yes | Reset PTZ position |
| `/LAPI/V1.0/Channel/0/PTZ/PTZCfg` | GET/PUT | Yes | PTZ configuration |
| `/LAPI/V1.0/Channel/0/PTZ/PTDrvCfg` | GET/PUT | Yes | PTZ driver config |
| `/LAPI/V1.0/Channel/0/PTZ/NetCtrlPTZ` | GET/PUT | Yes | Network PTZ control |
| `/LAPI/V1.0/Channel/0/PTZ/Patrols` | GET/PUT | Yes | Patrol routes |
| `/LAPI/V1.0/Channel/0/PTZ/Patrols/id/Start` | PUT | Yes | Start patrol |
| `/LAPI/V1.0/Channel/0/PTZ/Patrols/id/Stop` | PUT | Yes | Stop patrol |
| `/LAPI/V1.0/Channel/0/PTZ/WiperInfo` | GET/PUT | Yes | Wiper control |
| `/LAPI/V1.0/Channel/0/PTZ/OSD3DCoverPosition` | GET/PUT | Yes | 3D OSD cover position |
| `/LAPI/V1.0/Channels/0/PTZ/AreaZoomIn` | PUT | Yes | Area zoom in |
| `/LAPI/V1.0/Channels/0/PTZ/AreaZoomOut` | PUT | Yes | Area zoom out |
| `/LAPI/V1.0/Channels/0/PTZ/Presets` | GET/PUT | Yes | PTZ presets |
| `/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZ` | GET | Yes | PTZ status |
| `/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsPosition` | GET | Yes | Absolute PTZ position |
| `/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsZoom` | GET | Yes | Absolute zoom level |
| `/LAPI/V1.0/PTZ/Guard` | GET/PUT | Yes | PTZ guard position |
| `/LAPI/V1.0/PTZ/AreaFocus` | PUT | Yes | Area focus |
| `/LAPI/V1.0/PTZ/PTZAngleLimit` | GET/PUT | Yes | PTZ angle limits |
| `/LAPI/V1.0/PTZ/PTZAngleLimitSwitch` | GET/PUT | Yes | Angle limit switch |
| `/LAPI/V1.0/PTZ/PresetLink` | GET/PUT | Yes | Preset linkage |
| `/LAPI/V1.0/PTZ/ResumeTime` | GET/PUT | Yes | Resume time after manual |
| `/LAPI/PTZ/Capabilities` | GET | Yes | PTZ capabilities |
| `/LAPI/PTZ/IVACruisePlan` | GET/PUT | Yes | IVA cruise plan |

### Example: Move PTZ
```bash
curl -X PUT -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"Command": "LEFT", "Speed": 50}' \
  http://192.168.30.178/LAPI/V1.0/Channel/0/PTZ/PTZCtrl
```

---

## 7. Media & Streaming

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/Media/LivingStream` | GET | Yes | Live stream URL |
| `/LAPI/V1.0/Channel/0/Media/MediaStream` | GET/PUT | Yes | Media stream config |
| `/LAPI/V1.0/Channel/0/Media/MediaStream/StreamInfo/` | GET | Yes | Stream info |
| `/LAPI/V1.0/Channels/0/Media/Video/Streams/` | GET | Yes | Video streams list |
| `/LAPI/V1.0/Channels/0/Media/Video/Streams/RecordURL` | GET | Yes | Recording URL |
| `/LAPI/V1.0/Channels/0/Media/Video/Streams/AdaptiveCfg` | GET/PUT | Yes | Adaptive streaming config |
| `/LAPI/V1.0/Channel/0/Media/Video/Mode` | GET/PUT | Yes | Video mode |
| `/LAPI/V1.0/Channel/0/Media/Video/Streams/DetailInfos` | GET/PUT | Yes | Stream detail info |
| `/LAPI/V1.0/Channel/0/Media/Video/Streams/0/Records?Begin=` | GET | Yes | Search recordings |
| `/LAPI/V1.0/Channel/0/Media/RecordDownload/` | GET | Yes | Download recording |
| `/LAPI/V1.0/Channel/0/Media/RecordDownloadState` | GET | Yes | Download state |
| `/LAPI/V1.0/Channel/0/Media/AutoSendStreams` | GET/PUT | Yes | Auto send streams |
| `/LAPI/V1.0/Channels/0/Media/SnapshotURL` | GET | Yes | Snapshot URL |
| `/LAPI/V1.0/Media/Capture` | POST | Yes | Capture image |
| `/LAPI/V1.0/Media/Audio/Input` | GET/PUT | Yes | Audio input config |
| `/LAPI/V1.0/Media/KeyFrame` | POST | Yes | Request keyframe |
| `/LAPI/V1.0/Media/ImportFile` | POST | Yes | Import file |
| `/LAPI/Media/AnalogoutFormat` | GET/PUT | Yes | Analog output format |

### Example: Get Snapshot URL
```bash
curl -u admin:admin http://192.168.30.178/LAPI/V1.0/Channels/0/Media/SnapshotURL
```

---

## 8. Image & Video Settings

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/Media/OSD` | GET/PUT | Yes | OSD configuration |
| `/LAPI/V1.0/Channel/0/Media/OSDStyle` | GET/PUT | Yes | OSD style |
| `/LAPI/V1.0/Channel/0/Media/Marquee` | GET/PUT | Yes | Marquee text |
| `/LAPI/V1.0/Channel/0/Media/PrivacyMask` | GET/PUT | Yes | Privacy mask zones |
| `/LAPI/V1.0/Channel/0/Media/PrivacyMask/CoverOSD` | GET/PUT | Yes | OSD privacy cover |
| `/LAPI/V1.0/Channel/0/Media/PrivacyMask/Mode` | GET/PUT | Yes | Privacy mask mode |
| `/LAPI/V1.0/Channel/0/Media/CoverOSDZooms` | GET/PUT | Yes | OSD cover zoom |
| `/LAPI/V1.0/Channel/0/Media/ROI` | GET/PUT | Yes | Region of interest |
| `/LAPI/V1.0/Channel/0/Media/Orientation` | GET/PUT | Yes | Image orientation |
| `/LAPI/V1.0/Channel/0/Media/Watermark` | GET/PUT | Yes | Watermark settings |
| `/LAPI/V1.0/Channel/0/Media/RTSPMulticastAddr` | GET/PUT | Yes | RTSP multicast address |
| `/LAPI/V1.0/Channels/0/Image/Enhance` | GET/PUT | Yes | Image enhancement |
| `/LAPI/V1.0/Channels/0/Image/LampCtrl/` | GET/PUT | Yes | IR lamp control |
| `/LAPI/V1.0/Channel/0/Image/LensType` | GET/PUT | Yes | Lens type |
| `/LAPI/V1.0/Channel/0/Image/LensParam` | GET/PUT | Yes | Lens parameters |
| `/LAPI/V1.0/Channel/0/Image/LDC` | GET/PUT | Yes | Lens distortion correction |
| `/LAPI/V1.0/Channel/0/Image/Defog/` | GET/PUT | Yes | Defog settings |
| `/LAPI/V1.0/Channel/0/Image/ImageParamReset` | PUT | Yes | Reset image params |
| `/LAPI/V1.0/Channel/0/Image/DefaultScene` | GET/PUT | Yes | Default scene |
| `/LAPI/V1.0/Channel/0/Image/CurrentScene` | GET/PUT | Yes | Current scene |
| `/LAPI/V1.0/Channel/0/Image/Scene?Index=` | GET/PUT | Yes | Scene by index |
| `/LAPI/V1.0/Channel/0/Image/SceneEnvironment?Type=` | GET/PUT | Yes | Scene environment |
| `/LAPI/V1.0/Channel/0/Image/SceneAutoSwitch` | GET/PUT | Yes | Auto scene switching |
| `/LAPI/Image/Focus/` | GET/PUT | Yes | Focus settings |
| `/LAPI/Image/WhiteBalance` | GET/PUT | Yes | White balance |
| `/LAPI/Image/Advanced/Exposure` | GET/PUT | Yes | Exposure settings |
| `/LAPI/Image/LightMode` | GET/PUT | Yes | Light mode |
| `/LAPI/V1.0/Image/SetBackFocus` | PUT | Yes | Set back focus |
| `/LAPI/V1.0/Image/ImageStable` | GET/PUT | Yes | Image stabilization |
| `/LAPI/V1.0/Image/Enlarge` | GET/PUT | Yes | Digital zoom |
| `/LAPI/V1.0/Image/FocalLimit` | GET/PUT | Yes | Focal length limit |
| `/LAPI/Media/OSDs/Mode` | GET/PUT | Yes | OSD mode |
| `/LAPI/Media/PicOSD` | GET/PUT | Yes | Picture OSD |
| `/LAPI/Media/SubOSD` | GET/PUT | Yes | Sub OSD |
| `/LAPI/Media/SubOSDExpand` | GET/PUT | Yes | Sub OSD expand |

---

## 9. Storage

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/Media/Storage` | GET/PUT | Yes | Storage configuration |
| `/LAPI/V1.0/Channel/0/Media/AlarmStorage` | GET/PUT | Yes | Alarm storage settings |
| `/LAPI/V1.0/Channel/0/Media/SDFormat` | PUT | Yes | **Format SD card** |
| `/LAPI/V1.0/Channel/0/System/DeviceStatus/SD` | GET | Yes | SD card status |
| `/LAPI/Media/SDCardSwitch` | GET/PUT | Yes | SD card switch |
| `/LAPI/System/Nas` | GET/PUT | Yes | NAS configuration |

### Example: Format SD Card
```bash
curl -X PUT -u admin:admin \
  http://192.168.30.178/LAPI/V1.0/Channel/0/Media/SDFormat
```

---

## 10. Alarms & Events

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channels/0/Alarm/MotionDetection/AreaType` | GET/PUT | Yes | Motion detection type |
| `/LAPI/V1.0/Channels/0/Alarm/MotionDetection/Areas/Grid` | GET/PUT | Yes | Motion detection grid |
| `/LAPI/V1.0/Channels/0/Alarm/MotionDetection/LinkageActions` | GET/PUT | Yes | Motion linkage actions |
| `/LAPI/V.0/Channels/0/Alarm/MotionDetection/Areas/Rectangle` | GET/PUT | Yes | Motion detection areas |
| `/LAPI/V1.0/Alarm/MotionActivity/Areas` | GET/PUT | Yes | Motion activity areas |
| `/LAPI/V1.0/Alarm/MotionInterval` | GET/PUT | Yes | Motion interval |
| `/LAPI/Alarm/MotionAreaLinkPre` | GET/PUT | Yes | Motion area preset link |
| `/LAPI/V1.0/Channels/0/Alarm/AudioDetection/Rule` | GET/PUT | Yes | Audio detection rule |
| `/LAPI/V1.0/Channels/0/Alarm/AudioDetection/LinkageActions` | GET/PUT | Yes | Audio linkage actions |
| `/LAPI/V1.0/Channels/0/Alarm/TamperDetection/Rule` | GET/PUT | Yes | Tamper detection rule |
| `/LAPI/V1.0/Channels/0/Alarm/TamperDetection/LinkageActions` | GET/PUT | Yes | Tamper linkage actions |
| `/LAPI/V1.0/Alarm/LowTemperatureDetectLink` | GET/PUT | Yes | Low temp detection |
| `/LAPI/V1.0/Alarm/HighTemperatureDetectLink` | GET/PUT | Yes | High temp detection |
| `/LAPI/V1.0/Channel/0/Alarm/AudioVolume` | GET/PUT | Yes | Audio volume/alarm |
| `/LAPI/V1.0/Channel/0/Event/Subscription/Subscribers` | GET/PUT | Yes | Event subscribers |

### Event Status Endpoints
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/Event/Status/Update` | GET | Yes | Update events |
| `/LAPI/V1.0/Channel/0/Event/Status/NetWorkChange` | GET | Yes | Network change events |
| `/LAPI/V1.0/Channel/0/Event/Status/UserInfoChange` | GET | Yes | User info change events |
| `/LAPI/V1.0/Channel/0/Event/Status/MemoryCardFormate` | GET | Yes | SD format events |
| `/LAPI/V1.0/Channel/0/Event/Status/PortMap` | GET | Yes | Port map events |
| `/LAPI/V1.0/Channel/0/Event/Status/ManagerServer` | GET | Yes | Manager server events |
| `/LAPI/V1.0/Channel/0/Event/Status/PhotoServer` | GET | Yes | Photo server events |
| `/LAPI/V1.0/Channel/0/Event/Status/SD` | GET | Yes | SD card events |
| `/LAPI/V1.0/Channel/0/Event/Status/PTZ` | GET | Yes | PTZ events |
| `/LAPI/V1.0/Channel/0/Event/Status/SceneCurrent` | GET | Yes | Scene change events |

---

## 11. Smart/IVA Features

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Smart/Mode` | GET/PUT | Yes | Smart mode |
| `/LAPI/V1.0/Smart/DetectMode` | GET/PUT | Yes | Detection mode |
| `/LAPI/Smart/IVAEnable` | GET/PUT | Yes | IVA enable |
| `/LAPI/Smart/IVASceneList` | GET | Yes | IVA scene list |
| `/LAPI/Smart/IVARuleList` | GET/PUT | Yes | IVA rules |
| `/LAPI/Smart/IVAManualSnap` | POST | Yes | Manual IVA snapshot |
| `/LAPI/Smart/IVAPressLine` | GET/PUT | Yes | IVA line crossing |
| `/LAPI/Smart/IVAStayTime` | GET/PUT | Yes | IVA stay time |
| `/LAPI/Smart/IVALPRCheck` | GET/PUT | Yes | License plate check |
| `/LAPI/Smart/IVALinkStorSwitch` | GET/PUT | Yes | IVA storage link |
| `/LAPI/Smart/IVASnapPictureID` | GET | Yes | IVA snap picture ID |
| `/LAPI/V1.0/Channel/0/Smart/SmartRule/` | GET/PUT | Yes | Smart rules |
| `/LAPI/V1.0/Channel/0/Smart/PeopleCount` | GET/PUT | Yes | People counting |
| `/LAPI/V1.0/Channel/0/Smart/HeatMap` | GET/PUT | Yes | Heat map |
| `/LAPI/V1.0/Channel/0/Smart/RoadDetect` | GET/PUT | Yes | Road detection |
| `/LAPI/V1.0/Channels/0/Smart/AllDetection/Rule` | GET/PUT | Yes | All detection rules |
| `/LAPI/V1.0/Channels/0/Smart/AllDetection/Areas` | GET/PUT | Yes | Detection areas |
| `/LAPI/V1.0/Channels/0/Smart/AllDetection/LinkageActions` | GET/PUT | Yes | Detection linkage |
| `/LAPI/V1.0/Smart/ParkingDetection` | GET/PUT | Yes | Parking detection |
| `/LAPI/V1.0/Smart/IsPortsStat` | GET | Yes | Port status |
| `/LAPI/V1.0/Smart/IsStatus` | GET | Yes | Smart status |
| `/LAPI/V1.0/Smart/IsType` | GET | Yes | Smart type |
| `/LAPI/V1.0/Intelligent/InstallGuide` | GET | Yes | Installation guide |
| `/LAPI/Intelligent/ParkAllStatus` | GET | Yes | All parking status |
| `/LAPI/Intelligent/DetectArea` | GET/PUT | Yes | Detection area |
| `/LAPI/Intelligent/DrivewayLine` | GET/PUT | Yes | Driveway line |
| `/LAPI/Intelligent/TriggerLine` | GET/PUT | Yes | Trigger line |
| `/LAPI/Intelligent/PlateIdentify` | GET/PUT | Yes | Plate identification |
| `/LAPI/Intelligent/TrafficEvent` | GET/PUT | Yes | Traffic events |
| `/LAPI/Intelligent/TrafficParam` | GET/PUT | Yes | Traffic parameters |

---

## 12. Face Recognition

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Smart/FaceEnable` | GET/PUT | Yes | Enable face recognition |
| `/LAPI/V1.0/Smart/FaceDetection/Rule` | GET/PUT | Yes | Face detection rules |
| `/LAPI/V1.0/Smart/FaceDetection/Areas/Detections` | GET/PUT | Yes | Face detection areas |
| `/LAPI/V1.0/Smart/FaceDetection/LinkageActions` | GET/PUT | Yes | Face detection linkage |
| `/LAPI/V1.0/Smart/Face/Recognition/Monitor` | GET/PUT | Yes | Face recognition monitor |
| `/LAPI/V1.0/Smart/FaceRecognition/DatabaseInfo` | GET | Yes | Face database info |
| `/LAPI/V1.0/Smart/FaceRecognition/Database/id/BasicInfos` | GET/PUT | Yes | Face DB basic info |
| `/LAPI/V1.0/Smart/LibraryFile` | GET/PUT | Yes | Library file management |
| `/LAPI/V1.0/Smart/LibraryFile/Initialization?LibID=` | POST | Yes | Initialize library |
| `/LAPI/V1.0/Smart/LibraryFile/Initialization/Status?LibID=` | GET | Yes | Library init status |
| `/LAPI/V1.0/Smart/FaceLibraryFile?Type=1&Name=work/` | GET | Yes | Face library file |
| `/LAPI/V1.0/Smart/FacePicture?Type=1&Name=work/` | GET | Yes | Face picture |
| `/LAPI/V1.0/Smart/FeatureGalleyFile/` | GET | Yes | Feature gallery |
| `/LAPI/Smart/FeatureGalleyFileURL` | GET | Yes | Feature gallery URL |
| `/LAPI/V1.0/PeopleLibraries/` | GET | Yes | People libraries list |
| `/LAPI/V1.0/PeopleLibraries/BasicInfo` | GET | Yes | Libraries basic info |
| `/LAPI/V1.0/PeopleLibraries/Capabilities` | GET | Yes | Library capabilities |
| `/LAPI/V1.0/PeopleLibraries/Capacity` | GET | Yes | Library capacity |
| `/LAPI/V1.0/PeopleLibraries/ID/People` | GET/PUT/DELETE | Yes | People in library |
| `/LAPI/V1.0/PeopleLibraries/ID/People/Info` | GET | Yes | Person info |
| `/LAPI/V1.0/PeopleLibraries/ID/PermissionInfo` | GET/PUT | Yes | Permission info |
| `/LAPI/V1.0/PeopleLibraries/ID/UpdateTime` | GET | Yes | Library update time |

---

## 13. PACS (Access Control)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/PACS/DeviceInfo` | GET | Yes | PACS device info |
| `/LAPI/V1.0/PACS/Controller/WorkStatus` | GET | Yes | Controller status |
| `/LAPI/V1.0/PACS/Controller/OpenDoorMode` | GET/PUT | Yes | Door open mode |
| `/LAPI/V1.0/PACS/Controller/AlarmOutputCfg` | GET/PUT | Yes | Alarm output config |
| `/LAPI/V1.0/PACS/Controller/AttributeVerification/Rule` | GET/PUT | Yes | Attribute verification |
| `/LAPI/V1.0/PACS/Controller/LongConnectionInfo` | GET | Yes | Long connection info |
| `/LAPI/V1.0/PACS/Controller/KTPBasicInfo` | GET/PUT | Yes | KTP basic info |
| `/LAPI/V1.0/PACS/Controller/GUIFile` | GET/PUT | Yes | GUI file config |
| `/LAPI/V1.0/Channels/0/PACS/Controller/WRBasicInfo` | GET/PUT | Yes | WR basic info |
| `/LAPI/V1.0/PACS/GUI/HomeIcons` | GET/PUT | Yes | Home icons |
| `/LAPI/V1.0/PACS/GUI/HomeSlogan` | GET/PUT | Yes | Home slogan |
| `/LAPI/V1.0/PACS/GUI/ScreenSaverInfo` | GET/PUT | Yes | Screen saver |
| `/LAPI/V1.0/PACS/GUI/FaceFrameInfo` | GET/PUT | Yes | Face frame info |
| `/LAPI/V1.0/PACS/GUI/PicFile?Type=` | GET/PUT | Yes | Picture file |
| `/LAPI/V1.0/PACS/DoorStation/CallCfg` | GET/PUT | Yes | Door station call |
| `/LAPI/V1.0/PACS/Peripheral/BasicInfo` | GET/PUT | Yes | Peripheral info |
| `/LAPI/V1.0/PACS/Reader/QRCodeInfo` | GET/PUT | Yes | QR code reader |
| `/LAPI/V1.0/PACS/Temperature/Compensation` | GET/PUT | Yes | Temp compensation |
| `/LAPI/V1.0/PACS/VerifyTemplates/` | GET/PUT | Yes | Verify templates |
| `/LAPI/V1.0/PACS/VerifyTemplates/BasicInfo` | GET | Yes | Template basic info |
| `/LAPI/V1.0/Smart/FaceTurnstiles/ComparisonCfg` | GET/PUT | Yes | Turnstile comparison |
| `/LAPI/V1.0/Smart/FaceTurnstiles/GUIInfo` | GET/PUT | Yes | Turnstile GUI |
| `/LAPI/V1.0/Smart/FaceTurnstiles/LightCfg` | GET/PUT | Yes | Turnstile lights |
| `/LAPI/V1.0/Smart/FaceTurnstiles/RecordReportCfg` | GET/PUT | Yes | Record reporting |
| `/LAPI/V1.0/Smart/FaceTurnstiles/VerificationModeCfg` | GET/PUT | Yes | Verification mode |
| `/LAPI/V1.0/Smart/FaceTurnstiles/WorkModeCfg` | GET/PUT | Yes | Work mode |
| `/LAPI/V1.0/Intelligent/GateContrl?Open` | PUT | Yes | **Open gate/door** |

### Example: Open Door/Gate
```bash
curl -X PUT -u admin:admin \
  http://192.168.30.178/LAPI/V1.0/Intelligent/GateContrl?Open
```

---

## 14. I/O Control

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/IO/InputSwitches/id/BasicInfos` | GET/PUT | Yes | Input switch info |
| `/LAPI/V1.0/IO/InputSwitches/1/LinkageActions` | GET/PUT | Yes | Input linkage |
| `/LAPI/V1.0/IO/OutputSwitches/id/BasicInfos` | GET/PUT | Yes | Output switch info |
| `/LAPI/V1.0/Channel/0/IO/Serial` | GET/PUT | Yes | Serial port config |
| `/LAPI/V1.0/Channel/0/IO/SerialTrans` | GET/PUT | Yes | Serial transparent |
| `/LAPI/V1.0/Channel/0/IO/SerialOSDReport` | GET/PUT | Yes | Serial OSD report |
| `/LAPI/V1.0/IO/SecurityModuleCfg` | GET/PUT | Yes | Security module |
| `/LAPI/V1.0/IO/QRCodeCtrl` | GET/PUT | Yes | QR code control |
| `/LAPI/V1.0/IO/RangFinderCtrl` | GET/PUT | Yes | Range finder |
| `/LAPI/IO/IOPort` | GET/PUT | Yes | I/O ports |
| `/LAPI/IO/FlashLight` | GET/PUT | Yes | Flash light control |
| `/LAPI/IO/Laser` | GET/PUT | Yes | Laser control |
| `/LAPI/IO/NDFilter` | GET/PUT | Yes | ND filter |
| `/LAPI/IO/Polarizer` | GET/PUT | Yes | Polarizer control |
| `/LAPI/IO/Radar` | GET/PUT | Yes | Radar interface |
| `/LAPI/IO/VehicleDetector` | GET/PUT | Yes | Vehicle detector |
| `/LAPI/IO/USBDeviceInfo` | GET | Yes | USB device info |
| `/LAPI/IO/SubDeviceSwitch` | GET/PUT | Yes | Sub device switch |
| `/LAPI/IO/ExpandSubDevice` | GET/PUT | Yes | Expand sub device |
| `/LAPI/Demo/LaserControl/reboot` | PUT | Yes | Laser reboot |
| `/LAPI/Demo/LaserControl/restore` | PUT | Yes | Laser restore |

---

## 15. Demo/Debug Endpoints

**Hidden/Debug functionality**

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Channel/0/Demo/AcceptanceMode` | GET/PUT | Yes | Acceptance mode |
| `/LAPI/V1.0/Channel/0/Demo/BNCOSD` | GET/PUT | Yes | BNC OSD |
| `/LAPI/V1.0/Channel/0/Demo/ClearFog` | PUT | Yes | Clear fog |
| `/LAPI/V1.0/Channel/0/Demo/CustomOSDFontSize` | GET/PUT | Yes | Custom OSD font |
| `/LAPI/V1.0/Channel/0/Demo/DefaultOSDFontSize` | GET/PUT | Yes | Default OSD font |
| `/LAPI/V1.0/Channel/0/Demo/FacePicOptimization` | GET/PUT | Yes | Face pic optimize |
| `/LAPI/V1.0/Channel/0/Demo/GBTCPStream` | GET/PUT | Yes | GB TCP stream |
| `/LAPI/V1.0/Channel/0/Demo/H264PayloadType` | GET/PUT | Yes | H264 payload type |
| `/LAPI/V1.0/Channel/0/Demo/InvertOSDFont` | GET/PUT | Yes | Invert OSD font |
| `/LAPI/V1.0/Channel/0/Demo/LensMotorReset` | PUT | Yes | Lens motor reset |
| `/LAPI/V1.0/Channel/0/Demo/LowDelay` | GET/PUT | Yes | Low delay mode |
| `/LAPI/V1.0/Channel/0/Demo/ObjectTraceFrame` | GET/PUT | Yes | Object trace frame |
| `/LAPI/V1.0/Channel/0/Demo/ReviseTime` | GET/PUT | Yes | Revise time |
| `/LAPI/V1.0/Channel/0/Demo/SansuoCheck` | GET/PUT | Yes | Sansuo check |
| `/LAPI/V1.0/Channel/0/Demo/StreamSendMode` | GET/PUT | Yes | Stream send mode |
| `/LAPI/V1.0/Channel/0/Demo/ViewMode` | GET/PUT | Yes | View mode |
| `/LAPI/V1.0/Channel/0/Demo/ZoomLimitSwitch` | GET/PUT | Yes | Zoom limit switch |
| `/LAPI/V1.0/Channel/0/Demo/TLBreak` | GET/PUT | Yes | Traffic light break |
| `/LAPI/Demo/CoilSpeedAdjust` | GET/PUT | Yes | Coil speed adjust |
| `/LAPI/Demo/ExPtzSpecFunc` | GET/PUT | Yes | Extended PTZ |
| `/LAPI/Demo/FanCtrlMode` | GET/PUT | Yes | Fan control mode |
| `/LAPI/Demo/LensInitCfg` | GET/PUT | Yes | Lens init config |
| `/LAPI/Demo/LowDelay` | GET/PUT | Yes | Low delay |
| `/LAPI/Demo/PTZCapReportLimit` | GET/PUT | Yes | PTZ cap report limit |
| `/LAPI/V1.0/Channels/0/Demo/MotionMetaData` | GET/PUT | Yes | Motion metadata |

---

## 16. Intelligent Traffic

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/LAPI/V1.0/Intelligent/CarPlateList/BlackList` | GET/PUT | Yes | Blacklist plates |
| `/LAPI/V1.0/Intelligent/CarPlateList/WhiteList` | GET/PUT | Yes | Whitelist plates |
| `/LAPI/V1.0/Intelligent/CarPlateList/PeccancyList` | GET/PUT | Yes | Violation list |
| `/LAPI/V1.0/Intelligent/CarPlateList/PeccancyFilterList` | GET/PUT | Yes | Violation filter |
| `/LAPI/V1.0/Intelligent/CarPlateList/IdentifyCorrectList` | GET/PUT | Yes | ID correct list |
| `/LAPI/V1.0/Intelligent/CarPlateList/AccmmodationLaneList` | GET/PUT | Yes | Lane list |
| `/LAPI/V1.0/Intelligent/CarPlateList/PassCarWhiteList` | GET/PUT | Yes | Pass car whitelist |
| `/LAPI/Intelligent/IVABreakRule` | GET/PUT | Yes | IVA break rules |
| `/LAPI/Intelligent/IVASimilarLPRFilter` | GET/PUT | Yes | Similar LPR filter |
| `/LAPI/Intelligent/IVAZoomMarkFlag` | GET/PUT | Yes | Zoom mark flag |
| `/LAPI/Intelligent/IVAManualSnapObjMark` | GET/PUT | Yes | Manual snap mark |
| `/LAPI/Intelligent/LedRemoteCtrl` | GET/PUT | Yes | LED remote control |
| `/LAPI/Intelligent/ManualCapturePeccancy` | POST | Yes | Manual violation capture |
| `/LAPI/Intelligent/NetworkPeripheralList` | GET | Yes | Network peripherals |
| `/LAPI/Intelligent/PeccancyWay` | GET/PUT | Yes | Violation method |
| `/LAPI/Intelligent/PicBitRate` | GET/PUT | Yes | Picture bitrate |
| `/LAPI/Intelligent/TimerCapture` | GET/PUT | Yes | Timer capture |
| `/LAPI/Intelligent/TrafficLightInensity` | GET/PUT | Yes | Traffic light intensity |
| `/LAPI/Intelligent/VCPFilterPolicy` | GET/PUT | Yes | VCP filter policy |
| `/LAPI/INTELLIGENT/IVACapNoMoveObj` | GET/PUT | Yes | Capture non-moving |
| `/LAPI/INTELLIGENT/IVACaptureDelay` | GET/PUT | Yes | Capture delay |
| `/LAPI/INTELLIGENT/IVACarHeadTailClassify` | GET/PUT | Yes | Car head/tail classify |
| `/LAPI/INTELLIGENT/IVAIllegalParkFilter` | GET/PUT | Yes | Illegal park filter |
| `/LAPI/INTELLIGENT/PeccancyParamReset` | PUT | Yes | Reset violation params |
| `/LAPI/INTELLIGENT/IOParamReset` | PUT | Yes | Reset I/O params |
| `/LAPI/Smart/DriveWay` | GET/PUT | Yes | Driveway config |
| `/LAPI/Smart/EPDriveWay` | GET/PUT | Yes | EP driveway |
| `/LAPI/Smart/EPVideoDetect` | GET/PUT | Yes | EP video detection |
| `/LAPI/Smart/ExpandDriveWay` | GET/PUT | Yes | Expand driveway |
| `/LAPI/Smart/TrafficLight` | GET/PUT | Yes | Traffic light config |
| `/LAPI/Smart/RedLightParkTime` | GET/PUT | Yes | Red light park time |
| `/LAPI/Smart/ViolationCapture` | GET/PUT | Yes | Violation capture |
| `/LAPI/Smart/ViolationMode` | GET/PUT | Yes | Violation mode |
| `/LAPI/Smart/Illegal/IllegalVehicleParam` | GET/PUT | Yes | Illegal vehicle params |
| `/LAPI/Smart/Illegal/IllegalVideotape` | GET/PUT | Yes | Illegal videotape |
| `/LAPI/System/DeviceStatus/TrafficLightStatus` | GET | Yes | Traffic light status |
| `/LAPI/System/DeviceStatus/TrafficLightColour` | GET | Yes | Traffic light color |
| `/LAPI/System/DeviceStatus/VehQueueLen` | GET | Yes | Vehicle queue length |

---

## Security Testing Checklist

### High-Priority Endpoints for Auth Bypass Testing

```bash
# Test without authentication
TARGET=192.168.30.178

# Device info (often exposed)
curl -v http://$TARGET/LAPI/V1.0/System/DeviceBasicInfo

# RSA public key (may leak)
curl -v http://$TARGET/LAPI/V1.0/System/Security/RSA

# Telnet enable (critical)
curl -v http://$TARGET/LAPI/V1.0/Channel/0/NetWork/Telnet

# ONVIF debug (can disable auth)
curl -v http://$TARGET/LAPI/V1.0/Channel/0/Demo/OnvifDebug

# Reboot (critical)
curl -v http://$TARGET/LAPI/V1.0/System/Reboot

# Factory reset (critical)
curl -v http://$TARGET/LAPI/V1.0/System/FactoryReset

# Network config
curl -v http://$TARGET/LAPI/V1.0/Network/Interfaces/1

# User list
curl -v http://$TARGET/LAPI/V1.0/Channel/0/System/Users

# Snapshot
curl -v http://$TARGET/LAPI/V1.0/Channels/0/Media/SnapshotURL

# Open door/gate
curl -v http://$TARGET/LAPI/V1.0/Intelligent/GateContrl?Open
```

### Endpoints by Risk Level

**CRITICAL (Device Compromise)**
- `/LAPI/V1.0/Channel/0/NetWork/Telnet` - Enable remote shell
- `/LAPI/V1.0/System/FactoryReset` - Wipe device
- `/LAPI/V1.0/System/Reboot` - Denial of service
- `/LAPI/V1.0/System/UploadFirmware` - Firmware replacement
- `/LAPI/V1.0/System/Upgrade` - Firmware upgrade
- `/LAPI/V1.0/Intelligent/GateContrl?Open` - Physical access

**HIGH (Credential/Config Theft)**
- `/LAPI/V1.0/Channel/0/System/Users` - User enumeration
- `/LAPI/V1.0/System/ConfigurationInfo/` - Full config backup
- `/LAPI/V1.0/Network/Interfaces/1` - Network config
- `/LAPI/V1.0/PeopleLibraries/` - Biometric data

**MEDIUM (Information Disclosure)**
- `/LAPI/V1.0/System/DeviceBasicInfo` - Device fingerprinting
- `/LAPI/V1.0/System/Logs` - Log access
- `/LAPI/V1.0/Channels/0/Media/SnapshotURL` - Camera access

---

## HTTP Methods Reference

| Method | Usage |
|--------|-------|
| GET | Retrieve configuration/status |
| PUT | Update configuration |
| POST | Create resource / Execute action |
| DELETE | Remove resource |

---

## Response Codes

| Code | Meaning |
|------|---------|
| 0 | RESULT_CODE_SUCCEED |
| 1 | RESULT_CODE_FAIL |
| 2 | RESULT_CODE_INVALID_PARAM |
| 364 | ERR_SDK_COMMON_LOCK_USER |
| 458 | RESULT_CODE_USERFULL |
| 459 | RESULT_CODE_USERNONEXIST |
| 460 | RESULT_CODE_PASSWD_INVALID |
| 472 | RESULT_CODE_TIMEOUT |
| 999 | RESULT_CODE_KEEPALIVEFAIL |

---

## Notes

- All endpoints use JSON for request/response bodies
- Authentication: HTTP Basic Auth or session cookie
- Default port: 80 (HTTP), 443 (HTTPS)
- ONVIF services on port 81
- Many `/Demo/` endpoints are hidden debug functions
- `/LAPI/V1.0/Channel/0/Demo/OnvifDebug` can disable ONVIF authentication
