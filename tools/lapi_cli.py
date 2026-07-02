#!/usr/bin/env python3
"""
LAPI CLI - Uniview/Digital Ally REST API Testing Tool

Usage:
    ./lapi_cli.py -t 192.168.30.178 system info
    ./lapi_cli.py -t 192.168.30.178 -u admin -p admin telnet enable
    ./lapi_cli.py -t 192.168.30.178 --no-auth system info

Author: Jon 'GainSec' Gaines
Target: Uniview OET-213H-NB / Digital Ally ThermoVu DTM-600
"""

import argparse
import requests
import json
import sys
import urllib3
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin"
SUPER_PASSWORD = "87654321"
DEFAULT_TIMEOUT = 10

# ============================================================================
# LAPI Endpoint Definitions
# ============================================================================

class Endpoints:
    """All LAPI endpoint definitions organized by category"""

    # System & Device Info
    SYSTEM = {
        "info": "/LAPI/V1.0/System/DeviceBasicInfo",
        "run_info": "/LAPI/V1.0/System/DeviceRunInfo",
        "reboot": "/LAPI/V1.0/System/Reboot",
        "factory_reset": "/LAPI/V1.0/System/FactoryReset",
        "language": "/LAPI/V1.0/System/Language",
        "logs": "/LAPI/V1.0/System/Logs",
        "time": "/LAPI/V1.0/System/TimePrivate",
        "local_time": "/LAPI/V1.0/System/TimePrivate/LocalTime",
        "dst": "/LAPI/V1.0/System/Time/DST",
        "ntp": "/LAPI/V1.0/System/Time/NTP",
        "ntp_test": "/LAPI/System/Time/NTP/Test",
        "sync_mode": "/LAPI/V1.0/System/Time/SyncMode",
        "keepalive": "/LAPI/V1.0/System/KeepAlive",
        "location": "/LAPI/V1.0/System/LocationInfo",
        "battery": "/LAPI/V1.0/System/BatteryInfo",
        "fan": "/LAPI/V1.0/System/FanCtrl",
        "hide_info": "/LAPI/V1.0/System/HideDeviceInfo",
        "diagnosis_url": "/LAPI/V1.0/System/Diagnosis/FileURL",
        "diagnosis_status": "/LAPI/V1.0/System/Diagnosis/PackStatus",
        "config_url": "/LAPI/V1.0/System/ConfigurationInfoURL",
        "config": "/LAPI/V1.0/System/ConfigurationInfo/",
        "debug_msg": "/LAPI/V1.0/System/DebugMessage",
        "extra_log": "/LAPI/V1.0/System/ExtraLogSwitch",
        "manage_server": "/LAPI/V1.0/System/ManageServer",
        "bm_server": "/LAPI/V1.0/System/BMServer",
    }

    # Authentication & Security
    AUTH = {
        "login": "/LAPI/V1.0/System/Security/Login",
        "channel_login": "/LAPI/V1.0/Channel/0/System/Login",
        "users": "/LAPI/V1.0/Channel/0/System/Users",
        "rsa": "/LAPI/V1.0/System/Security/RSA",
        "access_policy": "/LAPI/V1.0/System/Security/AccessPolicy",
        "privacy_policy": "/LAPI/V1.0/System/PrivacyPolicy/Status",
        "password_info": "/LAPI/V1.0/System/CurrentPasswordInfo",
        "secret_key": "/LAPI/V1.0/System/SecretKeyInfo",
        "http_auth": "/LAPI/V1.0/NetWork/HttpAuth",
        "rtsp_auth": "/LAPI/V1.0/NetWork/RtspAuth",
        "secure_access": "/LAPI/V1.0/NetWork/SecureAccess",
    }

    # Network Configuration
    NETWORK = {
        "interfaces": "/LAPI/V1.0/Network/Interfaces/1",
        "dns": "/LAPI/V1.0/NetWork/DNS",
        "port": "/LAPI/V1.0/NetWork/Port",
        "ddns": "/LAPI/V1.0/NetWork/DDNS",
        "ftp": "/LAPI/V1.0/NetWork/FTP",
        "ftp_test": "/LAPI/V1.0/NetWork/FTP/Test",
        "email": "/LAPI/V1.0/Channel/0/NetWork/Email",
        "email_test": "/LAPI/V1.0/NetWork/Email/Test",
        "snmp": "/LAPI/V1.0/NetWork/SNMP",
        "https": "/LAPI/V1.0/NetWork/HTTPS",
        "ssl_cert": "/LAPI/V1.0/Network/HTTPS_SSLCERT",
        "upnp": "/LAPI/V1.0/NetWork/UNP",
        "regist_info": "/LAPI/V1.0/NetWork/RegistInfo",
        "arp_binding": "/LAPI/V1.0/NetWork/ArpBinding",
        "soft_ap": "/LAPI/V1.0/NetWork/SoftAP",
        "soft_ap_wifi": "/LAPI/V1.0/NetWork/SoftAPWiFi",
        "net_4g": "/LAPI/V1.0/NetWork/Net4G",
        "net_4g_status": "/LAPI/V1.0/NetWork/Net4GStatus",
        "ieee8021x": "/LAPI/V1.0/NetWork/IEEE8021x",
        "sslvpn": "/LAPI/V1.0/NetWork/SSLVPN",
        "wifi_config": "/LAPI/V1.0/NetWork/WiFi/Configuration",
        "wifi_scan": "/LAPI/V1.0/NetWork/WiFi/ScanInfo",
        "wifi_status": "/LAPI/V1.0/NetWork/WiFi/LinkStatus",
        "ip_filter": "/LAPI/V1.0/Channel/0/NetWork/IPFilter",
        "qos": "/LAPI/V1.0/Channel/0/NetWork/QOS",
        "port_map": "/LAPI/V1.0/Channel/0/NetWork/PortMap",
        "check_port": "/LAPI/V1.0/Channel/0/NetWork/CheckPort",
        "ddns_check": "/LAPI/V1.0/Channel/0/NetWork/DDNSDomainCheck",
        "routes": "/LAPI/Network/Routes",
        "cloud": "/LAPI/V1.0/Network/Cloud",
        "cloud_unreg": "/LAPI/V1.0/Network/Cloud/Unregistration",
    }

    # Telnet & Debug (Critical)
    TELNET = {
        "status": "/LAPI/V1.0/Channel/0/NetWork/Telnet",
        "enable": "/LAPI/V1.0/Channel/0/NetWork/Telnet",
        "disable": "/LAPI/V1.0/Channel/0/NetWork/Telnet",
        "onvif_debug": "/LAPI/V1.0/Channel/0/Demo/OnvifDebug",
        "net_detect": "/LAPI/V1.0/Channel/0/Demo/NetDetect",
        "wiegand_debug": "/LAPI/V1.0/Channel/0/Demo/WiegandDebug",
        "image_debug": "/LAPI/V1.0/Channel/0/Image/DebugSwitch",
        "ep_tg_type": "/LAPI/Demo/Debug/EpTgType",
        "debug_ep_msg": "/LAPI/Demo/Debug/DebugEpMsg",
        "debug_capture": "/LAPI/Demo/Debug/DebugCaputrePara",
        "debug_flash": "/LAPI/Demo/Debug/DebugFlashExposure",
        "debug_polarizer": "/LAPI/Demo/Debug/DebugPolarizer",
        "debug_heat": "/LAPI/Demo/Debug/Heat",
        "iq_debug": "/LAPI/V1.0/Channel/0/Demo/Debug/IQDebugInfo",
        "audio_agc": "/LAPI/V1.0/Channel/0/Demo/Debug/AudioAGC",
        "enhance_mode": "/LAPI/V1.0/Channel/0/Demo/Debug/EnhanceMode",
    }

    # Firmware & Updates
    FIRMWARE = {
        "upgrade": "/LAPI/V1.0/System/Upgrade",
        "upgrade_info": "/LAPI/V1.0/System/UpgradeInfo",
        "upload": "/LAPI/V1.0/System/UploadFirmware",
        "upgrade_uboot": "/LAPI/V1.0/System/UpgradeUboot",
        "update_status": "/LAPI/V1.0/System/UpdateStatus",
        "temp_upgrade": "/LAPI/PACS/TempModule/Upgrade",
        "temp_status": "/LAPI/PACS/TempModule/UpStatus",
    }

    # PTZ Control
    PTZ = {
        "ctrl": "/LAPI/V1.0/Channel/0/PTZ/PTZCtrl",
        "reset": "/LAPI/V1.0/Channel/0/PTZ/PTZReset",
        "config": "/LAPI/V1.0/Channel/0/PTZ/PTZCfg",
        "driver": "/LAPI/V1.0/Channel/0/PTZ/PTDrvCfg",
        "net_ctrl": "/LAPI/V1.0/Channel/0/PTZ/NetCtrlPTZ",
        "patrols": "/LAPI/V1.0/Channel/0/PTZ/Patrols",
        "wiper": "/LAPI/V1.0/Channel/0/PTZ/WiperInfo",
        "presets": "/LAPI/V1.0/Channels/0/PTZ/Presets",
        "status": "/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZ",
        "abs_position": "/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsPosition",
        "abs_zoom": "/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsZoom",
        "guard": "/LAPI/V1.0/PTZ/Guard",
        "area_focus": "/LAPI/V1.0/PTZ/AreaFocus",
        "angle_limit": "/LAPI/V1.0/PTZ/PTZAngleLimit",
        "capabilities": "/LAPI/PTZ/Capabilities",
        "area_zoom_in": "/LAPI/V1.0/Channels/0/PTZ/AreaZoomIn",
        "area_zoom_out": "/LAPI/V1.0/Channels/0/PTZ/AreaZoomOut",
    }

    # Media & Streaming
    MEDIA = {
        "live_stream": "/LAPI/V1.0/Channel/0/Media/LivingStream",
        "media_stream": "/LAPI/V1.0/Channel/0/Media/MediaStream",
        "stream_info": "/LAPI/V1.0/Channel/0/Media/MediaStream/StreamInfo/",
        "streams": "/LAPI/V1.0/Channels/0/Media/Video/Streams/",
        "record_url": "/LAPI/V1.0/Channels/0/Media/Video/Streams/RecordURL",
        "video_mode": "/LAPI/V1.0/Channel/0/Media/Video/Mode",
        "video_detail": "/LAPI/V1.0/Channel/0/Media/Video/Streams/DetailInfos",
        "record_download": "/LAPI/V1.0/Channel/0/Media/RecordDownload/",
        "download_state": "/LAPI/V1.0/Channel/0/Media/RecordDownloadState",
        "snapshot_url": "/LAPI/V1.0/Channels/0/Media/SnapshotURL",
        "capture": "/LAPI/V1.0/Media/Capture",
        "audio_input": "/LAPI/V1.0/Media/Audio/Input",
        "keyframe": "/LAPI/V1.0/Media/KeyFrame",
    }

    # Image & Video Settings
    IMAGE = {
        "osd": "/LAPI/V1.0/Channel/0/Media/OSD",
        "osd_style": "/LAPI/V1.0/Channel/0/Media/OSDStyle",
        "marquee": "/LAPI/V1.0/Channel/0/Media/Marquee",
        "privacy_mask": "/LAPI/V1.0/Channel/0/Media/PrivacyMask",
        "roi": "/LAPI/V1.0/Channel/0/Media/ROI",
        "orientation": "/LAPI/V1.0/Channel/0/Media/Orientation",
        "watermark": "/LAPI/V1.0/Channel/0/Media/Watermark",
        "enhance": "/LAPI/V1.0/Channels/0/Image/Enhance",
        "lamp_ctrl": "/LAPI/V1.0/Channels/0/Image/LampCtrl/",
        "lens_type": "/LAPI/V1.0/Channel/0/Image/LensType",
        "lens_param": "/LAPI/V1.0/Channel/0/Image/LensParam",
        "ldc": "/LAPI/V1.0/Channel/0/Image/LDC",
        "defog": "/LAPI/V1.0/Channel/0/Image/Defog/",
        "image_reset": "/LAPI/V1.0/Channel/0/Image/ImageParamReset",
        "default_scene": "/LAPI/V1.0/Channel/0/Image/DefaultScene",
        "current_scene": "/LAPI/V1.0/Channel/0/Image/CurrentScene",
        "scene_auto": "/LAPI/V1.0/Channel/0/Image/SceneAutoSwitch",
        "focus": "/LAPI/Image/Focus/",
        "white_balance": "/LAPI/Image/WhiteBalance",
        "exposure": "/LAPI/Image/Advanced/Exposure",
        "light_mode": "/LAPI/Image/LightMode",
        "back_focus": "/LAPI/V1.0/Image/SetBackFocus",
        "image_stable": "/LAPI/V1.0/Image/ImageStable",
        "enlarge": "/LAPI/V1.0/Image/Enlarge",
        "focal_limit": "/LAPI/V1.0/Image/FocalLimit",
    }

    # Storage
    STORAGE = {
        "config": "/LAPI/V1.0/Channel/0/Media/Storage",
        "alarm_storage": "/LAPI/V1.0/Channel/0/Media/AlarmStorage",
        "sd_format": "/LAPI/V1.0/Channel/0/Media/SDFormat",
        "sd_status": "/LAPI/V1.0/Channel/0/System/DeviceStatus/SD",
        "sd_switch": "/LAPI/Media/SDCardSwitch",
        "nas": "/LAPI/System/Nas",
    }

    # Alarms & Events
    ALARM = {
        "motion_type": "/LAPI/V1.0/Channels/0/Alarm/MotionDetection/AreaType",
        "motion_grid": "/LAPI/V1.0/Channels/0/Alarm/MotionDetection/Areas/Grid",
        "motion_linkage": "/LAPI/V1.0/Channels/0/Alarm/MotionDetection/LinkageActions",
        "motion_activity": "/LAPI/V1.0/Alarm/MotionActivity/Areas",
        "motion_interval": "/LAPI/V1.0/Alarm/MotionInterval",
        "audio_detect": "/LAPI/V1.0/Channels/0/Alarm/AudioDetection/Rule",
        "audio_linkage": "/LAPI/V1.0/Channels/0/Alarm/AudioDetection/LinkageActions",
        "tamper_detect": "/LAPI/V1.0/Channels/0/Alarm/TamperDetection/Rule",
        "tamper_linkage": "/LAPI/V1.0/Channels/0/Alarm/TamperDetection/LinkageActions",
        "low_temp": "/LAPI/V1.0/Alarm/LowTemperatureDetectLink",
        "high_temp": "/LAPI/V1.0/Alarm/HighTemperatureDetectLink",
        "audio_volume": "/LAPI/V1.0/Channel/0/Alarm/AudioVolume",
        "subscribers": "/LAPI/V1.0/Channel/0/Event/Subscription/Subscribers",
    }

    # Smart/IVA Features
    SMART = {
        "mode": "/LAPI/V1.0/Smart/Mode",
        "detect_mode": "/LAPI/V1.0/Smart/DetectMode",
        "iva_enable": "/LAPI/Smart/IVAEnable",
        "iva_scenes": "/LAPI/Smart/IVASceneList",
        "iva_rules": "/LAPI/Smart/IVARuleList",
        "iva_manual_snap": "/LAPI/Smart/IVAManualSnap",
        "iva_press_line": "/LAPI/Smart/IVAPressLine",
        "iva_stay_time": "/LAPI/Smart/IVAStayTime",
        "iva_lpr_check": "/LAPI/Smart/IVALPRCheck",
        "smart_rule": "/LAPI/V1.0/Channel/0/Smart/SmartRule/",
        "people_count": "/LAPI/V1.0/Channel/0/Smart/PeopleCount",
        "heat_map": "/LAPI/V1.0/Channel/0/Smart/HeatMap",
        "road_detect": "/LAPI/V1.0/Channel/0/Smart/RoadDetect",
        "all_detect_rule": "/LAPI/V1.0/Channels/0/Smart/AllDetection/Rule",
        "all_detect_areas": "/LAPI/V1.0/Channels/0/Smart/AllDetection/Areas",
        "parking": "/LAPI/V1.0/Smart/ParkingDetection",
        "is_status": "/LAPI/V1.0/Smart/IsStatus",
        "is_type": "/LAPI/V1.0/Smart/IsType",
        "detect_area": "/LAPI/Intelligent/DetectArea",
        "driveway_line": "/LAPI/Intelligent/DrivewayLine",
        "trigger_line": "/LAPI/Intelligent/TriggerLine",
        "plate_identify": "/LAPI/Intelligent/PlateIdentify",
        "traffic_event": "/LAPI/Intelligent/TrafficEvent",
        "traffic_param": "/LAPI/Intelligent/TrafficParam",
        "park_all_status": "/LAPI/Intelligent/ParkAllStatus",
    }

    # Face Recognition
    FACE = {
        "enable": "/LAPI/V1.0/Smart/FaceEnable",
        "detect_rule": "/LAPI/V1.0/Smart/FaceDetection/Rule",
        "detect_areas": "/LAPI/V1.0/Smart/FaceDetection/Areas/Detections",
        "detect_linkage": "/LAPI/V1.0/Smart/FaceDetection/LinkageActions",
        "recognition": "/LAPI/V1.0/Smart/Face/Recognition/Monitor",
        "db_info": "/LAPI/V1.0/Smart/FaceRecognition/DatabaseInfo",
        "library_file": "/LAPI/V1.0/Smart/LibraryFile",
        "people_libs": "/LAPI/V1.0/PeopleLibraries/",
        "people_libs_info": "/LAPI/V1.0/PeopleLibraries/BasicInfo",
        "people_libs_cap": "/LAPI/V1.0/PeopleLibraries/Capabilities",
        "people_libs_capacity": "/LAPI/V1.0/PeopleLibraries/Capacity",
        "feature_gallery": "/LAPI/V1.0/Smart/FeatureGalleyFile/",
    }

    # PACS (Access Control)
    PACS = {
        "device_info": "/LAPI/V1.0/PACS/DeviceInfo",
        "work_status": "/LAPI/V1.0/PACS/Controller/WorkStatus",
        "open_door_mode": "/LAPI/V1.0/PACS/Controller/OpenDoorMode",
        "alarm_output": "/LAPI/V1.0/PACS/Controller/AlarmOutputCfg",
        "attr_verify": "/LAPI/V1.0/PACS/Controller/AttributeVerification/Rule",
        "ktp_info": "/LAPI/V1.0/PACS/Controller/KTPBasicInfo",
        "gui_file": "/LAPI/V1.0/PACS/Controller/GUIFile",
        "home_icons": "/LAPI/V1.0/PACS/GUI/HomeIcons",
        "home_slogan": "/LAPI/V1.0/PACS/GUI/HomeSlogan",
        "screen_saver": "/LAPI/V1.0/PACS/GUI/ScreenSaverInfo",
        "face_frame": "/LAPI/V1.0/PACS/GUI/FaceFrameInfo",
        "door_call": "/LAPI/V1.0/PACS/DoorStation/CallCfg",
        "peripheral": "/LAPI/V1.0/PACS/Peripheral/BasicInfo",
        "qr_code": "/LAPI/V1.0/PACS/Reader/QRCodeInfo",
        "temp_comp": "/LAPI/V1.0/PACS/Temperature/Compensation",
        "verify_templates": "/LAPI/V1.0/PACS/VerifyTemplates/",
        "turnstile_compare": "/LAPI/V1.0/Smart/FaceTurnstiles/ComparisonCfg",
        "turnstile_gui": "/LAPI/V1.0/Smart/FaceTurnstiles/GUIInfo",
        "turnstile_light": "/LAPI/V1.0/Smart/FaceTurnstiles/LightCfg",
        "turnstile_verify": "/LAPI/V1.0/Smart/FaceTurnstiles/VerificationModeCfg",
        "turnstile_work": "/LAPI/V1.0/Smart/FaceTurnstiles/WorkModeCfg",
        "gate_open": "/LAPI/V1.0/Intelligent/GateContrl?Open",
    }

    # I/O Control
    IO = {
        "input_switch": "/LAPI/V1.0/IO/InputSwitches/id/BasicInfos",
        "input_linkage": "/LAPI/V1.0/IO/InputSwitches/1/LinkageActions",
        "output_switch": "/LAPI/V1.0/IO/OutputSwitches/id/BasicInfos",
        "serial": "/LAPI/V1.0/Channel/0/IO/Serial",
        "serial_trans": "/LAPI/V1.0/Channel/0/IO/SerialTrans",
        "serial_osd": "/LAPI/V1.0/Channel/0/IO/SerialOSDReport",
        "security_module": "/LAPI/V1.0/IO/SecurityModuleCfg",
        "qr_ctrl": "/LAPI/V1.0/IO/QRCodeCtrl",
        "range_finder": "/LAPI/V1.0/IO/RangFinderCtrl",
        "io_port": "/LAPI/IO/IOPort",
        "flash_light": "/LAPI/IO/FlashLight",
        "laser": "/LAPI/IO/Laser",
        "nd_filter": "/LAPI/IO/NDFilter",
        "polarizer": "/LAPI/IO/Polarizer",
        "radar": "/LAPI/IO/Radar",
        "vehicle_detector": "/LAPI/IO/VehicleDetector",
        "usb_info": "/LAPI/IO/USBDeviceInfo",
        "laser_reboot": "/LAPI/Demo/LaserControl/reboot",
        "laser_restore": "/LAPI/Demo/LaserControl/restore",
    }

    # Demo/Debug Endpoints
    DEMO = {
        "acceptance_mode": "/LAPI/V1.0/Channel/0/Demo/AcceptanceMode",
        "bnc_osd": "/LAPI/V1.0/Channel/0/Demo/BNCOSD",
        "clear_fog": "/LAPI/V1.0/Channel/0/Demo/ClearFog",
        "custom_osd_font": "/LAPI/V1.0/Channel/0/Demo/CustomOSDFontSize",
        "default_osd_font": "/LAPI/V1.0/Channel/0/Demo/DefaultOSDFontSize",
        "face_optimize": "/LAPI/V1.0/Channel/0/Demo/FacePicOptimization",
        "gb_tcp_stream": "/LAPI/V1.0/Channel/0/Demo/GBTCPStream",
        "h264_payload": "/LAPI/V1.0/Channel/0/Demo/H264PayloadType",
        "invert_osd": "/LAPI/V1.0/Channel/0/Demo/InvertOSDFont",
        "lens_reset": "/LAPI/V1.0/Channel/0/Demo/LensMotorReset",
        "low_delay": "/LAPI/V1.0/Channel/0/Demo/LowDelay",
        "object_trace": "/LAPI/V1.0/Channel/0/Demo/ObjectTraceFrame",
        "revise_time": "/LAPI/V1.0/Channel/0/Demo/ReviseTime",
        "stream_send_mode": "/LAPI/V1.0/Channel/0/Demo/StreamSendMode",
        "view_mode": "/LAPI/V1.0/Channel/0/Demo/ViewMode",
        "zoom_limit": "/LAPI/V1.0/Channel/0/Demo/ZoomLimitSwitch",
        "tl_break": "/LAPI/V1.0/Demo/TLBreak",
        "coil_speed": "/LAPI/Demo/CoilSpeedAdjust",
        "fan_mode": "/LAPI/Demo/FanCtrlMode",
        "lens_init": "/LAPI/Demo/LensInitCfg",
        "motion_meta": "/LAPI/V1.0/Channels/0/Demo/MotionMetaData",
    }

    # Traffic/Vehicle Intelligence
    TRAFFIC = {
        "blacklist": "/LAPI/V1.0/Intelligent/CarPlateList/BlackList",
        "whitelist": "/LAPI/V1.0/Intelligent/CarPlateList/WhiteList",
        "peccancy_list": "/LAPI/V1.0/Intelligent/CarPlateList/PeccancyList",
        "peccancy_filter": "/LAPI/V1.0/Intelligent/CarPlateList/PeccancyFilterList",
        "identify_correct": "/LAPI/V1.0/Intelligent/CarPlateList/IdentifyCorrectList",
        "lane_list": "/LAPI/V1.0/Intelligent/CarPlateList/AccmmodationLaneList",
        "pass_whitelist": "/LAPI/V1.0/Intelligent/CarPlateList/PassCarWhiteList",
        "iva_break_rule": "/LAPI/Intelligent/IVABreakRule",
        "similar_lpr": "/LAPI/Intelligent/IVASimilarLPRFilter",
        "led_remote": "/LAPI/Intelligent/LedRemoteCtrl",
        "manual_capture": "/LAPI/Intelligent/ManualCapturePeccancy",
        "network_peripheral": "/LAPI/Intelligent/NetworkPeripheralList",
        "peccancy_way": "/LAPI/Intelligent/PeccancyWay",
        "pic_bitrate": "/LAPI/Intelligent/PicBitRate",
        "timer_capture": "/LAPI/Intelligent/TimerCapture",
        "traffic_light_intensity": "/LAPI/Intelligent/TrafficLightInensity",
        "peccancy_reset": "/LAPI/INTELLIGENT/PeccancyParamReset",
        "io_reset": "/LAPI/INTELLIGENT/IOParamReset",
        "driveway": "/LAPI/Smart/DriveWay",
        "traffic_light": "/LAPI/Smart/TrafficLight",
        "red_light_park": "/LAPI/Smart/RedLightParkTime",
        "violation_capture": "/LAPI/Smart/ViolationCapture",
        "violation_mode": "/LAPI/Smart/ViolationMode",
        "traffic_light_status": "/LAPI/System/DeviceStatus/TrafficLightStatus",
        "traffic_light_color": "/LAPI/System/DeviceStatus/TrafficLightColour",
        "vehicle_queue": "/LAPI/System/DeviceStatus/VehQueueLen",
    }


