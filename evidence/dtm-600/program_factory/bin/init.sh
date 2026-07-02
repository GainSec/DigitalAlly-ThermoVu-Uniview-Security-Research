#!/bin/sh

PartitionName="program"
VolumeName="program"
DeviceName="ubi0"
FolderName="/program"
#PRODUCT_TYPE=`zcat /proc/config.gz | grep "CONFIG_UNIVIEW_" | grep "=y" | sed 's/=y//'`
PRODUCT_ID=255
BUILD_INFO="NULL"

#FLASH存在坏块时，使用manuinfotool会打印bad block等字段导致解析错误。故在此先调用
#一次manuinfotool，会在/tmp/目录下生成manuinfo文件，后续manuinfotool优先访问该文件
/program/bin/manuinfotool get LENS >/dev/null

#if [ -r /program/bin/top -a -r /usr/bin/top ]; then
#	rm -rf /usr/bin/top
#fi
	 
mdev -s

kernel_ver=$(uname -r) 


gt911_load()
{
	if [ -r /lib/modules/$kernel_ver/extra/kgt9xx.ko ]; then
		 insmod  /lib/modules/$kernel_ver/extra/kgt9xx.ko Modulename="gt911"
	fi

}

gt9271_load()
{
	if [ -r /lib/modules/$kernel_ver/extra/kgt9xx.ko ]; then
		 insmod  /lib/modules/$kernel_ver/extra/kgt9xx.ko Modulename="gt9271"
	fi
}

touch_load()
{
	case "$1" in
	"GT911_600_1024_7inch")
		echo "gt911_load: loading gt911 modules for 600*1024";
		gt911_load;
		;;
	"GT9271_800_1280_10inch")
		echo "gt9271_load: loading gt9271 modules for 800*1280";
		gt9271_load;
		;;
	"NO_TP")
		echo "do not need to load touch modules";
		;;
	*)
		echo "do not need to load touch modules";
		;;
	esac
}

security_module_load()
{
	case "$1" in
	"qptsv2r2b10" | "qptsv2r2b09" | "dipcv1r2b51" | "qptsv2r3b01" | "qptsv2r3b02" | "qptsv2r3b03")
		echo " loading security_module";
		/program/bin/isp_nuv -F /program/bin/NU76_SECURITY_MODULE.bin -U /dev/ttyAMA1 -B 9600 -n security_module;
		;;
	*)
		echo "do not need to load security modules";
		;;
	esac
}

temp_measure_log_recode()
{
	FOREHEAD_LOG=/config/TempModuleUpdate_forehead.log
	WRIST_LOG=/config/TempModuleUpdate_wrist.log
	result_forehead=0
	result_no_need_update=0
	result_wrist=0
	
	#判断日志文件是否存在，不存在创建
	if [ -e $FOREHEAD_LOG ]; then
		cat $FOREHEAD_LOG | grep "Update SUCCESS"
		result_forehead=$?
		echo "result_forehead: $result_forehead"
		cat $FOREHEAD_LOG | grep "no need to update mcu"
		result_no_need_update=$?
		echo "result_no_need_update: $result_no_need_update"
		if [ $result_forehead -eq 0 ] || [ $result_no_need_update -eq 0 ]; then
			#上一次升级是成功的或不需要升级，日志内容需要替换
			/program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_forehead > $FOREHEAD_LOG
		else
			#上一次升级是失败的，日志内容保留，不要覆盖
			echo "last update fail"
			#echo /program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_forehead
		fi
	else
		touch $FOREHEAD_LOG
		#日志文件不存在，日志需要覆盖
		/program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_forehead > $FOREHEAD_LOG
	fi
	
	if [ -e $WRIST_LOG ]; then
		cat $WRIST_LOG | grep "Update SUCCESS"
		result_wrist=$?
		echo "result_wrist: $result_wrist"
		cat $WRIST_LOG | grep "no need to update mcu"
		result_no_need_update=$?
		echo "result_no_need_update: $result_no_need_update"
		if [ $result_wrist -eq 0 ] || [ $result_no_need_update -eq 0 ]; then
			#上一次升级是成功的或不需要升级，日志内容需要替换
			/program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_wrist > $WRIST_LOG
		else
			#上一次升级是失败的，日志内容保留，不要覆盖
			echo "last update fail"
			#echo /program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_wrist
		fi
	else
		touch $WRIST_LOG
		#日志文件不存在，日志需要覆盖
		/program/bin/isp_nuv -F /program/bin/temp_measure_mod_app.bin -U /dev/ttyAMA1 -B 115200 -n temp_measure_wrist > $WRIST_LOG
	fi
}

