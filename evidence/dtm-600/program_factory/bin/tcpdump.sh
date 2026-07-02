#! /bin/sh
#---------- check input param ------
if [ $# != 2 ] ; then 
	echo "Usage: tcpdump.sh [FILE NAME] [TFTP SERVER]"
	exit 1; 
else
	#---------- download tcpdump file ------
	tftp -pl $1 $2 -b 8192
	rm -f $1
fi 
