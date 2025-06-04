"""
Enhanced market monitoring system with real-time alerts and position tracking.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
import time
from asx_trader.config import Config
from asx_trader.monitoring import MonitoringSystem
from asx_trader.market import MarketScanner
from asx_trader.position_manager import PositionManager

logger = logging.getLogger(__name__)

@dataclass
class MarketAlert:
    """Represents a market alert"""
    symbol: str
    alert_type: str  # 'PRICE_MOVE', 'VOLUME_SPIKE', 'NEWS', 'TECHNICAL'
    message: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    timestamp: datetime
    current_price: Optional[float] = None
    trigger_value: Optional[float] = None
    
class EnhancedMarketMonitor:
    """Enhanced market monitoring with real-time alerts and position tracking"""
    
    def __init__(self, position_manager: PositionManager = None, database=None):
        self.monitoring_system = MonitoringSystem()
        self.market_scanner = MarketScanner()
        self.position_manager = position_manager
        self.database = database
        
        # Monitoring configuration
        self.monitoring_active = False
        self.monitoring_thread = None
        self.update_interval = 60  # seconds
        
        # Alert thresholds
        self.price_change_threshold = 0.05  # 5% price change
        self.volume_spike_threshold = 2.0   # 2x average volume
        self.position_loss_threshold = -0.10  # 10% loss threshold
        
        # Historical data for comparison
        self.previous_market_data = {}
        self.alerts_history = []
        
        # Watchlist - symbols to monitor closely
        self.watchlist = set()
        
    def start_monitoring(self, symbols: List[str] = None):
        """Start real-time market monitoring"""
        try:
            if self.monitoring_active:
                logger.warning("Monitoring is already active")
                return
            
            if symbols:
                self.watchlist.update(symbols)
            
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            logger.info(f"Started enhanced market monitoring for {len(self.watchlist)} symbols")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop market monitoring"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            
            logger.info("Stopped market monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    def add_to_watchlist(self, symbols: List[str]):
        """Add symbols to monitoring watchlist"""
        self.watchlist.update(symbols)
        logger.info(f"Added {len(symbols)} symbols to watchlist: {symbols}")
    
    def remove_from_watchlist(self, symbols: List[str]):
        """Remove symbols from monitoring watchlist"""
        for symbol in symbols:
            self.watchlist.discard(symbol)
        logger.info(f"Removed {len(symbols)} symbols from watchlist: {symbols}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Market monitoring loop started")
        
        while self.monitoring_active:
            try:
                # Get current market data
                symbols_to_monitor = list(self.watchlist)
                
                # Add position symbols to monitoring
                if self.position_manager:
                    position_symbols = [pos.symbol for pos in self.position_manager.positions.values()]
                    symbols_to_monitor.extend(position_symbols)
                
                # Remove duplicates
                symbols_to_monitor = list(set(symbols_to_monitor))
                
                if symbols_to_monitor:
                    current_market_data = self.market_scanner.get_market_data(symbols_to_monitor)
                    
                    # Analyze market data for alerts
                    alerts = self._analyze_market_data(current_market_data)
                    
                    # Process alerts
                    if alerts:
                        self._process_alerts(alerts)
                    
                    # Update positions if position manager is available
                    if self.position_manager and current_market_data:
                        self.position_manager.update_positions(current_market_data)
                        
                        # Check for position-specific alerts
                        position_alerts = self._check_position_alerts()
                        if position_alerts:
                            self._process_alerts(position_alerts)
                    
                    # Store current data for next comparison
                    self.previous_market_data = current_market_data
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.update_interval)
    
    def _analyze_market_data(self, current_data: Dict[str, dict]) -> List[MarketAlert]:
        """Analyze market data and generate alerts"""
        alerts = []
        
        try:
            for symbol, data in current_data.items():
                current_price = data.get('current_price', 0)
                volume = data.get('volume', 0)
                price_change_pct = data.get('price_change_pct', 0)
                
                # Check for significant price movements
                if abs(price_change_pct) >= self.price_change_threshold:
                    severity = self._get_price_move_severity(abs(price_change_pct))
                    direction = "up" if price_change_pct > 0 else "down"
                    
                    alert = MarketAlert(
                        symbol=symbol,
                        alert_type='PRICE_MOVE',
                        message=f"{symbol} moved {direction} {abs(price_change_pct)*100:.1f}% to ${current_price}",
                        severity=severity,
                        timestamp=datetime.now(),
                        current_price=current_price,
                        trigger_value=price_change_pct
                    )
                    alerts.append(alert)
                
                # Check for volume spikes
                avg_volume = data.get('avg_volume', volume / 2)  # Fallback if no avg volume
                if avg_volume > 0 and volume >= avg_volume * self.volume_spike_threshold:
                    volume_ratio = volume / avg_volume
                    
                    alert = MarketAlert(
                        symbol=symbol,
                        alert_type='VOLUME_SPIKE',
                        message=f"{symbol} volume spike: {volume:,} ({volume_ratio:.1f}x average)",
                        severity='MEDIUM' if volume_ratio < 3 else 'HIGH',
                        timestamp=datetime.now(),
                        current_price=current_price,
                        trigger_value=volume_ratio
                    )
                    alerts.append(alert)
                
                # Check for technical levels (52-week highs/lows)
                high_52w = data.get('52w_high', 0)
                low_52w = data.get('52w_low', 0)
                
                if high_52w > 0 and current_price >= high_52w * 0.98:  # Within 2% of 52w high
                    alert = MarketAlert(
                        symbol=symbol,
                        alert_type='TECHNICAL',
                        message=f"{symbol} near 52-week high: ${current_price} (high: ${high_52w})",
                        severity='MEDIUM',
                        timestamp=datetime.now(),
                        current_price=current_price,
                        trigger_value=high_52w
                    )
                    alerts.append(alert)
                
                if low_52w > 0 and current_price <= low_52w * 1.02:  # Within 2% of 52w low
                    alert = MarketAlert(
                        symbol=symbol,
                        alert_type='TECHNICAL',
                        message=f"{symbol} near 52-week low: ${current_price} (low: ${low_52w})",
                        severity='MEDIUM',
                        timestamp=datetime.now(),
                        current_price=current_price,
                        trigger_value=low_52w
                    )
                    alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
        
        return alerts
    
    def _check_position_alerts(self) -> List[MarketAlert]:
        """Check for position-specific alerts"""
        alerts = []
        
        try:
            if not self.position_manager:
                return alerts
            
            for position in self.position_manager.positions.values():
                if not position.current_price:
                    continue
                
                pnl_pct = position.get_pnl_percentage()
                
                # Alert for significant losses
                if pnl_pct <= self.position_loss_threshold * 100:
                    alert = MarketAlert(
                        symbol=position.symbol,
                        alert_type='POSITION_LOSS',
                        message=f"Position {position.symbol} down {abs(pnl_pct):.1f}% (${position.unrealized_pnl:.2f})",
                        severity='HIGH' if pnl_pct <= -15 else 'MEDIUM',
                        timestamp=datetime.now(),
                        current_price=position.current_price,
                        trigger_value=pnl_pct
                    )
                    alerts.append(alert)
                
                # Alert for significant gains
                elif pnl_pct >= 10:  # 10% gain
                    alert = MarketAlert(
                        symbol=position.symbol,
                        alert_type='POSITION_GAIN',
                        message=f"Position {position.symbol} up {pnl_pct:.1f}% (${position.unrealized_pnl:.2f})",
                        severity='MEDIUM',
                        timestamp=datetime.now(),
                        current_price=position.current_price,
                        trigger_value=pnl_pct
                    )
                    alerts.append(alert)
                
                # Alert if approaching stop loss or take profit
                if position.stop_loss:
                    distance_to_stop = abs(position.current_price - position.stop_loss) / position.current_price
                    if distance_to_stop <= 0.02:  # Within 2% of stop loss
                        alert = MarketAlert(
                            symbol=position.symbol,
                            alert_type='STOP_LOSS_NEAR',
                            message=f"Position {position.symbol} approaching stop loss: ${position.current_price} (stop: ${position.stop_loss})",
                            severity='HIGH',
                            timestamp=datetime.now(),
                            current_price=position.current_price,
                            trigger_value=position.stop_loss
                        )
                        alerts.append(alert)
                
                if position.take_profit:
                    distance_to_target = abs(position.current_price - position.take_profit) / position.current_price
                    if distance_to_target <= 0.02:  # Within 2% of take profit
                        alert = MarketAlert(
                            symbol=position.symbol,
                            alert_type='TAKE_PROFIT_NEAR',
                            message=f"Position {position.symbol} approaching take profit: ${position.current_price} (target: ${position.take_profit})",
                            severity='MEDIUM',
                            timestamp=datetime.now(),
                            current_price=position.current_price,
                            trigger_value=position.take_profit
                        )
                        alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking position alerts: {e}")
        
        return alerts
    
    def _process_alerts(self, alerts: List[MarketAlert]):
        """Process and send alerts"""
        try:
            for alert in alerts:
                # Add to history
                self.alerts_history.append(alert)
                
                # Log alert
                log_level = {
                    'LOW': logging.INFO,
                    'MEDIUM': logging.WARNING,
                    'HIGH': logging.ERROR,
                    'CRITICAL': logging.CRITICAL
                }.get(alert.severity, logging.INFO)
                
                logger.log(log_level, f"ALERT [{alert.severity}] {alert.alert_type}: {alert.message}")
                
                # Send notification for high severity alerts
                if alert.severity in ['HIGH', 'CRITICAL']:
                    self.monitoring_system.send_notification(
                        subject=f"Trading Alert - {alert.symbol}",
                        message=f"{alert.alert_type}: {alert.message}\nTime: {alert.timestamp}\nSeverity: {alert.severity}"
                    )
                
                # Save to database if available
                if self.database:
                    self._save_alert_to_db(alert)
            
            # Keep only recent alerts in memory (last 1000)
            if len(self.alerts_history) > 1000:
                self.alerts_history = self.alerts_history[-1000:]
        
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    def _get_price_move_severity(self, price_change_pct: float) -> str:
        """Determine severity based on price change percentage"""
        if price_change_pct >= 0.15:  # 15%+
            return 'CRITICAL'
        elif price_change_pct >= 0.10:  # 10%+
            return 'HIGH'
        elif price_change_pct >= 0.07:  # 7%+
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_recent_alerts(self, hours: int = 24) -> List[MarketAlert]:
        """Get recent alerts within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts_history if alert.timestamp >= cutoff_time]
    
    def get_alerts_by_symbol(self, symbol: str, hours: int = 24) -> List[MarketAlert]:
        """Get alerts for a specific symbol"""
        recent_alerts = self.get_recent_alerts(hours)
        return [alert for alert in recent_alerts if alert.symbol == symbol]
    
    def get_monitoring_summary(self) -> Dict:
        """Get summary of monitoring status and recent activity"""
        try:
            recent_alerts = self.get_recent_alerts(24)
            
            # Count alerts by severity
            alert_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
            for alert in recent_alerts:
                alert_counts[alert.severity] += 1
            
            # Get position summary if available
            position_summary = {}
            if self.position_manager:
                position_summary = self.position_manager.get_position_summary()
            
            return {
                'monitoring_active': self.monitoring_active,
                'watchlist_size': len(self.watchlist),
                'watchlist_symbols': list(self.watchlist),
                'update_interval': self.update_interval,
                'recent_alerts_24h': len(recent_alerts),
                'alert_counts': alert_counts,
                'position_summary': position_summary,
                'last_update': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting monitoring summary: {e}")
            return {'error': str(e)}
    
    def set_alert_thresholds(self, price_change: float = None, volume_spike: float = None, 
                           position_loss: float = None):
        """Update alert thresholds"""
        if price_change is not None:
            self.price_change_threshold = price_change
            logger.info(f"Updated price change threshold to {price_change*100}%")
        
        if volume_spike is not None:
            self.volume_spike_threshold = volume_spike
            logger.info(f"Updated volume spike threshold to {volume_spike}x")
        
        if position_loss is not None:
            self.position_loss_threshold = position_loss
            logger.info(f"Updated position loss threshold to {position_loss*100}%")
    
    def _save_alert_to_db(self, alert: MarketAlert):
        """Save alert to database"""
        try:
            if self.database:
                alert_data = asdict(alert)
                alert_data['timestamp'] = alert.timestamp.isoformat()
                self.database.save_alert(alert_data)
        except Exception as e:
            logger.error(f"Error saving alert to database: {e}")
    
    def generate_monitoring_report(self) -> str:
        """Generate a comprehensive monitoring report"""
        try:
            summary = self.get_monitoring_summary()
            recent_alerts = self.get_recent_alerts(24)
            
            report = []
            report.append("=== ENHANCED MARKET MONITORING REPORT ===")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # Monitoring status
            report.append("MONITORING STATUS:")
            report.append(f"  Active: {'Yes' if summary['monitoring_active'] else 'No'}")
            report.append(f"  Watchlist: {summary['watchlist_size']} symbols")
            report.append(f"  Update Interval: {summary['update_interval']} seconds")
            report.append("")
            
            # Alert summary
            report.append("ALERT SUMMARY (24 hours):")
            report.append(f"  Total Alerts: {summary['recent_alerts_24h']}")
            for severity, count in summary['alert_counts'].items():
                report.append(f"  {severity}: {count}")
            report.append("")
            
            # Position summary
            if summary.get('position_summary'):
                pos_sum = summary['position_summary']
                report.append("POSITION SUMMARY:")
                report.append(f"  Total Positions: {pos_sum.get('total_positions', 0)}")
                report.append(f"  Total Exposure: ${pos_sum.get('total_exposure', 0):,.2f}")
                report.append(f"  Unrealized P&L: ${pos_sum.get('unrealized_pnl', 0):,.2f}")
                report.append(f"  Realized P&L: ${pos_sum.get('realized_pnl', 0):,.2f}")
                report.append("")
            
            # Recent high-priority alerts
            high_priority_alerts = [a for a in recent_alerts if a.severity in ['HIGH', 'CRITICAL']]
            if high_priority_alerts:
                report.append("HIGH PRIORITY ALERTS:")
                for alert in high_priority_alerts[-10:]:  # Last 10
                    report.append(f"  [{alert.severity}] {alert.symbol}: {alert.message}")
                    report.append(f"    Time: {alert.timestamp.strftime('%H:%M:%S')}")
                report.append("")
            
            # Watchlist
            if summary['watchlist_symbols']:
                report.append("WATCHLIST:")
                report.append(f"  {', '.join(summary['watchlist_symbols'])}")
            
            return "\n".join(report)
        
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            return f"Error generating report: {str(e)}"
