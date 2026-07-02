# Digital Ally ThermoVu DTM-600 Runtime Enumeration

**Date:** 2026-01-12
**Target:** 192.168.30.178:2323 (root shell via CVE-2021-45039 + CVE-2023-0773)
**Access Method:** `nc 192.168.30.178 2323`

---

## 1. System Identification

| Property | Value |
|----------|-------|
| **Device Model** | OET-213H-NB (ThermoVu DTM-600) |
| **Prototype** | OET-213H-NB-WH |
| **OEM Vendor** | Uniview (cn.uniview.com) |
| **SoC** | HiSilicon Hi3516DV300 |
| **Architecture** | ARMv7 Processor rev 5 (v7l), Dual-core Cortex-A7 |
| **Kernel** | Linux 4.9.37 SMP (Jul 7 2020) |
| **Compiler** | gcc 6.3.0 (HC&C V100R002C00B035_20190218) |
| **Manufacturing Date** | 2020-08-03 |
| **Region Code** | IN |

---

## 2. Hardware Specifications

### CPU
```
processor       : 0, 1
model name      : ARMv7 Processor rev 5 (v7l)
BogoMIPS        : 100.00
Features        : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm
Hardware        : Hisilicon HI3516DV300 DEMO Board
```

### Memory
```
MemTotal:         511880 kB (~500 MB)
MemFree:          366160 kB
MemAvailable:     379000 kB
SwapTotal:             0 kB (no swap)
```

### Storage (eMMC)
```
/dev/mmcblk2      3866624 blocks (~3.7 GB total)
```

---

## 3. Partition Layout

| Partition | Size | Mount Point | Filesystem | Mode |
|-----------|------|-------------|------------|------|
| mmcblk2p1 | 1 MB | - | boot | - |
| mmcblk2p2 | 16 MB | - | bootlogo | - |
| mmcblk2p3 | 16 MB | - | kernel | - |
| mmcblk2p4 | 16 MB | - | kernel_bak | - |
| mmcblk2p5 | 16 MB | /config | ext4 | rw |
| mmcblk2p6 | 16 MB | /cfgbak | ext4 | rw |
| mmcblk2p7 | 1 MB | - | cliinfo | - |
| mmcblk2p8 | 1 MB | - | cliinfo_bak | - |
| mmcblk2p9 | 1 MB | - | mtd_runtime | - |
| mmcblk2p10 | 32 MB | /calibration | ext4 | ro |
| mmcblk2p11 | 512 KB | - | update | - |
| mmcblk2p12 | 304 MB | /program | ext4 | **ro** |
| mmcblk2p13 | 304 MB | /cache | ext4 | rw |
| mmcblk2p14 | 3 GB | /data | ext4 | rw |

**Note:** `/program` is mounted read-only, contains firmware binaries.

---

## 4. Network Configuration

### Interface
```
eth0      HWaddr E4:F1:4C:25:D7:B2
          inet addr:192.168.30.178  Mask:255.255.255.0
          MTU:1454
```

### TCP Listeners

| Port | Process | Description |
|------|---------|-------------|
| 23 | telnetd | Default telnet (root/123456) |
| 80 | mwareserver | HTTP Web UI |
| 81 | mwareserver | ONVIF/SOAP |
| 85 | mwareserver | Unknown |
| 554 | mwareserver | RTSP streaming |
| 2323 | busybox telnetd | Backdoor shell (our access) |
| 20202 | mmi_client | MMI service |
| 49152 | mwareserver | SDK/proprietary |
| 54321 | mwareserver | Local IPC (127.0.0.1 only) |

### UDP Listeners

| Port | Process | Description |
|------|---------|-------------|
| 82 | mwareserver | Unknown |
| 161 | mwareserver | **SNMP** |
| 1025 | mwareserver | Unknown (x2) |
| 1900 | mwareserver | **SSDP/UPnP** |
| 2048 | mwareserver | Local IPC |
| 3702 | mwareserver | **WS-Discovery** |
| 7001 | mwareserver | Local IPC |
| **7788** | maintain | **VULNERABLE** (CVE-2021-45039) |

---

## 5. Running Processes

### Key Services
| PID | Process | Description |
|-----|---------|-------------|
| 915 | mwareserver | Main firmware application |
| 1386 | maintain | **Vulnerable UDP/7788 service** |
| 1387 | mmi_client | MMI/display client |
| 1393 | daemon | Web server daemon |
| 149 | telnetd | Default telnet service |
| 3002 | uvsh | Restricted vendor shell |

### Kernel Threads
- `hidog` - Hardware watchdog
- `irq/52-VI_CAP0` - Video input capture
- `motor_queue` - PTZ motor control
- `wiegand_in_wkqu` - Wiegand reader interface
- `goodix_wq` - Goodix touchscreen

---

## 6. Credentials Discovered

### System Accounts
```
/etc/passwd: root:dIkAjCy0Zma2s:0:0:Linux User,,,:/root:/bin/sh
```
Password hash `dIkAjCy0Zma2s` = "root" (DES crypt)

### Live Config Credentials (/config/config_a.xml)

| Line | Field | Hash/Value | Plaintext |
|------|-------|-----------|-----------|
| 40 | PPPOEPassword | 21232f297a57a5a743894a0e4a801fc3 | admin |
| 70,75 | WiFi Key | 12345678 | 12345678 |
| 374 | WebLoginPasswd | 2ac9cb7dc02b3c0083eb70898e549b63 | Password1 |
| 438 | UserPasswd | ee11cbb19052e40b07aac0ca060c23ee | user |
| 468 | UserPasswd | 4794d4584b7410210806d0d72ca5c32c | Unknown |

