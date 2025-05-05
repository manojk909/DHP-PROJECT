import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PriceAnalyzer:
    """Utility class for performing price analysis on cryptocurrency data"""
    
    def __init__(self):
        pass
    
    def calculate_moving_averages(self, prices_df):
        """
        Calculate simple moving averages for different periods
        
        Args:
            prices_df (DataFrame): DataFrame with price data
            
        Returns:
            DataFrame: DataFrame with moving averages added
        """
        # Calculate moving averages
        prices_df['MA7'] = prices_df['price'].rolling(window=7).mean()
        prices_df['MA14'] = prices_df['price'].rolling(window=14).mean()
        prices_df['MA30'] = prices_df['price'].rolling(window=30).mean()
        prices_df['MA50'] = prices_df['price'].rolling(window=50).mean()
        
        return prices_df
    
    def calculate_volatility(self, prices_df):
        """
        Calculate price volatility
        
        Args:
            prices_df (DataFrame): DataFrame with price data
            
        Returns:
            dict: Volatility metrics
        """
        # Calculate daily returns
        prices_df['daily_return'] = prices_df['price'].pct_change() * 100
        
        # Calculate volatility (standard deviation of returns)
        volatility = prices_df['daily_return'].std()
        
        # Calculate average daily range
        prices_df['price_change'] = prices_df['price'].diff().abs()
        avg_daily_change = prices_df['price_change'].mean()
        
        # Calculate volatility for different periods
        volatility_7d = prices_df['daily_return'].tail(7).std()
        volatility_14d = prices_df['daily_return'].tail(14).std()
        volatility_30d = prices_df['daily_return'].tail(30).std()
        
        return {
            'overall_volatility_percent': volatility,
            'avg_daily_change': avg_daily_change,
            'volatility_7d': volatility_7d,
            'volatility_14d': volatility_14d,
            'volatility_30d': volatility_30d
        }
    
    def price_momentum(self, prices_df):
        """
        Calculate price momentum indicators
        
        Args:
            prices_df (DataFrame): DataFrame with price data
            
        Returns:
            dict: Momentum metrics
        """
        # Calculate rate of change
        prices_df['ROC_7'] = prices_df['price'].pct_change(periods=7) * 100
        prices_df['ROC_14'] = prices_df['price'].pct_change(periods=14) * 100
        prices_df['ROC_30'] = prices_df['price'].pct_change(periods=30) * 100
        
        # Get latest values
        latest_roc_7 = prices_df['ROC_7'].iloc[-1] if not prices_df.empty else 0
        latest_roc_14 = prices_df['ROC_14'].iloc[-1] if not prices_df.empty else 0
        latest_roc_30 = prices_df['ROC_30'].iloc[-1] if not prices_df.empty else 0
        
        # Calculate momentum signals
        is_uptrend_7_14 = prices_df['MA7'].iloc[-1] > prices_df['MA14'].iloc[-1] if not prices_df.empty else False
        is_uptrend_14_30 = prices_df['MA14'].iloc[-1] > prices_df['MA30'].iloc[-1] if not prices_df.empty else False
        
        return {
            'roc_7d': latest_roc_7,
            'roc_14d': latest_roc_14,
            'roc_30d': latest_roc_30,
            'is_uptrend_7_14': bool(is_uptrend_7_14),
            'is_uptrend_14_30': bool(is_uptrend_14_30)
        }
    
    def predict_price_range(self, prices_df, volatility):
        """
        Estimate potential price range in the next 7 days based on volatility
        
        Args:
            prices_df (DataFrame): DataFrame with price data
            volatility (float): Price volatility percentage
            
        Returns:
            dict: Predicted price range
        """
        if prices_df.empty:
            return {
                'current_price': 0,
                'lower_bound': 0,
                'upper_bound': 0
            }
            
        # Get current price
        current_price = prices_df['price'].iloc[-1]
        
        # Calculate potential range based on volatility
        # This is a simple model: assumes normal distribution and uses volatility as daily std dev
        daily_vol = volatility / np.sqrt(7)  # scale to daily
        weekly_range = 1.96 * daily_vol * np.sqrt(7)  # 95% confidence interval over 7 days
        
        lower_bound = current_price * (1 - weekly_range/100)
        upper_bound = current_price * (1 + weekly_range/100)
        
        return {
            'current_price': current_price,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }
    
    def analyze(self, price_history):
        """
        Perform comprehensive price analysis on historical data
        
        Args:
            price_history (dict): Price history data from CoinGecko
            
        Returns:
            dict: Analysis results
        """
        try:
            # Extract prices and convert to DataFrame
            prices = price_history.get('prices', [])
            
            if not prices:
                return {
                    "error": "No price data available for analysis"
                }
                
            # Create DataFrame
            df = pd.DataFrame(prices)
            
            # Calculate moving averages
            df = self.calculate_moving_averages(df)
            
            # Calculate volatility
            volatility_data = self.calculate_volatility(df)
            
            # Calculate momentum
            momentum_data = self.price_momentum(df)
            
            # Predict potential price range
            price_prediction = self.predict_price_range(df, volatility_data['overall_volatility_percent'])
            
            # Prepare moving averages for response
            latest_ma = {}
            for ma in ['MA7', 'MA14', 'MA30', 'MA50']:
                if not df.empty and ma in df.columns:
                    latest_ma[ma] = df[ma].iloc[-1]
                else:
                    latest_ma[ma] = None
                    
            # Prepare summary and insights
            current_price = price_prediction['current_price']
            
            # Determine trend
            if momentum_data['is_uptrend_7_14'] and momentum_data['is_uptrend_14_30']:
                trend = "Strong Uptrend"
            elif momentum_data['is_uptrend_7_14']:
                trend = "Moderate Uptrend"
            elif not momentum_data['is_uptrend_7_14'] and not momentum_data['is_uptrend_14_30']:
                trend = "Strong Downtrend"
            else:
                trend = "Moderate Downtrend"
                
            # Determine volatility level
            if volatility_data['overall_volatility_percent'] > 5:
                volatility_level = "High"
            elif volatility_data['overall_volatility_percent'] > 2:
                volatility_level = "Medium"
            else:
                volatility_level = "Low"
                
            return {
                "coin_id": price_history.get('id', 'unknown'),
                "current_price": current_price,
                "moving_averages": latest_ma,
                "volatility": volatility_data,
                "momentum": momentum_data,
                "price_prediction": price_prediction,
                "summary": {
                    "trend": trend,
                    "volatility_level": volatility_level,
                    "recent_performance": f"{momentum_data['roc_7d']:.2f}% (7d)"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing price data: {str(e)}")
            return {
                "error": f"Failed to analyze price data: {str(e)}"
            }
