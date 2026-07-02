#kill mware relevant process
killall -9 daemon 1>/dev/null 2>&1
#send 20 to exit hisi mpp
killall -20 mwareserver 1>/dev/null 2>&1
sleep 1
killall -9 mwareserver 1>/dev/null 2>&1
killall -9 maintain 1>/dev/null 2>&1
killall -9 iwareserver 1>/dev/null 2>&1
killall -9 udhcpc_mware 1>/dev/null 2>&1
killall -9 mw_* 1>/dev/null 2>&1
 
