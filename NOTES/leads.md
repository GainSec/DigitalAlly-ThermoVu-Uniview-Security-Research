# Security Leads — Digital Ally / Uniview OET-213H-NB

Non-finding observations worth further exploration or chaining.

---

## Lead 1: _hide Binary - Factory/Debug Tool
**Artifact:** `/program/bin/_hide` (555KB)
**SHA256:** 812a65e6dd8d88d27b56a23d36fdc6f3e7f197b0d117fa3ef725490f3bb777e9
**Observation:** Hidden debug tool with subcommands: `box`, `calibration`, `boardinfo`. The `box` command spawns equipment test CLI `<IPC-OET-213H-NB-WH-equipment>`. May contain additional debug functionality or shell escapes.
**Next Steps:** Reverse engineer _hide binary; fuzz subcommand inputs; check for command injection.

---

## Lead 2: tcpdump -z Command Execution
**Artifact:** uvsh shell, tcpdump command
**Observation:** tcpdump available in uvsh with `-z` flag (post-rotation command). Classic privilege escalation vector but initial tests didn't yield shell. May require specific file rotation conditions.
**Next Steps:** Test with larger captures; try `-z /bin/sh` with proper file paths; check if LD_PRELOAD works.

---

## Lead 3: ONVIF GetSystemBackup Leaks Full Config
**Artifact:** ONVIF endpoint port 81, GetSystemBackup action
**Observation:** GetSystemBackup ONVIF call returns full device config tarball including credentials. May be accessible with default admin/admin auth.
**Next Steps:** Test authenticated ONVIF backup retrieval; check if any ONVIF actions allow config modification.

---

## Lead 4: mmi_client on Port 20202
**Artifact:** TCP port 20202, process `mmi_client`
**Observation:** Undocumented service listening on port 20202. Purpose unknown - possibly MMI (Man-Machine Interface) control.
**Next Steps:** Banner grab; protocol analysis; fuzz inputs.

---

## Lead 5: Mongoose Web Server Configuration
**Artifact:** `/program/www/mongoose_http.conf`, `mongoose_https.conf`
**Observation:** Web server is Mongoose. Config files may reveal CGI handlers, auth bypasses, or path traversal opportunities.
**Next Steps:** Analyze config; test CGI endpoints; check for known Mongoose vulnerabilities.

---

## Lead 6: Firmware Update Mechanism
**Artifact:** `updatecpld`, `fw_printenv`, `fw_setenv`
**Observation:** Multiple firmware update tools present. u-boot environment accessible via fw_printenv/fw_setenv. May allow boot parameter manipulation.
**Next Steps:** Dump u-boot environment; check for secure boot bypass; test firmware signing validation.

---

## Lead 7: ActiveX Components
**Artifact:** `/program/www/ActiveX/`
**Observation:** ActiveX directory present - suggests IE-based management interface with native code execution potential.
**Next Steps:** Extract and analyze ActiveX controls; check for memory corruption bugs.

---

## Lead 8: cgi-bin Directory
**Artifact:** `/program/www/cgi-bin/`
**Observation:** CGI directory present. May contain vulnerable scripts for command injection or auth bypass.
**Next Steps:** Enumerate and analyze all CGI scripts; test for injection vulnerabilities.

---

## Lead 9: HiSilicon Kernel 4.9.37
**Artifact:** Kernel version Linux 4.9.37
**Observation:** Older kernel (2020 build). May be vulnerable to known privilege escalation CVEs (DirtyCOW variants, etc.).
**Next Steps:** Check kernel CVE database for 4.9.37 armv7l vulnerabilities.

---

## Lead 10: FTP Service Behavior
**Artifact:** ftpget/ftpput in BusyBox
**Observation:** Device can initiate FTP connections for firmware updates. No certificate validation observed.
**Next Steps:** Test for MITM during update; check if arbitrary URLs can be specified.

---

## Lead 11: SNMP Configuration
**Artifact:** `/etc/snmp.conf`
**Observation:** SNMP config file present. May have default community strings or expose device info.
**Next Steps:** Test SNMP v1/v2c with common community strings; enumerate MIBs.

---

## Lead 12: Wiegand Interface
**Artifact:** `kwiegand.ko` kernel module, wiegand commands
**Observation:** Wiegand protocol support for access control integration. May allow badge cloning or replay attacks.
**Next Steps:** Analyze Wiegand implementation; test for replay vulnerabilities.

---

## Lead 13: LAPI REST API Auth Bypass Testing
**Artifact:** 200+ LAPI endpoints in `/program/www/script/common/ComScript.d7fe61b7.js`
**Observation:** Extensive REST API surface. Many endpoints may lack proper authentication or have auth bypass vulnerabilities. Priority targets: FactoryReset, Upgrade, Users_Cfg, TelnetEnableCfg.
**Next Steps:** Fuzz each endpoint without auth; test with default creds; check for IDOR; test parameter injection.

---

## Lead 14: main.cgi Binary Analysis
**Artifact:** `/program/www/cgi-bin/main.cgi` (9.7KB ARM ELF)
**Observation:** Single CGI binary handles web authentication. Parameters: cmd_type, web_id, userName, loginPwd, loginType. Binary analysis may reveal command injection or buffer overflow.
**Next Steps:** Reverse engineer with Ghidra; fuzz CGI parameters; check for format string bugs.

---

## Lead 15: Face Recognition Database APIs
**Artifact:** LAPI face library endpoints: PeopleLibs, FaceDetection, LibraryFile
**Observation:** Device handles biometric data via REST APIs. May contain PII exposure, bypass auth for face DB access, or template extraction vulnerabilities.
**Next Steps:** Test face library APIs for auth bypass; check for biometric data leakage; test import/export functions.

---

## Chain Opportunities

1. **Pre-auth RCE → Full Filesystem Dump:** UDP/7788 → telnet → uvsh → updatecpld → tar dump (ACHIEVED)
2. **Web Admin → Telnet Enable → Root:** admin/admin → enable telnet → root/123456
3. **Super Password → Debug Access:** 87654321 → hidden menus → ?
4. **ONVIF → Config Theft → Credential Extraction:** GetSystemBackup → config.tgz → creds

---

## Tools for Further Analysis

- Ghidra/IDA for binary RE (_hide, mwareserver, daemon)
- Burp Suite for web/ONVIF testing
- Wireshark for protocol analysis (port 20202)
- john/hashcat for password cracking
- AFL++/libFuzzer for CGI fuzzing
