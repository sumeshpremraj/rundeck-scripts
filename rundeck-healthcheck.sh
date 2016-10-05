#!/bin/bash
##################
# Rundeck healthcheck + takeover script
#
# This runs a health check, and then takes over all jobs
# when the other server goes down.
# Note: Use this only with Rundeck in cluster mode!
#
##################
# Edit the following section:

# See http://rundeck.org/2.6.9/api/index.html#token-authentication for token authentication
API_TOKEN="somesecretstring"

# Detect and set hostnames based on own hostname
### This script assumes you have two servers.
### You can set the two hostnames/IPs below, and run the same script on both servers
### without any changes, and the script will detect and set the correct IPs

if [ `hostname -I` == "IP_of_First_Server" ]
then
    OWN_IP="IP_of_First_Server"
    REMOTE_IP="IP_of_Second_Server"
else
    REMOTE_IP="IP_of_First_Server"
    OWN_IP="IP_of_Second_Server"
fi

##################
# Editable section ends
##################

# Set up logging
LOG="/var/log/rundeck-healthcheck"
exec > >(tee -a "$LOG") 2>&1

# Check if other server responds
curl -H "X-Rundeck-Auth-Token: $API_TOKEN" "http://$REMOTE_IP:4440/api/1/system/info"| grep "result success='true'"

# If other server is up
if [ $? -eq 0 ];then
    echo "`date`: Rundeck running"

# If other server is down
else

    # Get a list of running jobs (that might be stuck)
    for execution in $(curl -s -H "Content-Type: application/json" -H "X-Rundeck-Auth-Token: $API_TOKEN" "http://$OWN_IP:4440/api/17/project/Production/executions/running" |grep execution|grep id|grep running|cut -f2 -d'='|sed "s/\'\(.*\)\' href/\1/g" | sed "s/'//g"| cut -f1 -d' ' )
    do
        # Abort currently running jobs
        curl -s -H "Content-Type: application/xml" -H "X-Rundeck-Auth-Token: $API_TOKEN" "http://$OWN_IP:4440/api/17/execution/$execution/abort" | grep 'execution id'| grep "status='aborted'"

        if [ $? -eq 0 ]
        then
            echo "`date`: Execution $execution aborted"
        else
            echo "`date`: Failed to abort execution $execution"
        fi
    done

    # Jobs aborted, call takeover API
    echo "`date`: Rundeck down, calling takeover API"
    curl -s -H "Content-Type: application/xml" -H "X-Rundeck-Auth-Token: $API_TOKEN" -X PUT "http://$OWN_IP:4440/api/14/scheduler/takeover" -d "<takeoverSchedule><server all=\"true\"/></takeoverSchedule>" >/dev/null 2>&1

    if [ $? -eq 0 ]; then echo "`date`: Takeover successfull"; fi
fi
