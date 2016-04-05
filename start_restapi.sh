#!/bin/bash
WD=$PWD
COMMAND="python restapi.py"
SIMPLE_SERVER_PORT=8001
SIMPLE_SERVER_COMMAND="python -m SimpleHTTPServer $SIMPLE_SERVER_PORT"
SERVICE_NAME=restapi
LOGS_FOLDER=$WD/logs
LOG_FILE=$LOGS_FOLDER/restapi.log
SIMPLE_SERVER_LOG_FILE=$LOGS_FOLDER/simple_server.log
PID_FOLDER=$WD/pids
PID_FILE=$PID_FOLDER/restapi.pid
SIMPLE_SERVER_PID_FILE=$PID_FOLDER/simple_server.pid
DATA_FOLDER=$WD/data

CURRENT_SERV_PID=0
if [ -e "$PID_FILE" ];
   then 
     CURRENT_SERV_PID=`cat $PID_FILE`
     if ! (ps -ef | grep $CURRENT_SERV_PID | grep -v grep 1>/dev/null);
       then CURRENT_SERV_PID=0;
     fi
fi

CURRENT_SIMPLE_SERV_PID=0
if [ -e "$SIMPLE_SERVER_PID_FILE" ];
   then 
     CURRENT_SIMPLE_SERV_PID=`cat $SIMPLE_SERVER_PID_FILE`
     if ! (ps -ef | grep $CURRENT_SIMPLE_SERV_PID | grep -v grep 1>/dev/null);
       then CURRENT_SIMPLE_SERV_PID=0;
     fi
fi


case $1 in
     start)
       if [ $CURRENT_SERV_PID -eq 0 ];
         then
              echo "Starting $SERVICE_NAME"
              echo "$COMMAND > $LOG_FILE 2>&1 &"
              eval "$COMMAND > $LOG_FILE 2>&1 &"
              echo  $! > $PID_FILE;
         else
              echo "Service $SERVICE_NAME already running with pid: $CURRENT_SERV_PID ";
       fi
       if [ $CURRENT_SIMPLE_SERV_PID -eq 0 ];
         then
              echo "Starting SIMPLE_SERVER"
              cd $DATA_FOLDER
              echo "$SIMPLE_SERVER_COMMAND > $SIMPLE_SERVER_LOG_FILE 2>&1 &"
              eval "$SIMPLE_SERVER_COMMAND > $SIMPLE_SERVER_LOG_FILE 2>&1 &"
              echo  $! > $SIMPLE_SERVER_PID_FILE;
         else
              echo "SIMPLE_SERVER already running with pid: $CURRENT_SIMPLE_SERV_PID ";
       fi
     ;;
     stop)
       if [ $CURRENT_SERV_PID -eq 0 ];
         then
              echo "Service $SERVICE_NAME not running";
         else
              echo "Stopping $SERVICE_NAME"
              kill -9  $CURRENT_SERV_PID;
              rm $PID_FILE
       fi
       if [ $CURRENT_SIMPLE_SERV_PID -eq 0 ];
         then
              echo "SIMPLE SERVER not running";
         else
              echo 'Stopping SIMPLE SERVER'
              kill -9  $CURRENT_SIMPLE_SERV_PID;
              rm $SIMPLE_SERVER_PID_FILE
       fi
     ;;
     *)
       echo "usage: start {start|stop}" ;;
esac

