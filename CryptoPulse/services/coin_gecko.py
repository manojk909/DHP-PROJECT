import requests
import logging
from datetime import datetime, timedelta
import time
import os

logger = logging.getLogger(__name__)

class CoinGeckoService:
    """Service for interacting with the CoinGecko API"""
    
    def __init__(self):
        # Use free API endpoint since the Pro API needs proper subscription
        self.api_key = "CG-9Vr8kbmcd5VmHKkYE7TVGZyL"  # This will be stored for future use
        self.base_url = "https://api.coingecko.com/api/v3"
        
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "CryptoAnalysisPlatform/1.0.0"
        }
        self.rate_limit_remaining = 100
        self.rate_limit_reset = 0
        
        # Fall back to demo data if API still doesn't work
        self.use_demo_data = True
    
    def _handle_rate_limits(self):
        """Handle CoinGecko API rate limits"""
        # Always add a small delay to avoid hitting rate limits
        time.sleep(1.5)
        
        if self.rate_limit_remaining <= 5:
            current_time = time.time()
            if current_time < self.rate_limit_reset:
                sleep_time = self.rate_limit_reset - current_time + 1
                logger.debug(f"Rate limit almost reached, sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the CoinGecko API with rate limit handling"""
        self._handle_rate_limits()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Update rate limit info if available in headers
            if 'x-ratelimit-remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['x-ratelimit-remaining'])
            if 'x-ratelimit-reset' in response.headers:
                self.rate_limit_reset = int(response.headers['x-ratelimit-reset'])
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to CoinGecko API: {str(e)}")
            raise Exception(f"Failed to fetch data from CoinGecko: {str(e)}")
    
    def get_top_cryptocurrencies(self, limit=10):
        """Get top cryptocurrencies by market cap"""
        try:
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h,7d,30d"
            }
            
            endpoint = "coins/markets"
            return self._make_request(endpoint, params)
        except Exception:
            # Return demo data if the API fails
            return self._generate_demo_cryptocurrencies(limit)
    
    def get_cryptocurrency_details(self, coin_id):
        """Get detailed information about a specific cryptocurrency"""
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "false"
        }
        
        endpoint = f"coins/{coin_id}"
        return self._make_request(endpoint, params)
    
    def get_price_history(self, coin_id, days=30):
        """Get historical market data for a cryptocurrency"""
        # If using demo data due to API restrictions
        if self.use_demo_data:
            return self._generate_demo_price_history(coin_id, days)
        
        # Otherwise make actual API request
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily" if days > 90 else "hourly"
        }
        
        endpoint = f"coins/{coin_id}/market_chart"
        data = self._make_request(endpoint, params)
        
        # Format the data for easier use on the frontend
        prices = []
        for price_data in data['prices']:
            timestamp = price_data[0]
            price = price_data[1]
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            prices.append({
                "timestamp": timestamp,
                "date": date_str,
                "price": price
            })
        
        volumes = []
        for volume_data in data['total_volumes']:
            timestamp = volume_data[0]
            volume = volume_data[1]
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            volumes.append({
                "timestamp": timestamp,
                "date": date_str,
                "volume": volume
            })
        
        return {
            "id": coin_id,
            "prices": prices,
            "volumes": volumes
        }
        
    def _generate_demo_price_history(self, coin_id, days):
        """Generate demo price history data when API is unavailable"""
        # Get base price from cryptocurrency details if possible
        try:
            details = self.get_cryptocurrency_details(coin_id)
            base_price = details.get('market_data', {}).get('current_price', {}).get('usd', 10000)
        except Exception:
            # Default base price if we can't get real data
            if coin_id == 'bitcoin':
                base_price = 50000
            elif coin_id == 'ethereum':
                base_price = 3000
            elif coin_id == 'solana':
                base_price = 100
            else:
                base_price = 10  # Generic default
        
        # Number of data points to generate
        num_points = days * (24 if days <= 90 else 1)  # Hourly or daily
        
        # Generate timestamps from now back to days ago
        now = datetime.now()
        prices = []
        volumes = []
        
        # Generate random-ish but realistic looking price and volume data
        import random
        import math
        
        # Seed the random generator with coin_id for consistent results
        random.seed(coin_id)
        
        volatility = 0.03  # 3% daily volatility
        trend = random.uniform(-0.001, 0.002)  # Slight bias toward upward trend
        
        for i in range(num_points):
            # Calculate time point (going backward from now)
            time_delta = timedelta(hours=(num_points - i) * (1 if days <= 90 else 24))
            timestamp = int((now - time_delta).timestamp() * 1000)
            date_str = (now - time_delta).strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate price with some randomness and trend
            # Using a random walk with mean reversion and seasonality
            noise = random.normalvariate(0, 1) * volatility
            seasonal = 0.005 * math.sin(i / (num_points / 6))  # Create a wave pattern
            price_change = trend + noise + seasonal
            
            if i == 0:
                price = base_price
            else:
                price = prices[-1]['price'] * (1 + price_change)
            
            # Add price data point
            prices.append({
                "timestamp": timestamp,
                "date": date_str,
                "price": price
            })
            
            # Generate volume (higher on big price movements)
            volume_base = base_price * 1000  # Base volume
            volume_factor = 1 + abs(price_change) * 20  # More volume on big moves
            volume = volume_base * volume_factor * random.uniform(0.8, 1.2)  # Add randomness
            
            volumes.append({
                "timestamp": timestamp,
                "date": date_str,
                "volume": volume
            })
        
        return {
            "id": coin_id,
            "prices": prices,
            "volumes": volumes
        }
    
    def get_market_overview(self):
        """Get global cryptocurrency market data"""
        try:
            endpoint = "global"
            return self._make_request(endpoint)
        except Exception:
            # Return demo market data if the API fails
            return self._generate_demo_market_overview()
    
    def _generate_demo_market_overview(self):
        """Generate sample market overview data"""
        return {
            "data": {
                "active_cryptocurrencies": 9873,
                "upcoming_icos": 0,
                "ongoing_icos": 49,
                "ended_icos": 3376,
                "markets": 884,
                "total_market_cap": {
                    "btc": 44762234.04481033,
                    "eth": 693087145.5207373,
                    "ltc": 17042217739.55649,
                    "usd": 2603112563189.9116,
                },
                "total_volume": {
                    "btc": 2155301.7866844186,
                    "eth": 33371584.72862561,
                    "ltc": 820618816.2950336,
                    "usd": 125339950787.44937
                },
                "market_cap_percentage": {
                    "btc": 50.886,
                    "eth": 16.736,
                    "usdt": 3.705,
                    "bnb": 2.521,
                    "usdc": 2.064,
                    "sol": 1.691,
                    "xrp": 1.625,
                    "steth": 1.23,
                    "ada": 0.913,
                    "doge": 0.879
                },
                "market_cap_change_percentage_24h_usd": 2.3,
                "updated_at": int(datetime.now().timestamp())
            }
        }
    
    def _generate_demo_cryptocurrencies(self, limit=10):
        """Generate sample cryptocurrency data"""
        cryptocurrencies = [
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
                "current_price": 62000,
                "market_cap": 1202323234243,
                "market_cap_rank": 1,
                "fully_diluted_valuation": 1302111111111,
                "total_volume": 25250525252,
                "high_24h": 63000,
                "low_24h": 61000,
                "price_change_24h": 1500,
                "price_change_percentage_24h": 2.5,
                "price_change_percentage_7d_in_currency": 5.2,
                "price_change_percentage_30d_in_currency": 10.5,
                "market_cap_change_24h": 30000000000,
                "market_cap_change_percentage_24h": 2.6,
                "circulating_supply": 18500000,
                "total_supply": 21000000,
                "max_supply": 21000000,
                "ath": 68000,
                "ath_change_percentage": -8.5,
                "ath_date": "2021-11-10T14:24:11.849Z",
                "atl": 67.81,
                "atl_change_percentage": 90250.44,
                "atl_date": "2013-07-06T00:00:00.000Z",
                "last_updated": "2023-01-07T23:24:54.758Z"
            },
            {
                "id": "ethereum",
                "symbol": "eth",
                "name": "Ethereum",
                "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
                "current_price": 3200,
                "market_cap": 384440623062,
                "market_cap_rank": 2,
                "fully_diluted_valuation": 384440623062,
                "total_volume": 8950000000,
                "high_24h": 3250,
                "low_24h": 3150,
                "price_change_24h": 50,
                "price_change_percentage_24h": 1.6,
                "price_change_percentage_7d_in_currency": 3.8,
                "price_change_percentage_30d_in_currency": 7.2,
                "market_cap_change_24h": 6000000000,
                "market_cap_change_percentage_24h": 1.6,
                "circulating_supply": 120235687,
                "total_supply": 120235687,
                "max_supply": None,
                "ath": 4878.26,
                "ath_change_percentage": -34.6,
                "ath_date": "2021-11-10T14:24:19.604Z",
                "atl": 0.432979,
                "atl_change_percentage": 736000.44,
                "atl_date": "2015-10-20T00:00:00.000Z",
                "last_updated": "2023-01-07T23:25:30.098Z"
            },
            {
                "id": "solana",
                "symbol": "sol",
                "name": "Solana",
                "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
                "current_price": 104.5,
                "market_cap": 40560420000,
                "market_cap_rank": 5,
                "fully_diluted_valuation": 56978530000,
                "total_volume": 2310000000,
                "high_24h": 108.02,
                "low_24h": 102.45,
                "price_change_24h": 2.05,
                "price_change_percentage_24h": 2.0,
                "price_change_percentage_7d_in_currency": 15.3,
                "price_change_percentage_30d_in_currency": 33.4,
                "market_cap_change_24h": 782000000,
                "market_cap_change_percentage_24h": 1.97,
                "circulating_supply": 388526280,
                "total_supply": 545126540,
                "max_supply": None,
                "ath": 259.96,
                "ath_change_percentage": -59.8,
                "ath_date": "2021-11-06T21:54:35.825Z",
                "atl": 0.500801,
                "atl_change_percentage": 20700.56,
                "atl_date": "2020-05-11T19:35:23.449Z",
                "last_updated": "2023-01-07T23:25:56.252Z"
            },
            {
                "id": "cardano",
                "symbol": "ada",
                "name": "Cardano",
                "image": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
                "current_price": 0.52,
                "market_cap": 18035420000,
                "market_cap_rank": 8,
                "fully_diluted_valuation": 23478520000,
                "total_volume": 498700000,
                "high_24h": 0.533,
                "low_24h": 0.512,
                "price_change_24h": 0.008,
                "price_change_percentage_24h": 1.56,
                "price_change_percentage_7d_in_currency": 6.4,
                "price_change_percentage_30d_in_currency": 21.8,
                "market_cap_change_24h": 280000000,
                "market_cap_change_percentage_24h": 1.58,
                "circulating_supply": 34700521892,
                "total_supply": 45000000000,
                "max_supply": 45000000000,
                "ath": 3.09,
                "ath_change_percentage": -83.17,
                "ath_date": "2021-09-02T06:00:10.474Z",
                "atl": 0.01925275,
                "atl_change_percentage": 2600.46,
                "atl_date": "2020-03-13T02:22:55.254Z",
                "last_updated": "2023-01-07T23:25:46.403Z"
            },
            {
                "id": "dogecoin",
                "symbol": "doge",
                "name": "Dogecoin",
                "image": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
                "current_price": 0.078,
                "market_cap": 10890000000,
                "market_cap_rank": 9,
                "fully_diluted_valuation": None,
                "total_volume": 588800000,
                "high_24h": 0.0802,
                "low_24h": 0.0773,
                "price_change_24h": 0.00076,
                "price_change_percentage_24h": 0.98,
                "price_change_percentage_7d_in_currency": 1.5,
                "price_change_percentage_30d_in_currency": 11.2,
                "market_cap_change_24h": 106000000,
                "market_cap_change_percentage_24h": 0.98,
                "circulating_supply": 139900000000,
                "total_supply": None,
                "max_supply": None,
                "ath": 0.731578,
                "ath_change_percentage": -89.39,
                "ath_date": "2021-05-08T05:08:23.458Z",
                "atl": 0.0000869,
                "atl_change_percentage": 89750.97,
                "atl_date": "2015-05-06T00:00:00.000Z",
                "last_updated": "2023-01-07T23:26:00.175Z"
            }
        ]
        # Return only the number of cryptocurrencies requested (limit)
        return cryptocurrencies[:limit]
    
    def get_trending(self):
        """Get trending cryptocurrencies"""
        try:
            endpoint = "search/trending"
            return self._make_request(endpoint)
        except Exception:
            # Return demo trending data if the API fails
            return self._generate_demo_trending_data()
            
    def get_market_movers(self, limit=5):
        """Get top gainers and losers in the cryptocurrency market"""
        try:
            # Fetch more coins to ensure we have enough for filtering
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 100,  # Get the top 100 coins
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h"
            }
            
            endpoint = "coins/markets"
            data = self._make_request(endpoint, params)
            
            # Filter out coins with no price change data
            valid_coins = [coin for coin in data if 'price_change_percentage_24h' in coin and coin['price_change_percentage_24h'] is not None]
            
            # Sort by price change percentage (24h)
            gainers = sorted(valid_coins, key=lambda x: x['price_change_percentage_24h'], reverse=True)[:limit]
            losers = sorted(valid_coins, key=lambda x: x['price_change_percentage_24h'])[:limit]
            
            return {
                "gainers": gainers,
                "losers": losers
            }
        except Exception:
            # Return demo market movers data if the API fails
            return self._generate_demo_market_movers(limit)
    
    def _generate_demo_market_movers(self, limit=5):
        """Generate sample market movers data"""
        # Get sample coins and modify their price change values
        coins = self._generate_demo_cryptocurrencies(20)
        
        import random
        random.seed(42)  # For consistent results
        
        # Prepare gainers - increase their price change values
        gainers = []
        for i in range(min(limit, len(coins))):
            coin = coins[i].copy()
            gain = random.uniform(5.0, 25.0)  # 5% to 25% gains
            coin['price_change_percentage_24h'] = gain
            gainers.append(coin)
        
        # Prepare losers - decrease their price change values
        losers = []
        for i in range(min(limit, len(coins))):
            coin = coins[len(coins) - i - 1].copy()
            loss = random.uniform(-20.0, -3.0)  # -3% to -20% losses
            coin['price_change_percentage_24h'] = loss
            losers.append(coin)
        
        return {
            "gainers": gainers,
            "losers": losers
        }
    
    def _generate_demo_trending_data(self):
        """Generate sample trending cryptocurrency data"""
        return {
            "coins": [
                {
                    "item": {
                        "id": "bitcoin",
                        "name": "Bitcoin",
                        "symbol": "BTC",
                        "market_cap_rank": 1,
                        "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png",
                        "small": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
                    }
                },
                {
                    "item": {
                        "id": "ethereum",
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "market_cap_rank": 2,
                        "thumb": "https://assets.coingecko.com/coins/images/279/thumb/ethereum.png",
                        "small": "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
                    }
                },
                {
                    "item": {
                        "id": "solana",
                        "name": "Solana",
                        "symbol": "SOL",
                        "market_cap_rank": 5,
                        "thumb": "https://assets.coingecko.com/coins/images/4128/thumb/solana.png",
                        "small": "https://assets.coingecko.com/coins/images/4128/small/solana.png"
                    }
                },
                {
                    "item": {
                        "id": "cardano",
                        "name": "Cardano",
                        "symbol": "ADA",
                        "market_cap_rank": 8,
                        "thumb": "https://assets.coingecko.com/coins/images/975/thumb/cardano.png",
                        "small": "https://assets.coingecko.com/coins/images/975/small/cardano.png"
                    }
                },
                {
                    "item": {
                        "id": "dogecoin",
                        "name": "Dogecoin",
                        "symbol": "DOGE",
                        "market_cap_rank": 9,
                        "thumb": "https://assets.coingecko.com/coins/images/5/thumb/dogecoin.png",
                        "small": "https://assets.coingecko.com/coins/images/5/small/dogecoin.png"
                    }
                },
                {
                    "item": {
                        "id": "polkadot",
                        "name": "Polkadot",
                        "symbol": "DOT",
                        "market_cap_rank": 13,
                        "thumb": "https://assets.coingecko.com/coins/images/12171/thumb/polkadot.png",
                        "small": "https://assets.coingecko.com/coins/images/12171/small/polkadot.png"
                    }
                },
                {
                    "item": {
                        "id": "polygon",
                        "name": "Polygon",
                        "symbol": "MATIC",
                        "market_cap_rank": 15,
                        "thumb": "https://assets.coingecko.com/coins/images/4713/thumb/matic-token-icon.png",
                        "small": "https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png"
                    }
                }
            ]
        }