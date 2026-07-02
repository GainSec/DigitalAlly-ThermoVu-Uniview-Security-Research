# Future Security Testing Leads - Digital Ally OET-213H / DTM-600

**Target:** Uniview-based facial recognition/thermal access control device
**Device Model:** OET-213H-NB-WH (India region)
**Firmware Date:** 2020-08-03
**Manufacturer:** Uniview (rebranded as Digital Ally)

---

## CRITICAL - Hardcoded Credentials & Keys

### 1. Root Password Hashes (DES Crypt)
- **Location:** `firmware-dump/dump/etc/passwd`
- **Hash:** `root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh`
- **Backup Hash:** `root:ab8nBoH3mb8.g:0:0::/root:/bin/sh` (passwd-)
- **Testing:** Crack with John/Hashcat; DES crypt is weak
- **Shell:** Custom restricted shell `/usr/bin/uvsh` - test for escape

### 2. Embedded SSL Private Key
- **Location:** `firmware-dump/dump/config/ssl_cert.pem`
- **Issue:** RSA private key shipped in firmware - enables MITM
- **Cert CN:** `cn.uniview.com`
- **Cert Expiry:** 2021-08-27 (expired)
- **Testing:** Use key for TLS interception on all devices with same firmware

### 3. SNMP Default Community Strings
- **Location:** `firmware-dump/dump/etc/snmp.conf`
- **Read:** `rocommunity public`
- **Read/Write:** `rwcommunity private`
- **Testing:** SNMP walk, configuration extraction, potential RCE via SNMP SET

### 4. Web Interface Default Credentials
- **Location:** `firmware-dump/dump/config/config_a.xml`
- **Username:** `admin`
- **Password Hash (MD5):** `2ac9cb7dc02b3c0083eb70898e549b63`
- **Default Hash (MD5):** `21232f297a57a5a743894a0e4a801fc3` = "admin"
- **Test User:** `test` / `ee11cbb19052e40b07aac0ca060c23ee` (MD5 of "user")
- **User6 (Level 10/Admin):** `4794d4584b7410210806d0d72ca5c32c`

### 5. SNMPv3 Hardcoded Credentials
- **Location:** `firmware-dump/dump/config/default_cfg.xml:2661-2665`
- **Username:** `admin`
- **AuthKey:** `Snmp@123`
- **PrivKey:** `Snmp@123`

### 6. WiFi Default Key
- **Location:** `firmware-dump/dump/config/config_a.xml:70-75`
- **Key:** `12345678` (WPA/WPA2)
- **Gateway:** `172.16.0.1`

### 7. SIP/Registration Password (Obfuscated)
- **Location:** `firmware-dump/dump/config/config_a.xml:354`
- **Value:** `0X]&amp;0D]]05` (custom encoding)
- **Testing:** Reverse engineer encoding scheme in mwareserver binary

### 8. PPPoE Credentials
- **Location:** `firmware-dump/dump/config/config_a.xml:39-40`
- **Username:** `user`
- **Password:** `admin` (MD5: `21232f297a57a5a743894a0e4a801fc3`)

---

## HIGH - Network Services & Attack Surface

### 9. Telnet Enabled
- **Location:** `firmware-dump/dump/config/config_a.xml:315-317`
- **Status:** `<TelnetEnable><Enable>1</Enable></TelnetEnable>`
- **Testing:** Connect, test default creds, check for unauthenticated access

### 10. Mongoose Web Server
- **Location:** `firmware-dump/dump/program/www/mongoose_http.conf`
- **Ports:** 80 (HTTP), 443 (HTTPS)
- **Document Root:** `/www/`
- **SSL Cert:** Uses embedded private key
- **Testing:** Web app vuln scanning, directory traversal, auth bypass

### 11. ONVIF Implementation
- **Location:** `firmware-dump/dump/program/www/page/common/onvif_test.8e029ca4.htm`
- **Features:** Device discovery, authentication toggle
- **Testing:** ONVIF-specific vulns, auth bypass, CVE scanning

### 12. iSCSI Client
- **Location:** `firmware-dump/dump/etc/iscsi/iscsid.conf`
- **Status:** Manual startup, CHAP disabled by default
- **Testing:** Unauthorized storage access, credential injection

---

## HIGH - Binary Analysis Targets