temp_measure_load()
{
	case "$1" in
	"qptsv2r2b10" | "qptsv2r2b09" | "dipcv1r2b51" | "qptsv2r3b01" | "qptsv2r3b02" | "qptsv2r3b03")
		echo " loading temp_measure";
		temp_measure_log_recode;
		;;
	*)
		echo "do not need to load security modules";
		;;
	esac
}

mcu_load()                                                                        
{
	MCU_MOT=`/program/bin/manuinfotool | grep BUILD_INFO | grep MOT | awk -F "MOT-" '{print $2}' | cut -c 1-8`
	MCU_POW=`/program/bin/manuinfotool get POW`
	MCU_ENC=`/program/bin/manuinfotool get ENC`
	
	if [ "$MCU_ENC" = "0302C22D" ]; then
		ln -sf /dev/ttyAMA1 /dev/ttyMcuNuv
		#ln -sf /dev/ttyAMA3 /dev/ttyMcuGd
		#/program/bin/isp_ca -b 115200 -d /dev/ttyAMA3 -C /program/bin/telegboard_app.bin -n uart_expand
		#/program/bin/isp_nuv -c /program/bin/ctrlboard_app.bin
	fi
	if [ "$MCU_ENC" = "0302C28M" ] || [ "$MCU_ENC" = "0302C2GK" ]; then
		/program/bin/isp_nuv -F /program/bin/card_reader_app.bin -U /dev/ttyAMA4 -B 19200 -n card_reader
	fi
	
	# other mcu, reverse
	return 0
}

# 检测函数入参是否为纯数字，只支持十进制
is_digital()
{
	echo "$1" | [ -n "`sed -n '/^[0-9][0-9]*$/p'`" ] && echo "yes" || echo "no"
}

motor_load_hcm()
{
	#机芯电机模块：非法值是8个f
	PATH_MOTOR_KO=/lib/modules/$kernel_ver/extra/kmotorcm.ko
	MOTOR_INVALID_VAL=0xffffffff
	
    #读取电机掉电记忆位置
    if [ -r /config/motorpos ];then
        zoompos=`cat /config/motorpos | grep ZOOM | awk -F ':' '{print $2}'`
        focuspos=`cat /config/motorpos | grep FOCUS | awk -F ':' '{print $4}'`
        status=`cat /config/motorpos | grep STATUS | awk -F ':' '{print $6}'`
	fi

    #以下3种情况删除motorpos文件，驱动复位电机，AF触发聚焦：
	#1. 位置和状态参数不是纯数字(为空or非法值)
	#2. 当前处于工厂模式。
	#3. 电机未处于静止状态时系统被复位(or 断电)。
	if [ "$(is_digital $zoompos)" = "no" -o "$(is_digital $focuspos)" = "no" -o "$(is_digital $status)" = "no" -o \
		 -r /calibration/factory.txt -o \
		 "$status" != "0" ]; then
        
		#删除motorpos文件，复位电机(坐标系)
		echo "motor_load_hcm: reset motor position axes, zoompos=[$zoompos] focuspos=[$focuspos] status=[$status]"
		rm -rf /config/motorpos
        zoompos=${MOTOR_INVALID_VAL}
        focuspos=${MOTOR_INVALID_VAL}
        status=${MOTOR_INVALID_VAL}
	fi

    # 加载电机模块
	if [ -r $PATH_MOTOR_KO ]; then
		insmod $PATH_MOTOR_KO guiZoomPos=$zoompos guiFocusPos=$focuspos g_uiStatus=$status
	else
		echo "motor_load_hcm: loading $PATH_MOTOR_KO failed,  file not found"
	fi
}

