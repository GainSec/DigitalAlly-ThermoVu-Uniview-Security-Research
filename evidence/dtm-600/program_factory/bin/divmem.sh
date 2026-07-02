#!/bin/sh

#set -x

#脚本用途：1. 通过调整uboot环境变量，设置OS内存大小，设备重启生效。
#          2. OS内存影响设备启动情况，必须执行严格的参数检查。
# 检测函数入参是否为纯数字，只支持十进制
is_digital()
{
	echo "$1" | [ -n "`sed -n '/^[0-9][0-9]*$/p'`" ] && echo "yes" || echo "no"
}

__help()
{
	echo "usage: $0 [os_memory_mb], such as:"
	echo "$0 192"
}

if [ $# -ne 1 ]; then
	__help
	exit 1
fi

#内存大小入参不是纯数字，禁止划分OS/MMZ内存
OS_MEM_MB=$1
if [ "$(is_digital $OS_MEM_MB)" = "no" ]; then
	echo "fail: $OS_MEM_MB is not pure digitals"
	exit 1
fi

#无电子标签，无法获知物理内存大小，禁止划分OS/MMZ内存
DEVICENAME=`/program/bin/manuinfotool | grep PROTOTYPE_NAME|cut -d : -f 2`
if [ -z "$DEVICENAME" ]; then
	echo "fail: there is no manuinfo, forbidding divide physical memroy"
	exit 1
fi

#获取物理内存大小失败，禁止划分OS/MMZ内存
PHY_MEM_TOTAL=`cat /proc/driver/memsize |grep total| cut -d : -f 2`
if [ -z "$PHY_MEM_TOTAL" ]; then
	echo "fail: get total physical memory size failed"
	exit 1
fi

#待设置OS内存大小不得大于等于物理内存
if [ $OS_MEM_MB -ge $PHY_MEM_TOTAL ]; then
	echo "fail: forbidding setting os memory[$OS_MEM_MB] >= physical memory[$PHY_MEM_TOTAL]"
	exit 1
fi

#检查uboot环境变量工具权限
UBOOT_ENV_SET_TOOL="/program/bin/fw_setenv"
UBOOT_ENV_GET_TOOL="/program/bin/fw_printenv"
if [ ! -x "$UBOOT_ENV_SET_TOOL" -o ! -x "$UBOOT_ENV_GET_TOOL" ]; then
	echo "fail: $UBOOT_ENV_SET_TOOL($UBOOT_ENV_GET_TOOL) not found or not executable"
	exit 1
fi

#获取现有uboot环境变量bootargs字段
BOOT_ARGS_OLD=$($UBOOT_ENV_GET_TOOL | grep bootargs | sed -r 's/bootargs=(.*)/\1/g')
if [ -z "$BOOT_ARGS_OLD" ]; then
	echo "fail: $UBOOT_ENV_GET_TOOL get bootargs failed"
	exit 1
fi

#从bootargs字段截取mem字段value，仅保留数字。例如mem=192M，截取后为192
OS_MEM_IN_UBOOT_ENV=$(echo $BOOT_ARGS_OLD | awk '{for (f=1; f <= NF; f+=1) {if ($f ~ /mem=/) {print $NR}}}' | tr -cd "[0-9]")
if [ -z "$OS_MEM_IN_UBOOT_ENV" ]; then
	echo "fail: grep os memory from bootargs failed, old_bootargs=${BOOT_ARGS_OLD}"
	exit 1
fi

#设置的OS内存大小跟现有uboot环境变量一致，直接返回成功
if [ "$OS_MEM_IN_UBOOT_ENV" = "$OS_MEM_MB" ]; then
	echo "os memory size[${OS_MEM_MB}MB] is same to uboot environmnet, do nothing "
	exit 0
fi

#替换mem字段，得到新的bootargs
BOOT_ARGS_NEW=$(echo $BOOT_ARGS_OLD | sed -r "s/mem=([0-9]*)M/mem=${OS_MEM_MB}M/g")
if [ -z "$BOOT_ARGS_NEW" -o "$BOOT_ARGS_OLD" = "$BOOT_ARGS_NEW" ]; then
	echo "fail: replacing bootargs failed, old_bootargs=${BOOT_ARGS_OLD}, new_bootargs=${BOOT_ARGS_NEW}"
	exit 1
fi

#设置新的bootargs环境变量
$UBOOT_ENV_SET_TOOL bootargs "$BOOT_ARGS_NEW"
if [ $? -ne 0 ]; then
	echo "fail: $UBOOT_ENV_SET_TOOL bootargs $OS_MEM_MB"
fi

sync;sync;
echo "success: setting os memory to ${OS_MEM_MB}MB, please reboot the system"
#echo "bootargs=${BOOT_ARGS_NEW}"
exit 0
