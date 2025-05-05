import nltk
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Service for performing sentiment analysis on text content"""
    
    def __init__(self):
        # Download NLTK resources if not already downloaded
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
        
        # Initialize VADER sentiment analyzer
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Add crypto-specific terms to the lexicon
        self._add_crypto_specific_terms()
    
    def analyze_text(self, text):
        """
        Analyze sentiment of a single text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Sentiment scores and classification
        """
        if not text or text.strip() == "":
            return {
                "compound": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "sentiment": "neutral",
                "sentences": [],
                "explanation": "No text provided"
            }
        
        # Split text into sentences (simple split by period, question and exclamation marks)
        # This is a basic approach - in a production environment, consider using a more robust
        # sentence tokenizer from NLTK or other NLP libraries
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        # Analyze each sentence 
        sentence_analysis = []
        for sentence in sentences:
            if sentence.strip():
                sent_scores = self.analyzer.polarity_scores(sentence)
                
                # Determine sentiment for this sentence
                sent_compound = sent_scores['compound']
                if sent_compound >= 0.05:
                    sent_sentiment = "positive"
                elif sent_compound <= -0.05:
                    sent_sentiment = "negative"
                else:
                    sent_sentiment = "neutral"
                
                sentence_analysis.append({
                    "text": sentence,
                    "compound": sent_scores['compound'],
                    "sentiment": sent_sentiment
                })
                
        # Analyze full text
        full_scores = self.analyzer.polarity_scores(text)
        
        # Determine overall sentiment classification
        compound = full_scores['compound']
        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Generate a simple explanation
        explanation = self._generate_sentiment_explanation(full_scores, sentiment, sentence_analysis)
            
        return {
            "compound": full_scores['compound'],
            "positive": full_scores['pos'],
            "neutral": full_scores['neu'],
            "negative": full_scores['neg'],
            "sentiment": sentiment,
            "sentences": sentence_analysis,
            "explanation": explanation
        }
        
    def _generate_sentiment_explanation(self, scores, sentiment, sentence_analysis):
        """Generate a human-readable explanation of sentiment analysis"""
        
        # Count sentiment distribution in sentences
        sentence_sentiments = {"positive": 0, "neutral": 0, "negative": 0}
        for sent in sentence_analysis:
            sentiment_key = sent.get("sentiment", "neutral")
            # Make sure the key is valid
            if sentiment_key not in sentence_sentiments:
                sentiment_key = "neutral"
            sentence_sentiments[sentiment_key] += 1
            
        # Create explanation based on overall sentiment
        if sentiment == "positive":
            if scores.get("pos", 0) > 0.6:
                intensity = "very positive"
            else:
                intensity = "somewhat positive"
                
            explanation = f"This text is {intensity}"
            
            # Add crypto-specific context if applicable
            if scores.get("pos", 0) > 0.4 and len(sentence_analysis) > 0:
                explanation += f", with {sentence_sentiments['positive']} positive statement(s)"
                if sentence_sentiments["negative"] > 0:
                    explanation += f" and {sentence_sentiments['negative']} negative statement(s)"
            
        elif sentiment == "negative":
            if scores.get("neg", 0) > 0.6:
                intensity = "very negative"
            else:
                intensity = "somewhat negative"
                
            explanation = f"This text is {intensity}"
            
            # Add crypto-specific context if applicable
            if scores.get("neg", 0) > 0.4 and len(sentence_analysis) > 0:
                explanation += f", with {sentence_sentiments['negative']} negative statement(s)"
                if sentence_sentiments["positive"] > 0:
                    explanation += f" and {sentence_sentiments['positive']} positive statement(s)"
                    
        else:  # neutral
            explanation = "This text is neutral"
            if len(sentence_analysis) > 1:
                explanation += f", with a mix of {sentence_sentiments['positive']} positive, {sentence_sentiments['negative']} negative, and {sentence_sentiments['neutral']} neutral statements"
            
        explanation += "."
        return explanation
    
    def _add_crypto_specific_terms(self):
        """
        Add cryptocurrency-specific terminology to the VADER lexicon
        with appropriate sentiment scores
        """
        # Positive crypto terms
        crypto_positive = {
            'bullish': 3.0,
            'bull market': 3.0,
            'bull run': 3.0,
            'hodl': 1.8,
            'to the moon': 3.5,
            'mooning': 3.2,
            'diamond hands': 2.5,
            'green candle': 2.0,
            'all time high': 2.8,
            'ath': 2.5,
            'dca': 1.5,  # Dollar-cost averaging is generally seen as positive
            'staking': 1.8,
            'yield farming': 1.5,
            'airdrop': 2.0,
            'fomo': 0.5,  # Fear of missing out - slightly positive in crypto context
            'altseason': 2.0,
            'nft boom': 2.2,
            'metaverse': 1.2,
            'web3': 1.5,
            'defi': 1.5
        }
        
        # Negative crypto terms
        crypto_negative = {
            'bearish': -3.0,
            'bear market': -3.0,
            'bear trap': -2.0,
            'paper hands': -2.0,
            'panic sell': -3.0,
            'red candle': -2.0,
            'rug pull': -4.0,
            'pump and dump': -3.5,
            'ponzi': -4.0,
            'scamcoin': -4.0,
            'shitcoin': -3.0,
            'bagholder': -2.0,
            'dead cat bounce': -1.5,
            'fud': -2.5,  # Fear, uncertainty, doubt
            'rekt': -3.5,
            'dumping': -2.5,
            'flash crash': -3.0,
            'correction': -1.5,
            'liquidation': -2.5,
            'whale dump': -2.8
        }
        
        # Add terms to lexicon
        for term, score in crypto_positive.items():
            self.analyzer.lexicon[term] = score
            
        for term, score in crypto_negative.items():
            self.analyzer.lexicon[term] = score
            
        logger.info(f"Added {len(crypto_positive) + len(crypto_negative)} crypto-specific terms to sentiment lexicon")
    
    def analyze_posts(self, posts):
        """
        Analyze sentiment of multiple Reddit posts
        
        Args:
            posts (list): List of post dictionaries
            
        Returns:
            dict: Aggregated sentiment analysis results
        """
        if not posts:
            return {
                "overall_sentiment": "neutral",
                "average_scores": {
                    "compound": 0,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "posts_analyzed": 0,
                "posts_details": []
            }
            
        total_scores = {
            "compound": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
        
        sentiment_counts = Counter()
        posts_details = []
        
        # Analyze each post
        for post in posts:
            try:
                # Combine title and text for analysis
                full_text = f"{post['title']} {post.get('selftext', '')}"
                
                # Analyze sentiment
                sentiment_result = self.analyze_text(full_text)
                
                # Extract basic sentiment info for storage in post details
                basic_sentiment = {
                    'compound': sentiment_result.get('compound', 0),
                    'positive': sentiment_result.get('positive', 0),
                    'neutral': sentiment_result.get('neutral', 0),
                    'negative': sentiment_result.get('negative', 0),
                    'sentiment': sentiment_result.get('sentiment', 'neutral')
                }
                
                # Update totals
                for key in total_scores:
                    if key in basic_sentiment:
                        total_scores[key] += basic_sentiment[key]
                
                sentiment_key = basic_sentiment.get('sentiment', 'neutral')
                sentiment_counts[sentiment_key] += 1
                
                # Add sentiment analysis to post details
                post_detail = {
                    'id': post['id'],
                    'title': post['title'],
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'sentiment': basic_sentiment
                }
                posts_details.append(post_detail)
            except Exception as e:
                logger.error(f"Error analyzing post: {str(e)}")
                # Continue with the next post
                continue
        
        # Handle case where all posts failed to analyze
        post_count = len(posts_details)
        if post_count == 0:
            return {
                "overall_sentiment": "neutral",
                "average_scores": {
                    "compound": 0,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "posts_analyzed": 0,
                "posts_details": []
            }
        
        # Calculate averages
        average_scores = {
            key: value / post_count for key, value in total_scores.items()
        }
        
        # Determine overall sentiment
        compound_avg = average_scores.get('compound', 0)
        if compound_avg >= 0.05:
            overall_sentiment = "positive"
        elif compound_avg <= -0.05:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
            
        # Prepare sentiment distribution
        sentiment_distribution = {
            sentiment: count / post_count for sentiment, count in sentiment_counts.items()
        }
        
        # Ensure all sentiments are present
        for sentiment in ['positive', 'neutral', 'negative']:
            if sentiment not in sentiment_distribution:
                sentiment_distribution[sentiment] = 0
        
        # Return aggregated results
        return {
            "overall_sentiment": overall_sentiment,
            "average_scores": average_scores,
            "sentiment_distribution": sentiment_distribution,
            "posts_analyzed": post_count,
            "posts_details": posts_details
        }