motor_load_abf()
{
	#abf电机模块：非法值是7个f
	PATH_MOTOR_KO=/lib/modules/$kernel_ver/extra/kmotor.ko
	MOTOR_INVALID_VAL=0xfffffff
	
	#读取电机掉电记忆位置
	if [ -r /config/motorpos ];then
		abfpos=`cat /config/motorpos | grep ABF | awk -F ':' '{print $2}'`
		abfstate=`cat /config/motorpos | grep SATATE | awk -F ':' '{print $2}'`
	fi

    #以下3种情况删除motorpos文件，驱动复位电机，AF触发聚焦：
	#1. 位置和状态参数不是纯数字(为空or非法值)
	#2. 当前处于工厂模式。
	#3. 电机未处于静止状态时系统被复位(or 断电)。
	if [ "$(is_digital $abfpos)" = "no" -o "$(is_digital $abfstate)" = "no" -o \
		 -r /calibration/factory.txt -o \
		 "$abfstate" != "0" ]; then
        
		#删除motorpos文件，复位电机(坐标系)
		echo "motor_load_abf: reset motor position axes, abfpos=[$abfpos] abfstate=[$abfstate]"
		rm -rf /config/motorpos
        abfpos=${MOTOR_INVALID_VAL}
        abfstate=${MOTOR_INVALID_VAL}
	fi

    # 加载电机模块
	if [ -r $PATH_MOTOR_KO ]; then
		insmod $PATH_MOTOR_KO glAbfPos=$abfpos gulABFSavedState=$abfstate
	else
		echo "motor_load_abf: loading $PATH_MOTOR_KO failed,  file not found"
	fi
}

motor_load_fixdome()
{
	PATH_MOTOR_KO=/lib/modules/$kernel_ver/extra/kmotor.ko
	if [ -r $PATH_MOTOR_KO ]; then
		insmod $PATH_MOTOR_KO
	else
		echo "motor_load_fixdome: loading $PATH_MOTOR_KO failed,  file not found"
	fi
}
insert_wiegand_ko()
{
	case "$1" in
	"qptsv2r2b10" | "qptsv2r2b09" | "dipcv1r2b51" | "dipcv1r2b51_1" | "dfdmv1r1b03" | "qptsv2r3b01" | "qptsv2r3b02" | "qptsv2r3b03")
		if [ -r /lib/modules/$kernel_ver/extra/kwiegand.ko ]; then
			insmod /lib/modules/$kernel_ver/extra/kwiegand.ko
			#韦根接口的中断在cpu0上会丢失，强行绑定到cpu1上，dv300使用gpio3对应中断号39，cv500使用gpio5中断号41
			echo 2 > /proc/irq/41/smp_affinity
			echo 2 > /proc/irq/39/smp_affinity
			echo "wiegand_load: loading wiegand modules ok";
		else
			echo "wiegand_load: loading wiegand modules failed"
		fi	
		;;
	*)
		echo "wiegand_load: no need wiegand";
		;;
	esac
}

motor_load()
{
	case "$1" in
	"qipcv6r3b01" | "qipcv5r6b01")
		#机芯模式：spi控制电机驱动芯片(如41908/41929)，支持af
		echo "motor_load: loading motor modules in hcm mode";
		motor_load_hcm;
		;;
	"qipcv1r2b31" | "qipcv1r2b32")
		#枪机模式：gpio控制电机驱动芯片(如MS311D)，支持abf
		echo "motor_load: loading motor modules in abf mode";
		motor_load_abf;
		;;
	*)
		#定焦模式：gpio控制电机驱动芯片(如MS311D)，一般仅用于驱动IRCUT和不支持变倍跟随的镜头
		echo "motor_load: loading motor modules in fixdome mode";
		motor_load_fixdome;
		;;
	esac
}

cp /program/bin/manuinfotool /usr/bin/updateflag -rf
chmod +x /usr/bin/updateflag

#updateflag check
UPDATE_FLAG=`/usr/bin/updateflag get | grep updateflag |cut -d : -f 2`
if [ "$UPDATE_FLAG" = "set" ]; then
	/usr/bin/updateflag clear
	TIME=0
	if [ -e /config/powerofftime ]
	then
		TIME=$(cat /config/powerofftime | awk '{if(NR==1)print $0;}')
	fi

	touch /config/powerofftime
	echo $((TIME+1)) > /config/powerofftime
	date >> /config/powerofftime	
