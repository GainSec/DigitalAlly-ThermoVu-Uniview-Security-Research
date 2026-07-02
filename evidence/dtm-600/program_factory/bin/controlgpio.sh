#!/bin/sh

if [ "$2" = "up" ]; then
echo -w $1 1 > /proc/driver/gpiodev_info
elif [ "$2" = "down" ]; then
echo -w $1 0 > /proc/driver/gpiodev_info
else
echo "eg:controlgpio 98 up/down"
fi

