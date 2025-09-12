#!/bin/bash

# Nginx health check and auto-recovery script
# This script monitors the strategy service connection and automatically fixes 502 errors

LOG_FILE="/var/log/nginx/healthcheck.log"
STRATEGY_SERVICE_URL="http://strategy-service:8002/health"
EXTERNAL_TEST_URL="http://localhost/strategies"

echo "$(date): Starting nginx health check monitor..." >> $LOG_FILE

while true do
    # Wait 30 seconds between checks
    sleep 30
    
    # Test if strategy service is directly accessible
    if curl -s --connect-timeout 5 "$STRATEGY_SERVICE_URL" > /dev/null 2>&1; then
        echo "$(date): Strategy service is healthy" >> $LOG_FILE
        
        # Test if nginx proxy is working
        if ! curl -s --connect-timeout 5 "$EXTERNAL_TEST_URL" > /dev/null 2>&1; then
            echo "$(date): Nginx proxy failing, reloading nginx..." >> $LOG_FILE
            nginx -s reload
            sleep 5
        fi
    else
        echo "$(date): Strategy service is down, waiting..." >> $LOG_FILE
    fi
done