### 13. mwareserver (Main Application)
- **Location:** `firmware-dump/dump/program/bin/mwareserver`
- **Size:** 6.6MB
- **Functions Found:** `BP_DigestAuth`, `BP_FillAuthPasswdPrefix`, `BP_CheckIsWeakPasswd`, `IMOS_Passwd2Cipher`, `KDM_Key_*`
- **Testing:** Reverse engineer auth logic, fuzzing, buffer overflow analysis

### 14. mmi_client (GUI Application)
- **Location:** `firmware-dump/dump/program/bin/mmi_client`
- **Size:** 6MB
- **Testing:** IPC analysis, local privilege escalation

### 15. main.cgi (Web CGI Handler)
- **Location:** `firmware-dump/dump/program/www/cgi-bin/main.cgi`
- **Size:** 9.7KB
- **Type:** ARM ELF, stripped
- **Testing:** Command injection, auth bypass, input validation

### 16. _hide (Diagnostic Tool)
- **Location:** `firmware-dump/dump/program/bin/_hide`
- **Size:** 555KB
- **Functions:** `Systest_CmdProc_*` (hardware control, license test, Bluetooth, RFID, etc.)
- **Testing:** Undocumented debug interface, hardware manipulation

### 17. update_move (Firmware Update Handler)
- **Location:** `firmware-dump/dump/program/bin/update_move`
- **Size:** 1.1MB
- **Testing:** Firmware verification bypass, code injection during update

### 18. cfgtool (Configuration Tool)
- **Location:** `firmware-dump/dump/program/bin/cfgtool`
- **Size:** 97KB
- **Testing:** Configuration manipulation, privilege escalation

---

## MEDIUM - Init Scripts & Boot Process

### 19. init.sh Boot Script
- **Location:** `firmware-dump/dump/program/bin/init.sh`
- **Issues Found:**
  - Password replacement from `/config/passwd` (line 638-649)
  - WiFi module loading without validation (line 616-627)
  - udhcpc runs without authentication when no manuinfo label
  - Environment variable injection potential
- **Testing:** Boot persistence, config file manipulation

### 20. passwd.sh
- **Location:** `firmware-dump/dump/program/bin/passwd.sh`
- **Function:** Copies `/etc/passwd` to `/config/passwd`
- **Testing:** Race condition, symlink attacks

### 21. prepare_hide.sh
- **Location:** `firmware-dump/dump/program/bin/prepare_hide.sh`
- **Function:** Kills mwareserver and related processes
- **Testing:** Service disruption, DoS

---

## MEDIUM - Configuration & Data Exposure

### 22. Device Capabilities XML
- **Location:** `firmware-dump/dump/config/device_cap.xml`
- **Contents:** Full device feature enumeration
- **Testing:** Feature fingerprinting, capability abuse

### 23. Manufacturing Info
- **Location:** `firmware-dump/dump/config/manuinfo.xml`
- **Contents:** `ActiveCode: 3148ENOOCQUF7E6D7LYQOHXAQ`
- **Testing:** License bypass, device cloning

### 24. Flash Logs
- **Location:** `firmware-dump/dump/config/flashlog/log.tgz`
- **Size:** 342KB
- **Contents:** Historical logs, potentially sensitive data
- **Testing:** Information disclosure, credential leakage

### 25. dmesg Boot Log
- **Location:** `firmware-dump/dump/config/flashlog/dmesg.log`
- **Contents:** Kernel boot messages, hardware info
- **Testing:** Kernel version, module vulnerabilities

---

## MEDIUM - Cryptographic Weaknesses

### 26. MD5 Password Hashing
- **Location:** Multiple XML configs
- **Issue:** MD5 used for password storage (unsalted)
- **Testing:** Rainbow table attacks, hash cracking

### 27. Custom Encoding Scheme (Passwd20)
- **Location:** `config_a.xml` `<WebLoginPasswd20>`, `<UserPasswd20>`
- **Examples:** `!S]5+Nb?+b]S+I]&?X`, `+lb?0lbD`
- **Testing:** Reverse engineer encoding, potential weak crypto

### 28. KDM Key Library
- **Referenced in:** mwareserver strings
- **Functions:** `KDM_Key_Init`, `KDM_Key_DecData`, `KDM_Key_ApplyVkd`
- **Testing:** Key extraction, encryption bypass

