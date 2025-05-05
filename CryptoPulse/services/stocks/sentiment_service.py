import pandas as pd
import logging
from services.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class StockSentimentService:
    """Service for performing sentiment analysis on stock market news"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        
    def analyze_headlines(self, news_df):
        """
        Analyze sentiment of news headlines
        
        Args:
            news_df (DataFrame): Dataframe containing news headlines
            
        Returns:
            dict: Sentiment analysis results
        """
        if news_df.empty or 'Headline' not in news_df.columns:
            return {
                'sentiment_counts': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'sentiment_distribution': {
                    'positive': 0,
                    'neutral': 1,  # Default to neutral if no data
                    'negative': 0
                },
                'sentiment_scores': {
                    'compound': 0,
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'headlines_analyzed': 0,
                'overall_sentiment': 'neutral',
                'analyzed_headlines': []
            }
        
        # Get headlines
        headlines = news_df['Headline'].tolist()
        
        # Analyze each headline
        analyzed_headlines = []
        sentiment_counts = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        total_compound = 0
        
        for idx, headline in enumerate(headlines):
            try:
                # Analyze sentiment
                result = self.sentiment_analyzer.analyze_text(headline)
                
                # Add to counts
                sentiment = result.get('sentiment', 'neutral')
                sentiment_counts[sentiment] += 1
                
                # Add to total compound score
                total_compound += result.get('scores', {}).get('compound', 0)
                
                # Add analyzed headline
                analyzed_headline = {
                    'headline': headline,
                    'sentiment': sentiment,
                    'compound_score': result.get('scores', {}).get('compound', 0),
                    'published_at': news_df['PublishedAt'].iloc[idx] if 'PublishedAt' in news_df.columns else None,
                    'company': news_df['Company'].iloc[idx] if 'Company' in news_df.columns else None,
                    'source': news_df['Source'].iloc[idx] if 'Source' in news_df.columns else None
                }
                
                analyzed_headlines.append(analyzed_headline)
            except Exception as e:
                logger.error(f"Error analyzing headline: {str(e)}")
        
        # Calculate sentiment distribution
        total_headlines = len(analyzed_headlines)
        sentiment_distribution = {
            'positive': sentiment_counts['positive'] / total_headlines if total_headlines > 0 else 0,
            'neutral': sentiment_counts['neutral'] / total_headlines if total_headlines > 0 else 0,
            'negative': sentiment_counts['negative'] / total_headlines if total_headlines > 0 else 0
        }
        
        # Calculate overall sentiment scores
        avg_compound = total_compound / total_headlines if total_headlines > 0 else 0
        
        # Determine overall sentiment
        overall_sentiment = 'neutral'
        if avg_compound >= 0.05:
            overall_sentiment = 'positive'
        elif avg_compound <= -0.05:
            overall_sentiment = 'negative'
        
        # Create more specific sentiment label
        if avg_compound >= 0.5:
            overall_sentiment = 'very_positive'
        elif avg_compound >= 0.2:
            overall_sentiment = 'positive'
        elif avg_compound >= 0.05:
            overall_sentiment = 'slightly_positive'
        elif avg_compound <= -0.5:
            overall_sentiment = 'very_negative'
        elif avg_compound <= -0.2:
            overall_sentiment = 'negative'
        elif avg_compound <= -0.05:
            overall_sentiment = 'slightly_negative'
        
        # Return results
        return {
            'sentiment_counts': sentiment_counts,
            'sentiment_distribution': sentiment_distribution,
            'sentiment_scores': {
                'compound': avg_compound,
                'positive': sentiment_distribution['positive'],
                'neutral': sentiment_distribution['neutral'],
                'negative': sentiment_distribution['negative']
            },
            'headlines_analyzed': total_headlines,
            'overall_sentiment': overall_sentiment,
            'analyzed_headlines': analyzed_headlines
        }
    
    def analyze_company_sentiment(self, company, news_df=None):
        """
        Analyze sentiment for a specific company
        
        Args:
            company (str): Company name
            news_df (DataFrame): Optional dataframe with news data
            
        Returns:
            dict: Sentiment analysis for the company
        """
        try:
            from services.stocks.data_service import StocksDataService
            
            # If news data not provided, load from service
            if news_df is None:
                data_service = StocksDataService()
                news_df = data_service.get_stock_news(company, limit=50)
            
            # Analyze headlines
            results = self.analyze_headlines(news_df)
            
            # Add company info
            results['company'] = company
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing company sentiment: {str(e)}")
            return {
                'error': str(e),
                'company': company,
                'sentiment_counts': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'sentiment_distribution': {
                    'positive': 0,
                    'neutral': 1,
                    'negative': 0
                },
                'overall_sentiment': 'neutral'
            }
    
    def analyze_market_sentiment(self, news_df=None, max_headlines=100):
        """
        Analyze overall market sentiment
        
        Args:
            news_df (DataFrame): Optional dataframe with news data
            max_headlines (int): Maximum number of headlines to analyze
            
        Returns:
            dict: Overall market sentiment analysis
        """
        try:
            from services.stocks.data_service import StocksDataService
            
            # If news data not provided, load from service
            if news_df is None:
                data_service = StocksDataService()
                news_df = data_service.get_stock_news(limit=max_headlines)
            
            # Analyze headlines
            results = self.analyze_headlines(news_df)
            
            # Add market info
            results['market'] = 'overall'
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {str(e)}")
            return {
                'error': str(e),
                'market': 'overall',
                'sentiment_counts': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'sentiment_distribution': {
                    'positive': 0,
                    'neutral': 1,
                    'negative': 0
                },
                'overall_sentiment': 'neutral'
            }
    
    def analyze_stock_news_impact(self, symbol, news_df=None):
        """
        Analyze news sentiment impact on stock price
        
        Args:
            symbol (str): Stock symbol
            news_df (DataFrame): Optional dataframe with news data
            
        Returns:
            dict: Analysis of news sentiment impact
        """
        try:
            from services.stocks.data_service import StocksDataService
            
            # Load data service
            data_service = StocksDataService()
            
            # Get stock data
            stock_data = data_service.get_stock_price_history(symbol, days=30)
            
            # If no data available, return error
            if stock_data.empty:
                return {
                    'error': 'No stock data available',
                    'symbol': symbol
                }
            
            # Get company name from symbol (simplified approach)
            company = symbol.split('.')[0] if '.' in symbol else symbol
            
            # If news data not provided, load from service
            if news_df is None:
                news_df = data_service.get_stock_news(company, limit=30)
            
            # If no news available, return error
            if news_df.empty:
                return {
                    'error': 'No news data available',
                    'symbol': symbol,
                    'company': company
                }
            
            # Analyze news sentiment
            sentiment_results = self.analyze_headlines(news_df)
            
            # Calculate price change
            if len(stock_data) >= 2:
                start_price = stock_data.iloc[0]['Close']
                end_price = stock_data.iloc[-1]['Close']
                price_change = ((end_price - start_price) / start_price) * 100
            else:
                price_change = 0
            
            # Determine sentiment-price correlation
            sentiment_score = sentiment_results.get('sentiment_scores', {}).get('compound', 0)
            
            correlation = 'aligned'
            if (sentiment_score > 0 and price_change > 0) or (sentiment_score < 0 and price_change < 0):
                correlation = 'aligned'
            else:
                correlation = 'divergent'
            
            # Return results
            return {
                'symbol': symbol,
                'company': company,
                'price_change': price_change,
                'sentiment_score': sentiment_score,
                'correlation': correlation,
                'sentiment_analysis': sentiment_results
            }
        except Exception as e:
            logger.error(f"Error analyzing news impact: {str(e)}")
            return {
                'error': str(e),
                'symbol': symbol
            }