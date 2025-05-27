#!/bin/bash
service_status=$(systemctl is-active asx-trader)
if [ "$service_status" != "active" ]; then
    echo "ASX Trader service is not running! Status: $service_status"
    echo "Attempting to restart..."
    sudo systemctl restart asx-trader
    
    # Check if restart was successful
    sleep 5
    new_status=$(systemctl is-active asx-trader)
    if [ "$new_status" != "active" ]; then
        echo "Failed to restart ASX Trader service!"
    else
        echo "ASX Trader service restarted successfully."
    fi
fi