---

## LOW - Additional Attack Surface

### 29. WiFi Module Support
- **Modules:** RTL8188FTV, RTL8188EUS, RTL8821CU
- **Testing:** Deauth attacks, WPA cracking, driver vulns

### 30. 4G Module Support
- **Module:** GobiNet_Y (Quectel)
- **Testing:** APN manipulation, network pivoting

### 31. Wiegand Interface
- **Location:** `firmware-dump/dump/program/bin/init.sh:244-262`
- **Testing:** Card cloning, RFID attacks

### 32. Face Recognition Models
- **Location:** `firmware-dump/dump/program/factory/models/`
- **Files:** TensorEngine, VNP.mvcmd (7.6MB)
- **Testing:** Model extraction, adversarial attacks

### 33. Temperature Module Firmware
- **Location:** `firmware-dump/dump/program/bin/temp_measure_mod_app_*.bin`
- **Testing:** Firmware modification, measurement tampering

### 34. USB Hotplug Scripts
- **Location:** `firmware-dump/dump/etc/udev/usbdev-hotplug.sh`
- **Testing:** USB-based attack vectors, autorun exploitation

---

## DTM-600 LiveFS Additional Leads

### 35. Extracted Filesystem Tarballs
- **Location:** `dtm-600/livefs/dump.tar` (154MB), `dump-data.tar` (32MB)
- **Testing:** Extract and analyze for runtime secrets, logs

### 36. Config Export Files
- **Location:** `dtm-600/diag/OET-213H-NB_192.168.30.178_config.tgz`
- **Contents:** Device-specific config_a.xml
- **Testing:** Compare configs, identify unique secrets

### 37. ACS Data Info
- **Location:** `dtm-600/diag/ACSDataInfo.tgz`
- **Testing:** Access control system data, user records

### 38. ONVIF Test Script
- **Location:** `dtm-600/run_onvif_from_markdown.py`
- **Testing:** ONVIF API testing, auth bypass

---

## Recommended Testing Priority

