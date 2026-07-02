#!/usr/bin/env python3
"""
LAPI Interactive CLI - Full Endpoint Browser & Executor

Interactive menu-driven tool to browse and execute ALL LAPI endpoints.

Usage:
    ./lapi_interactive.py -t 192.168.30.178
    ./lapi_interactive.py -t 192.168.30.178 -u admin -p admin
    ./lapi_interactive.py -t 192.168.30.178 --no-auth

Author: Jon 'GainSec' Gaines
Target: Uniview OET-213H-NB / Digital Ally ThermoVu DTM-600
"""

import argparse
import requests
import json
import sys
import os
import urllib3
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin"
SUPER_PASSWORD = "87654321"
DEFAULT_TIMEOUT = 10

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def colored(text: str, color: str) -> str:
    """Apply color to text"""
    return f"{color}{text}{Colors.ENDC}"

# ============================================================================
# Complete LAPI Endpoint Database
# ============================================================================

# Each entry: (endpoint, method, description, parameters, risk_level)
# risk_level: 0=info, 1=low, 2=medium, 3=high, 4=critical

ENDPOINTS = {
    "System & Device": {
        "Device Basic Info": ("/LAPI/V1.0/System/DeviceBasicInfo", "GET", "Get device model, serial, firmware", None, 0),
        "Device Run Info": ("/LAPI/V1.0/System/DeviceRunInfo", "GET", "Get runtime info, uptime, memory", None, 0),
        "Reboot Device": ("/LAPI/V1.0/System/Reboot", "PUT", "Reboot the device", None, 4),
        "Factory Reset": ("/LAPI/V1.0/System/FactoryReset", "PUT", "Factory reset - ERASES ALL", None, 4),
        "System Language": ("/LAPI/V1.0/System/Language", "GET", "Get system language", None, 0),
        "Set Language": ("/LAPI/V1.0/System/Language", "PUT", "Set system language", {"Language": "int (0=CN, 1=EN)"}, 1),
        "System Logs": ("/LAPI/V1.0/System/Logs", "GET", "Get system logs", None, 1),
        "System Time": ("/LAPI/V1.0/System/TimePrivate", "GET", "Get system time config", None, 0),
        "Set System Time": ("/LAPI/V1.0/System/TimePrivate", "PUT", "Set system time", {"LocalTime": "ISO datetime"}, 2),
        "Local Time": ("/LAPI/V1.0/System/TimePrivate/LocalTime", "GET", "Get local time", None, 0),
        "DST Config": ("/LAPI/V1.0/System/Time/DST", "GET", "Get daylight saving config", None, 0),
        "NTP Config": ("/LAPI/V1.0/System/Time/NTP", "GET", "Get NTP server config", None, 0),
        "Set NTP Server": ("/LAPI/V1.0/System/Time/NTP", "PUT", "Set NTP server", {"NTPServer": "hostname", "Enable": "1"}, 2),
        "Test NTP": ("/LAPI/System/Time/NTP/Test", "POST", "Test NTP connection", None, 1),
        "Time Sync Mode": ("/LAPI/V1.0/System/Time/SyncMode", "GET", "Get time sync mode", None, 0),
        "Keepalive": ("/LAPI/V1.0/System/KeepAlive", "POST", "Session keepalive ping", None, 0),
        "Location Info": ("/LAPI/V1.0/System/LocationInfo", "GET", "Get device location", None, 0),
        "Battery Info": ("/LAPI/V1.0/System/BatteryInfo", "GET", "Get battery status", None, 0),
        "Fan Control": ("/LAPI/V1.0/System/FanCtrl", "GET", "Get fan settings", None, 0),
        "Set Fan Mode": ("/LAPI/V1.0/System/FanCtrl", "PUT", "Set fan mode", {"Mode": "int (0-3)"}, 1),
        "Hide Device Info": ("/LAPI/V1.0/System/HideDeviceInfo", "GET", "Get hide info setting", None, 0),
        "Diagnosis URL": ("/LAPI/V1.0/System/Diagnosis/FileURL", "GET", "Get diagnostic file URL", None, 1),
        "Diagnosis Status": ("/LAPI/V1.0/System/Diagnosis/PackStatus", "GET", "Get diagnostic status", None, 0),
        "Config Backup URL": ("/LAPI/V1.0/System/ConfigurationInfoURL", "GET", "Get config backup URL", None, 2),
        "Config Backup": ("/LAPI/V1.0/System/ConfigurationInfo/", "GET", "Download full config backup", None, 3),
        "Debug Messages": ("/LAPI/V1.0/System/DebugMessage", "GET", "Get debug messages", None, 1),
        "Extra Log Switch": ("/LAPI/V1.0/System/ExtraLogSwitch", "GET", "Get extra logging state", None, 0),
        "Manage Server": ("/LAPI/V1.0/System/ManageServer", "GET", "Get management server config", None, 1),
        "BM Server": ("/LAPI/V1.0/System/BMServer", "GET", "Get BM server config", None, 1),
        "Device Work Mode": ("/LAPI/V1.0/System/DeviceWorkMode", "GET", "Get device work mode", None, 0),
    },

    "Authentication & Security": {
        "Web Login": ("/LAPI/V1.0/System/Security/Login", "POST", "Web login endpoint", {"UserName": "str", "Password": "base64"}, 0),
        "Channel Login": ("/LAPI/V1.0/Channel/0/System/Login", "POST", "Channel login", {"UserName": "str", "Password": "base64"}, 0),
        "List Users": ("/LAPI/V1.0/Channel/0/System/Users", "GET", "List all users", None, 2),
        "RSA Public Key": ("/LAPI/V1.0/System/Security/RSA", "GET", "Get RSA public key for login", None, 0),
        "Access Policy": ("/LAPI/V1.0/System/Security/AccessPolicy", "GET", "Get access/friendly password policy", None, 2),
        "Set Access Policy": ("/LAPI/V1.0/System/Security/AccessPolicy", "PUT", "Set access policy", {"FriendlyPassword": {"Enabled": "bool"}}, 3),
        "Privacy Policy": ("/LAPI/V1.0/System/PrivacyPolicy/Status", "GET", "Get privacy policy status", None, 0),
        "Password Info": ("/LAPI/V1.0/System/CurrentPasswordInfo", "GET", "Get current password info", None, 2),
        "Secret Key Info": ("/LAPI/V1.0/System/SecretKeyInfo", "GET", "Get secret key info", None, 2),
        "HTTP Auth Config": ("/LAPI/V1.0/NetWork/HttpAuth", "GET", "Get HTTP auth settings", None, 1),
        "Set HTTP Auth": ("/LAPI/V1.0/NetWork/HttpAuth", "PUT", "Enable/disable HTTP auth", {"Enable": "0 or 1"}, 3),
        "RTSP Auth Config": ("/LAPI/V1.0/NetWork/RtspAuth", "GET", "Get RTSP auth settings", None, 1),
        "Set RTSP Auth": ("/LAPI/V1.0/NetWork/RtspAuth", "PUT", "Enable/disable RTSP auth", {"Enable": "0 or 1"}, 3),
        "Secure Access": ("/LAPI/V1.0/NetWork/SecureAccess", "GET", "Get secure access config", None, 1),
    },

    "Network Configuration": {
        "Network Interfaces": ("/LAPI/V1.0/Network/Interfaces/1", "GET", "Get network interface config", None, 1),
        "Set Network Config": ("/LAPI/V1.0/Network/Interfaces/1", "PUT", "Set IP/mask/gateway", {"IPAddress": "x.x.x.x", "SubnetMask": "x.x.x.x", "DefaultGateway": "x.x.x.x"}, 3),
        "DNS Config": ("/LAPI/V1.0/NetWork/DNS", "GET", "Get DNS servers", None, 0),
        "Set DNS": ("/LAPI/V1.0/NetWork/DNS", "PUT", "Set DNS servers", {"PrimaryDNS": "x.x.x.x", "SecondaryDNS": "x.x.x.x"}, 2),
        "Port Config": ("/LAPI/V1.0/NetWork/Port", "GET", "Get port configuration", None, 1),
        "DDNS Config": ("/LAPI/V1.0/NetWork/DDNS", "GET", "Get DDNS configuration", None, 1),
        "FTP Config": ("/LAPI/V1.0/NetWork/FTP", "GET", "Get FTP settings", None, 1),
        "Test FTP": ("/LAPI/V1.0/NetWork/FTP/Test", "POST", "Test FTP connection", None, 1),
        "Email Config": ("/LAPI/V1.0/Channel/0/NetWork/Email", "GET", "Get email/SMTP settings", None, 1),
        "Test Email": ("/LAPI/V1.0/NetWork/Email/Test", "POST", "Test email settings", None, 1),
        "SNMP Config": ("/LAPI/V1.0/NetWork/SNMP", "GET", "Get SNMP configuration", None, 1),
        "HTTPS Config": ("/LAPI/V1.0/NetWork/HTTPS", "GET", "Get HTTPS settings", None, 1),
        "SSL Certificate": ("/LAPI/V1.0/Network/HTTPS_SSLCERT", "GET", "Get SSL certificate info", None, 2),
        "UPnP Config": ("/LAPI/V1.0/NetWork/UNP", "GET", "Get UPnP configuration", None, 1),
        "Registration Info": ("/LAPI/V1.0/NetWork/RegistInfo", "GET", "Get registration info", None, 1),
        "ARP Binding": ("/LAPI/V1.0/NetWork/ArpBinding", "GET", "Get ARP binding", None, 1),
        "Soft AP Config": ("/LAPI/V1.0/NetWork/SoftAP", "GET", "Get Soft AP settings", None, 1),
        "Soft AP WiFi": ("/LAPI/V1.0/NetWork/SoftAPWiFi", "GET", "Get Soft AP WiFi", None, 1),
        "4G Config": ("/LAPI/V1.0/NetWork/Net4G", "GET", "Get 4G network config", None, 1),
        "4G Status": ("/LAPI/V1.0/NetWork/Net4GStatus", "GET", "Get 4G network status", None, 0),
        "802.1X Config": ("/LAPI/V1.0/NetWork/IEEE8021x", "GET", "Get 802.1X authentication", None, 1),
        "SSL VPN": ("/LAPI/V1.0/NetWork/SSLVPN", "GET", "Get SSL VPN config", None, 1),
        "WiFi Config": ("/LAPI/V1.0/NetWork/WiFi/Configuration", "GET", "Get WiFi configuration", None, 1),
        "WiFi Scan": ("/LAPI/V1.0/NetWork/WiFi/ScanInfo", "GET", "Scan for WiFi networks", None, 0),
        "WiFi Status": ("/LAPI/V1.0/NetWork/WiFi/LinkStatus", "GET", "Get WiFi connection status", None, 0),
        "IP Filter": ("/LAPI/V1.0/Channel/0/NetWork/IPFilter", "GET", "Get IP filter/whitelist", None, 2),
        "QoS Config": ("/LAPI/V1.0/Channel/0/NetWork/QOS", "GET", "Get QoS settings", None, 1),
        "Port Mapping": ("/LAPI/V1.0/Channel/0/NetWork/PortMap", "GET", "Get port mapping", None, 1),
        "Check Port": ("/LAPI/V1.0/Channel/0/NetWork/CheckPort", "POST", "Check port availability", {"Port": "int"}, 1),
        "DDNS Domain Check": ("/LAPI/V1.0/Channel/0/NetWork/DDNSDomainCheck", "POST", "Check DDNS domain", None, 1),
        "Routes": ("/LAPI/Network/Routes", "GET", "Get routing table", None, 1),
        "Cloud Config": ("/LAPI/V1.0/Network/Cloud", "GET", "Get cloud service config", None, 1),
        "Cloud Unregister": ("/LAPI/V1.0/Network/Cloud/Unregistration", "DELETE", "Unregister from cloud", None, 3),
    },

    "Telnet & Debug [CRITICAL]": {
        "Telnet Status": ("/LAPI/V1.0/Channel/0/NetWork/Telnet", "GET", "Get Telnet enable status", None, 2),
        "Enable Telnet": ("/LAPI/V1.0/Channel/0/NetWork/Telnet", "PUT", "ENABLE TELNET SERVICE", {"Enable": "1"}, 4),
        "Disable Telnet": ("/LAPI/V1.0/Channel/0/NetWork/Telnet", "PUT", "Disable Telnet service", {"Enable": "0"}, 3),
        "ONVIF Debug Config": ("/LAPI/V1.0/Channel/0/Demo/OnvifDebug", "GET", "Get ONVIF debug settings", None, 2),
        "Disable ONVIF Auth": ("/LAPI/V1.0/Channel/0/Demo/OnvifDebug", "PUT", "DISABLE ONVIF AUTHENTICATION", {"OnvifEnabled": "1", "AuthenticationEnabled": "0", "DetectionEnbalbed": "1"}, 4),
        "Enable ONVIF Auth": ("/LAPI/V1.0/Channel/0/Demo/OnvifDebug", "PUT", "Enable ONVIF authentication", {"OnvifEnabled": "1", "AuthenticationEnabled": "1", "DetectionEnbalbed": "1"}, 2),
        "Network Detect": ("/LAPI/V1.0/Channel/0/Demo/NetDetect", "GET", "Get network detection config", None, 1),
        "Run Network Detect": ("/LAPI/V1.0/Channel/0/Demo/NetDetect", "POST", "Run network diagnostics", {"TargetIP": "x.x.x.x"}, 1),
        "Wiegand Debug": ("/LAPI/V1.0/Channel/0/Demo/WiegandDebug", "GET", "Get Wiegand debug settings", None, 1),
        "Image Debug Switch": ("/LAPI/V1.0/Channel/0/Image/DebugSwitch", "GET", "Get image debug switch", None, 1),
        "EP TG Type Debug": ("/LAPI/Demo/Debug/EpTgType", "GET", "Get EP/TG debug type", None, 1),
        "Debug EP Messages": ("/LAPI/Demo/Debug/DebugEpMsg", "GET", "Get debug EP messages", None, 1),
        "Debug EP Temp Msg": ("/LAPI/Demo/Debug/DebugEpTmpMsg", "GET", "Get debug EP temp messages", None, 1),
        "Debug Capture Para": ("/LAPI/Demo/Debug/DebugCaputrePara", "GET", "Get debug capture params", None, 1),
        "Debug Flash Exposure": ("/LAPI/Demo/Debug/DebugFlashExposure", "GET", "Get debug flash exposure", None, 1),
        "Debug Polarizer": ("/LAPI/Demo/Debug/DebugPolarizer", "GET", "Get debug polarizer", None, 1),
        "Debug Heat": ("/LAPI/Demo/Debug/Heat", "GET", "Get heat debug", None, 1),
        "Saturation Switch": ("/LAPI/Demo/Debug/SaturationSwitch", "GET", "Get saturation debug switch", None, 1),
        "Polarizer Inverse": ("/LAPI/Demo/Debug/PolarizerInverseSwitch", "GET", "Get polarizer inverse", None, 1),
        "IQ Debug Info": ("/LAPI/V1.0/Channel/0/Demo/Debug/IQDebugInfo", "GET", "Get IQ debug info", None, 1),
        "Audio AGC Debug": ("/LAPI/V1.0/Channel/0/Demo/Debug/AudioAGC", "GET", "Get audio AGC debug", None, 1),
        "Enhance Mode Debug": ("/LAPI/V1.0/Channel/0/Demo/Debug/EnhanceMode", "GET", "Get enhance mode debug", None, 1),
        "Profile Mode Debug": ("/LAPI/V1.0/Channel/0/Demo/Debug/ProfileMode", "GET", "Get profile mode debug", None, 1),
        "Special Lens Type": ("/LAPI/V1.0/Channel/0/Demo/Debug/SpecialLensType", "GET", "Get special lens type", None, 1),
    },

    "Firmware & Updates [CRITICAL]": {
        "Update Status": ("/LAPI/V1.0/System/UpdateStatus", "GET", "Get firmware update status", None, 0),
        "Upgrade Info": ("/LAPI/V1.0/System/UpgradeInfo", "GET", "Get upgrade information", None, 0),
        "Start Upgrade": ("/LAPI/V1.0/System/Upgrade", "POST", "Start firmware upgrade", {"URL": "firmware URL (optional)"}, 4),
        "Upload Firmware": ("/LAPI/V1.0/System/UploadFirmware", "POST", "Upload firmware file", {"file": "multipart"}, 4),
        "Upgrade U-Boot": ("/LAPI/V1.0/System/UpgradeUboot", "POST", "Upgrade U-Boot bootloader", None, 4),
        "Temp Module Upgrade": ("/LAPI/PACS/TempModule/Upgrade", "POST", "Upgrade temp module", None, 3),
        "Temp Module Status": ("/LAPI/PACS/TempModule/UpStatus", "GET", "Get temp module upgrade status", None, 0),
    },

    "PTZ Control": {
        "PTZ Status": ("/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZ", "GET", "Get PTZ status", None, 0),
        "PTZ Control": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Control PTZ movement", {"Command": "UP/DOWN/LEFT/RIGHT/STOP", "Speed": "1-100"}, 1),
        "PTZ Stop": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Stop PTZ movement", {"Command": "STOP"}, 1),
        "PTZ Up": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Move PTZ up", {"Command": "UP", "Speed": "50"}, 1),
        "PTZ Down": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Move PTZ down", {"Command": "DOWN", "Speed": "50"}, 1),
        "PTZ Left": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Move PTZ left", {"Command": "LEFT", "Speed": "50"}, 1),
        "PTZ Right": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Move PTZ right", {"Command": "RIGHT", "Speed": "50"}, 1),
        "PTZ Zoom In": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Zoom in", {"Command": "ZOOM_IN", "Speed": "50"}, 1),
        "PTZ Zoom Out": ("/LAPI/V1.0/Channel/0/PTZ/PTZCtrl", "PUT", "Zoom out", {"Command": "ZOOM_OUT", "Speed": "50"}, 1),
        "PTZ Reset": ("/LAPI/V1.0/Channel/0/PTZ/PTZReset", "PUT", "Reset PTZ position", None, 2),
        "PTZ Config": ("/LAPI/V1.0/Channel/0/PTZ/PTZCfg", "GET", "Get PTZ configuration", None, 0),
        "PTZ Driver Config": ("/LAPI/V1.0/Channel/0/PTZ/PTDrvCfg", "GET", "Get PTZ driver config", None, 0),
        "Net Ctrl PTZ": ("/LAPI/V1.0/Channel/0/PTZ/NetCtrlPTZ", "GET", "Get network PTZ control", None, 0),
        "PTZ Patrols": ("/LAPI/V1.0/Channel/0/PTZ/Patrols", "GET", "Get patrol routes", None, 0),
        "PTZ Presets": ("/LAPI/V1.0/Channels/0/PTZ/Presets", "GET", "Get PTZ presets", None, 0),
        "Go To Preset": ("/LAPI/V1.0/Channels/0/PTZ/Presets", "PUT", "Go to preset", {"PresetID": "int"}, 1),
        "PTZ Wiper": ("/LAPI/V1.0/Channel/0/PTZ/WiperInfo", "GET", "Get wiper info", None, 0),
        "Abs Position": ("/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsPosition", "GET", "Get absolute position", None, 0),
        "Abs Zoom": ("/LAPI/V1.0/Channel/0/System/DeviceStatus/PTZAbsZoom", "GET", "Get absolute zoom", None, 0),
        "PTZ Guard": ("/LAPI/V1.0/PTZ/Guard", "GET", "Get PTZ guard config", None, 0),
        "Area Focus": ("/LAPI/V1.0/PTZ/AreaFocus", "PUT", "Set area focus", None, 1),
        "Angle Limit": ("/LAPI/V1.0/PTZ/PTZAngleLimit", "GET", "Get PTZ angle limits", None, 0),
        "PTZ Capabilities": ("/LAPI/PTZ/Capabilities", "GET", "Get PTZ capabilities", None, 0),
        "Area Zoom In": ("/LAPI/V1.0/Channels/0/PTZ/AreaZoomIn", "PUT", "Area zoom in", None, 1),
        "Area Zoom Out": ("/LAPI/V1.0/Channels/0/PTZ/AreaZoomOut", "PUT", "Area zoom out", None, 1),
    },

    "Media & Streaming": {
        "Live Stream URL": ("/LAPI/V1.0/Channel/0/Media/LivingStream", "GET", "Get live stream URL", None, 1),
        "Media Stream Config": ("/LAPI/V1.0/Channel/0/Media/MediaStream", "GET", "Get media stream config", None, 0),
        "Stream Info": ("/LAPI/V1.0/Channel/0/Media/MediaStream/StreamInfo/", "GET", "Get stream info", None, 0),
        "Video Streams": ("/LAPI/V1.0/Channels/0/Media/Video/Streams/", "GET", "List video streams", None, 0),
        "Record URL": ("/LAPI/V1.0/Channels/0/Media/Video/Streams/RecordURL", "GET", "Get recording URL", None, 1),
        "Adaptive Config": ("/LAPI/V1.0/Channels/0/Media/Video/Streams/AdaptiveCfg", "GET", "Get adaptive streaming", None, 0),
        "Video Mode": ("/LAPI/V1.0/Channel/0/Media/Video/Mode", "GET", "Get video mode", None, 0),
        "Video Detail Info": ("/LAPI/V1.0/Channel/0/Media/Video/Streams/DetailInfos", "GET", "Get video detail info", None, 0),
        "Download State": ("/LAPI/V1.0/Channel/0/Media/RecordDownloadState", "GET", "Get download state", None, 0),
        "Auto Send Streams": ("/LAPI/V1.0/Channel/0/Media/AutoSendStreams", "GET", "Get auto send streams", None, 0),
        "Snapshot URL": ("/LAPI/V1.0/Channels/0/Media/SnapshotURL", "GET", "Get snapshot URL", None, 1),
        "Capture Image": ("/LAPI/V1.0/Media/Capture", "POST", "Capture image", None, 1),
        "Audio Input": ("/LAPI/V1.0/Media/Audio/Input", "GET", "Get audio input config", None, 0),
        "Request Keyframe": ("/LAPI/V1.0/Media/KeyFrame", "POST", "Request keyframe", None, 0),
        "Import File": ("/LAPI/V1.0/Media/ImportFile", "POST", "Import media file", None, 2),
        "Analog Out Format": ("/LAPI/Media/AnalogoutFormat", "GET", "Get analog output format", None, 0),
        "RTSP Multicast": ("/LAPI/V1.0/Channel/0/Media/RTSPMulticastAddr", "GET", "Get RTSP multicast", None, 0),
    },

    "Image & Video Settings": {
        "OSD Config": ("/LAPI/V1.0/Channel/0/Media/OSD", "GET", "Get OSD configuration", None, 0),
        "OSD Style": ("/LAPI/V1.0/Channel/0/Media/OSDStyle", "GET", "Get OSD style", None, 0),
        "Marquee": ("/LAPI/V1.0/Channel/0/Media/Marquee", "GET", "Get marquee text", None, 0),
        "Privacy Mask": ("/LAPI/V1.0/Channel/0/Media/PrivacyMask", "GET", "Get privacy mask zones", None, 0),
        "Privacy Mask Mode": ("/LAPI/V1.0/Channel/0/Media/PrivacyMask/Mode", "GET", "Get privacy mask mode", None, 0),
        "Cover OSD": ("/LAPI/V1.0/Channel/0/Media/PrivacyMask/CoverOSD", "GET", "Get cover OSD", None, 0),
        "Cover OSD Zooms": ("/LAPI/V1.0/Channel/0/Media/CoverOSDZooms", "GET", "Get cover OSD zooms", None, 0),
        "ROI Config": ("/LAPI/V1.0/Channel/0/Media/ROI", "GET", "Get region of interest", None, 0),
        "Orientation": ("/LAPI/V1.0/Channel/0/Media/Orientation", "GET", "Get image orientation", None, 0),
        "Set Orientation": ("/LAPI/V1.0/Channel/0/Media/Orientation", "PUT", "Set flip/mirror", {"Flip": "0 or 1", "Mirror": "0 or 1"}, 1),
        "Watermark": ("/LAPI/V1.0/Channel/0/Media/Watermark", "GET", "Get watermark settings", None, 0),
        "Image Enhance": ("/LAPI/V1.0/Channels/0/Image/Enhance", "GET", "Get image enhancement", None, 0),
        "Lamp Control": ("/LAPI/V1.0/Channels/0/Image/LampCtrl/", "GET", "Get IR lamp control", None, 0),
        "Lens Type": ("/LAPI/V1.0/Channel/0/Image/LensType", "GET", "Get lens type", None, 0),
        "Lens Params": ("/LAPI/V1.0/Channel/0/Image/LensParam", "GET", "Get lens parameters", None, 0),
        "LDC Config": ("/LAPI/V1.0/Channel/0/Image/LDC", "GET", "Get lens distortion correction", None, 0),
        "Defog Config": ("/LAPI/V1.0/Channel/0/Image/Defog/", "GET", "Get defog settings", None, 0),
        "Enable Defog": ("/LAPI/V1.0/Channel/0/Image/Defog/", "PUT", "Enable defog", {"Enable": "1"}, 1),
        "Reset Image Params": ("/LAPI/V1.0/Channel/0/Image/ImageParamReset", "PUT", "Reset image parameters", None, 2),
        "Default Scene": ("/LAPI/V1.0/Channel/0/Image/DefaultScene", "GET", "Get default scene", None, 0),
        "Current Scene": ("/LAPI/V1.0/Channel/0/Image/CurrentScene", "GET", "Get current scene", None, 0),
        "Scene Auto Switch": ("/LAPI/V1.0/Channel/0/Image/SceneAutoSwitch", "GET", "Get scene auto switch", None, 0),
        "Focus Config": ("/LAPI/Image/Focus/", "GET", "Get focus settings", None, 0),
        "White Balance": ("/LAPI/Image/WhiteBalance", "GET", "Get white balance", None, 0),
        "Exposure": ("/LAPI/Image/Advanced/Exposure", "GET", "Get exposure settings", None, 0),
        "Light Mode": ("/LAPI/Image/LightMode", "GET", "Get light mode", None, 0),
        "Set Back Focus": ("/LAPI/V1.0/Image/SetBackFocus", "PUT", "Set back focus", None, 1),
        "Image Stabilization": ("/LAPI/V1.0/Image/ImageStable", "GET", "Get image stabilization", None, 0),
        "Digital Zoom": ("/LAPI/V1.0/Image/Enlarge", "GET", "Get digital zoom", None, 0),
        "Focal Limit": ("/LAPI/V1.0/Image/FocalLimit", "GET", "Get focal length limit", None, 0),
    },

    "Storage": {
        "Storage Config": ("/LAPI/V1.0/Channel/0/Media/Storage", "GET", "Get storage configuration", None, 0),
        "Alarm Storage": ("/LAPI/V1.0/Channel/0/Media/AlarmStorage", "GET", "Get alarm storage settings", None, 0),
        "SD Card Status": ("/LAPI/V1.0/Channel/0/System/DeviceStatus/SD", "GET", "Get SD card status", None, 0),
        "Format SD Card": ("/LAPI/V1.0/Channel/0/Media/SDFormat", "PUT", "FORMAT SD CARD - DATA LOSS", None, 4),
        "SD Card Switch": ("/LAPI/Media/SDCardSwitch", "GET", "Get SD card switch", None, 0),
        "NAS Config": ("/LAPI/System/Nas", "GET", "Get NAS configuration", None, 1),
    },

    "Alarms & Events": {
        "Motion Detection Type": ("/LAPI/V1.0/Channels/0/Alarm/MotionDetection/AreaType", "GET", "Get motion detection type", None, 0),
        "Motion Detection Grid": ("/LAPI/V1.0/Channels/0/Alarm/MotionDetection/Areas/Grid", "GET", "Get motion grid config", None, 0),
        "Motion Linkage": ("/LAPI/V1.0/Channels/0/Alarm/MotionDetection/LinkageActions", "GET", "Get motion linkage actions", None, 0),
        "Motion Activity Areas": ("/LAPI/V1.0/Alarm/MotionActivity/Areas", "GET", "Get motion activity areas", None, 0),
        "Motion Interval": ("/LAPI/V1.0/Alarm/MotionInterval", "GET", "Get motion interval", None, 0),
        "Audio Detection Rule": ("/LAPI/V1.0/Channels/0/Alarm/AudioDetection/Rule", "GET", "Get audio detection rule", None, 0),
        "Audio Linkage": ("/LAPI/V1.0/Channels/0/Alarm/AudioDetection/LinkageActions", "GET", "Get audio linkage actions", None, 0),
        "Tamper Detection": ("/LAPI/V1.0/Channels/0/Alarm/TamperDetection/Rule", "GET", "Get tamper detection rule", None, 0),
        "Tamper Linkage": ("/LAPI/V1.0/Channels/0/Alarm/TamperDetection/LinkageActions", "GET", "Get tamper linkage", None, 0),
        "Low Temp Detection": ("/LAPI/V1.0/Alarm/LowTemperatureDetectLink", "GET", "Get low temp detection", None, 0),
        "High Temp Detection": ("/LAPI/V1.0/Alarm/HighTemperatureDetectLink", "GET", "Get high temp detection", None, 0),
        "Audio Volume": ("/LAPI/V1.0/Channel/0/Alarm/AudioVolume", "GET", "Get audio volume", None, 0),
        "Set Audio Volume": ("/LAPI/V1.0/Channel/0/Alarm/AudioVolume", "PUT", "Set audio volume", {"Volume": "0-100"}, 1),
        "Event Subscribers": ("/LAPI/V1.0/Channel/0/Event/Subscription/Subscribers", "GET", "Get event subscribers", None, 0),
    },

    "Smart/IVA Features": {
        "Smart Mode": ("/LAPI/V1.0/Smart/Mode", "GET", "Get smart mode", None, 0),
        "Detect Mode": ("/LAPI/V1.0/Smart/DetectMode", "GET", "Get detection mode", None, 0),
        "IVA Enable Status": ("/LAPI/Smart/IVAEnable", "GET", "Get IVA enable status", None, 0),
        "Enable IVA": ("/LAPI/Smart/IVAEnable", "PUT", "Enable IVA", {"Enable": "1"}, 2),
        "Disable IVA": ("/LAPI/Smart/IVAEnable", "PUT", "Disable IVA", {"Enable": "0"}, 1),
        "IVA Scene List": ("/LAPI/Smart/IVASceneList", "GET", "Get IVA scenes", None, 0),
        "IVA Rule List": ("/LAPI/Smart/IVARuleList", "GET", "Get IVA rules", None, 0),
        "IVA Manual Snap": ("/LAPI/Smart/IVAManualSnap", "POST", "Manual IVA snapshot", None, 1),
        "IVA Press Line": ("/LAPI/Smart/IVAPressLine", "GET", "Get IVA line crossing", None, 0),
        "IVA Stay Time": ("/LAPI/Smart/IVAStayTime", "GET", "Get IVA stay time", None, 0),
        "IVA LPR Check": ("/LAPI/Smart/IVALPRCheck", "GET", "Get license plate check", None, 0),
        "Smart Rules": ("/LAPI/V1.0/Channel/0/Smart/SmartRule/", "GET", "Get smart rules", None, 0),
        "People Counting": ("/LAPI/V1.0/Channel/0/Smart/PeopleCount", "GET", "Get people counting", None, 0),
        "Heat Map": ("/LAPI/V1.0/Channel/0/Smart/HeatMap", "GET", "Get heat map config", None, 0),
        "Road Detection": ("/LAPI/V1.0/Channel/0/Smart/RoadDetect", "GET", "Get road detection", None, 0),
        "All Detection Rules": ("/LAPI/V1.0/Channels/0/Smart/AllDetection/Rule", "GET", "Get all detection rules", None, 0),
        "All Detection Areas": ("/LAPI/V1.0/Channels/0/Smart/AllDetection/Areas", "GET", "Get detection areas", None, 0),
        "Parking Detection": ("/LAPI/V1.0/Smart/ParkingDetection", "GET", "Get parking detection", None, 0),
        "Smart Status": ("/LAPI/V1.0/Smart/IsStatus", "GET", "Get smart status", None, 0),
        "Smart Type": ("/LAPI/V1.0/Smart/IsType", "GET", "Get smart type", None, 0),
        "Install Guide": ("/LAPI/V1.0/Intelligent/InstallGuide", "GET", "Get installation guide", None, 0),
        "Park All Status": ("/LAPI/Intelligent/ParkAllStatus", "GET", "Get all parking status", None, 0),
        "Detection Area": ("/LAPI/Intelligent/DetectArea", "GET", "Get detection area", None, 0),
        "Driveway Line": ("/LAPI/Intelligent/DrivewayLine", "GET", "Get driveway line", None, 0),
        "Trigger Line": ("/LAPI/Intelligent/TriggerLine", "GET", "Get trigger line", None, 0),
        "Plate Identify": ("/LAPI/Intelligent/PlateIdentify", "GET", "Get plate identification", None, 0),
        "Traffic Event": ("/LAPI/Intelligent/TrafficEvent", "GET", "Get traffic events", None, 0),
        "Traffic Params": ("/LAPI/Intelligent/TrafficParam", "GET", "Get traffic parameters", None, 0),
    },

    "Face Recognition": {
        "Face Enable Status": ("/LAPI/V1.0/Smart/FaceEnable", "GET", "Get face recognition status", None, 0),
        "Enable Face Recognition": ("/LAPI/V1.0/Smart/FaceEnable", "PUT", "Enable face recognition", {"Enable": "1"}, 2),
        "Disable Face Recognition": ("/LAPI/V1.0/Smart/FaceEnable", "PUT", "Disable face recognition", {"Enable": "0"}, 1),
        "Face Detection Rules": ("/LAPI/V1.0/Smart/FaceDetection/Rule", "GET", "Get face detection rules", None, 0),
        "Face Detection Areas": ("/LAPI/V1.0/Smart/FaceDetection/Areas/Detections", "GET", "Get face detection areas", None, 0),
        "Face Detection Linkage": ("/LAPI/V1.0/Smart/FaceDetection/LinkageActions", "GET", "Get face linkage actions", None, 0),
        "Face Recognition Monitor": ("/LAPI/V1.0/Smart/Face/Recognition/Monitor", "GET", "Get recognition monitor", None, 0),
        "Face DB Info": ("/LAPI/V1.0/Smart/FaceRecognition/DatabaseInfo", "GET", "Get face database info", None, 1),
        "Library File": ("/LAPI/V1.0/Smart/LibraryFile", "GET", "Get library file info", None, 1),
        "People Libraries": ("/LAPI/V1.0/PeopleLibraries/", "GET", "List people libraries", None, 2),
        "Libraries Basic Info": ("/LAPI/V1.0/PeopleLibraries/BasicInfo", "GET", "Get libraries basic info", None, 1),
        "Libraries Capabilities": ("/LAPI/V1.0/PeopleLibraries/Capabilities", "GET", "Get library capabilities", None, 0),
        "Libraries Capacity": ("/LAPI/V1.0/PeopleLibraries/Capacity", "GET", "Get library capacity", None, 0),
        "Feature Gallery": ("/LAPI/V1.0/Smart/FeatureGalleyFile/", "GET", "Get feature gallery", None, 1),
    },

    "PACS (Access Control) [CRITICAL]": {
        "PACS Device Info": ("/LAPI/V1.0/PACS/DeviceInfo", "GET", "Get PACS device info", None, 0),
        "Controller Work Status": ("/LAPI/V1.0/PACS/Controller/WorkStatus", "GET", "Get controller status", None, 0),
        "OPEN DOOR/GATE": ("/LAPI/V1.0/Intelligent/GateContrl?Open", "PUT", "OPEN THE DOOR/GATE", None, 4),
        "Open Door Mode": ("/LAPI/V1.0/PACS/Controller/OpenDoorMode", "GET", "Get door open mode", None, 0),
        "Set Door Mode": ("/LAPI/V1.0/PACS/Controller/OpenDoorMode", "PUT", "Set door open mode", {"Mode": "int"}, 2),
        "Alarm Output Config": ("/LAPI/V1.0/PACS/Controller/AlarmOutputCfg", "GET", "Get alarm output config", None, 0),
        "Attribute Verification": ("/LAPI/V1.0/PACS/Controller/AttributeVerification/Rule", "GET", "Get attr verification", None, 0),
        "KTP Basic Info": ("/LAPI/V1.0/PACS/Controller/KTPBasicInfo", "GET", "Get KTP basic info", None, 0),
        "GUI File Config": ("/LAPI/V1.0/PACS/Controller/GUIFile", "GET", "Get GUI file config", None, 0),
        "Long Connection Info": ("/LAPI/V1.0/PACS/Controller/LongConnectionInfo", "GET", "Get long connection info", None, 0),
        "Home Icons": ("/LAPI/V1.0/PACS/GUI/HomeIcons", "GET", "Get home icons", None, 0),
        "Home Slogan": ("/LAPI/V1.0/PACS/GUI/HomeSlogan", "GET", "Get home slogan", None, 0),
        "Screen Saver": ("/LAPI/V1.0/PACS/GUI/ScreenSaverInfo", "GET", "Get screen saver", None, 0),
        "Face Frame Info": ("/LAPI/V1.0/PACS/GUI/FaceFrameInfo", "GET", "Get face frame info", None, 0),
        "Door Station Call": ("/LAPI/V1.0/PACS/DoorStation/CallCfg", "GET", "Get door station call", None, 0),
        "Peripheral Info": ("/LAPI/V1.0/PACS/Peripheral/BasicInfo", "GET", "Get peripheral info", None, 0),
        "QR Code Info": ("/LAPI/V1.0/PACS/Reader/QRCodeInfo", "GET", "Get QR code reader", None, 0),
        "Temp Compensation": ("/LAPI/V1.0/PACS/Temperature/Compensation", "GET", "Get temp compensation", None, 0),
        "Verify Templates": ("/LAPI/V1.0/PACS/VerifyTemplates/", "GET", "Get verify templates", None, 0),
        "Turnstile Comparison": ("/LAPI/V1.0/Smart/FaceTurnstiles/ComparisonCfg", "GET", "Get turnstile comparison", None, 0),
        "Turnstile GUI": ("/LAPI/V1.0/Smart/FaceTurnstiles/GUIInfo", "GET", "Get turnstile GUI", None, 0),
        "Turnstile Lights": ("/LAPI/V1.0/Smart/FaceTurnstiles/LightCfg", "GET", "Get turnstile lights", None, 0),
        "Turnstile Verify Mode": ("/LAPI/V1.0/Smart/FaceTurnstiles/VerificationModeCfg", "GET", "Get verify mode", None, 0),
        "Turnstile Work Mode": ("/LAPI/V1.0/Smart/FaceTurnstiles/WorkModeCfg", "GET", "Get work mode", None, 0),
    },

    "I/O Control": {
        "Serial Config": ("/LAPI/V1.0/Channel/0/IO/Serial", "GET", "Get serial port config", None, 0),
        "Serial Transparent": ("/LAPI/V1.0/Channel/0/IO/SerialTrans", "GET", "Get serial transparent", None, 0),
        "Serial OSD Report": ("/LAPI/V1.0/Channel/0/IO/SerialOSDReport", "GET", "Get serial OSD report", None, 0),
        "Security Module": ("/LAPI/V1.0/IO/SecurityModuleCfg", "GET", "Get security module", None, 0),
        "QR Code Control": ("/LAPI/V1.0/IO/QRCodeCtrl", "GET", "Get QR code control", None, 0),
        "Range Finder": ("/LAPI/V1.0/IO/RangFinderCtrl", "GET", "Get range finder", None, 0),
        "I/O Ports": ("/LAPI/IO/IOPort", "GET", "Get I/O ports config", None, 0),
        "Flash Light": ("/LAPI/IO/FlashLight", "GET", "Get flash light config", None, 0),
        "Enable Flash": ("/LAPI/IO/FlashLight", "PUT", "Enable flash light", {"Enable": "1"}, 1),
        "Laser Config": ("/LAPI/IO/Laser", "GET", "Get laser config", None, 0),
        "Enable Laser": ("/LAPI/IO/Laser", "PUT", "Enable laser", {"Enable": "1"}, 1),
        "ND Filter": ("/LAPI/IO/NDFilter", "GET", "Get ND filter", None, 0),
        "Polarizer": ("/LAPI/IO/Polarizer", "GET", "Get polarizer config", None, 0),
        "Radar": ("/LAPI/IO/Radar", "GET", "Get radar config", None, 0),
        "Vehicle Detector": ("/LAPI/IO/VehicleDetector", "GET", "Get vehicle detector", None, 0),
        "USB Device Info": ("/LAPI/IO/USBDeviceInfo", "GET", "Get USB device info", None, 0),
        "Sub Device Switch": ("/LAPI/IO/SubDeviceSwitch", "GET", "Get sub device switch", None, 0),
        "Expand Sub Device": ("/LAPI/IO/ExpandSubDevice", "GET", "Get expand sub device", None, 0),
        "Laser Reboot": ("/LAPI/Demo/LaserControl/reboot", "PUT", "Reboot laser", None, 2),
        "Laser Restore": ("/LAPI/Demo/LaserControl/restore", "PUT", "Restore laser", None, 2),
    },

    "Demo/Debug Endpoints": {
        "Acceptance Mode": ("/LAPI/V1.0/Channel/0/Demo/AcceptanceMode", "GET", "Get acceptance mode", None, 1),
        "BNC OSD": ("/LAPI/V1.0/Channel/0/Demo/BNCOSD", "GET", "Get BNC OSD", None, 0),
        "Clear Fog": ("/LAPI/V1.0/Channel/0/Demo/ClearFog", "PUT", "Clear fog", None, 1),
        "Custom OSD Font": ("/LAPI/V1.0/Channel/0/Demo/CustomOSDFontSize", "GET", "Get custom OSD font", None, 0),
        "Default OSD Font": ("/LAPI/V1.0/Channel/0/Demo/DefaultOSDFontSize", "GET", "Get default OSD font", None, 0),
        "Face Pic Optimize": ("/LAPI/V1.0/Channel/0/Demo/FacePicOptimization", "GET", "Get face pic optimize", None, 0),
        "GB TCP Stream": ("/LAPI/V1.0/Channel/0/Demo/GBTCPStream", "GET", "Get GB TCP stream", None, 0),
        "H264 Payload Type": ("/LAPI/V1.0/Channel/0/Demo/H264PayloadType", "GET", "Get H264 payload type", None, 0),
        "Invert OSD Font": ("/LAPI/V1.0/Channel/0/Demo/InvertOSDFont", "GET", "Get invert OSD font", None, 0),
        "Lens Motor Reset": ("/LAPI/V1.0/Channel/0/Demo/LensMotorReset", "PUT", "Reset lens motor", None, 2),
        "Low Delay Mode": ("/LAPI/V1.0/Channel/0/Demo/LowDelay", "GET", "Get low delay mode", None, 0),
        "Enable Low Delay": ("/LAPI/V1.0/Channel/0/Demo/LowDelay", "PUT", "Enable low delay", {"Enable": "1"}, 1),
        "Object Trace Frame": ("/LAPI/V1.0/Channel/0/Demo/ObjectTraceFrame", "GET", "Get object trace frame", None, 0),
        "Revise Time": ("/LAPI/V1.0/Channel/0/Demo/ReviseTime", "GET", "Get revise time", None, 0),
        "Stream Send Mode": ("/LAPI/V1.0/Channel/0/Demo/StreamSendMode", "GET", "Get stream send mode", None, 0),
        "View Mode": ("/LAPI/V1.0/Channel/0/Demo/ViewMode", "GET", "Get view mode", None, 0),
        "Zoom Limit Switch": ("/LAPI/V1.0/Channel/0/Demo/ZoomLimitSwitch", "GET", "Get zoom limit switch", None, 0),
        "TL Break": ("/LAPI/V1.0/Demo/TLBreak", "GET", "Get TL break", None, 0),
        "Coil Speed Adjust": ("/LAPI/Demo/CoilSpeedAdjust", "GET", "Get coil speed adjust", None, 0),
        "Fan Control Mode": ("/LAPI/Demo/FanCtrlMode", "GET", "Get fan control mode", None, 0),
        "Lens Init Config": ("/LAPI/Demo/LensInitCfg", "GET", "Get lens init config", None, 0),
        "Motion Metadata": ("/LAPI/V1.0/Channels/0/Demo/MotionMetaData", "GET", "Get motion metadata", None, 0),
    },

    "Traffic/Vehicle Intelligence": {
        "Plate Blacklist": ("/LAPI/V1.0/Intelligent/CarPlateList/BlackList", "GET", "Get plate blacklist", None, 1),
        "Add to Blacklist": ("/LAPI/V1.0/Intelligent/CarPlateList/BlackList", "PUT", "Add plate to blacklist", {"PlateNumber": "ABC123"}, 2),
        "Plate Whitelist": ("/LAPI/V1.0/Intelligent/CarPlateList/WhiteList", "GET", "Get plate whitelist", None, 1),
        "Add to Whitelist": ("/LAPI/V1.0/Intelligent/CarPlateList/WhiteList", "PUT", "Add plate to whitelist", {"PlateNumber": "ABC123"}, 2),
        "Violation List": ("/LAPI/V1.0/Intelligent/CarPlateList/PeccancyList", "GET", "Get violation list", None, 1),
        "Violation Filter": ("/LAPI/V1.0/Intelligent/CarPlateList/PeccancyFilterList", "GET", "Get violation filter", None, 0),
        "ID Correct List": ("/LAPI/V1.0/Intelligent/CarPlateList/IdentifyCorrectList", "GET", "Get ID correct list", None, 0),
        "Lane List": ("/LAPI/V1.0/Intelligent/CarPlateList/AccmmodationLaneList", "GET", "Get lane list", None, 0),
        "Pass Car Whitelist": ("/LAPI/V1.0/Intelligent/CarPlateList/PassCarWhiteList", "GET", "Get pass car whitelist", None, 1),
        "IVA Break Rules": ("/LAPI/Intelligent/IVABreakRule", "GET", "Get IVA break rules", None, 0),
        "Similar LPR Filter": ("/LAPI/Intelligent/IVASimilarLPRFilter", "GET", "Get similar LPR filter", None, 0),
        "LED Remote Control": ("/LAPI/Intelligent/LedRemoteCtrl", "GET", "Get LED remote control", None, 0),
        "Manual Violation Capture": ("/LAPI/Intelligent/ManualCapturePeccancy", "POST", "Manual violation capture", None, 1),
        "Network Peripherals": ("/LAPI/Intelligent/NetworkPeripheralList", "GET", "Get network peripherals", None, 0),
        "Violation Method": ("/LAPI/Intelligent/PeccancyWay", "GET", "Get violation method", None, 0),
        "Picture Bitrate": ("/LAPI/Intelligent/PicBitRate", "GET", "Get picture bitrate", None, 0),
        "Timer Capture": ("/LAPI/Intelligent/TimerCapture", "GET", "Get timer capture", None, 0),
        "Traffic Light Intensity": ("/LAPI/Intelligent/TrafficLightInensity", "GET", "Get traffic light intensity", None, 0),
        "Reset Violation Params": ("/LAPI/INTELLIGENT/PeccancyParamReset", "PUT", "Reset violation params", None, 2),
        "Reset I/O Params": ("/LAPI/INTELLIGENT/IOParamReset", "PUT", "Reset I/O params", None, 2),
        "Driveway Config": ("/LAPI/Smart/DriveWay", "GET", "Get driveway config", None, 0),
        "Traffic Light Config": ("/LAPI/Smart/TrafficLight", "GET", "Get traffic light config", None, 0),
        "Red Light Park Time": ("/LAPI/Smart/RedLightParkTime", "GET", "Get red light park time", None, 0),
        "Violation Capture": ("/LAPI/Smart/ViolationCapture", "GET", "Get violation capture", None, 0),
        "Violation Mode": ("/LAPI/Smart/ViolationMode", "GET", "Get violation mode", None, 0),
        "Traffic Light Status": ("/LAPI/System/DeviceStatus/TrafficLightStatus", "GET", "Get traffic light status", None, 0),
        "Traffic Light Color": ("/LAPI/System/DeviceStatus/TrafficLightColour", "GET", "Get traffic light color", None, 0),
        "Vehicle Queue Length": ("/LAPI/System/DeviceStatus/VehQueueLen", "GET", "Get vehicle queue length", None, 0),
    },
}

