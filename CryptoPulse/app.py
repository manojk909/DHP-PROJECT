import os
import logging
from flask import Flask, jsonify, request, send_from_directory, send_file
from services.coin_gecko import CoinGeckoService
from services.reddit_service import RedditService
from services.sentiment_analyzer import SentimentAnalyzer
from utils.analysis import PriceAnalyzer
from services.stocks.data_service import StocksDataService
from services.stocks.sentiment_service import StockSentimentService
from services.stocks.visualization_service import StockVisualizationService

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize services
coin_gecko_service = CoinGeckoService()
reddit_service = RedditService()
sentiment_analyzer = SentimentAnalyzer()
price_analyzer = PriceAnalyzer()
stocks_data_service = StocksDataService()
stock_sentiment_service = StockSentimentService()
stock_visualization_service = StockVisualizationService()

import math

def sanitize_for_json(data):
    if isinstance(data, float) and math.isnan(data):
        return None
    elif isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(v) for v in data]
    return data

# Page routes
@app.route('/')
def index():
    return send_file('static/html/index.html')

@app.route('/analysis')
def analysis():
    return send_file('static/html/analysis.html')

@app.route('/comparison')
def comparison():
    return send_file('static/html/comparison.html')

@app.route('/sentiment')
def sentiment():
    return send_file('static/html/sentiment.html')

