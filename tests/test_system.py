"""
Tests for the main trading system.
"""
import unittest
from unittest.mock import patch, MagicMock
from asx_trader.system import TradingSystem

class TestTradingSystem(unittest.TestCase):
    """Test cases for the TradingSystem class."""
    
    @patch('asx_trader.system.Config')
    @patch('asx_trader.system.ASXNewsCollector')
    @patch('asx_trader.system.GPTEnhancedPredictionEngine')
    @patch('asx_trader.system.RiskManagement')
    @patch('asx_trader.system.BrokerAPI')
    @patch('asx_trader.system.MonitoringSystem')
    @patch('asx_trader.system.AWSDeployment')
    def test_execute_trading_cycle(self, mock_aws, mock_monitoring, mock_broker, 
                                 mock_risk, mock_prediction, mock_news, mock_config):
        """Test full trading cycle execution."""
        # Configure mocks
        mock_config.WATCH_SYMBOLS = ["BHP", "CBA"]
        mock_config.MAX_POSITION_SIZE = 10000
        mock_config.TRADING_ENABLED = False
        mock_config.validate.return_value = True
        
        # News collector mock
        mock_news_instance = MagicMock()
        mock_news.return_value = mock_news_instance
        mock_news_instance.fetch_latest_news.return_value = [
            {"id": "news1", "headline": "Test News", "symbols": ["BHP"]}
        ]
        
        # Prediction engine mock
        mock_prediction_instance = MagicMock()
        mock_prediction.return_value = mock_prediction_instance
        mock_prediction_instance.analyze_news.return_value = [
            {"news_id": "news1", "headline": "Test News", "symbols": ["BHP"], 
             "signal": "BUY", "confidence": "high"}
        ]
        
        # Risk management mock
        mock_risk_instance = MagicMock()
        mock_risk.return_value = mock_risk_instance
        mock_risk_instance.assess_market_risk.return_value = {
            "overall_risk_level": "Low",
            "symbol_risks": [{"symbol": "BHP", "risk_level": "Low"}],
            "market_data": {"BHP": {"current_price": 100}}
        }
        
        # Create system and run cycle
        system = TradingSystem()
        result = system.execute_trading_cycle()
        
        # Verify result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["signals"], 1)
        self.assertGreaterEqual(result["orders"], 0)
        
        # Verify component calls
        mock_news_instance.fetch_latest_news.assert_called_once()
        mock_prediction_instance.analyze_news.assert_called_once()
        mock_risk_instance.assess_market_risk.assert_called_once()
        
    @patch('asx_trader.system.Config')
    @patch('asx_trader.system.ASXNewsCollector')
    def test_empty_news_skip(self, mock_news, mock_config):
        """Test cycle skips when no news is found."""
        # Configure mocks
        mock_config.validate.return_value = True
        
        # News collector returns empty list
        mock_news_instance = MagicMock()
        mock_news.return_value = mock_news_instance
        mock_news_instance.fetch_latest_news.return_value = []
        
        # Create system and run cycle
        system = TradingSystem()
        result = system.execute_trading_cycle()
        
        # Verify cycle was skipped
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "no news")

if __name__ == '__main__':
    unittest.main()