# ============================================================================
# API Client
# ============================================================================

class LAPIClient:
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

    def request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                resp = self.session.get(url, timeout=self.timeout, verify=False)
            elif method == "PUT":
                resp = self.session.put(url, json=data, timeout=self.timeout, verify=False)
            elif method == "POST":
                resp = self.session.post(url, json=data, timeout=self.timeout, verify=False)
            elif method == "DELETE":
                resp = self.session.delete(url, timeout=self.timeout, verify=False)
            else:
                return {"error": f"Unknown method: {method}"}

            try:
                body = resp.json()
            except:
                body = resp.text

            return {
                "status": resp.status_code,
                "body": body,
                "url": url,
                "method": method
            }
        except requests.exceptions.Timeout:
            return {"error": "Timeout", "url": url}
        except requests.exceptions.ConnectionError as e:
            return {"error": f"Connection failed: {e}", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}


# ============================================================================
# Interactive Menu
# ============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(target: str, auth: str):
    print(colored("=" * 70, Colors.CYAN))
    print(colored("  LAPI Interactive CLI - Uniview/Digital Ally Endpoint Browser", Colors.BOLD))
    print(colored("=" * 70, Colors.CYAN))
    print(f"  Target: {colored(target, Colors.GREEN)}")
    print(f"  Auth:   {colored(auth, Colors.YELLOW)}")
    print(colored("-" * 70, Colors.DIM))

