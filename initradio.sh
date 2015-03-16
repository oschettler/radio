### BEGIN INIT INFO
# Provides: Radio / LCD date / time / ip address
# Required-Start: $remote_fs $syslog
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Controll MPD
# Description: Radio / LCD date / time / ip address
### END INIT INFO


#! /bin/sh
# /etc/init.d/radio


export HOME
case "$1" in
    start)
        echo "Starting Radio"
        /home/pi/radio/radio.py  2>&1 &
    ;;
    stop)
        echo "Stopping Radio"
	RADIO_PID=`ps auxwww | grep radio.py | head -1 | awk '{print $2}'`
	kill -9 $RADIO_PID
    ;;
    *)
        echo "Usage: /etc/init.d/radio {start|stop}"
        exit 1
    ;;
esac
exit 0

