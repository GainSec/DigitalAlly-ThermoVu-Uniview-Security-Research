#!/bin/sh

result="fail"

echo "@"

while [ 1 ]
do 
    if [ -r /tmp/stateofmware ]; then
        mw_state=`cat /tmp/stateofmware |grep state|awk -F '[][]' '{print $2}'`
        if [ $mw_state = 1 ]; then
        echo "mware ready"
        else
            echo "mware not ready"
            break
        fi
    else
        echo "mware not ready"
        break
	fi
    
	if [ -x /program/bin/check_isp_int.sh ];then
        isp_state=`sh /program/bin/check_isp_int.sh |grep status|awk -F '[][]' '{print $2}'`
        if [ $isp_state = 1 ]; then
            echo "isp interrupts ready"
        else
            echo "isp interrupts not ready"
            break
        fi
    else
        echo "check isp interrupt fail"
		break
	fi
    
    result="pass"
    break
done

echo ""
echo "test result:"$result
echo "\$\$"