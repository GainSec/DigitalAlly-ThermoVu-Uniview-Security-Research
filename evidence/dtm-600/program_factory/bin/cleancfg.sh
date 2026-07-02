#! /bin/sh
echo "@"
killall -9 mwareserver
killall -9 daemon
rm -rf /config/*
rm -rf /cfgbak/* 
echo "test result:pass"
echo '$$'