"""
Tests for the prediction engine module.
"""
import unittest
from unittest.mock import patch, MagicMock
from asx_trader.prediction import GPTEnhancedPredictionEngine

class TestPredictionEngine(unittest.TestCase):
    """Test cases for the GPTEnhancedPredictionEngine class."""
    
    @patch('asx_trader.prediction.OpenAI')
    def test_analyze_news(self, mock_openai_class):
        """Test news analysis and signal generation."""
        # Set up mock for OpenAI
        mock_openai = MagicMock()
        mock_openai_class.return_value = mock_openai
        
        # Mock completion response
        mock_choice = MagicMock()
        mock_choice.message.content = '{"signal": "BUY", "confidence": "high", "reasoning": "Positive earnings"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_openai.chat.completions.create.return_value = mock_response
        
        # Create test news item
        news_item = {
            "id": "news1",
            "headline": "Company X Reports Strong Earnings",
            "content": "Company X reported earnings above expectations.",
            "published_date": "2023-07-15",
            "symbols": ["BHP"]
        }
        
        # Create prediction engine and analyze news
        engine = GPTEnhancedPredictionEngine()
        results = engine.analyze_news([news_item])
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["signal"], "BUY")
        self.assertEqual(results[0]["confidence"], "high")
        self.assertEqual(results[0]["news_id"], "news1")
        self.assertEqual(results[0]["symbols"], ["BHP"])
        
        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()