def print_risk_badge(risk: int) -> str:
    badges = {
        0: colored("[INFO]", Colors.DIM),
        1: colored("[LOW]", Colors.GREEN),
        2: colored("[MED]", Colors.YELLOW),
        3: colored("[HIGH]", Colors.RED),
        4: colored("[CRIT]", Colors.RED + Colors.BOLD),
    }
    return badges.get(risk, "[?]")

def show_categories() -> List[str]:
    """Show category menu and return list of categories"""
    print(colored("\nCategories:", Colors.BOLD))
    categories = list(ENDPOINTS.keys())
    for i, cat in enumerate(categories, 1):
        # Count endpoints in category
        count = len(ENDPOINTS[cat])
        # Check if critical
        marker = colored(" [!]", Colors.RED) if "CRITICAL" in cat else ""
        print(f"  {colored(str(i).rjust(2), Colors.CYAN)}. {cat} ({count} endpoints){marker}")

    print(f"\n  {colored(' 0', Colors.CYAN)}. Exit")
    print(f"  {colored(' s', Colors.CYAN)}. Scan all (no auth test)")
    print(f"  {colored(' r', Colors.CYAN)}. Raw endpoint")
    return categories

def show_endpoints(category: str) -> List[Tuple]:
    """Show endpoints in a category"""
    print(colored(f"\n{category}:", Colors.BOLD))
    endpoints = list(ENDPOINTS[category].items())

    for i, (name, (endpoint, method, desc, params, risk)) in enumerate(endpoints, 1):
        method_color = {
            "GET": Colors.GREEN,
            "PUT": Colors.YELLOW,
            "POST": Colors.BLUE,
            "DELETE": Colors.RED
        }.get(method, Colors.DIM)

        risk_badge = print_risk_badge(risk)
        method_str = colored(method.ljust(6), method_color)

        print(f"  {colored(str(i).rjust(2), Colors.CYAN)}. {risk_badge} {method_str} {name}")
        print(f"      {colored(desc, Colors.DIM)}")

    print(f"\n  {colored(' 0', Colors.CYAN)}. Back to categories")
    print(f"  {colored(' a', Colors.CYAN)}. Execute ALL in category")
    return endpoints