# Serve static files
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('static/js', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('static/css', filename)

# API Routes
@app.route('/api/cryptocurrencies', methods=['GET'])
def get_cryptocurrencies():
    """Get list of top cryptocurrencies by market cap"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        cryptocurrencies = coin_gecko_service.get_top_cryptocurrencies(limit)
        return jsonify(cryptocurrencies)
    except Exception as e:
        logger.error(f"Error fetching cryptocurrencies: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cryptocurrency/<coin_id>', methods=['GET'])
def get_cryptocurrency(coin_id):
    """Get details for a specific cryptocurrency"""
    try:
        cryptocurrency = coin_gecko_service.get_cryptocurrency_details(coin_id)
        return jsonify(cryptocurrency)
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cryptocurrency/<coin_id>/price-history', methods=['GET'])
def get_price_history(coin_id):
    """Get historical price data for a cryptocurrency"""
    try:
        days = request.args.get('days', default=30, type=int)
        price_history = coin_gecko_service.get_price_history(coin_id, days)
        return jsonify(price_history)
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/price-correlation', methods=['GET'])
def get_price_correlation():
    """Get price correlation data for multiple cryptocurrencies"""
    try:
        # Get coin IDs from query parameters (comma-separated)
        coin_ids = request.args.get('coins', '')
        days = request.args.get('days', default=30, type=int)
        
        if not coin_ids:
            return jsonify({"error": "No coins specified"}), 400
            
        # Split the comma-separated list
        coin_id_list = coin_ids.split(',')
        
        if len(coin_id_list) < 2:
            return jsonify({"error": "At least two coins are required for correlation"}), 400
        
        # Check if we've hit rate limits
        hit_rate_limit = False    
            
        # Get price history for each coin
        price_data = {}
        for coin_id in coin_id_list:
            try:
                price_history = coin_gecko_service.get_price_history(coin_id, days)
                # Extract just the prices (we need same length arrays for correlation)
                prices = [point[1] for point in price_history.get('prices', [])]
                if prices:
                    price_data[coin_id] = prices
                else:
                    # Handle case where prices list is empty
                    hit_rate_limit = True
                    logger.warning(f"No price data available for {coin_id}")
            except Exception as coin_error:
                hit_rate_limit = True
                logger.warning(f"Could not get price history for {coin_id}: {str(coin_error)}")
        
        # Generate demo data if we've hit rate limits or couldn't get real data
        if hit_rate_limit or len(price_data) < 2:
            price_data, coin_details = generate_demo_correlation_data(coin_id_list, days)
            
            # Calculate correlations between all pairs
            correlation_matrix = {}
            import numpy as np
            
            for coin1 in price_data.keys():
                correlation_matrix[coin1] = {}
                for coin2 in price_data.keys():
                    if coin1 == coin2:
                        # Perfect correlation with self
                        correlation_matrix[coin1][coin2] = 1.0
                    else:
                        # For demo data, generate a correlation value that's realistic
                        # Most crypto pairs have moderate to high positive correlation
                        # BTC and major coins: high correlation (0.7-0.9)
                        # Stablecoins with other coins: low correlation (0-0.3)
                        # Some pairs have negative correlation (e.g., inverse tokens)
                        
                        # Use consistent correlation values for the same pairs
                        seed = hash(f"{coin1}-{coin2}") % 1000 / 1000.0
                        
                        if "tether" in coin1 or "tether" in coin2 or "usdc" in coin1 or "usdc" in coin2:
                            # Stablecoins have low correlation with other coins
                            correlation = seed * 0.3  # 0 to 0.3
                        elif "bitcoin" in coin1 and "ethereum" in coin2 or "bitcoin" in coin2 and "ethereum" in coin1:
                            # BTC and ETH have high correlation
                            correlation = 0.7 + seed * 0.2  # 0.7 to 0.9
                        else:
                            # Other pairs have moderate correlation
                            correlation = 0.3 + seed * 0.4  # 0.3 to 0.7
                        
                        correlation_matrix[coin1][coin2] = float(correlation)
                        # Make sure the matrix is symmetric
                        correlation_matrix.setdefault(coin2, {})[coin1] = float(correlation)
            
            return jsonify({
                'correlation_matrix': correlation_matrix,
                'coin_details': coin_details,
                'days': days,
                'demo_data': True
            })
        
        # Make sure we have enough data
        if len(price_data) < 2:
            return jsonify({"error": "Could not get price data for at least two coins"}), 500
            
        # Calculate correlation matrix
        correlation_matrix = {}
        
        # Get coin details for names
        coin_details = {}
        for coin_id in price_data.keys():
            try:
                details = coin_gecko_service.get_cryptocurrency_details(coin_id)
                coin_details[coin_id] = {
                    'name': details.get('name', coin_id),
                    'symbol': details.get('symbol', coin_id).upper()
                }
            except:
                # Use basic details if API fails
                symbol = coin_id[:4].upper() if len(coin_id) > 3 else coin_id.upper()
                name = coin_id.title()
                coin_details[coin_id] = {
                    'name': name,
                    'symbol': symbol
                }
        
        # Calculate correlations between all pairs
        import numpy as np
        
        for coin1 in price_data.keys():
            correlation_matrix[coin1] = {}
            for coin2 in price_data.keys():
                # Use numpy to calculate correlation
                try:
                    # Make sure arrays are of the same length
                    min_length = min(len(price_data[coin1]), len(price_data[coin2]))
                    if min_length > 0:
                        data1 = np.array(price_data[coin1][-min_length:])
                        data2 = np.array(price_data[coin2][-min_length:])
                        correlation = np.corrcoef(data1, data2)[0, 1]
                        correlation_matrix[coin1][coin2] = float(correlation)
                    else:
                        correlation_matrix[coin1][coin2] = 1.0 if coin1 == coin2 else 0
                except Exception as corr_error:
                    logger.warning(f"Error calculating correlation between {coin1} and {coin2}: {str(corr_error)}")
                    correlation_matrix[coin1][coin2] = 1.0 if coin1 == coin2 else 0
        
        return jsonify({
            'correlation_matrix': correlation_matrix,
            'coin_details': coin_details,
            'days': days
        })
    except Exception as e:
        logger.error(f"Error calculating price correlation: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
def generate_demo_correlation_data(coin_id_list, days):
    """Generate demo data for correlation analysis when hitting API rate limits"""
    import numpy as np
    import random
    
    # Set the random seed for reproducible results
    random.seed(42)
    np.random.seed(42)
    
    price_data = {}
    coin_details = {}
    
    # Create a mapping for known coins
    known_coins = {
        "bitcoin": {"name": "Bitcoin", "symbol": "BTC"},
        "ethereum": {"name": "Ethereum", "symbol": "ETH"},
        "tether": {"name": "Tether", "symbol": "USDT"},
        "usd-coin": {"name": "USD Coin", "symbol": "USDC"},
        "binancecoin": {"name": "BNB", "symbol": "BNB"},
        "ripple": {"name": "XRP", "symbol": "XRP"},
        "solana": {"name": "Solana", "symbol": "SOL"},
        "cardano": {"name": "Cardano", "symbol": "ADA"},
        "dogecoin": {"name": "Dogecoin", "symbol": "DOGE"},
        "avalanche-2": {"name": "Avalanche", "symbol": "AVAX"},
        "polkadot": {"name": "Polkadot", "symbol": "DOT"},
        "matic-network": {"name": "Polygon", "symbol": "MATIC"},
        "litecoin": {"name": "Litecoin", "symbol": "LTC"}
    }
    
    # Generate data for each coin
    for coin_id in coin_id_list:
        # Get or create coin details
        if coin_id in known_coins:
            coin_details[coin_id] = known_coins[coin_id]
        else:
            # If the coin isn't in our list, create a sensible default
            symbol = coin_id[:4].upper() if len(coin_id) > 3 else coin_id.upper()
            name = coin_id.title()
            coin_details[coin_id] = {
                "name": name,
                "symbol": symbol
            }
        
        # Generate price history with reasonable patterns
        # Start with a base price depending on the coin
        if coin_id == "bitcoin":
            base_price = 50000
        elif coin_id == "ethereum":
            base_price = 3000
        elif coin_id in ["tether", "usd-coin"]:
            base_price = 1
        elif coin_id in ["ripple", "dogecoin"]:
            base_price = 0.5
        else:
            # Random base price for other coins
            base_price = random.uniform(0.1, 1000)
        
        # Create a series of prices with a slight upward or downward trend
        # Add some randomness to simulate real price movements
        trend = random.uniform(-0.01, 0.01)  # Daily trend, -1% to 1%
        
        # Generate 100 days of data regardless of requested days
        # This provides enough data for correlation calculation
        num_data_points = 100
        
        # Start with the base price
        prices = [base_price]
        
        # For stablecoins, keep the price very stable around 1
        if coin_id in ["tether", "usd-coin"]:
            for _ in range(num_data_points - 1):
                last_price = prices[-1]
                # Very small random changes for stablecoins (±0.5%)
                change = last_price * random.uniform(-0.005, 0.005)
                new_price = max(0.95, min(1.05, last_price + change))
                prices.append(new_price)
        else:
            # For regular coins, follow trends and add some volatility
            for _ in range(num_data_points - 1):
                last_price = prices[-1]
                # Daily change combines trend and random volatility
                change_percent = trend + random.uniform(-0.03, 0.03)  # Daily volatility, -3% to 3%
                change = last_price * change_percent
                new_price = max(0.01, last_price + change)  # Prevent prices from going too low
                prices.append(new_price)
        
        # Store the price data
        price_data[coin_id] = prices
    
    return price_data, coin_details

@app.route('/api/cryptocurrency/<coin_id>/analysis', methods=['GET'])
def get_price_analysis(coin_id):
    """Get price analysis for a cryptocurrency"""
    try:
        days = request.args.get('days', default=30, type=int)
        price_history = coin_gecko_service.get_price_history(coin_id, days)
        analysis = price_analyzer.analyze(price_history)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing price data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reddit/sentiment', methods=['GET'])
def get_reddit_sentiment():
    """Get Reddit sentiment analysis for a cryptocurrency or search term"""
    try:
        query = request.args.get('query', default=None)
        subreddit = request.args.get('subreddit', default='cryptocurrency')
        limit = request.args.get('limit', default=100, type=int)
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        # Check if Reddit API credentials are available
        if not reddit_service.client_id or not reddit_service.client_secret:
            error_message = "Reddit API credentials are not configured. This feature requires Reddit API credentials."
            logger.error(error_message)
            return jsonify({
                "error": error_message,
                "missing_credentials": True,
                "needs_configuration": True,
                "instructions": [
                    "Register a Reddit app at https://www.reddit.com/prefs/apps",
                    "Create an application of type 'script'",
                    "Add the Client ID and Client Secret to your environment variables as REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET"
                ],
                "credential_keys": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
            }), 401
            
        posts = reddit_service.get_posts(subreddit, query, limit)
        sentiment_results = sentiment_analyzer.analyze_posts(posts)
        
        return jsonify(sentiment_results)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error performing Reddit sentiment analysis: {error_message}")
        
        # Check if it's a credentials error
        if "Reddit API credentials are missing" in error_message:
            return jsonify({
                "error": "Reddit API credentials are not configured. This feature requires Reddit API credentials.",
                "missing_credentials": True,
                "needs_configuration": True,
                "instructions": [
                    "Register a Reddit app at https://www.reddit.com/prefs/apps",
                    "Create an application of type 'script'",
                    "Add the Client ID and Client Secret to your environment variables as REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET"
                ],
                "credential_keys": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
            }), 401
        
        # Return a proper error response for other errors
        return jsonify({
            "error": f"Error performing sentiment analysis: {error_message}",
            "status": "error"
        }), 500

@app.route('/api/text/sentiment', methods=['POST'])
def analyze_text_sentiment():
    """Analyze sentiment of a provided text"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
            
        sentiment_result = sentiment_analyzer.analyze_text(text)
        
        # Ensure we have all required fields in the sentiment result
        for key in ['compound', 'positive', 'neutral', 'negative', 'sentiment']:
            if key not in sentiment_result:
                sentiment_result[key] = 0 if key != 'sentiment' else 'neutral'
                
        return jsonify(sentiment_result)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error analyzing text sentiment: {error_message}")
        return jsonify({
            "error": f"Error analyzing text sentiment: {error_message}",
            "status": "error"
        }), 500

@app.route('/api/market-overview', methods=['GET'])
def get_market_overview():
    """Get overall cryptocurrency market overview"""
    try:
        market_data = coin_gecko_service.get_market_overview()
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Error fetching market overview: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trending', methods=['GET'])
def get_trending():
    """Get trending cryptocurrencies"""
    try:
        trending_data = coin_gecko_service.get_trending()
        return jsonify(trending_data)
    except Exception as e:
        logger.error(f"Error fetching trending cryptocurrencies: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/market/movers', methods=['GET'])
def get_market_movers():
    """Get top gainers and losers in the cryptocurrency market"""
    try:
        limit = request.args.get('limit', default=5, type=int)
        movers = coin_gecko_service.get_market_movers(limit)
        return jsonify(movers)
    except Exception as e:
        logger.error(f"Error fetching market movers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ask-for-secrets', methods=['POST'])
def ask_for_secrets():
    """Ask the user to provide secrets (API credentials)"""
    try:
        data = request.json
        keys = data.get('keys', [])
        message = data.get('message', 'API credentials are required')
        
        logger.info(f"User requested to add API credentials: {keys}")
        
        # Use the ask_secrets tool if it's available
        try:
            from ask_secrets import ask_secrets
            
            if ask_secrets(keys, message):
                logger.info("User provided API credentials")
                return jsonify({
                    "success": True,
                    "message": "API credentials have been added successfully."
                })
            else:
                logger.warning("Failed to get API credentials from user")
                return jsonify({
                    "success": False,
                    "message": "Could not obtain API credentials."
                })
        except ImportError:
            # If we can't import ask_secrets, it's probably not available in this environment
            logger.warning("ask_secrets module not available")
            return jsonify({
                "success": False,
                "message": "Please add the following environment variables to use this feature: " + ", ".join(keys)
            })
        except Exception as inner_e:
            logger.error(f"Error using ask_secrets: {str(inner_e)}")
            # Fall back to returning instructions
            return jsonify({
                "success": False,
                "message": "Please add the following environment variables to use this feature: " + ", ".join(keys)
            })
    except Exception as e:
        logger.error(f"Error asking for secrets: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/check-credentials', methods=['POST'])
def check_credentials():
    """Check if specified credentials are available"""
    try:
        data = request.json
        keys = data.get('keys', [])
        
        results = {}
        for key in keys:
            results[key] = key in os.environ and os.environ[key] != ""
            
        return jsonify({
            "results": results,
            "all_available": all(results.values())
        })
    except Exception as e:
        logger.error(f"Error checking credentials: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Stock Market API Routes
@app.route('/stocks', methods=['GET'])
def stocks_page():
    """Stock market analysis page"""
    return send_file('static/html/stocks.html')

@app.route('/api/stocks/symbols', methods=['GET'])
def get_stock_symbols():
    """Get list of available stock symbols"""
    try:
        symbols = stocks_data_service.get_available_symbols()
        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Error fetching stock symbols: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/price-history/<symbol>', methods=['GET'])
def get_stock_price_history(symbol):
    """Get historical price data for a specific stock"""
    try:
        days = request.args.get('days', default=30, type=int)
        price_history = stocks_data_service.get_stock_price_history(symbol, days)
        
        # Convert to JSON-serializable format
        data = {
            'symbol': symbol,
            'data': price_history.to_dict(orient='records')
        }
        sanitized = sanitize_for_json(data)
        
        return jsonify(sanitized)
    except Exception as e:
        logger.error(f"Error fetching stock price history: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/stocks/analysis/<symbol>', methods=['GET'])
def get_stock_analysis(symbol):
    """Get analysis for a specific stock"""
    try:
        analysis = stocks_data_service.get_stock_analysis(symbol)
        sanitized = sanitize_for_json(analysis)
        return jsonify(sanitized)
    except Exception as e:
        logger.error(f"Error analyzing stock: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/stocks/movers', methods=['GET'])
def get_stock_movers():
    """Get top gainers and losers"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        gainers = stocks_data_service.get_top_gainers(limit)
        losers = stocks_data_service.get_top_losers(limit)
        
        # Convert to JSON-serializable format
        data = {
            'gainers': gainers.to_dict(orient='records'),
            'losers': losers.to_dict(orient='records')
        }
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching stock movers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/news', methods=['GET'])
def get_stock_news():
    """Get stock market news"""
    try:
        company = request.args.get('company', default=None)
        limit = request.args.get('limit', default=20, type=int)
        
        news = stocks_data_service.get_stock_news(company, limit)
        
        # Convert to JSON-serializable format
        data = {
            'news': news.to_dict(orient='records')
        }
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching stock news: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/sentiment', methods=['GET'])
def get_stock_sentiment():
    """Get sentiment analysis for stock market or specific company"""
    try:
        company = request.args.get('company', default=None)
        
        if company:
            # Get sentiment for specific company
            sentiment_results = stock_sentiment_service.analyze_company_sentiment(company)
        else:
            # Get overall market sentiment
            sentiment_results = stock_sentiment_service.analyze_market_sentiment()
            
        return jsonify(sentiment_results)
    except Exception as e:
        logger.error(f"Error analyzing stock sentiment: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/charts/price/<symbol>', methods=['GET'])
def get_stock_price_chart(symbol):
    """Get price chart data for a specific stock"""
    try:
        days = request.args.get('days', default=30, type=int)
        
        # Get price history
        price_history = stocks_data_service.get_stock_price_history(symbol, days)
        
        # Get stock analysis for moving averages
        analysis = stocks_data_service.get_stock_analysis(symbol)
        
        # Prepare chart data
        chart_data = stock_visualization_service.prepare_price_history_data(price_history)
        
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error preparing stock price chart: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/charts/volume/<symbol>', methods=['GET'])
def get_stock_volume_chart(symbol):
    """Get volume chart data for a specific stock"""
    try:
        days = request.args.get('days', default=30, type=int)
        
        # Get price history (which includes volume)
        price_history = stocks_data_service.get_stock_price_history(symbol, days)
        
        # Prepare chart data
        chart_data = stock_visualization_service.prepare_volume_data(price_history)
        
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error preparing stock volume chart: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/charts/sentiment', methods=['GET'])
def get_stock_sentiment_chart():
    """Get sentiment distribution chart data"""
    try:
        company = request.args.get('company', default=None)
        
        if company:
            # Get sentiment for specific company
            sentiment_results = stock_sentiment_service.analyze_company_sentiment(company)
        else:
            # Get overall market sentiment
            sentiment_results = stock_sentiment_service.analyze_market_sentiment()
            
        # Prepare chart data
        chart_data = stock_visualization_service.prepare_sentiment_distribution_data(sentiment_results)
        
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error preparing sentiment chart: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/charts/movers', methods=['GET'])
def get_stock_movers_chart():
    """Get market movers chart data"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        # Get top gainers and losers
        gainers = stocks_data_service.get_top_gainers(limit)
        losers = stocks_data_service.get_top_losers(limit)
        
        # Prepare chart data
        chart_data = stock_visualization_service.prepare_market_movers_data(gainers, losers, limit)
        
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Error preparing market movers chart: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