fi

#无电子标签启动中止，自动启动dhcp等待写入电子标签
#check manuinfo
DEVICENAME=`/program/bin/manuinfotool | grep PROTOTYPE_NAME|cut -d : -f 2`
if [ -z "$DEVICENAME" ]; then
      #restart udhcpc & exit
	  echo "-----------------------------------------------------------"
	  echo "----------------begin to start udhcpc----------------------"
	  echo "-----------------------------------------------------------"
	  #无电子标签时 拷贝update 程序至/tmp/bin 支持版本升级
	  cd /
      mkdir -p /tmp/bin   
      cp -rf /program/bin/update_move /tmp/bin/update
      chmod a+x /tmp/bin/update
      cp -rf /program/bin/reboot.sh  /tmp/bin/reboot.sh
      chmod a+x /tmp/bin/reboot.sh

      cp /program/bin/mwarecmd.sh /tmp/bin/mwarecmd.sh -f
      chmod a+x /tmp/bin/mwarecmd.sh     	
 
      killall -9 udhcpc
      #HWD65766：将udhcpc.script重命名为default.script
      udhcpc -s /usr/share/udhcpc/default.script > /dev/null &
      exit 1
fi

#单板类型需要用电子标签获得
BUILD_INFO=`/program/bin/manuinfotool | grep BUILD_INFO|cut -d : -f 2`
PROTOTYPE_NAME=`/program/bin/manuinfotool | grep PROTOTYPE_NAME|cut -d : -f 2`
OS_MEMORY_MB=`cat /proc/cmdline | awk '{for (f=1; f <= NF; f+=1) {if ($f ~ /mem=/) {print $NR}}}' | tr -cd "[0-9]"`

if [ -r /lib/modules/$kernel_ver/extra/kmanuparse.ko ]; then
	insmod /lib/modules/$kernel_ver/extra/kmanuparse.ko  pszBuildInfo=$BUILD_INFO pszProductTypeName=$PROTOTYPE_NAME pszPTInfo=$PT_NAME guiOsMemMb=$OS_MEMORY_MB
		case "$?" in
		0)
		UV_BOARD_NAME=$(cat /proc/driver/productname)
		UV_SENSOR_TYPE=$(cat /proc/driver/sensortype)
		UV_LCD_TYPE=$(cat /proc/driver/lcdname)
		UV_TP_TYPE=$(cat /proc/driver/TPname)
		;;
		*)
		echo "odporbe kamnuparse failed!"
		;;
	esac
fi	

if [ -r /lib/modules/$kernel_ver/extra/kgpio.ko ]; then
	insmod /lib/modules/$kernel_ver/extra/kgpio.ko
fi	

DDR_FREQ=$(cat /proc/driver/ddrhz)
CONFIG_DDRHZ=$(cat /config/config_ddrhz)

if [ -r /config/config_ddrhz ]; then
	if [ "$CONFIG_DDRHZ" != "533" -a  "$CONFIG_DDRHZ" != "640" ] || [ $CONFIG_DDRHZ = $DDR_FREQ ]; then
		echo "config_ddrhz=$CONFIG_DDRHZ needn't change ddr"
	else
		updateuboot "$CONFIG_DDRHZ""M"
		echo "update ddr frequency from $DDR_FREQ to $CONFIG_DDRHZ then reboot"
		reboot -f
	fi
else	
	if [ "$DDR_FREQ" = 533 ]; then		
		updateuboot 640M
		echo "update ddr frequency from 533M to 640M then reboot"
		reboot -f
	else
		echo "DDR is 640M"
	fi
	
fi

tdNum=`cat /proc/mtd | grep $PartitionName | awk '{print $1}' | sed -e s/mtd// | sed -e s/\://`
load_mem_total=`cat /proc/driver/memsize |grep total| cut -d : -f 2`
load_mem_os=`cat /proc/driver/memsize |grep os| cut -d : -f 2`
load_mem_logo=`cat /proc/cmdline | awk '{for (f=1; f <= NF; f+=1) {if ($f ~ /logosize=/) {print $f}}}' | tr -cd "[0-9]"`