def get_params_from_user(params: Dict) -> Dict:
    """Prompt user for parameters"""
    if not params:
        return None

    print(colored("\nParameters required:", Colors.YELLOW))
    result = {}
    for key, hint in params.items():
        if hint == "multipart":
            print(f"  {key}: (file upload - not supported in interactive mode)")
            continue
        value = input(f"  {key} ({hint}): ").strip()
        if value:
            # Try to parse as int/bool
            if value.isdigit():
                result[key] = int(value)
            elif value.lower() in ('true', 'false'):
                result[key] = value.lower() == 'true'
            else:
                result[key] = value
    return result if result else None

def execute_endpoint(client: LAPIClient, name: str, endpoint: str, method: str,
                     desc: str, params: Dict, risk: int, prompt_params: bool = True):
    """Execute an endpoint and show results"""
    print(colored(f"\n{'=' * 60}", Colors.DIM))
    print(f"Executing: {colored(name, Colors.BOLD)}")
    print(f"Endpoint:  {colored(endpoint, Colors.CYAN)}")
    print(f"Method:    {method}")
    print(f"Risk:      {print_risk_badge(risk)}")

    # Handle critical actions
    if risk >= 4:
        confirm = input(colored("\n⚠️  CRITICAL ACTION - Type 'yes' to confirm: ", Colors.RED))
        if confirm.lower() != 'yes':
            print(colored("Cancelled.", Colors.YELLOW))
            return

    # Get parameters if needed
    data = None
    if params and method in ("PUT", "POST") and prompt_params:
        data = get_params_from_user(params)
    elif params and not prompt_params:
        data = params  # Use default params

    print(colored("-" * 60, Colors.DIM))
    print("Sending request...")

    result = client.request(method, endpoint, data)

    if "error" in result:
        print(colored(f"ERROR: {result['error']}", Colors.RED))
    else:
        status = result['status']
        status_color = Colors.GREEN if status == 200 else Colors.YELLOW if status == 401 else Colors.RED
        print(f"Status: {colored(str(status), status_color)}")
        print(colored("-" * 60, Colors.DIM))

        body = result['body']
        if isinstance(body, dict):
            print(json.dumps(body, indent=2))
        else:
            print(body[:2000] if len(str(body)) > 2000 else body)

    print(colored("=" * 60, Colors.DIM))

