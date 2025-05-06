"""
Tests for the broker API module.
"""
import unittest
from unittest.mock import patch, MagicMock
from asx_trader.broker import BrokerAPI

class TestBrokerAPI(unittest.TestCase):
    """Test cases for the BrokerAPI class."""
    
    @patch('asx_trader.broker.requests.post')
    def test_place_trade_success(self, mock_post):
        """Test successful trade placement."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"order_id": "12345", "status": "submitted"}
        mock_post.return_value = mock_response
        
        # Create broker and place trade
        broker = BrokerAPI()
        result = broker.place_trade("BHP", "BUY", 100)
        
        # Verify
        self.assertEqual(result["order_id"], "12345")
        self.assertEqual(result["status"], "submitted")
        mock_post.assert_called_once()
    
    @patch('asx_trader.broker.requests.post')
    def test_place_trade_error(self, mock_post):
        """Test error handling during trade placement."""
        # Set up mock to raise exception
        mock_post.side_effect = Exception("API error")
        
        # Create broker and place trade
        broker = BrokerAPI()
        result = broker.place_trade("BHP", "BUY", 100)
        
        # Verify error handling
        self.assertEqual(result["status"], "error")
        self.assertIn("API error", result["message"])

if __name__ == '__main__':
    unittest.main()