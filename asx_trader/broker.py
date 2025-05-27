
"""
Broker API integration for executing trades.
Currently supports IG Markets API.
"""
import logging
import json
import requests
from datetime import datetime
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class IGBroker:
    """
    IG Markets API integration for executing trades.
    Documentation: https://labs.ig.com/rest-trading-api-reference
    """
    
    def __init__(self):
        self.api_key = Config.BROKER_API_KEY
        self.username = Config.BROKER_USERNAME
        self.password = Config.BROKER_PASSWORD
        self.account_type = Config.BROKER_ACCOUNT_TYPE or "DEMO"  # Default to DEMO for safety
        self.base_url = Config.BROKER_API_URL or "https://demo-api.ig.com/gateway/deal"
        self.session_token = None
        self.cst_token = None
        
        # Initialize account balance to a safe default
        self.account_balance = 0
        
        # Only attempt login if credentials are provided
        if self.api_key and self.username and self.password:
            self._login()
            # Get the real account balance after login
            self._update_account_balance()
    
    def _login(self):
        """
        Login to IG API to get session tokens.
        These tokens are required for all subsequent API calls.
        """
        try:
            url = f"{self.base_url}/session"
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json; charset=utf-8",
                "X-IG-API-KEY": self.api_key,
                "Version": "2"
            }
            
            payload = {
                "identifier": self.username,
                "password": self.password,
                "encryptedPassword": False
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Extract session tokens
                self.session_token = response.headers.get("X-SECURITY-TOKEN")
                self.cst_token = response.headers.get("CST")
                logger.info("Successfully logged in to IG API")
                return True
            else:
                logger.error(f"Failed to login to IG API: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging in to IG API: {e}")
            return False
    
    def _update_account_balance(self):
        """
        Update account balance from IG API.
        This provides the real account balance instead of relying on configuration.
        """
        try:
            account_info = self.get_account_info()
            
            if not account_info or "accounts" not in account_info:
                logger.warning("Could not retrieve account information")
                return
                
            # Find the preferred account or the first one
            preferred_account = None
            for account in account_info["accounts"]:
                if account.get("preferred", False):
                    preferred_account = account
                    break
            
            # If no preferred account, use the first one
            if not preferred_account and account_info["accounts"]:
                preferred_account = account_info["accounts"][0]
            
            # Update the account balance
            if preferred_account and "balance" in preferred_account:
                balance_data = preferred_account["balance"]
                
                # Get available balance, deposit, or overall balance
                if "available" in balance_data:
                    self.account_balance = float(balance_data["available"])
                elif "balance" in balance_data:
                    self.account_balance = float(balance_data["balance"])
                elif "deposit" in balance_data:
                    self.account_balance = float(balance_data["deposit"])
                
                logger.info(f"Retrieved account balance from IG API: ${self.account_balance:.2f}")
                
                # Also log account details for reference
                logger.info(f"Account ID: {preferred_account.get('accountId', 'Unknown')}")
                logger.info(f"Account Type: {preferred_account.get('accountType', 'Unknown')}")
                logger.info(f"Account Status: {preferred_account.get('status', 'Unknown')}")
                
            else:
                logger.warning("No balance information found in account data")
                
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
    
    def _get_auth_headers(self):
        """Get the authentication headers required for API calls."""
        if not self.session_token or not self.cst_token:
            if not self._login():
                raise Exception("Not authenticated with IG API")
                
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-IG-API-KEY": self.api_key,
            "X-SECURITY-TOKEN": self.session_token,
            "CST": self.cst_token
        }
    
    def get_account_info(self):
        """Get information about the trading account."""
        try:
            url = f"{self.base_url}/accounts"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get account info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self):
        """Get current positions in the account."""
        try:
            url = f"{self.base_url}/positions"
            headers = self._get_auth_headers()
            headers["Version"] = "2"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get positions: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None
    
    def search_market(self, search_term):
        """
        Search for a market by name or code.
        For ASX stocks, append '.AU' to the symbol.
        """
        try:
            # For ASX stocks, append .AU if not already present
            if search_term and not search_term.endswith('.AU') and len(search_term) <= 3:
                search_term = f"{search_term}.AU"
                
            url = f"{self.base_url}/markets?searchTerm={search_term}"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to search market: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching market: {e}")
            return None
    
    def execute_trade(self, symbol, direction, quantity, order_type="MARKET", limit_price=None):
        """
        Execute a trade through the IG API.
        
        Args:
            symbol: Stock symbol (e.g., 'CBA' for Commonwealth Bank)
            direction: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET' or 'LIMIT'
            limit_price: Limit price if order_type is 'LIMIT'
            
        Returns:
            dict: Result of the order placement
        """
        try:
            # Refresh account balance to ensure it's current
            self._update_account_balance()
            
            # Check account balance
            if not self._check_account_balance(symbol, direction, quantity, limit_price):
                return {
                    "status": "ERROR",
                    "reason": "Insufficient account balance",
                    "details": f"Account balance ${self.account_balance} is insufficient for this trade"
                }
            
            # If simulation or not live, return simulated result
            if not self.api_key or self.account_type != "LIVE":
                logger.warning(f"SIMULATED TRADE (not executed): {direction} {quantity} {symbol}")
                return {
                    "status": "SIMULATED",
                    "dealReference": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "details": f"{direction} {quantity} {symbol} - Simulated, not executed"
                }
            
            # First, search for the market to get epic
            market_results = self.search_market(symbol)
            if not market_results or "markets" not in market_results:
                logger.error(f"Could not find market for symbol: {symbol}")
                return {
                    "status": "ERROR",
                    "reason": f"Could not find market for symbol: {symbol}"
                }
            
            # Find exact match for the symbol
            epic = None
            for market in market_results.get("markets", []):
                if market.get("streamingPricesAvailable", False) and (
                    market.get("epic", "").endswith(f"{symbol}.AU") or 
                    market.get("instrumentName", "").startswith(symbol)):
                    epic = market.get("epic")
                    break
            
            if not epic:
                logger.error(f"Could not find matching epic for symbol: {symbol}")
                return {
                    "status": "ERROR",
                    "reason": f"Could not find matching epic for symbol: {symbol}"
                }
            
            # Now place the trade
            url = f"{self.base_url}/positions/otc"
            headers = self._get_auth_headers()
            headers["Version"] = "2"
            
            # Convert direction to IG format
            ig_direction = "BUY" if direction == "BUY" else "SELL"
            
            payload = {
                "epic": epic,
                "direction": ig_direction,
                "size": str(quantity),
                "orderType": order_type,
                "timeInForce": "FILL_OR_KILL",
                "guaranteedStop": "false",
                "forceOpen": "true"
            }
            
            if order_type == "LIMIT" and limit_price:
                payload["level"] = str(limit_price)
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Trade executed: {direction} {quantity} {symbol} - Reference: {result.get('dealReference')}")
                # Update account balance after trade
                self._update_account_balance()
                return {
                    "status": "SUCCESS",
                    "dealReference": result.get("dealReference"),
                    "details": result
                }
            else:
                logger.error(f"Failed to execute trade: {response.status_code} - {response.text}")
                return {
                    "status": "ERROR",
                    "reason": f"API Error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                "status": "ERROR",
                "reason": str(e)
            }
    
    def _check_account_balance(self, symbol, direction, quantity, limit_price=None):
        """
        Check if account has sufficient balance for the trade.
        
        Returns:
            bool: True if sufficient balance, False otherwise
        """
        try:
            # For SELL orders, always allow (increases balance)
            if direction == "SELL":
                return True
                
            # For BUY orders, check if we have enough balance
            # Get current price if not provided
            price = limit_price
            if not price:
                # Try to get from IG if possible
                market_results = self.search_market(symbol)
                if market_results and "markets" in market_results:
                    for market in market_results.get("markets", []):
                        if market.get("streamingPricesAvailable", False) and (
                            market.get("epic", "").endswith(f"{symbol}.AU") or 
                            market.get("instrumentName", "").startswith(symbol)):
                            price = market.get("offer", 0)
                            break
            
            # If still no price, return False (can't determine)
            if not price or price <= 0:
                logger.warning(f"Could not determine price for {symbol}, rejecting trade")
                return False
                
            # Calculate total cost
            total_cost = price * quantity
            
            # Add 5% buffer for fees/slippage
            total_cost_with_buffer = total_cost * 1.05
            
            # Check if we have enough balance
            if total_cost_with_buffer > self.account_balance:
                logger.warning(f"Insufficient balance for trade: {direction} {quantity} {symbol} @ ${price}. " + 
                              f"Required: ${total_cost_with_buffer:.2f}, Available: ${self.account_balance:.2f}")
                return False
                
            logger.info(f"Account balance check passed: ${self.account_balance:.2f} available for " + 
                       f"${total_cost_with_buffer:.2f} trade")
            return True
            
        except Exception as e:
            logger.error(f"Error checking account balance: {e}")
            # Default to reject trade on error
            return False