def scan_all_endpoints(client: LAPIClient):
    """Scan all endpoints for unauthenticated access"""
    print(colored("\n[*] Scanning all endpoints...", Colors.CYAN))
    print(colored("-" * 60, Colors.DIM))

    accessible = []
    total = 0

    for category, endpoints in ENDPOINTS.items():
        print(f"\n{colored(category, Colors.BOLD)}")
        for name, (endpoint, method, desc, params, risk) in endpoints.items():
            if method != "GET":  # Only scan GET for safety
                continue
            total += 1
            result = client.request("GET", endpoint, None)
            status = result.get("status", "ERR")

            if status == 200:
                marker = colored("[OPEN]", Colors.GREEN + Colors.BOLD)
                accessible.append((category, name, endpoint))
            elif status == 401:
                marker = colored("[AUTH]", Colors.YELLOW)
            elif status == 403:
                marker = colored("[DENY]", Colors.RED)
            elif status == 404:
                marker = colored("[N/A]", Colors.DIM)
            else:
                marker = f"[{status}]"

            print(f"  {marker} {name}")

    print(colored("\n" + "=" * 60, Colors.CYAN))
    print(colored(f"Scan complete: {total} endpoints tested", Colors.BOLD))

    if accessible:
        print(colored(f"\n⚠️  {len(accessible)} ACCESSIBLE WITHOUT AUTH:", Colors.RED + Colors.BOLD))
        for cat, name, ep in accessible:
            print(f"  - [{cat}] {name}")
            print(f"    {colored(ep, Colors.CYAN)}")
    else:
        print(colored("\n✓ No unauthenticated access found", Colors.GREEN))

