import pandas as pd
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StocksDataService:
    """Service for processing stock market data from CSV files"""
    
    def __init__(self):
        self.historical_data = None
        self.news_data = None
        self.gainers_data = None
        self.losers_data = None
        
        # Load data on initialization
        self.load_historical_data()
        self.load_news_data()
        self.load_market_movers()
    
    def load_historical_data(self, filename='all_nifty50_200day_hist.csv'):
        """
        Load historical stock data from CSV file
        
        Args:
            filename (str): Name of the CSV file
            
        Returns:
            DataFrame: Pandas DataFrame with the historical data
        """
        try:
            file_path = os.path.join('attached_assets', filename)
            data = pd.read_csv(file_path)
            
            # Convert date column to datetime
            data['Date'] = pd.to_datetime(data['Date'])
            
            # Sort by date
            data = data.sort_values('Date')
            
            self.historical_data = data
            logger.info(f"Loaded historical stock data from {filename}: {len(data)} rows")
            return data
        except Exception as e:
            logger.error(f"Error loading historical stock data: {str(e)}")
            # Return empty DataFrame
            self.historical_data = pd.DataFrame()
            return pd.DataFrame()
    
    def load_news_data(self, filename='all_stocks_news.csv'):
        """
        Load stock news data from CSV file
        
        Args:
            filename (str): Name of the CSV file
            
        Returns:
            DataFrame: Pandas DataFrame with the news data
        """
        try:
            file_path = os.path.join('attached_assets', filename)
            data = pd.read_csv(file_path)
            
            # Convert date columns to datetime if they exist
            date_columns = ['PublishedAt', 'Date']
            for col in date_columns:
                if col in data.columns:
                    data[col] = pd.to_datetime(data[col], errors='coerce')
            
            # Sort by date if available
            if 'PublishedAt' in data.columns:
                data = data.sort_values('PublishedAt', ascending=False)
            elif 'Date' in data.columns:
                data = data.sort_values('Date', ascending=False)
            
            self.news_data = data
            logger.info(f"Loaded news data from {filename}: {len(data)} rows")
            return data
        except Exception as e:
            logger.error(f"Error loading news data: {str(e)}")
            # Return empty DataFrame
            self.news_data = pd.DataFrame()
            return pd.DataFrame()
    
    def load_market_movers(self, gainers_file='top_gainers.csv', losers_file='top_losers.csv'):
        """
        Load market movers (top gainers and losers) data from CSV files
        
        Args:
            gainers_file (str): Name of the top gainers CSV file
            losers_file (str): Name of the top losers CSV file
            
        Returns:
            tuple: Tuple containing (gainers_df, losers_df)
        """
        try:
            # Load gainers
            gainers_path = os.path.join('attached_assets', gainers_file)
            gainers_df = pd.read_csv(gainers_path)
            
            # Process gainers data
            if 'Change (%)' in gainers_df.columns:
                # The values are already numerical in this dataset, no need to strip % symbol
                gainers_df['Change (%)'] = gainers_df['Change (%)'].astype('float')
            
            self.gainers_data = gainers_df
            logger.info(f"Loaded top gainers from {gainers_file}: {len(gainers_df)} rows")
        except Exception as e:
            logger.error(f"Error loading gainers data: {str(e)}")
            # Create empty DataFrame
            self.gainers_data = pd.DataFrame()
            gainers_df = pd.DataFrame()
        
        try:
            # Load losers
            losers_path = os.path.join('attached_assets', losers_file)
            losers_df = pd.read_csv(losers_path)
            
            # Process losers data
            if 'Change (%)' in losers_df.columns:
                # The values are already numerical in this dataset
                losers_df['Change (%)'] = losers_df['Change (%)'].astype('float')
                # Ensure negative values for consistency
                losers_df['Change (%)'] = losers_df['Change (%)'].apply(lambda x: -abs(x) if x < 0 else x)
            
            self.losers_data = losers_df
            logger.info(f"Loaded top losers from {losers_file}: {len(losers_df)} rows")
        except Exception as e:
            logger.error(f"Error loading losers data: {str(e)}")
            # Create empty DataFrame
            self.losers_data = pd.DataFrame()
            losers_df = pd.DataFrame()
        
        return (gainers_df, losers_df)
    
    def get_top_gainers(self, limit=10):
        """
        Get top gaining stocks
        
        Args:
            limit (int): Number of stocks to return
            
        Returns:
            DataFrame: Top gainers
        """
        if self.gainers_data is None or self.gainers_data.empty:
            return pd.DataFrame()
        
        return self.gainers_data.head(limit)
    
    def get_top_losers(self, limit=10):
        """
        Get top losing stocks
        
        Args:
            limit (int): Number of stocks to return
            
        Returns:
            DataFrame: Top losers
        """
        if self.losers_data is None or self.losers_data.empty:
            return pd.DataFrame()
        
        return self.losers_data.head(limit)
    
    def get_stock_price_history(self, symbol, days=30):
        """
        Get historical price data for a specific stock
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days of history to return
            
        Returns:
            DataFrame: Historical price data
        """
        if self.historical_data is None or self.historical_data.empty:
            return pd.DataFrame()
        
        # Filter for the specific symbol
        stock_data = self.historical_data[self.historical_data['Symbol'] == symbol].copy()
        
        # If no data found, return empty DataFrame
        if stock_data.empty:
            return pd.DataFrame()
        
        # Sort by date
        stock_data = stock_data.sort_values('Date')
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter for the requested time period
        stock_data = stock_data[stock_data['Date'] >= cutoff_date]
        
        # Calculate moving averages
        if len(stock_data) > 7:
            stock_data['7_day_ma'] = stock_data['Close'].rolling(window=7).mean()
            
        if len(stock_data) > 30:
            stock_data['30_day_ma'] = stock_data['Close'].rolling(window=30).mean()
        
        return stock_data
    
    def get_stock_news(self, company=None, limit=20):
        """
        Get news for a specific company or all companies
        
        Args:
            company (str): Company name or None for all news
            limit (int): Maximum number of news items to return
            
        Returns:
            DataFrame: News data
        """
        if self.news_data is None or self.news_data.empty:
            return pd.DataFrame()
        
        # Filter for the specific company if provided
        if company and 'Company' in self.news_data.columns:
            # Case-insensitive search in Company column
            news = self.news_data[self.news_data['Company'].str.contains(company, case=False, na=False)].copy()
            
            # If no exact match, try searching in headlines
            if news.empty and 'Headline' in self.news_data.columns:
                news = self.news_data[self.news_data['Headline'].str.contains(company, case=False, na=False)].copy()
        else:
            news = self.news_data.copy()
        
        # Limit the number of items
        news = news.head(limit)
        
        return news
    
    def get_available_symbols(self):
        """
        Get list of available stock symbols
        
        Returns:
            list: List of unique stock symbols
        """
        if self.historical_data is None or self.historical_data.empty:
            return []
        
        # Extract unique symbols
        symbols = self.historical_data['Symbol'].unique().tolist()
        
        return sorted(symbols)
    
    def get_stock_analysis(self, symbol):
        """
        Generate analysis for a specific stock
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Analysis results
        """
        # Get price history
        price_history = self.get_stock_price_history(symbol, days=90)
        
        if price_history.empty:
            return {
                "error": "No data available for this symbol"
            }
        
        # Latest data
        latest_data = price_history.iloc[-1]
        
        # Calculate moving averages
        ma_7 = price_history['7_day_ma'].iloc[-1] if '7_day_ma' in price_history.columns and not pd.isna(price_history['7_day_ma'].iloc[-1]) else None
        ma_30 = price_history['30_day_ma'].iloc[-1] if '30_day_ma' in price_history.columns and not pd.isna(price_history['30_day_ma'].iloc[-1]) else None
        
        # Calculate price vs MA
        current_price = latest_data['Close']
        price_vs_ma7 = 'above' if ma_7 and current_price > ma_7 else 'below'
        price_vs_ma30 = 'above' if ma_30 and current_price > ma_30 else 'below'
        
        # Calculate volatility
        if len(price_history) > 5:
            # Calculate daily returns
            price_history['Daily Return'] = price_history['Close'].pct_change()
            
            # Calculate volatility (standard deviation of daily returns)
            volatility = price_history['Daily Return'].std() * 100  # Convert to percentage
        else:
            volatility = 0
        
        # Determine trend
        if len(price_history) > 10:
            # Use price vs MA to determine trend
            if ma_7 and ma_30:
                if price_vs_ma7 == 'above' and price_vs_ma30 == 'above' and ma_7 > ma_30:
                    # Price above both MAs and short-term MA above long-term MA
                    trend = 'strong_uptrend'
                elif price_vs_ma7 == 'above' and price_vs_ma30 == 'above':
                    trend = 'uptrend'
                elif price_vs_ma7 == 'below' and price_vs_ma30 == 'below' and ma_7 < ma_30:
                    # Price below both MAs and short-term MA below long-term MA
                    trend = 'strong_downtrend'
                elif price_vs_ma7 == 'below' and price_vs_ma30 == 'below':
                    trend = 'downtrend'
                else:
                    # Mixed signals
                    trend = 'neutral'
            else:
                # Simple trend using recent price
                # Check if price has risen over the past 5 days
                if len(price_history) >= 5:
                    five_days_ago = price_history.iloc[-5]['Close']
                    if current_price > five_days_ago * 1.05:  # 5% increase
                        trend = 'uptrend'
                    elif current_price < five_days_ago * 0.95:  # 5% decrease
                        trend = 'downtrend'
                    else:
                        trend = 'neutral'
                else:
                    trend = 'neutral'
        else:
            trend = 'neutral'
        
        # Return analysis
        return {
            "symbol": symbol,
            "current_price": current_price,
            "moving_averages": {
                "ma_7": ma_7,
                "ma_30": ma_30,
                "price_vs_ma7": price_vs_ma7,
                "price_vs_ma30": price_vs_ma30
            },
            "volatility_percent": volatility,
            "trend": trend,
            "data_points": len(price_history)
        }