if [ -z "$load_mem_logo" ]; then		
		load_mem_logo=2
fi


case "${UV_LCD_TYPE}" in
"HOLITECH_600_1024_7inch")
	echo "hifb vram0_size: 2400K";      #ARGB1555:600*1024*2*2/1024   
	load_fb_size=2400;
	;;
"HOLITECH_800_1280_10inch")
	echo "hifb vram0_size: 4000K";		#ARGB1555:800*1280*2*2/1024   
	load_fb_size=4000;
	;;
"QIUTIANWEI_800_1280_10inch")
	echo "hifb vram0_size: 4000K";		#ARGB1555:800*1280*2*2/1024   
	load_fb_size=4000;
	;;
"STRONG_800_1280_7inch")
	echo "hifb vram0_size: 4000K";		#ARGB1555:800*1280*2*2/1024   
	load_fb_size=4000;
	;;
"STRONG_800_1280_10inch")
	echo "hifb vram0_size: 4000K";		#ARGB1555:800*1280*2*2/1024   
	load_fb_size=4000;
	;;
"YIQING_600_1024_7inch")
	echo "hifb vram0_size: 2400K";      #ARGB1555:600*1024*2*2/1024   
	load_fb_size=2400;
	;;
"QIUTIANWEI_600_1024_7inch")
	echo "hifb vram0_size: 2400K";      #ARGB1555:600*1024*2*2/1024   
	load_fb_size=2400;
	;;
"QIUTIANWEI_QC_600_1024_7inch")
	echo "hifb vram0_size: 2400K";      #ARGB1555:600*1024*2*2/1024   
	load_fb_size=2400;
	;;
"RUIFUHUA_600_1024_7inch")
	echo "hifb vram0_size: 2400K";      #ARGB1555:600*1024*2*2/1024   
	load_fb_size=2400;
	;;	
*)
	echo "hifb vram0_size: 2048K";		# default 2M
	load_fb_size=2024;
	;;
esac

UV_SENSOR_TYPE0=$(echo "$UV_SENSOR_TYPE" | awk -F '-' '{print $1}')
UV_SENSOR_TYPE1=$(echo "$UV_SENSOR_TYPE" | awk -F '-' '{print $2}')
if [ "$UV_SENSOR_TYPE1" = "" ]; then
	UV_SENSOR_TYPE1=NULL;
fi

#load3516dv300
if [ -x /lib/modules/$kernel_ver/extra/load3516dv300 ]; then
    #在线模式和离线模式选择
	if [ -e "/config/online" ]; then
	    echo "online mode!"
		cd /lib/modules/$kernel_ver/extra;chmod +x ./load3516dv300;./load3516dv300 -i -sensor0 $UV_SENSOR_TYPE0 -sensor1 $UV_SENSOR_TYPE1 -osmem $load_mem_os -total $load_mem_total -logosize $load_mem_logo -hifbsize $load_fb_size;cd -
	else
        echo "offline mode!"
		#封装层调试：暂时直接写死。已知问题：1.total入参按总内存即2048传入时，ko加载crash，原因未知(SDK版本C001)；2./proc/driver/memsize不显示内存信息
		cd /lib/modules/$kernel_ver/extra;chmod +x ./load3516dv300;./load3516dv300 -offline -i -sensor0 $UV_SENSOR_TYPE0 -sensor1 $UV_SENSOR_TYPE1 -osmem $load_mem_os -total $load_mem_total -logosize $load_mem_logo -hifbsize $load_fb_size;cd -
	fi
else
    echo "load3516dv300 not exist"
	exit 1
fi

if [ "$UV_SENSOR_TYPE" = "sc2310" ]; then
	ln -sf /program/lib/libsns_sc2310.so /tmp/libsns.so;
fi
if [ "$UV_SENSOR_TYPE" = "sc4210" ]; then
	ln -sf /program/lib/libsns_sc4210.so /tmp/libsns.so;
fi
if [ "$UV_SENSOR_TYPE" = "sc2232" ]; then
	ln -sf /program/lib/libsns_sc2232.so /tmp/libsns.so;