def raw_endpoint(client: LAPIClient):
    """Execute raw endpoint"""
    print(colored("\nRaw Endpoint Access", Colors.BOLD))
    method = input("Method (GET/PUT/POST/DELETE): ").upper().strip() or "GET"
    endpoint = input("Endpoint: ").strip()
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    data = None
    if method in ("PUT", "POST"):
        data_str = input("JSON data (or empty): ").strip()
        if data_str:
            try:
                data = json.loads(data_str)
            except:
                print(colored("Invalid JSON", Colors.RED))
                return

    execute_endpoint(client, "Raw", endpoint, method, "Raw endpoint", None, 0, prompt_params=False)

def main_loop(client: LAPIClient, target: str, auth_str: str):
    """Main interactive loop"""
    while True:
        clear_screen()
        print_header(target, auth_str)
        categories = show_categories()

        choice = input(colored("\nSelect category: ", Colors.CYAN)).strip().lower()

        if choice == '0' or choice == 'q':
            print("Goodbye!")
            break
        elif choice == 's':
            scan_all_endpoints(client)
            input(colored("\nPress Enter to continue...", Colors.DIM))
        elif choice == 'r':
            raw_endpoint(client)
            input(colored("\nPress Enter to continue...", Colors.DIM))
        elif choice.isdigit() and 1 <= int(choice) <= len(categories):
            category = categories[int(choice) - 1]

            while True:
                clear_screen()
                print_header(target, auth_str)
                endpoints = show_endpoints(category)

                ep_choice = input(colored("\nSelect endpoint: ", Colors.CYAN)).strip().lower()

                if ep_choice == '0' or ep_choice == 'b':
                    break
                elif ep_choice == 'a':
                    # Execute all
                    confirm = input(colored(f"Execute ALL {len(endpoints)} endpoints? (y/N): ", Colors.YELLOW))
                    if confirm.lower() == 'y':
                        for name, (endpoint, method, desc, params, risk) in endpoints:
                            if method == "GET":  # Only GET for batch
                                execute_endpoint(client, name, endpoint, method, desc, params, risk, prompt_params=False)
                        input(colored("\nPress Enter to continue...", Colors.DIM))
                elif ep_choice.isdigit() and 1 <= int(ep_choice) <= len(endpoints):
                    name, (endpoint, method, desc, params, risk) = endpoints[int(ep_choice) - 1]
                    execute_endpoint(client, name, endpoint, method, desc, params, risk)
                    input(colored("\nPress Enter to continue...", Colors.DIM))