### Default Telnet Credentials
- `root` / `123456` (spawned by CVE-2021-45039)

---

## 7. SSL/TLS Certificate & Private Key

**Location:** `/config/ssl_cert.pem`

```
Subject: C=CN, ST=ZheJiang, O=uniview, OU=uniview, CN=cn.uniview.com
Issuer:  C=CN, ST=ZheJiang, L=HangZhou, O=uniview, OU=uniview, CN=cn.uniview.com
Valid:   Aug 28 08:20:22 2018 - Aug 27 08:20:22 2021 (EXPIRED)
```

**CRITICAL:** RSA private key is embedded in the same file and shared across all devices.

---

## 8. U-Boot Environment

```
bootargs=mem=256M console=ttyAMA0,115200 blkdevparts=mmcblk2:...
bootcmd=mmc read 0 82000000 1800 8000;bootm 0x82000000
bootdelay=2
ipaddr=192.168.0.2
serverip=192.168.0.10
board=hi3516dv300
vendor=hisilicon
```

**Serial Console:** ttyAMA0 @ 115200 baud

---

## 9. Kernel Modules (HiSilicon SDK)

| Module | Size | Description |
|--------|------|-------------|
| hi3516cv500_base | 56 KB | Base platform |
| hi3516cv500_vi | 489 KB | Video input |
| hi3516cv500_vpss | 325 KB | Video processing |
| hi3516cv500_venc | 231 KB | Video encoding |
| hi3516cv500_h264e | 125 KB | H.264 encoder |
| hi3516cv500_h265e | 146 KB | H.265 encoder |
| hi3516cv500_nnie | 75 KB | Neural network inference |
| hi3516cv500_ive | 185 KB | Intelligent video |
| hi_cipher | 150 KB | Crypto acceleration |
| NetUserDrv | 323 KB | Network user driver |
| kmotor | 81 KB | Motor/PTZ control |
| kwiegand | 21 KB | Wiegand interface |
| kruntime | 11 KB | Runtime support |

---

## 10. Filesystem Structure

```
/
├── bin/          # BusyBox applets
├── sbin/         # System binaries
├── etc/          # Configuration (symlinks to /config)
├── lib/          # Libraries + kernel modules
├── program/      # Firmware application (RO)
│   ├── bin/      # 107 binaries/scripts
│   ├── lib/      # Application libraries
│   ├── www/      # Web interface
│   ├── factory/  # Factory test tools
│   └── firmware/ # Embedded firmware blobs
├── config/       # Live configuration (RW)
├── data/         # User data, logs (RW)
├── cache/        # Cache partition (RW)
├── calibration/  # Thermal calibration (RO)
├── tmp/          # Temporary files (tmpfs)
└── var/          # Variable data (tmpfs)
```

---

## 11. Notable Binaries (/program/bin/)

| Binary | Description |
|--------|-------------|
| mwareserver | Main firmware application |
| maintain | **Vulnerable** UDP/7788 service |
| updatecpld.sh | **Vulnerable** FTP exec (CVE-2023-0773) |
| daemon | Web server |
| mmi_client | Display/MMI interface |
| cfgtool | Configuration tool |
| fw_printenv/fw_setenv | U-Boot env access |
| hostapd | WiFi AP daemon |
| disktool | Storage management |
| _hide | Unknown hidden binary (555 KB) |
| uvsh | Restricted vendor shell |

---

## 12. BusyBox Applets

Full BusyBox installation with common applets including:
- Network: `telnetd`, `ftpget`, `ftpput`, `wget`, `nc`, `arp`, `ifconfig`, `netstat`, `route`
- System: `mount`, `umount`, `reboot`, `poweroff`, `init`, `login`, `passwd`
- Files: `cat`, `cp`, `mv`, `rm`, `ls`, `find`, `grep`, `sed`, `awk`
- Editors: `vi`
- Compression: `gzip`, `gunzip`, `tar`, `unzip`

---

## 13. Attack Surface Summary

### Critical
- UDP/7788 maintain service (CVE-2021-45039) - RCE via buffer overflow
- updatecpld FTP exec (CVE-2023-0773) - Arbitrary code execution
- Shared TLS private key across all devices
- Expired TLS certificate

### High
- Default telnet credentials (root/123456)
- Weak web admin password (Password1)
- Hardcoded WiFi key (12345678)
- SNMP service on UDP/161
- UPnP/SSDP on UDP/1900

### Medium
- RTSP streaming without auth verification needed
- Multiple hardcoded credentials in config
- PPPoE credentials (admin)
- No password shadow file (DES crypt in /etc/passwd)

---

## 14. Recommendations for Further Testing

1. **SNMP enumeration** - Check community strings, extract MIBs
2. **RTSP testing** - Check for unauthenticated streams
3. **Web API fuzzing** - Test ONVIF/SOAP endpoints
4. **Firmware extraction** - Dump /program partition for offline analysis
5. **Binary analysis** - Reverse engineer mwareserver, maintain, _hide
6. **WiFi testing** - Test AP mode with weak key
7. **U-Boot** - Test serial console access for bootloader manipulation