fi
if [ "$UV_SENSOR_TYPE" = "sc2310-sc2232" ]; then
	ln -sf /program/lib/libsns_sc2310_sc2232.so /tmp/libsns.so;
	#ln -sf /program/lib/libsns_sc2310.so /tmp/libsns.so;
fi
if [ "$UV_SENSOR_TYPE" = "GZ_TEST" ]; then
	ln -sf /program/lib/libsns_sc2310.so /tmp/libsns.so;
fi

echo 3145728 > /proc/sys/net/core/wmem_default
echo 5242880 > /proc/sys/net/core/wmem_max
	
if [ ${load_mem_os} = "128" ]; then
#小内存产品调整分片内存使用大小
	echo 196608 > /proc/sys/net/ipv4/ipfrag_low_thresh
	echo 262144 > /proc/sys/net/ipv4/ipfrag_high_thresh
fi

touch_load ${UV_TP_TYPE};

#spi模块
#insmod /lib/modules/$kernel_ver/extra/extdrv/hi_ssp_sony.ko

#load MCU MOTOR
UV_PRODUCT_NAME=$(cat /proc/driver/productname)
motor_load ${UV_PRODUCT_NAME};
insert_wiegand_ko ${UV_PRODUCT_NAME};

#DMA uart模块
if [ -r /lib/modules/$kernel_ver/extra/hi_uart.ko ]; then
       insmod  /lib/modules/$kernel_ver/extra/hi_uart.ko
       ln -sf /dev/ttyHI0 /dev/ttyAMA1
       ln -sf /dev/ttyHI1 /dev/ttyAMA2
fi    

##机芯单卖产品，使用UART1控制电机变倍
if [ "$UV_PRODUCT_NAME" = "hcmv1r1b06" ]; then
    ln -sf /dev/ttyHI0 /dev/tty_RS232_1
fi

KERNEL_PRODUCT_TYPE=$(cat /proc/driver/producttype)

MOT=`/program/bin/manuinfotool get MOT` 

if [ "$KERNEL_PRODUCT_TYPE" = "NET_CAM" ]; then
    # 机芯(无MOT)和标球(MOT为0302C08T)使用串口2用作485，其他球机使用串口1做485; 
	# 使用manuinfotool get MOT，如果无MOT字段，会打印unknown
	if [ "$MOT" = "" -o "$MOT" = "0302C08T" -o "$MOT" = "unknown" ]; then
	    ln -sf /dev/ttyAMA2 /dev/ttyAMBA1
	else
	    ln -sf /dev/ttyAMA1 /dev/ttyAMBA1
	fi
	
else
    ln -sf /dev/ttyAMA1 /dev/ttyAMBA1
fi

# mcu load bin file
mcu_load;
security_module_load ${UV_BOARD_NAME};
temp_measure_load ${UV_BOARD_NAME};

#runtime模块
insmod /lib/modules/$kernel_ver/extra/kruntime.ko

#电子罗盘模块
if [ -r /lib/modules/$kernel_ver/extra/kecompass.ko ]; then
	# 大球I2C转串口单片机升级,需要放在云台升级之前, 否则第一次读取版本号I2C会报错
	if [ -r /program/bin/STM8S007C8_PWBD.bin ];then
		POW_BD=`/program/bin/manuinfotool get POW`
		if [ "$POW_BD" = "0302C0VW" ];then
			/program/bin/stm8_load -e 2 /program/bin/STM8S007C8_PWBD.bin
		fi
	fi
	insmod  /lib/modules/$kernel_ver/extra/kecompass.ko
fi

# 二代球电源板器件替换 STM8 ---> NU76E616 ，模拟PCA9555
#if [ "$UV_BOARD_NAME" = "qipcv2r1b23" -o "$UV_BOARD_NAME" = "dipcv1r1b26" ];then
	#if [ -r /program/bin/NU76E616_PWBD.bin ];then
		#/program/bin/stm8_load -j 2 /program/bin/NU76E616_PWBD.bin
	#fi
#fi

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/program/lib

