#!/bin/bash

COMMAND="python twitter2015.py keywords"
SERVICE_NAME="BUT Twitter Crawler"
LOGS_FOLDER=logs
LOG_FILE=$LOGS_FOLDER/but_tw_crawler.log
PID_FOLDER=pids
PID_FILE=$PID_FOLDER/but_tw_crawler.pid
CURRENT_SERV_PID=0
if [ -e "$PID_FILE" ];
   then 
     CURRENT_SERV_PID=`cat $PID_FILE`
     if ! (ps -ef | grep $CURRENT_SERV_PID | grep -v grep 1>/dev/null);
       then CURRENT_SERV_PID=0;
     fi
fi


case $1 in
     start)
       if [ $CURRENT_SERV_PID -eq 0 ];
         then
              echo "Arrancando $SERVICE_NAME"
              echo "$COMMAND > $LOG_FILE 2>&1 &"
              eval "$COMMAND > $LOG_FILE 2>&1 &"
              echo  $! > $PID_FILE;
         else
              echo "Service $SERVICE_NAME already running with pid: $CURRENT_SERV_PID ";
       fi
     ;;
     stop)
       if [ $CURRENT_SERV_PID -eq 0 ];
         then
              echo "Servicio $SERVICE_NAME not running";
         else
              echo 'Stopping $SERVICE_NAME'
              kill -9  $CURRENT_SERV_PID;
              rm $PID_FILE
       fi
     ;;
     *)
       echo "usage: start {start|stop}" ;;
esac