# ============================================================================
# API Client
# ============================================================================

class LAPIClient:
    """LAPI REST API Client"""

    def __init__(self, host: str, port: int = 80, username: str = None,
                 password: str = None, use_https: bool = False, timeout: int = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_https = use_https
        self.timeout = timeout
        self.session = requests.Session()

        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        if username and password:
            self.session.auth = (username, password)

    def _request(self, method: str, endpoint: str, data: Dict = None,
                 params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to LAPI endpoint"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout, verify=False)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=self.timeout, verify=False)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=self.timeout, verify=False)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=self.timeout, verify=False)
            else:
                return {"error": f"Unsupported method: {method}"}

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": self._parse_response(response),
                "url": url,
                "method": method.upper()
            }
        except requests.exceptions.Timeout:
            return {"error": "Request timed out", "url": url}
        except requests.exceptions.ConnectionError as e:
            return {"error": f"Connection error: {e}", "url": url}
        except Exception as e:
            return {"error": f"Request failed: {e}", "url": url}

    def _parse_response(self, response) -> Any:
        """Parse response body"""
        try:
            return response.json()
        except:
            return response.text

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        return self._request("GET", endpoint, params=params)

    def put(self, endpoint: str, data: Dict = None) -> Dict:
        return self._request("PUT", endpoint, data=data)

    def post(self, endpoint: str, data: Dict = None) -> Dict:
        return self._request("POST", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict:
        return self._request("DELETE", endpoint)


# ============================================================================
# CLI Command Handlers
# ============================================================================

def print_result(result: Dict, verbose: bool = False):
    """Print API result"""
    if "error" in result:
        print(f"[ERROR] {result['error']}")
        if "url" in result:
            print(f"[URL] {result['url']}")
        return

    if verbose:
        print(f"[URL] {result.get('url', 'N/A')}")
        print(f"[METHOD] {result.get('method', 'N/A')}")
        print(f"[STATUS] {result.get('status_code', 'N/A')}")
        print("[HEADERS]")
        for k, v in result.get('headers', {}).items():
            print(f"  {k}: {v}")
        print("[BODY]")

    body = result.get('body', {})
    if isinstance(body, dict):
        print(json.dumps(body, indent=2))
    else:
        print(body)


def cmd_system(client: LAPIClient, args):
    """System commands"""
    endpoints = Endpoints.SYSTEM

    if args.action == "info":
        result = client.get(endpoints["info"])
    elif args.action == "run_info":
        result = client.get(endpoints["run_info"])
    elif args.action == "reboot":
        if not args.force:
            confirm = input("Are you sure you want to reboot? [y/N]: ")
            if confirm.lower() != 'y':
                print("Aborted")
                return
        result = client.put(endpoints["reboot"])
    elif args.action == "factory_reset":
        if not args.force:
            confirm = input("DANGER: Factory reset will erase all settings! [y/N]: ")
            if confirm.lower() != 'y':
                print("Aborted")
                return
        result = client.put(endpoints["factory_reset"])
    elif args.action == "logs":
        result = client.get(endpoints["logs"])
    elif args.action == "time":
        if args.set_time:
            result = client.put(endpoints["time"], {"LocalTime": args.set_time})
        else:
            result = client.get(endpoints["time"])
    elif args.action == "ntp":
        if args.server:
            result = client.put(endpoints["ntp"], {"NTPServer": args.server, "Enable": 1})
        else:
            result = client.get(endpoints["ntp"])
    elif args.action == "config":
        result = client.get(endpoints["config"])
    elif args.action == "diagnosis":
        result = client.get(endpoints["diagnosis_url"])
    elif args.action == "fan":
        if args.mode is not None:
            result = client.put(endpoints["fan"], {"Mode": args.mode})
        else:
            result = client.get(endpoints["fan"])
    elif args.action == "keepalive":
        result = client.post(endpoints["keepalive"])
    else:
        print(f"Unknown action: {args.action}")
        print(f"Available: {', '.join(endpoints.keys())}")
        return

    print_result(result, args.verbose)


def cmd_auth(client: LAPIClient, args):
    """Authentication commands"""
    endpoints = Endpoints.AUTH

    if args.action == "login":
        import base64
        pwd_b64 = base64.b64encode(args.login_pass.encode()).decode() if args.login_pass else ""
        result = client.post(endpoints["login"], {
            "UserName": args.login_user or "admin",
            "Password": pwd_b64
        })
    elif args.action == "users":
        result = client.get(endpoints["users"])
    elif args.action == "rsa":
        result = client.get(endpoints["rsa"])
    elif args.action == "access_policy":
        result = client.get(endpoints["access_policy"])
    elif args.action == "http_auth":
        if args.enable is not None:
            result = client.put(endpoints["http_auth"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["http_auth"])
    elif args.action == "rtsp_auth":
        if args.enable is not None:
            result = client.put(endpoints["rtsp_auth"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["rtsp_auth"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["users"]))

    print_result(result, args.verbose)


def cmd_network(client: LAPIClient, args):
    """Network commands"""
    endpoints = Endpoints.NETWORK

    if args.action == "interfaces":
        if args.ip:
            data = {"IPAddress": args.ip}
            if args.mask:
                data["SubnetMask"] = args.mask
            if args.gateway:
                data["DefaultGateway"] = args.gateway
            result = client.put(endpoints["interfaces"], data)
        else:
            result = client.get(endpoints["interfaces"])
    elif args.action == "dns":
        if args.primary_dns:
            data = {"PrimaryDNS": args.primary_dns}
            if args.secondary_dns:
                data["SecondaryDNS"] = args.secondary_dns
            result = client.put(endpoints["dns"], data)
        else:
            result = client.get(endpoints["dns"])
    elif args.action == "wifi_scan":
        result = client.get(endpoints["wifi_scan"])
    elif args.action == "wifi_status":
        result = client.get(endpoints["wifi_status"])
    elif args.action == "ip_filter":
        if args.add_ip:
            result = client.put(endpoints["ip_filter"], {"IPAddress": args.add_ip, "Enable": 1})
        else:
            result = client.get(endpoints["ip_filter"])
    elif args.action == "cloud":
        result = client.get(endpoints["cloud"])
    elif args.action == "ftp_test":
        result = client.post(endpoints["ftp_test"])
    elif args.action == "email_test":
        result = client.post(endpoints["email_test"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["interfaces"]))

    print_result(result, args.verbose)


def cmd_telnet(client: LAPIClient, args):
    """Telnet/Debug commands - CRITICAL"""
    endpoints = Endpoints.TELNET

    if args.action == "status":
        result = client.get(endpoints["status"])
    elif args.action == "enable":
        result = client.put(endpoints["enable"], {"Enable": 1})
    elif args.action == "disable":
        result = client.put(endpoints["disable"], {"Enable": 0})
    elif args.action == "onvif_debug":
        if args.auth_enable is not None:
            result = client.put(endpoints["onvif_debug"], {
                "OnvifEnabled": 1,
                "AuthenticationEnabled": 1 if args.auth_enable else 0,
                "DetectionEnbalbed": 1
            })
        else:
            result = client.get(endpoints["onvif_debug"])
    elif args.action == "net_detect":
        if args.target_ip:
            result = client.post(endpoints["net_detect"], {"TargetIP": args.target_ip})
        else:
            result = client.get(endpoints["net_detect"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["status"]))

    print_result(result, args.verbose)


def cmd_firmware(client: LAPIClient, args):
    """Firmware commands - CRITICAL"""
    endpoints = Endpoints.FIRMWARE

    if args.action == "status":
        result = client.get(endpoints["update_status"])
    elif args.action == "info":
        result = client.get(endpoints["upgrade_info"])
    elif args.action == "upgrade":
        if not args.force:
            confirm = input("DANGER: Upgrade firmware? [y/N]: ")
            if confirm.lower() != 'y':
                print("Aborted")
                return
        if args.url:
            result = client.post(endpoints["upgrade"], {"URL": args.url})
        else:
            result = client.post(endpoints["upgrade"])
    elif args.action == "upload":
        if not args.file:
            print("Error: --file required for upload")
            return
        # File upload requires multipart form
        with open(args.file, 'rb') as f:
            files = {'file': f}
            url = f"{client.base_url}{endpoints['upload']}"
            response = client.session.post(url, files=files, timeout=300, verify=False)
            result = {"status_code": response.status_code, "body": response.text}
    else:
        result = client.get(endpoints.get(args.action, endpoints["update_status"]))

    print_result(result, args.verbose)


def cmd_ptz(client: LAPIClient, args):
    """PTZ commands"""
    endpoints = Endpoints.PTZ

    if args.action == "status":
        result = client.get(endpoints["status"])
    elif args.action == "ctrl":
        data = {"Command": args.command.upper() if args.command else "STOP"}
        if args.speed:
            data["Speed"] = args.speed
        result = client.put(endpoints["ctrl"], data)
    elif args.action == "reset":
        result = client.put(endpoints["reset"])
    elif args.action == "presets":
        if args.preset_id:
            result = client.put(endpoints["presets"], {"PresetID": args.preset_id})
        else:
            result = client.get(endpoints["presets"])
    elif args.action == "abs_position":
        result = client.get(endpoints["abs_position"])
    elif args.action == "abs_zoom":
        result = client.get(endpoints["abs_zoom"])
    elif args.action == "guard":
        if args.enable is not None:
            result = client.put(endpoints["guard"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["guard"])
    elif args.action == "capabilities":
        result = client.get(endpoints["capabilities"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["status"]))

    print_result(result, args.verbose)


def cmd_media(client: LAPIClient, args):
    """Media commands"""
    endpoints = Endpoints.MEDIA

    if args.action == "live_stream":
        result = client.get(endpoints["live_stream"])
    elif args.action == "snapshot":
        result = client.get(endpoints["snapshot_url"])
    elif args.action == "capture":
        result = client.post(endpoints["capture"])
    elif args.action == "streams":
        result = client.get(endpoints["streams"])
    elif args.action == "video_mode":
        if args.mode:
            result = client.put(endpoints["video_mode"], {"Mode": args.mode})
        else:
            result = client.get(endpoints["video_mode"])
    elif args.action == "record_url":
        result = client.get(endpoints["record_url"])
    elif args.action == "audio":
        result = client.get(endpoints["audio_input"])
    elif args.action == "keyframe":
        result = client.post(endpoints["keyframe"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["live_stream"]))

    print_result(result, args.verbose)


def cmd_image(client: LAPIClient, args):
    """Image settings commands"""
    endpoints = Endpoints.IMAGE

    if args.action == "osd":
        result = client.get(endpoints["osd"])
    elif args.action == "privacy_mask":
        result = client.get(endpoints["privacy_mask"])
    elif args.action == "orientation":
        if args.flip is not None or args.mirror is not None:
            data = {}
            if args.flip is not None:
                data["Flip"] = 1 if args.flip else 0
            if args.mirror is not None:
                data["Mirror"] = 1 if args.mirror else 0
            result = client.put(endpoints["orientation"], data)
        else:
            result = client.get(endpoints["orientation"])
    elif args.action == "enhance":
        result = client.get(endpoints["enhance"])
    elif args.action == "defog":
        if args.enable is not None:
            result = client.put(endpoints["defog"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["defog"])
    elif args.action == "exposure":
        result = client.get(endpoints["exposure"])
    elif args.action == "white_balance":
        result = client.get(endpoints["white_balance"])
    elif args.action == "focus":
        result = client.get(endpoints["focus"])
    elif args.action == "scene":
        result = client.get(endpoints["current_scene"])
    elif args.action == "reset":
        result = client.put(endpoints["image_reset"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["osd"]))

    print_result(result, args.verbose)


def cmd_storage(client: LAPIClient, args):
    """Storage commands"""
    endpoints = Endpoints.STORAGE

    if args.action == "config":
        result = client.get(endpoints["config"])
    elif args.action == "status":
        result = client.get(endpoints["sd_status"])
    elif args.action == "format":
        if not args.force:
            confirm = input("DANGER: Format SD card? All data will be lost! [y/N]: ")
            if confirm.lower() != 'y':
                print("Aborted")
                return
        result = client.put(endpoints["sd_format"])
    elif args.action == "nas":
        result = client.get(endpoints["nas"])
    elif args.action == "alarm_storage":
        result = client.get(endpoints["alarm_storage"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["config"]))

    print_result(result, args.verbose)


def cmd_alarm(client: LAPIClient, args):
    """Alarm commands"""
    endpoints = Endpoints.ALARM

    if args.action == "motion":
        result = client.get(endpoints["motion_type"])
    elif args.action == "motion_grid":
        result = client.get(endpoints["motion_grid"])
    elif args.action == "audio":
        result = client.get(endpoints["audio_detect"])
    elif args.action == "tamper":
        result = client.get(endpoints["tamper_detect"])
    elif args.action == "temperature":
        result = client.get(endpoints["high_temp"])
    elif args.action == "subscribers":
        result = client.get(endpoints["subscribers"])
    elif args.action == "volume":
        if args.level is not None:
            result = client.put(endpoints["audio_volume"], {"Volume": args.level})
        else:
            result = client.get(endpoints["audio_volume"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["motion"]))

    print_result(result, args.verbose)


def cmd_smart(client: LAPIClient, args):
    """Smart/IVA commands"""
    endpoints = Endpoints.SMART

    if args.action == "mode":
        result = client.get(endpoints["mode"])
    elif args.action == "enable":
        result = client.put(endpoints["iva_enable"], {"Enable": 1})
    elif args.action == "disable":
        result = client.put(endpoints["iva_enable"], {"Enable": 0})
    elif args.action == "scenes":
        result = client.get(endpoints["iva_scenes"])
    elif args.action == "rules":
        result = client.get(endpoints["iva_rules"])
    elif args.action == "manual_snap":
        result = client.post(endpoints["iva_manual_snap"])
    elif args.action == "people_count":
        result = client.get(endpoints["people_count"])
    elif args.action == "heat_map":
        result = client.get(endpoints["heat_map"])
    elif args.action == "parking":
        result = client.get(endpoints["parking"])
    elif args.action == "park_status":
        result = client.get(endpoints["park_all_status"])
    elif args.action == "detect_area":
        result = client.get(endpoints["detect_area"])
    elif args.action == "status":
        result = client.get(endpoints["is_status"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["mode"]))

    print_result(result, args.verbose)


def cmd_face(client: LAPIClient, args):
    """Face recognition commands"""
    endpoints = Endpoints.FACE

    if args.action == "enable":
        result = client.put(endpoints["enable"], {"Enable": 1})
    elif args.action == "disable":
        result = client.put(endpoints["enable"], {"Enable": 0})
    elif args.action == "status":
        result = client.get(endpoints["enable"])
    elif args.action == "rules":
        result = client.get(endpoints["detect_rule"])
    elif args.action == "areas":
        result = client.get(endpoints["detect_areas"])
    elif args.action == "recognition":
        result = client.get(endpoints["recognition"])
    elif args.action == "db_info":
        result = client.get(endpoints["db_info"])
    elif args.action == "libraries":
        result = client.get(endpoints["people_libs"])
    elif args.action == "lib_info":
        result = client.get(endpoints["people_libs_info"])
    elif args.action == "capacity":
        result = client.get(endpoints["people_libs_capacity"])
    elif args.action == "capabilities":
        result = client.get(endpoints["people_libs_cap"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["enable"]))

    print_result(result, args.verbose)


def cmd_pacs(client: LAPIClient, args):
    """PACS (Access Control) commands"""
    endpoints = Endpoints.PACS

    if args.action == "info":
        result = client.get(endpoints["device_info"])
    elif args.action == "status":
        result = client.get(endpoints["work_status"])
    elif args.action == "open_door":
        result = client.put(endpoints["gate_open"])
    elif args.action == "door_mode":
        if args.mode:
            result = client.put(endpoints["open_door_mode"], {"Mode": args.mode})
        else:
            result = client.get(endpoints["open_door_mode"])
    elif args.action == "alarm_output":
        result = client.get(endpoints["alarm_output"])
    elif args.action == "verify_rule":
        result = client.get(endpoints["attr_verify"])
    elif args.action == "qr_code":
        result = client.get(endpoints["qr_code"])
    elif args.action == "temp_comp":
        result = client.get(endpoints["temp_comp"])
    elif args.action == "turnstile":
        result = client.get(endpoints["turnstile_work"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["device_info"]))

    print_result(result, args.verbose)


def cmd_io(client: LAPIClient, args):
    """I/O Control commands"""
    endpoints = Endpoints.IO

    if args.action == "serial":
        result = client.get(endpoints["serial"])
    elif args.action == "input":
        result = client.get(endpoints["input_switch"].replace("id", str(args.port or 1)))
    elif args.action == "output":
        result = client.get(endpoints["output_switch"].replace("id", str(args.port or 1)))
    elif args.action == "flash":
        if args.enable is not None:
            result = client.put(endpoints["flash_light"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["flash_light"])
    elif args.action == "laser":
        if args.enable is not None:
            result = client.put(endpoints["laser"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["laser"])
    elif args.action == "laser_reboot":
        result = client.put(endpoints["laser_reboot"])
    elif args.action == "laser_restore":
        result = client.put(endpoints["laser_restore"])
    elif args.action == "radar":
        result = client.get(endpoints["radar"])
    elif args.action == "usb":
        result = client.get(endpoints["usb_info"])
    elif args.action == "polarizer":
        result = client.get(endpoints["polarizer"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["serial"]))

    print_result(result, args.verbose)


def cmd_demo(client: LAPIClient, args):
    """Demo/Debug commands"""
    endpoints = Endpoints.DEMO

    if args.action == "list":
        print("Available demo endpoints:")
        for name, endpoint in endpoints.items():
            print(f"  {name}: {endpoint}")
        return
    elif args.action == "low_delay":
        if args.enable is not None:
            result = client.put(endpoints["low_delay"], {"Enable": 1 if args.enable else 0})
        else:
            result = client.get(endpoints["low_delay"])
    elif args.action == "lens_reset":
        result = client.put(endpoints["lens_reset"])
    elif args.action == "clear_fog":
        result = client.put(endpoints["clear_fog"])
    elif args.action == "view_mode":
        if args.mode:
            result = client.put(endpoints["view_mode"], {"Mode": args.mode})
        else:
            result = client.get(endpoints["view_mode"])
    else:
        endpoint = endpoints.get(args.action)
        if endpoint:
            result = client.get(endpoint)
        else:
            print(f"Unknown action: {args.action}")
            return

    print_result(result, args.verbose)


def cmd_traffic(client: LAPIClient, args):
    """Traffic/Vehicle commands"""
    endpoints = Endpoints.TRAFFIC

    if args.action == "blacklist":
        if args.plate:
            result = client.put(endpoints["blacklist"], {"PlateNumber": args.plate})
        else:
            result = client.get(endpoints["blacklist"])
    elif args.action == "whitelist":
        if args.plate:
            result = client.put(endpoints["whitelist"], {"PlateNumber": args.plate})
        else:
            result = client.get(endpoints["whitelist"])
    elif args.action == "peccancy":
        result = client.get(endpoints["peccancy_list"])
    elif args.action == "traffic_light":
        result = client.get(endpoints["traffic_light"])
    elif args.action == "light_status":
        result = client.get(endpoints["traffic_light_status"])
    elif args.action == "light_color":
        result = client.get(endpoints["traffic_light_color"])
    elif args.action == "vehicle_queue":
        result = client.get(endpoints["vehicle_queue"])
    elif args.action == "manual_capture":
        result = client.post(endpoints["manual_capture"])
    elif args.action == "led":
        result = client.get(endpoints["led_remote"])
    elif args.action == "driveway":
        result = client.get(endpoints["driveway"])
    elif args.action == "violation":
        result = client.get(endpoints["violation_capture"])
    elif args.action == "reset_peccancy":
        result = client.put(endpoints["peccancy_reset"])
    else:
        result = client.get(endpoints.get(args.action, endpoints["blacklist"]))

    print_result(result, args.verbose)


def cmd_scan(client: LAPIClient, args):
    """Scan all endpoints for auth bypass"""
    print(f"[*] Scanning {client.base_url} for unauthenticated access...")
    print(f"[*] Auth: {'Disabled' if not client.username else f'{client.username}:***'}")
    print("-" * 60)

    # High-priority endpoints to test
    critical_endpoints = [
        ("/LAPI/V1.0/System/DeviceBasicInfo", "Device Info"),
        ("/LAPI/V1.0/System/Security/RSA", "RSA Public Key"),
        ("/LAPI/V1.0/Channel/0/NetWork/Telnet", "Telnet Config"),
        ("/LAPI/V1.0/Channel/0/Demo/OnvifDebug", "ONVIF Debug"),
        ("/LAPI/V1.0/System/Reboot", "Reboot"),
        ("/LAPI/V1.0/System/FactoryReset", "Factory Reset"),
        ("/LAPI/V1.0/Network/Interfaces/1", "Network Config"),
        ("/LAPI/V1.0/Channel/0/System/Users", "User List"),
        ("/LAPI/V1.0/Channels/0/Media/SnapshotURL", "Snapshot URL"),
        ("/LAPI/V1.0/Intelligent/GateContrl?Open", "Gate Open"),
        ("/LAPI/V1.0/System/Logs", "System Logs"),
        ("/LAPI/V1.0/Smart/FaceEnable", "Face Recognition"),
        ("/LAPI/V1.0/PeopleLibraries/", "People Libraries"),
        ("/LAPI/V1.0/System/ConfigurationInfo/", "Config Backup"),
    ]

    accessible = []

    for endpoint, desc in critical_endpoints:
        result = client.get(endpoint)
        status = result.get("status_code", "ERR")

        if status == 200:
            marker = "[OPEN]"
            accessible.append((endpoint, desc))
        elif status == 401:
            marker = "[AUTH]"
        elif status == 403:
            marker = "[DENY]"
        elif status == 404:
            marker = "[N/A]"
        else:
            marker = f"[{status}]"

        print(f"{marker} {desc}: {endpoint}")

    print("-" * 60)
    if accessible:
        print(f"[!] Found {len(accessible)} accessible endpoints without auth:")
        for ep, desc in accessible:
            print(f"    - {desc}: {ep}")
    else:
        print("[*] No unauthenticated access found")


def cmd_raw(client: LAPIClient, args):
    """Raw endpoint access"""
    method = args.method.upper()
    endpoint = args.endpoint

    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON data: {args.data}")
            return

    if method == "GET":
        result = client.get(endpoint)
    elif method == "PUT":
        result = client.put(endpoint, data)
    elif method == "POST":
        result = client.post(endpoint, data)
    elif method == "DELETE":
        result = client.delete(endpoint)
    else:
        print(f"Unsupported method: {method}")
        return

    print_result(result, args.verbose)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LAPI CLI - Uniview/Digital Ally REST API Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t 192.168.30.178 system info
  %(prog)s -t 192.168.30.178 -u admin -p admin telnet enable
  %(prog)s -t 192.168.30.178 --no-auth scan
  %(prog)s -t 192.168.30.178 raw GET /LAPI/V1.0/System/DeviceBasicInfo
  %(prog)s -t 192.168.30.178 pacs open_door

Categories:
  system    - System & device info, reboot, factory reset
  auth      - Authentication, users, security settings
  network   - Network configuration, WiFi, DNS, FTP
  telnet    - Telnet enable/disable, debug settings (CRITICAL)
  firmware  - Firmware upgrade, upload (CRITICAL)
  ptz       - PTZ control, presets, patrols
  media     - Streaming, snapshots, recording
  image     - OSD, image settings, exposure
  storage   - SD card, NAS storage
  alarm     - Motion detection, tamper, audio alarms
  smart     - IVA, people counting, detection
  face      - Face recognition, libraries
  pacs      - Access control, door/gate open (CRITICAL)
  io        - I/O ports, serial, laser
  demo      - Debug/demo endpoints
  traffic   - Vehicle detection, license plates
  scan      - Scan for unauthenticated endpoints
  raw       - Raw endpoint access
        """
    )

    # Global arguments
    parser.add_argument("-t", "--target", required=True, help="Target IP address")
    parser.add_argument("-P", "--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("-u", "--user", default=DEFAULT_USER, help=f"Username (default: {DEFAULT_USER})")
    parser.add_argument("-p", "--password", default=DEFAULT_PASS, help=f"Password (default: {DEFAULT_PASS})")
    parser.add_argument("--super", action="store_true", help=f"Use super password ({SUPER_PASSWORD})")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication")
    parser.add_argument("--https", action="store_true", help="Use HTTPS")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout")

    subparsers = parser.add_subparsers(dest="category", help="Command category")

    # System commands
    system_parser = subparsers.add_parser("system", help="System commands")
    system_parser.add_argument("action", choices=["info", "run_info", "reboot", "factory_reset",
                                                   "logs", "time", "ntp", "config", "diagnosis",
                                                   "fan", "keepalive"],
                               help="Action to perform")
    system_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    system_parser.add_argument("--set-time", help="Set system time (ISO format)")
    system_parser.add_argument("--server", help="NTP server address")
    system_parser.add_argument("--mode", type=int, help="Fan mode (0-3)")

    # Auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication commands")
    auth_parser.add_argument("action", choices=["login", "users", "rsa", "access_policy",
                                                 "http_auth", "rtsp_auth", "password_info",
                                                 "secure_access"],
                             help="Action to perform")
    auth_parser.add_argument("--login-user", help="Login username")
    auth_parser.add_argument("--login-pass", help="Login password")
    auth_parser.add_argument("--enable", type=int, choices=[0, 1], help="Enable (1) or disable (0)")

    # Network commands
    network_parser = subparsers.add_parser("network", help="Network commands")
    network_parser.add_argument("action", choices=["interfaces", "dns", "port", "wifi_scan",
                                                    "wifi_status", "ip_filter", "cloud",
                                                    "ftp_test", "email_test", "snmp", "https",
                                                    "ddns", "upnp", "routes"],
                                help="Action to perform")
    network_parser.add_argument("--ip", help="IP address")
    network_parser.add_argument("--mask", help="Subnet mask")
    network_parser.add_argument("--gateway", help="Default gateway")
    network_parser.add_argument("--primary-dns", help="Primary DNS")
    network_parser.add_argument("--secondary-dns", help="Secondary DNS")
    network_parser.add_argument("--add-ip", help="Add IP to filter")

    # Telnet commands (CRITICAL)
    telnet_parser = subparsers.add_parser("telnet", help="Telnet/Debug commands (CRITICAL)")
    telnet_parser.add_argument("action", choices=["status", "enable", "disable", "onvif_debug",
                                                   "net_detect", "wiegand_debug", "image_debug",
                                                   "ep_tg_type", "iq_debug"],
                               help="Action to perform")
    telnet_parser.add_argument("--auth-enable", type=int, choices=[0, 1],
                               help="ONVIF auth enable (1) or disable (0)")
    telnet_parser.add_argument("--target-ip", help="Target IP for net detect")

    # Firmware commands
    firmware_parser = subparsers.add_parser("firmware", help="Firmware commands (CRITICAL)")
    firmware_parser.add_argument("action", choices=["status", "info", "upgrade", "upload"],
                                 help="Action to perform")
    firmware_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    firmware_parser.add_argument("--url", help="Firmware URL")
    firmware_parser.add_argument("--file", help="Firmware file path")

    # PTZ commands
    ptz_parser = subparsers.add_parser("ptz", help="PTZ commands")
    ptz_parser.add_argument("action", choices=["status", "ctrl", "reset", "presets",
                                                "abs_position", "abs_zoom", "guard",
                                                "capabilities", "config", "patrols"],
                            help="Action to perform")
    ptz_parser.add_argument("--command", choices=["up", "down", "left", "right", "stop",
                                                   "zoom_in", "zoom_out", "focus_near",
                                                   "focus_far", "iris_open", "iris_close"],
                            help="PTZ command")
    ptz_parser.add_argument("--speed", type=int, help="PTZ speed (1-100)")
    ptz_parser.add_argument("--preset-id", type=int, help="Preset ID")
    ptz_parser.add_argument("--enable", type=int, choices=[0, 1], help="Enable guard")

    # Media commands
    media_parser = subparsers.add_parser("media", help="Media commands")
    media_parser.add_argument("action", choices=["live_stream", "snapshot", "capture",
                                                  "streams", "video_mode", "record_url",
                                                  "audio", "keyframe"],
                              help="Action to perform")
    media_parser.add_argument("--mode", type=int, help="Video mode")

    # Image commands
    image_parser = subparsers.add_parser("image", help="Image settings commands")
    image_parser.add_argument("action", choices=["osd", "privacy_mask", "orientation",
                                                  "enhance", "defog", "exposure",
                                                  "white_balance", "focus", "scene", "reset"],
                              help="Action to perform")
    image_parser.add_argument("--flip", type=int, choices=[0, 1], help="Flip image")
    image_parser.add_argument("--mirror", type=int, choices=[0, 1], help="Mirror image")
    image_parser.add_argument("--enable", type=int, choices=[0, 1], help="Enable feature")

    # Storage commands
    storage_parser = subparsers.add_parser("storage", help="Storage commands")
    storage_parser.add_argument("action", choices=["config", "status", "format", "nas",
                                                    "alarm_storage"],
                                help="Action to perform")
    storage_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Alarm commands
    alarm_parser = subparsers.add_parser("alarm", help="Alarm commands")
    alarm_parser.add_argument("action", choices=["motion", "motion_grid", "audio", "tamper",
                                                  "temperature", "subscribers", "volume"],
                              help="Action to perform")
    alarm_parser.add_argument("--level", type=int, help="Volume level (0-100)")

    # Smart commands
    smart_parser = subparsers.add_parser("smart", help="Smart/IVA commands")
    smart_parser.add_argument("action", choices=["mode", "enable", "disable", "scenes",
                                                  "rules", "manual_snap", "people_count",
                                                  "heat_map", "parking", "park_status",
                                                  "detect_area", "status"],
                              help="Action to perform")

    # Face commands
    face_parser = subparsers.add_parser("face", help="Face recognition commands")
    face_parser.add_argument("action", choices=["enable", "disable", "status", "rules",
                                                 "areas", "recognition", "db_info",
                                                 "libraries", "lib_info", "capacity",
                                                 "capabilities"],
                             help="Action to perform")

    # PACS commands
    pacs_parser = subparsers.add_parser("pacs", help="PACS (Access Control) commands")
    pacs_parser.add_argument("action", choices=["info", "status", "open_door", "door_mode",
                                                 "alarm_output", "verify_rule", "qr_code",
                                                 "temp_comp", "turnstile"],
                             help="Action to perform")
    pacs_parser.add_argument("--mode", type=int, help="Door open mode")

    # I/O commands
    io_parser = subparsers.add_parser("io", help="I/O Control commands")
    io_parser.add_argument("action", choices=["serial", "input", "output", "flash",
                                               "laser", "laser_reboot", "laser_restore",
                                               "radar", "usb", "polarizer"],
                           help="Action to perform")
    io_parser.add_argument("--port", type=int, help="I/O port number")
    io_parser.add_argument("--enable", type=int, choices=[0, 1], help="Enable feature")

    # Demo commands
    demo_parser = subparsers.add_parser("demo", help="Demo/Debug commands")
    demo_parser.add_argument("action", help="Action to perform (use 'list' to see all)")
    demo_parser.add_argument("--enable", type=int, choices=[0, 1], help="Enable feature")
    demo_parser.add_argument("--mode", type=int, help="Mode value")

    # Traffic commands
    traffic_parser = subparsers.add_parser("traffic", help="Traffic/Vehicle commands")
    traffic_parser.add_argument("action", choices=["blacklist", "whitelist", "peccancy",
                                                    "traffic_light", "light_status",
                                                    "light_color", "vehicle_queue",
                                                    "manual_capture", "led", "driveway",
                                                    "violation", "reset_peccancy"],
                                help="Action to perform")
    traffic_parser.add_argument("--plate", help="License plate number")

    # Scan commands
    scan_parser = subparsers.add_parser("scan", help="Scan for unauthenticated endpoints")

    # Raw endpoint access
    raw_parser = subparsers.add_parser("raw", help="Raw endpoint access")
    raw_parser.add_argument("method", choices=["GET", "PUT", "POST", "DELETE"],
                            help="HTTP method")
    raw_parser.add_argument("endpoint", help="API endpoint (e.g., /LAPI/V1.0/System/DeviceBasicInfo)")
    raw_parser.add_argument("--data", help="JSON data for PUT/POST")

    args = parser.parse_args()

    if not args.category:
        parser.print_help()
        return

    # Setup authentication
    username = None
    password = None
    if not args.no_auth:
        if args.super:
            password = SUPER_PASSWORD
            username = args.user
        else:
            username = args.user
            password = args.password

    # Create client
    client = LAPIClient(
        host=args.target,
        port=args.port,
        username=username,
        password=password,
        use_https=args.https,
        timeout=args.timeout
    )

    # Route to command handler
    handlers = {
        "system": cmd_system,
        "auth": cmd_auth,
        "network": cmd_network,
        "telnet": cmd_telnet,
        "firmware": cmd_firmware,
        "ptz": cmd_ptz,
        "media": cmd_media,
        "image": cmd_image,
        "storage": cmd_storage,
        "alarm": cmd_alarm,
        "smart": cmd_smart,
        "face": cmd_face,
        "pacs": cmd_pacs,
        "io": cmd_io,
        "demo": cmd_demo,
        "traffic": cmd_traffic,
        "scan": cmd_scan,
        "raw": cmd_raw,
    }

    handler = handlers.get(args.category)
    if handler:
        handler(client, args)
    else:
        print(f"Unknown category: {args.category}")


if __name__ == "__main__":
    main()
