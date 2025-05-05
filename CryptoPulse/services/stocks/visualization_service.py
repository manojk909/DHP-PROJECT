import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)

class StockVisualizationService:
    """Service for generating visualization data for stock market analysis"""
    
    def __init__(self):
        pass
        
    def prepare_price_history_data(self, stock_data):
        """
        Prepare stock price history data for Chart.js
        
        Args:
            stock_data (DataFrame): Stock price history data
            
        Returns:
            dict: Data formatted for Chart.js
        """
        if stock_data.empty:
            return {
                "labels": [],
                "datasets": []
            }
            
        try:
            # Convert dates to string format for Chart.js
            date_labels = stock_data['Date'].dt.strftime('%Y-%m-%d').tolist()
            
            # Prepare price data
            price_data = {
                "labels": date_labels,
                "datasets": [
                    {
                        "label": "Closing Price",
                        "data": stock_data['Close'].tolist(),
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "borderWidth": 2,
                        "pointRadius": 1,
                        "fill": False
                    }
                ]
            }
            
            # If we have moving averages, add them
            if '7_day_ma' in stock_data.columns:
                # Remove NaN values
                ma_data = stock_data.dropna(subset=['7_day_ma'])
                
                if not ma_data.empty:
                    ma_dates = ma_data['Date'].dt.strftime('%Y-%m-%d').tolist()
                    
                    # Find indices where the MA dates match the original date labels
                    indices = [date_labels.index(date) for date in ma_dates if date in date_labels]
                    
                    # Create a full array with nulls for missing dates
                    ma_values = [None] * len(date_labels)
                    for i, idx in enumerate(indices):
                        ma_values[idx] = ma_data['7_day_ma'].iloc[i]
                    
                    price_data["datasets"].append({
                        "label": "7-Day MA",
                        "data": ma_values,
                        "borderColor": "rgba(255, 99, 132, 1)",
                        "backgroundColor": "rgba(255, 99, 132, 0)",
                        "borderWidth": 1,
                        "pointRadius": 0,
                        "fill": False
                    })
            
            if '30_day_ma' in stock_data.columns:
                # Remove NaN values
                ma_data = stock_data.dropna(subset=['30_day_ma'])
                
                if not ma_data.empty:
                    ma_dates = ma_data['Date'].dt.strftime('%Y-%m-%d').tolist()
                    
                    # Find indices where the MA dates match the original date labels
                    indices = [date_labels.index(date) for date in ma_dates if date in date_labels]
                    
                    # Create a full array with nulls for missing dates
                    ma_values = [None] * len(date_labels)
                    for i, idx in enumerate(indices):
                        ma_values[idx] = ma_data['30_day_ma'].iloc[i]
                    
                    price_data["datasets"].append({
                        "label": "30-Day MA",
                        "data": ma_values,
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "backgroundColor": "rgba(54, 162, 235, 0)",
                        "borderWidth": 1,
                        "pointRadius": 0,
                        "fill": False
                    })
            
            return price_data
        except Exception as e:
            logger.error(f"Error preparing price history data: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }
            
    def prepare_volume_data(self, stock_data):
        """
        Prepare stock volume data for Chart.js
        
        Args:
            stock_data (DataFrame): Stock price history data
            
        Returns:
            dict: Volume data formatted for Chart.js
        """
        if stock_data.empty or 'Volume' not in stock_data.columns:
            return {
                "labels": [],
                "datasets": []
            }
            
        try:
            # Convert dates to string format for Chart.js
            date_labels = stock_data['Date'].dt.strftime('%Y-%m-%d').tolist()
            
            # Prepare volume data
            volume_data = {
                "labels": date_labels,
                "datasets": [
                    {
                        "label": "Volume",
                        "data": stock_data['Volume'].tolist(),
                        "backgroundColor": "rgba(153, 102, 255, 0.5)",
                        "borderColor": "rgba(153, 102, 255, 1)",
                        "borderWidth": 1
                    }
                ]
            }
            
            return volume_data
        except Exception as e:
            logger.error(f"Error preparing volume data: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }
            
    def prepare_sentiment_distribution_data(self, sentiment_results):
        """
        Prepare sentiment distribution data for Chart.js
        
        Args:
            sentiment_results (dict): Sentiment analysis results
            
        Returns:
            dict: Sentiment distribution data formatted for Chart.js
        """
        if not sentiment_results or 'sentiment_distribution' not in sentiment_results:
            return {
                "labels": [],
                "datasets": []
            }
            
        try:
            distribution = sentiment_results['sentiment_distribution']
            
            # Prepare sentiment distribution data for doughnut/pie chart
            sentiment_data = {
                "labels": ["Positive", "Neutral", "Negative"],
                "datasets": [
                    {
                        "data": [
                            distribution.get('positive', 0) * 100,
                            distribution.get('neutral', 0) * 100,
                            distribution.get('negative', 0) * 100
                        ],
                        "backgroundColor": [
                            "rgba(75, 192, 192, 0.7)",
                            "rgba(201, 203, 207, 0.7)",
                            "rgba(255, 99, 132, 0.7)"
                        ],
                        "borderColor": [
                            "rgba(75, 192, 192, 1)",
                            "rgba(201, 203, 207, 1)",
                            "rgba(255, 99, 132, 1)"
                        ],
                        "borderWidth": 1
                    }
                ]
            }
            
            return sentiment_data
        except Exception as e:
            logger.error(f"Error preparing sentiment distribution data: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }
            
    def prepare_market_movers_data(self, gainers_df, losers_df, limit=10):
        """
        Prepare market movers data for Chart.js
        
        Args:
            gainers_df (DataFrame): Top gainers data
            losers_df (DataFrame): Top losers data
            limit (int): Number of stocks to include
            
        Returns:
            dict: Market movers data formatted for Chart.js
        """
        if gainers_df.empty and losers_df.empty:
            return {
                "labels": [],
                "datasets": []
            }
            
        try:
            # Process gainers data
            top_gainers = gainers_df.head(limit) if not gainers_df.empty else pd.DataFrame()
            # Process losers data
            top_losers = losers_df.head(limit) if not losers_df.empty else pd.DataFrame()
            
            # Prepare labels and data arrays
            gainer_labels = []
            gainer_values = []
            loser_labels = []
            loser_values = []
            
            if not top_gainers.empty and 'Company' in top_gainers.columns and 'Change (%)' in top_gainers.columns:
                gainer_labels = top_gainers['Company'].tolist()
                gainer_values = top_gainers['Change (%)'].tolist()
                
            if not top_losers.empty and 'Company' in top_losers.columns and 'Change (%)' in top_losers.columns:
                loser_labels = top_losers['Company'].tolist()
                loser_values = top_losers['Change (%)'].tolist()
            
            # Prepare market movers data for horizontal bar chart
            movers_data = {
                "labels": gainer_labels + loser_labels,
                "datasets": [
                    {
                        "label": "Price Change (%)",
                        "data": gainer_values + loser_values,
                        "backgroundColor": [
                            "rgba(75, 192, 192, 0.7)" if val >= 0 else "rgba(255, 99, 132, 0.7)"
                            for val in gainer_values + loser_values
                        ],
                        "borderColor": [
                            "rgba(75, 192, 192, 1)" if val >= 0 else "rgba(255, 99, 132, 1)"
                            for val in gainer_values + loser_values
                        ],
                        "borderWidth": 1
                    }
                ]
            }
            
            return movers_data
        except Exception as e:
            logger.error(f"Error preparing market movers data: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }
            
    def prepare_sentiment_timeline_data(self, headlines):
        """
        Prepare sentiment timeline data for Chart.js
        
        Args:
            headlines (list): List of headlines with sentiment data
            
        Returns:
            dict: Sentiment timeline data formatted for Chart.js
        """
        if not headlines:
            return {
                "labels": [],
                "datasets": []
            }
            
        try:
            # Sort headlines by date
            sorted_headlines = sorted(headlines, key=lambda x: x.get('published_at', ''))
            
            # Group by date
            from collections import defaultdict
            sentiment_by_date = defaultdict(lambda: {'positive': 0, 'neutral': 0, 'negative': 0, 'count': 0})
            
            for headline in sorted_headlines:
                # Skip if no published date
                if not headline.get('published_at'):
                    continue
                    
                # Convert to date string (YYYY-MM-DD)
                date_str = headline['published_at'].split('T')[0] if isinstance(headline['published_at'], str) else ""
                if not date_str:
                    continue
                
                # Update counts
                sentiment = headline.get('sentiment', 'neutral')
                sentiment_by_date[date_str][sentiment] += 1
                sentiment_by_date[date_str]['count'] += 1
            
            # Convert to arrays for Chart.js
            dates = list(sentiment_by_date.keys())
            positive_pcts = [sentiment_by_date[d]['positive'] / sentiment_by_date[d]['count'] * 100 for d in dates]
            neutral_pcts = [sentiment_by_date[d]['neutral'] / sentiment_by_date[d]['count'] * 100 for d in dates]
            negative_pcts = [sentiment_by_date[d]['negative'] / sentiment_by_date[d]['count'] * 100 for d in dates]
            
            # Prepare sentiment timeline data for line chart
            timeline_data = {
                "labels": dates,
                "datasets": [
                    {
                        "label": "Positive",
                        "data": positive_pcts,
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "borderWidth": 2,
                        "fill": False
                    },
                    {
                        "label": "Neutral",
                        "data": neutral_pcts,
                        "borderColor": "rgba(201, 203, 207, 1)",
                        "backgroundColor": "rgba(201, 203, 207, 0.2)",
                        "borderWidth": 2,
                        "fill": False
                    },
                    {
                        "label": "Negative",
                        "data": negative_pcts,
                        "borderColor": "rgba(255, 99, 132, 1)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "borderWidth": 2,
                        "fill": False
                    }
                ]
            }
            
            return timeline_data
        except Exception as e:
            logger.error(f"Error preparing sentiment timeline data: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }