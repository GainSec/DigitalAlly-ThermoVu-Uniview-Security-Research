#!/bin/sh

isp_int_info=`cat /proc/interrupts|grep -iE 'ISP|VI_CAP'`

cpu_num=`cat /proc/interrupts | awk '(NR == 1){print NF}'` 
echo -e $cpu_num"\n${isp_int_info}" | awk '                     
BEGIN {ok=0}
{
    if (1 == NR)
    {
        num=$1
    }
    else
    {
        #print "num:"num
        for(i=0;i<num;i++)
        {
            n=i+2;
            #print "i:"i
            if ($n>0)
            {
                print "sensor["i"] int ok"
			    # 目前只有一个sensor，所以只要有一个sensor有中断就认为ok，多目设备这里需要修改
				ok=1
            }
        }
    }
}
END {print "isp int status: ["ok"]"}
'