1. **Immediate:** Crack root password hashes (#1)
2. **Immediate:** Test telnet with default creds (#9)
3. **Immediate:** SNMP enumeration with public/private (#3)
4. **High:** Web interface auth bypass & injection (#10, #15)
5. **High:** Binary reverse engineering of mwareserver (#13)
6. **Medium:** Firmware update mechanism (#17)
7. **Medium:** Custom encoding scheme reversal (#27)

---

## Tools Required

- John the Ripper / Hashcat (password cracking)
- Ghidra / IDA Pro (binary analysis)
- Burp Suite (web testing)
- Wireshark / tcpdump (network analysis)
- snmpwalk / snmpset (SNMP testing)
- ONVIF Device Manager (ONVIF testing)
- Frida (runtime instrumentation)
- binwalk (firmware extraction)

---

## DETAILED ATTACK SURFACE ANALYSIS

### Web Server (Mongoose) - 337 LAPI Endpoints Identified

**Critical API Categories:**
```
/LAPI/V1.0/Channel/0/NetWork/Telnet     - Telnet control
/LAPI/V1.0/NetWork/HTTPS                - HTTPS config
/LAPI/V1.0/NetWork/SNMP                 - SNMP config
/LAPI/V1.0/NetWork/FTP                  - FTP server
/LAPI/V1.0/Smart/FaceRecognition/*      - Face DB access
/LAPI/V1.0/PACS/Controller/*            - Access control
/LAPI/V1.0/IO/DoorControlCfg            - Door control
/LAPI/V1.0/IO/WiegandInfo               - Wiegand/RFID
/LAPI/Demo/Debug/*                      - Debug functions
/LAPI/Demo/LaserControl/reboot          - Device reboot
/LAPI/Demo/LaserControl/restore         - Factory restore
```

**main.cgi CGI Handler:**
- **Parameters:** `cmd_type`, `web_id`, `userName`, `loginPwd`, `loginType`, `menuType`, `langinfo`, `passwdEmpt`, `sdkPort`, `rtspPort`, `IsVMNB`
- **Potential XSS:** User parameters reflected in iframe src without sanitization
- **Format String:** Uses `%s=%s` pattern for parameter output

---

### mwareserver Command Injection Vectors

**Confirmed shell command patterns with user-controlled %s:**
```c
cp -f %s /etc/localtime              // Timezone injection
cp %s /config/flashlog               // Path injection
cp %s %s                             // Double path injection
tar zxf %s %s                        // Archive command injection
cp -r %s %s%s                        // Recursive copy injection
echo -n UNVNonBrandDev%s | md5sum    // Echo injection
umount %s                            // Unmount injection
mount -t ext2 %s %s                  // Mount injection
rm -rf %s                            // Delete injection
mv /cache/update/%s                  // Update path injection
sh /program/bin/DelConfig.sh         // Direct shell execution
/program/bin/resetconfig.sh &        // Background shell exec
```

**Dangerous Functions:**
- `IMOS_system()` - system() wrapper
- `IMOS_system_nofd()` - system() variant without fd
- `IMOS_popen()` - popen() wrapper
- `execle()` - Direct execution
- `IMOS_strcpy()`, `IMOS_strcat()` - Buffer overflow potential

**Debug/Backdoor Functions:**
- `BP_RegDebugCmd` - Register debug commands
- `LOG_SetAllModuleDebug` - Enable all debug
- `debug_config_turn_on_debugging` - Turn on debug mode
- `MW_MCP_IQDebug` - IQ debug interface

---

### ONVIF Implementation

**Config Endpoints:**
- `MW_CTRL_GetOnvifCfg` - Get ONVIF config
- `MW_CTRL_OnvifVerifyAuth` - Auth verification
- `LAPI_URL.OnvifDebug` - Debug settings

**Features:**
- `OnvifEnabled` - Enable/disable ONVIF
- `AuthenticationEnabled` - Auth toggle (can be disabled!)
- `DetectionEnbalbed` - Device discovery
- `OnvifTestEnabled` - Test mode

**Attack Vector:** Disable `AuthenticationEnabled` via API to bypass authentication

---

### iSCSI Client (No Authentication)

**Config:** `/etc/iscsi/iscsid.conf`
- CHAP disabled by default: `#node.session.auth.authmethod = CHAP`
- Manual startup: `node.startup = manual`
- No authentication configured

**Functions in mwareserver:**
- `MAS_MR_OPENISCSI_Login` - iSCSI login
- `MAS_MR_ISCSI_GetDev` - Get devices
- `ISCSI_ReloginThread` - Auto-reconnect

**Attack Vector:** Configure malicious iSCSI target, device will connect without auth

---

### mmi_client GUI Binary

**Interesting Paths:**
```
/root/mmi/Check/TemperMode
/root/mmi/Check/IDCard
/root/mmi/Check/ICCard
/root/mmi/Check/Face
/root/mmi/Check/Card_Face
MW_CMD_DOORCTL_PASSWD_INFO
MW_CMD_EG_FACE_DET_HALT
```

**Functions:**
- `IMOS_system` - System command execution
- `execl` - Direct execution
- `MMI_Creat_LoginDlg` - Login dialog creation

---

### Authentication Bypass Vectors

1. **ONVIF Auth Toggle:** Disable via `/LAPI/V1.0/Channel/0/Demo/OnvifDebug`
2. **Debug Mode:** Enable via `LOG_SetAllModuleDebug`, `debug_config_turn_on_debugging`
3. **RTSP Auth Mode:** Variable `gulRTSPAuthMode` controls RTSP authentication
4. **Web Session:** Check for session fixation, cookie manipulation

---

## EXPLOIT DEVELOPMENT PRIORITIES

### Priority 1: Pre-Auth RCE
1. Test LAPI endpoints without authentication
2. Command injection via timezone/path parameters
3. Format string vulnerabilities in CGI

### Priority 2: Auth Bypass
1. Crack MD5 password hashes (rainbow tables)
2. Crack DES root password hash
3. Disable ONVIF/RTSP authentication via API

### Priority 3: Post-Auth RCE
1. Firmware update mechanism abuse
2. Configuration backup/restore injection
3. Debug command registration

### Priority 4: Persistence
1. Modify `/config/passwd` for persistent root access
2. Add SSH keys to root
3. Modify init scripts for backdoor

---

*Generated: 2025-12-15*
*Source: firmware-dump/, dtm-600/livefs/*
*Analysis: Mongoose web server, mwareserver binary, main.cgi, ONVIF, iSCSI*
