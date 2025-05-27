#!/bin/bash

function show_help {
    echo "ASX Trader Service Manager"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start the service"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  status      Check service status"
    echo "  logs        View service logs"
    echo "  tail        Tail service logs in real-time"
    echo "  update      Update from git and restart service"
    echo "  backup      Backup the database"
}

case "$1" in
    start)
        sudo systemctl start asx-trader
        echo "ASX Trader service started"
        ;;
    stop)
        sudo systemctl stop asx-trader
        echo "ASX Trader service stopped"
        ;;
    restart)
        sudo systemctl restart asx-trader
        echo "ASX Trader service restarted"
        ;;
    status)
        sudo systemctl status asx-trader
        ;;
    logs)
        if [ -z "$2" ]; then
            lines=100
        else
            lines=$2
        fi
        sudo journalctl -u asx-trader -n $lines
        ;;
    tail)
        sudo journalctl -u asx-trader -f
        ;;
    update)
        echo "Updating ASX Trader from git repository..."
        cd ~/apps/ASX-Auto-Trader
        sudo systemctl stop asx-trader
        git pull
        source venv/bin/activate
        pip install -r requirements.txt
        sudo systemctl start asx-trader
        echo "ASX Trader updated and restarted"
        ;;
    backup)
        echo "Backing up ASX Trader database..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp ~/apps/ASX-Auto-Trader/data/asx_trader.db ~/apps/ASX-Auto-Trader/data/asx_trader_backup_$timestamp.db
        echo "Database backed up to ~/apps/ASX-Auto-Trader/data/asx_trader_backup_$timestamp.db"
        ;;
    *)
        show_help
        exit 1
        ;;
esac
exit 0