class BrokerFactory:
    """Factory class to create the appropriate broker instance."""
    
    @staticmethod
    def get_broker():
        """Get the appropriate broker based on configuration."""
        broker_type = Config.BROKER_TYPE or "IG"
        
        if broker_type.upper() == "IG":
            return IGBroker()
        else:
            logger.warning(f"Unsupported broker type: {broker_type}. Using simulation.")
            return SimulationBroker()

class SimulationBroker:
    """Simulated broker for testing without real trades."""
    
    def __init__(self):
        # Try to get account balance from config, default to $1,000
        self.account_balance = Config.BROKER_ACCOUNT_BALANCE if hasattr(Config, 'BROKER_ACCOUNT_BALANCE') else 1000.0
        logger.info(f"Using simulation broker with ${self.account_balance} balance - no real trades will be executed")
        
    def execute_trade(self, symbol, direction, quantity, order_type="MARKET", limit_price=None):
        """Simulate trade execution."""
        # Estimate price if not provided
        if not limit_price:
            import random
            limit_price = random.uniform(10, 100)
            
        # Calculate trade cost
        total_cost = limit_price * quantity
        
        # Check account balance for BUY orders
        if direction == "BUY":
            if total_cost > self.account_balance:
                logger.warning(f"Insufficient balance for simulated trade: {direction} {quantity} {symbol} @ ${limit_price}. " + 
                              f"Required: ${total_cost:.2f}, Available: ${self.account_balance:.2f}")
                return {
                    "status": "ERROR",
                    "reason": "Insufficient balance",
                    "details": f"Account balance ${self.account_balance} is insufficient for this trade"
                }
        
        logger.info(f"SIMULATED TRADE: {direction} {quantity} {symbol} @ ${limit_price:.2f}")
        
        # Update simulated balance
        if direction == "BUY":
            self.account_balance -= total_cost
        else:
            # For SELL, assume we already own the shares and add to balance
            self.account_balance += total_cost
            
        logger.info(f"Simulated account balance after trade: ${self.account_balance:.2f}")
            
        return {
            "status": "SIMULATED",
            "dealReference": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "details": f"{direction} {quantity} {symbol} @ ${limit_price:.2f} - Simulated, balance now ${self.account_balance:.2f}"
        }
    
    def get_account_info(self):
        """Get simulated account info."""
        return {
            "accounts": [
                {
                    "accountId": "SIMULATED",
                    "accountName": "Simulation Account",
                    "accountType": "DEMO",
                    "preferred": True,
                    "balance": {
                        "available": self.account_balance,
                        "balance": self.account_balance,
                        "deposit": 0,
                        "profitLoss": 0
                    }
                }
            ]
        }
    
    def get_positions(self):
        """Get simulated positions."""
        return {
            "positions": []
        }

# Create a broker instance for easy importing
broker = BrokerFactory.get_broker()

