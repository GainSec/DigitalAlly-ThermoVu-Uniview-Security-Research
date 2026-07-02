#!/bin/sh

if [ $1 ]; then
ftpget $1 IPC0DMA01002.vme
ftpget $1 cpldload
chmod 777 cpldload
./cpldload IPC0DMA01002.vme
else
echo "eg:updatecpld x.x.x.x"
fi