def main():
    parser = argparse.ArgumentParser(description="LAPI Interactive CLI")
    parser.add_argument("-t", "--target", required=True, help="Target IP")
    parser.add_argument("-P", "--port", type=int, default=80, help="Port (default: 80)")
    parser.add_argument("-u", "--user", default=DEFAULT_USER, help="Username")
    parser.add_argument("-p", "--password", default=DEFAULT_PASS, help="Password")
    parser.add_argument("--super", action="store_true", help="Use super password")
    parser.add_argument("--no-auth", action="store_true", help="No authentication")
    parser.add_argument("--https", action="store_true", help="Use HTTPS")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout")

    args = parser.parse_args()

    # Setup auth
    username = None
    password = None
    auth_str = "None (testing unauthenticated access)"

    if not args.no_auth:
        username = args.user
        if args.super:
            password = SUPER_PASSWORD
            auth_str = f"{username}:{SUPER_PASSWORD} (super)"
        else:
            password = args.password
            auth_str = f"{username}:{'*' * len(password)}"

    client = LAPIClient(
        host=args.target,
        port=args.port,
        username=username,
        password=password,
        use_https=args.https,
        timeout=args.timeout
    )

    target = f"{args.target}:{args.port}"

    try:
        main_loop(client, target, auth_str)
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")


if __name__ == "__main__":
    main()