if [ -r /lib/modules/$kernel_ver/extra/kmultisend.ko ]; then

	insmod /lib/modules/$kernel_ver/extra/kmultisend.ko
    case "$?" in
	0)
        echo "insmod kmultisend.ko ok!"
	;;
	*)
	    echo "insmod kmultisend.ko failed!"
	    exit 1
	;;
	esac
fi
insert_wifi_ko()
{
	#Added by g05675, 2019/1/9
	#IPCD66586：增加wifi依赖模块和8821wifi芯片驱动加载
	insmod /lib/modules/4.9.37/kernel/net/wireless/cfg80211.ko
	insmod /lib/modules/4.9.37/kernel/net/mac80211/mac80211.ko
	if [ "$1" = "f179" ]
	then
		insmod /program/lib/8188fu.ko rtw_80211d=1
		echo "insmod RTL8188FTV for wifi success"
	elif [ "$1" = "8179" ]
	then
		insmod /program/lib/8188eu.ko rtw_80211d=1
		echo "insmod RTL8188EUS for wifi success"
	elif [ "$1" = "c811" ]
	then
		insmod /program/lib/rtl8821cu.ko rtw_80211d=1
		echo "insmod RTL8821CU for wifi success"
	else
		echo "There is no WiFi module!!"
	fi
}

# 加载4G模块驱动
insert_4G_Module_ko()
{
	if [ "$1" = "0125" ]
	then
		insmod /program/lib/GobiNet_Y.ko
		echo "insmod GobiNet_Y for 4G success"
	elif [ "$1" = "c35a" ]
	then
		echo "No insmode module"
	else
		echo "There is no 4G Module!!"
	fi
}

set_wifi_mac()
{
    MACADDR_STRING=`/program/bin/mactool -wifi`
    #include dos chracter
    MAC_ADDR_COPPER_TEMP=${MACADDR_STRING#*is:}
    #delete dos chracter
    MAC_ADDR_COPPER=`echo $MAC_ADDR_COPPER_TEMP |awk '{print $1}'`
    if [ "MAC_ADDR_COPPER" != "invalid" ]; then
		ifconfig wlan0 hw ether $MAC_ADDR_COPPER
    else
        echo "wifi mac addr is invalid,so use random mac addr"
    fi
}

wpas_softlink()                                                                
{                                                                              
    mkdir -p /tmp/bin                                                          
    ln -sf /program/bin/wpa_supplicant /tmp/bin/mw_wpas_WiFi            
} 

#gpio 模块加载成功后，检测wifi 模组是否有接入到设备上，若有加载wifi模块

WIFI_ID=`lsusb |grep -E 'f179|8179|c811' | cut -d : -f 3`
if [ -n "$WIFI_ID" ]; then
    insert_wifi_ko $WIFI_ID
	sleep 3
	#只应答目标IP地址是来访接口IP地址的ARP请求 防止在wlan0和eth0在同网段情况下 wifi down掉后 仍然可通过eth0访问
	echo 1 > /proc/sys/net/ipv4/conf/all/arp_ignore
	#与厂家交流，芯片自带mac地址，无需再设置。如需保持原有策略，请将下句打开
	#set_wifi_mac     
	ifconfig wlan0 up  
	wpas_softlink
fi

#加载4G模块
FOURG_ID=`lsusb |grep -E '0125|c35a' |cut -d : -f 3`
if [ -n "$FOURG_ID" ]; then
	insert_4G_Module_ko $FOURG_ID
fi

#Run mware.sh
/program/bin/mware_init.sh  &

#只替换root用户密码部分，问题单PCD54901
if [ -e "/config/passwd" ]; then
    CONF_DIR="/config/passwd"                    
    ETC_DIR="/etc/passwd"                        
    conf_var=`cat ${CONF_DIR} | grep ^root:`
    etc_var=`cat ${ETC_DIR} | grep ^root:`
    conf_temp=`echo $conf_var  | cut -f2 -d':'`
    etc_temp=`echo $etc_var  | cut -f2 -d':'`
    if [ "$conf_temp" != "$etc_temp" ]; then 
        echo "passwd has changed"
        sed -i "s:$etc_temp:$conf_temp:g" ${ETC_DIR}
    fi
fi
