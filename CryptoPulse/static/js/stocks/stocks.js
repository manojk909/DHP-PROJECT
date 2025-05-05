// Stocks Analysis JavaScript

// Global variables for charts
let priceChart = null;
let volumeChart = null;
let sentimentChart = null;
let moversChart = null;

// Global variables for data
let currentStock = null;
let newsData = [];
let currentNewsPage = 1;
let newsPerPage = 10;
let currentNewsSentimentFilter = 'all';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

// Initialize the application
function initApp() {
    // Load market overview data
    loadMarketOverview();
    
    // Load stock symbols
    loadStockSymbols();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial news
    loadNews();
    
    // Hide loading spinner
    document.getElementById('loading-spinner').classList.add('d-none');
}

// Set up event listeners
function setupEventListeners() {
    // Stock select change event
    const stockSelect = document.getElementById('stock-select');
    stockSelect.addEventListener('change', handleStockChange);
    
    // Time range change event
    const timeRange = document.getElementById('time-range');
    timeRange.addEventListener('change', handleTimeRangeChange);
    
    // Company search event
    const searchButton = document.getElementById('search-button');
    searchButton.addEventListener('click', handleCompanySearch);
    
    // Enter key in search box
    const companySearch = document.getElementById('company-search');
    companySearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleCompanySearch();
        }
    });
    
    // News filter buttons
    const filterButtons = document.querySelectorAll('.news-filter');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                // Remove solid background color
                if (btn.classList.contains('btn-success')) {
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-success');
                } else if (btn.classList.contains('btn-warning')) {
                    btn.classList.remove('btn-warning');
                    btn.classList.add('btn-outline-warning');
                } else if (btn.classList.contains('btn-danger')) {
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-outline-danger');
                }
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Change to solid background for active button
            const sentiment = this.getAttribute('data-sentiment');
            if (sentiment === 'all') {
                this.classList.remove('btn-outline-success');
                this.classList.add('btn-success');
            } else if (sentiment === 'positive') {
                this.classList.remove('btn-outline-success');
                this.classList.add('btn-success');
            } else if (sentiment === 'neutral') {
                this.classList.remove('btn-outline-warning');
                this.classList.add('btn-warning');
            } else if (sentiment === 'negative') {
                this.classList.remove('btn-outline-danger');
                this.classList.add('btn-danger');
            }
            
            // Apply filter
            currentNewsSentimentFilter = sentiment;
            displayNewsItems(newsData);
        });
    });
    
    // Load more news button
    const loadMoreButton = document.getElementById('load-more-button');
    loadMoreButton.addEventListener('click', function() {
        currentNewsPage++;
        displayNewsItems(newsData);
    });
    
    // Company tag click events - quick search
    const companyTags = document.querySelectorAll('.company-tag');
    companyTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const company = this.textContent.trim();
            document.getElementById('company-search').value = company;
            
            // Reset page number
            currentNewsPage = 1;
            
            // Show loading spinner
            document.getElementById('loading-spinner').classList.remove('d-none');
            
            // Load news for the company
            loadNews(company);
            
            // Highlight the selected tag
            companyTags.forEach(t => {
                t.classList.remove('bg-primary', 'text-white');
                t.classList.add('bg-secondary', 'text-white');
            });
            this.classList.add('bg-primary', 'text-white');
            this.classList.remove('bg-secondary');
        });
    });
}

// Load market overview data
function loadMarketOverview() {
    // Load market movers chart
    fetch('/api/stocks/charts/movers')
        .then(response => response.json())
        .then(data => {
            updateMoversChart(data);
        })
        .catch(error => {
            console.error('Error loading market movers:', error);
            showErrorMessage('Failed to load market movers data');
        });
    
    // Load market sentiment chart
    fetch('/api/stocks/charts/sentiment')
        .then(response => response.json())
        .then(data => {
            updateSentimentChart(data);
            updateMarketSentiment();
        })
        .catch(error => {
            console.error('Error loading market sentiment:', error);
            showErrorMessage('Failed to load market sentiment data');
        });
}

// Load stock symbols for dropdown
function loadStockSymbols() {
    fetch('/api/stocks/symbols')
        .then(response => response.json())
        .then(symbols => {
            populateStockDropdown(symbols);
        })
        .catch(error => {
            console.error('Error loading stock symbols:', error);
            showErrorMessage('Failed to load stock symbols');
        });
}

// Populate stock dropdown with symbols
function populateStockDropdown(symbols) {
    const stockSelect = document.getElementById('stock-select');
    
    // Clear existing options (except the placeholder)
    while (stockSelect.options.length > 1) {
        stockSelect.options.remove(1);
    }
    
    // Add symbols to dropdown
    symbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        stockSelect.appendChild(option);
    });
}

// Handle stock selection change
function handleStockChange() {
    const symbol = document.getElementById('stock-select').value;
    
    if (!symbol) {
        document.getElementById('stock-data-container').classList.add('d-none');
        document.getElementById('no-stock-selected').classList.remove('d-none');
        return;
    }
    
    // Show loading spinner
    document.getElementById('loading-spinner').classList.remove('d-none');
    
    // Update current stock
    currentStock = symbol;
    
    // Get time range
    const days = parseInt(document.getElementById('time-range').value);
    
    // Show stock data container
    document.getElementById('stock-data-container').classList.remove('d-none');
    document.getElementById('no-stock-selected').classList.add('d-none');
    
    // Load stock data
    loadStockData(symbol, days);
}

// Handle time range change
function handleTimeRangeChange() {
    const days = parseInt(document.getElementById('time-range').value);
    
    if (currentStock) {
        // Show loading spinner
        document.getElementById('loading-spinner').classList.remove('d-none');
        
        // Load stock data for new time range
        loadStockData(currentStock, days);
    }
}

// Load stock data for the selected symbol and time range
function loadStockData(symbol, days) {
    // Load price history data
    fetch(`/api/stocks/price-history/${symbol}?days=${days}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch price history');
            }
            return response.text(); // Get as text first to check for validity
        })
        .then(text => {
            try {
                // Try to parse as JSON, cleaning any NaN values
                const priceData = JSON.parse(text.replace(/"7_day_ma":NaN/g, '"7_day_ma":null')
                                            .replace(/"30_day_ma":NaN/g, '"30_day_ma":null')
                                            .replace(/:NaN/g, ':null'));
                
                // Load stock analysis data
                return fetch(`/api/stocks/analysis/${symbol}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Failed to fetch stock analysis');
                        }
                        return response.text(); // Get as text for safety
                    })
                    .then(analysisText => {
                        try {
                            const analysis = JSON.parse(analysisText);
                            return { priceData, analysis };
                        } catch (e) {
                            console.error('Error parsing analysis JSON:', e);
                            console.log('Raw analysis response:', analysisText);
                            // Continue with price data only
                            return { priceData, analysis: {} };
                        }
                    })
                    .catch(error => {
                        console.error('Error loading stock analysis:', error);
                        // Continue with price data only
                        return { priceData, analysis: {} };
                    });
            } catch (e) {
                console.error('Error parsing price data JSON:', e);
                console.log('Raw price response:', text);
                throw new Error('Invalid price data format');
            }
        })
        .then(data => {
            // Update stock info
            updateStockInfo(data.priceData, data.analysis);
            
            // Update charts
            updateCharts(data.priceData, data.analysis);
            
            // Hide loading spinner
            document.getElementById('loading-spinner').classList.add('d-none');
        })
        .catch(error => {
            console.error('Error loading stock data:', error);
            showErrorMessage(`Failed to load data for ${symbol}`);
            
            // Hide loading spinner
            document.getElementById('loading-spinner').classList.add('d-none');
        });
}

// Update stock information display
function updateStockInfo(priceData, analysis) {
    // Update stock name and symbol
    document.getElementById('stock-name').textContent = priceData.symbol.split('.')[0] || 'Stock';
    document.getElementById('stock-symbol').textContent = priceData.symbol;
    
    // Update price information
    if (priceData.data && priceData.data.length > 0) {
        const latestData = priceData.data[priceData.data.length - 1];
        const previousData = priceData.data.length > 1 ? priceData.data[priceData.data.length - 2] : latestData;
        
        // Update price
        document.getElementById('stock-price').textContent = formatCurrency(latestData.Close, '$');
        
        // Calculate and update daily change
        const priceChange = ((latestData.Close - previousData.Close) / previousData.Close) * 100;
        const priceChangeElement = document.getElementById('price-change');
        priceChangeElement.textContent = formatPercentage(priceChange);
        
        // Apply color based on price change
        if (priceChange > 0) {
            priceChangeElement.className = 'fs-5 percent-change-positive';
            priceChangeElement.innerHTML = `<i class="fas fa-caret-up me-1"></i>${formatPercentage(priceChange)}`;
        } else if (priceChange < 0) {
            priceChangeElement.className = 'fs-5 percent-change-negative';
            priceChangeElement.innerHTML = `<i class="fas fa-caret-down me-1"></i>${formatPercentage(priceChange)}`;
        } else {
            priceChangeElement.className = 'fs-5 text-muted';
        }
        
        // Update volume
        document.getElementById('volume').textContent = formatNumber(latestData.Volume);
    }
    
    // Update analysis information
    if (analysis) {
        // Update trend
        const trendLabel = document.getElementById('trend-label');
        switch (analysis.trend) {
            case 'strong_uptrend':
                trendLabel.innerHTML = '<i class="fas fa-arrow-trend-up me-1"></i>Strong Uptrend';
                trendLabel.className = 'percent-change-positive fw-bold';
                break;
            case 'uptrend':
                trendLabel.innerHTML = '<i class="fas fa-caret-up me-1"></i>Uptrend';
                trendLabel.className = 'percent-change-positive';
                break;
            case 'strong_downtrend':
                trendLabel.innerHTML = '<i class="fas fa-arrow-trend-down me-1"></i>Strong Downtrend';
                trendLabel.className = 'percent-change-negative fw-bold';
                break;
            case 'downtrend':
                trendLabel.innerHTML = '<i class="fas fa-caret-down me-1"></i>Downtrend';
                trendLabel.className = 'percent-change-negative';
                break;
            default:
                trendLabel.textContent = 'Neutral';
                trendLabel.className = 'text-muted';
        }
        
        // Update volatility
        const volatilityElem = document.getElementById('volatility');
        const volatilityValue = analysis.volatility_percent || 0;
        
        if (volatilityValue > 3) {
            volatilityElem.innerHTML = '<i class="fas fa-arrow-trend-up me-1"></i>High';
            volatilityElem.className = 'percent-change-negative';
        } else if (volatilityValue > 1.5) {
            volatilityElem.textContent = 'Medium';
            volatilityElem.className = 'text-warning';
        } else {
            volatilityElem.innerHTML = '<i class="fas fa-arrow-trend-down me-1"></i>Low';
            volatilityElem.className = 'percent-change-positive';
        }
        
        // Update moving averages
        if (analysis.moving_averages) {
            const ma7 = analysis.moving_averages.ma_7;
            const ma30 = analysis.moving_averages.ma_30;
            
            if (ma7) {
                document.getElementById('ma-7').textContent = formatCurrency(ma7, '$');
            }
            
            if (ma30) {
                document.getElementById('ma-30').textContent = formatCurrency(ma30, '$');
            }
            
            // Update price vs MA description
            const priceVsMA = document.getElementById('price-vs-ma');
            if (analysis.moving_averages.price_vs_ma7 === 'above' && analysis.moving_averages.price_vs_ma30 === 'above') {
                priceVsMA.innerHTML = '<i class="fas fa-caret-up me-1"></i>Price is above both 7-day and 30-day MAs (bullish)';
                priceVsMA.className = 'percent-change-positive';
            } else if (analysis.moving_averages.price_vs_ma7 === 'below' && analysis.moving_averages.price_vs_ma30 === 'below') {
                priceVsMA.innerHTML = '<i class="fas fa-caret-down me-1"></i>Price is below both 7-day and 30-day MAs (bearish)';
                priceVsMA.className = 'percent-change-negative';
            } else if (analysis.moving_averages.price_vs_ma7 === 'above' && analysis.moving_averages.price_vs_ma30 === 'below') {
                priceVsMA.innerHTML = '<i class="fas fa-caret-up me-1"></i>Price crossed above 30-day MA (potential uptrend)';
                priceVsMA.className = 'percent-change-positive';
            } else {
                priceVsMA.textContent = 'Price is between 7-day and 30-day MAs (mixed signals)';
                priceVsMA.className = 'text-warning';
            }
        }
        
        // Update volatility description
        const volatilityDesc = document.getElementById('volatility-description');
        if (volatilityValue > 3) {
            volatilityDesc.textContent = `This stock shows high volatility (${formatPercentage(volatilityValue)}), indicating significant price swings and potential risk.`;
        } else if (volatilityValue > 1.5) {
            volatilityDesc.textContent = `This stock shows moderate volatility (${formatPercentage(volatilityValue)}), with some price fluctuations but not extreme.`;
        } else {
            volatilityDesc.textContent = `This stock shows low volatility (${formatPercentage(volatilityValue)}), with relatively stable price movements.`;
        }
        
        // Update recommendation
        const recommendation = document.getElementById('recommendation');
        if (analysis.trend === 'strong_uptrend') {
            recommendation.innerHTML = '<i class="fas fa-arrow-trend-up me-1"></i>Based on technical indicators, this stock appears to be in a strong uptrend. Consider buying or holding positions.';
            recommendation.className = 'percent-change-positive';
        } else if (analysis.trend === 'uptrend') {
            recommendation.innerHTML = '<i class="fas fa-caret-up me-1"></i>This stock is in an uptrend. Consider buying on dips or maintaining existing positions.';
            recommendation.className = 'percent-change-positive';
        } else if (analysis.trend === 'strong_downtrend') {
            recommendation.innerHTML = '<i class="fas fa-arrow-trend-down me-1"></i>This stock is in a strong downtrend. Consider avoiding new positions or reducing exposure.';
            recommendation.className = 'percent-change-negative';
        } else if (analysis.trend === 'downtrend') {
            recommendation.innerHTML = '<i class="fas fa-caret-down me-1"></i>This stock is in a downtrend. Exercise caution when entering new positions.';
            recommendation.className = 'percent-change-negative';
        } else {
            recommendation.textContent = 'This stock is showing neutral signals. Consider waiting for clearer trend development before making decisions.';
            recommendation.className = 'text-muted';
        }
    }
}

// Update price and volume charts
function updateCharts(priceData, analysis) {
    // Update price chart
    updatePriceChart(priceData);
    
    // Update volume chart
    updateVolumeChart(priceData);
}

// Update price chart with data
function updatePriceChart(priceData) {
    // Get canvas element
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Prepare data for chart
    if (priceData.data && priceData.data.length > 0) {
        // Extract dates and prices
        const dates = priceData.data.map(item => {
            const date = new Date(item.Date);
            return date.toLocaleDateString();
        });
        
        const prices = priceData.data.map(item => item.Close);
        
        // Destroy existing chart if it exists
        if (priceChart) {
            priceChart.destroy();
        }
        
        // Create new chart
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Price ($)',
                    data: prices,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    pointRadius: 1,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '$' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// Update volume chart with data
function updateVolumeChart(priceData) {
    // Get canvas element
    const ctx = document.getElementById('volume-chart').getContext('2d');
    
    // Prepare data for chart
    if (priceData.data && priceData.data.length > 0) {
        // Extract dates and volumes
        const dates = priceData.data.map(item => {
            const date = new Date(item.Date);
            return date.toLocaleDateString();
        });
        
        const volumes = priceData.data.map(item => item.Volume);
        
        // Destroy existing chart if it exists
        if (volumeChart) {
            volumeChart.destroy();
        }
        
        // Create new chart
        volumeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Volume',
                    data: volumes,
                    backgroundColor: 'rgba(153, 102, 255, 0.7)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCompactNumber(value);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Volume: ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// Update sentiment chart with data
function updateSentimentChart(data) {
    try {
        // Get canvas element
        const chartElement = document.getElementById('sentiment-chart');
        if (!chartElement) {
            console.error('Sentiment chart element not found');
            return;
        }
        const ctx = chartElement.getContext('2d');
        
        // Destroy existing chart if it exists
        if (sentimentChart) {
            sentimentChart.destroy();
        }
    
        // Create new chart
        sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: data.datasets && data.datasets.length > 0 ? data.datasets[0].data : [33, 33, 34],
                    backgroundColor: data.datasets && data.datasets.length > 0 ? 
                        data.datasets[0].backgroundColor : 
                        ['rgba(75, 192, 192, 0.7)', 'rgba(201, 203, 207, 0.7)', 'rgba(255, 99, 132, 0.7)'],
                    borderColor: data.datasets && data.datasets.length > 0 ? 
                        data.datasets[0].borderColor : 
                        ['rgba(75, 192, 192, 1)', 'rgba(201, 203, 207, 1)', 'rgba(255, 99, 132, 1)'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating sentiment chart:', error);
    }
}

// Update market movers chart with data
function updateMoversChart(data) {
    try {
        // Get canvas element
        const ctx = document.getElementById('movers-chart');
        if (!ctx) {
            console.error('Movers chart canvas element not found');
            return;
        }
        
        const context2D = ctx.getContext('2d');
        
        // Destroy existing chart if it exists
        if (moversChart) {
            moversChart.destroy();
        }
        
        // Create new chart
        moversChart = new Chart(context2D, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Price Change (%)',
                    data: data.datasets && data.datasets.length > 0 ? data.datasets[0].data : [],
                    backgroundColor: data.datasets && data.datasets.length > 0 ? data.datasets[0].backgroundColor : [],
                    borderColor: data.datasets && data.datasets.length > 0 ? data.datasets[0].borderColor : [],
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Change: ' + context.parsed.x.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating movers chart:', error);
    }
}

// Update market sentiment information
function updateMarketSentiment() {
    fetch('/api/stocks/sentiment')
        .then(response => response.json())
        .then(data => {
            // Update overall sentiment label
            const sentimentLabel = document.getElementById('overall-sentiment');
            let sentiment = data.overall_sentiment || 'neutral';
            
            // Capitalize and format sentiment
            let displaySentiment = sentiment.replace('_', ' ');
            displaySentiment = displaySentiment.charAt(0).toUpperCase() + displaySentiment.slice(1);
            
            sentimentLabel.textContent = displaySentiment;
            
            // Apply appropriate sentiment class
            sentimentLabel.className = '';
            if (sentiment.includes('positive')) {
                sentimentLabel.innerHTML = '<i class="fas fa-caret-up me-1"></i>' + displaySentiment;
                sentimentLabel.classList.add('percent-change-positive');
            } else if (sentiment.includes('negative')) {
                sentimentLabel.innerHTML = '<i class="fas fa-caret-down me-1"></i>' + displaySentiment;
                sentimentLabel.classList.add('percent-change-negative');
            } else {
                sentimentLabel.textContent = displaySentiment;
                sentimentLabel.classList.add('text-muted');
            }
            
            // Update sentiment summary
            const sentimentSummary = document.getElementById('sentiment-summary');
            let headlinesAnalyzed = data.headlines_analyzed || 0;
            
            if (headlinesAnalyzed > 0) {
                sentimentSummary.textContent = `Based on analysis of ${headlinesAnalyzed} recent news headlines.`;
            } else {
                sentimentSummary.textContent = 'Based on recent market activity.';
            }
        })
        .catch(error => {
            console.error('Error fetching sentiment data:', error);
        });
}

// Handle company search
function handleCompanySearch() {
    const company = document.getElementById('company-search').value.trim();
    
    if (company) {
        // Reset page number
        currentNewsPage = 1;
        
        // Show loading spinner
        document.getElementById('loading-spinner').classList.remove('d-none');
        
        // Load news for the company
        loadNews(company);
    } else {
        // If search is cleared, load all news
        currentNewsPage = 1;
        loadNews();
    }
}

// Load news data
function loadNews(company = null) {
    let url = '/api/stocks/news';
    if (company) {
        url += `?company=${encodeURIComponent(company)}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Received news data:', data); // Debug log
            if (data.news && data.news.length > 0) {
                newsData = data.news;
                console.log(`Found ${newsData.length} news items`); // Debug log
                displayNewsItems(newsData);
            } else {
                console.log('No news items found in response'); // Debug log
                newsData = [];
                displayNewsItems([]);
            }
            
            // Hide loading spinner
            document.getElementById('loading-spinner').classList.add('d-none');
        })
        .catch(error => {
            console.error('Error loading news:', error);
            showErrorMessage('Failed to load news data');
            
            // Hide loading spinner
            document.getElementById('loading-spinner').classList.add('d-none');
        });
}

// Display news items with pagination and filtering
function displayNewsItems(items) {
    try {
        const newsList = document.getElementById('news-list');
        if (!newsList) {
            console.warn('News list element not found, news section might be disabled');
            return;
        }
        
        const noNewsMessage = document.getElementById('no-news-message');
        const loadMoreContainer = document.getElementById('load-more-container');
        
        // Clear existing news items
        newsList.innerHTML = '';
        
        console.log('Processing news items:', items); // Debug log
        
        // Filter news by sentiment if needed
        let filteredItems = items;
        if (currentNewsSentimentFilter !== 'all') {
            // Need to analyze sentiment for each headline first
            // For simplicity, we'll use a basic keyword approach
    
            filteredItems = items.filter(item => {
                // Skip if already analyzed
                if (item.sentiment) {
                    return item.sentiment === currentNewsSentimentFilter;
                }
                
                try {
                    // Basic sentiment analysis based on keywords
                    const headline = item.Headline ? item.Headline.toLowerCase() : '';
                    if (!headline) return false;
                    
                    // Positive keywords
                    const positiveWords = ['rise', 'gain', 'grow', 'up', 'bull', 'surge', 'climb', 'jump', 'positive', 'profit'];
                    
                    // Negative keywords
                    const negativeWords = ['fall', 'drop', 'decline', 'down', 'bear', 'plunge', 'sink', 'negative', 'loss', 'crash'];
                    
                    let positiveCount = 0;
                    let negativeCount = 0;
                    
                    // Count occurrences of sentiment words
                    positiveWords.forEach(word => {
                        if (headline.includes(word)) {
                            positiveCount++;
                        }
                    });
                    
                    negativeWords.forEach(word => {
                        if (headline.includes(word)) {
                            negativeCount++;
                        }
                    });
                    
                    // Determine sentiment
                    let sentiment = 'neutral';
                    if (positiveCount > negativeCount) {
                        sentiment = 'positive';
                    } else if (negativeCount > positiveCount) {
                        sentiment = 'negative';
                    }
                    
                    // Store sentiment for future use
                    item.sentiment = sentiment;
                    
                    return sentiment === currentNewsSentimentFilter;
                } catch (e) {
                    console.error('Error analyzing headline sentiment:', e);
                    return false;
                }
            });
        }
        
        console.log('Filtered items:', filteredItems.length); // Debug log
        
        // Show no news message if no items
        if (!filteredItems || filteredItems.length === 0) {
            newsList.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-newspaper fa-5x text-muted mb-3"></i>
                    <h3 class="text-muted">No news found</h3>
                </div>
            `;
            if (noNewsMessage) noNewsMessage.classList.add('d-none');
            if (loadMoreContainer) loadMoreContainer.classList.add('d-none');
            return;
        }
        
        // Hide no news message
        if (noNewsMessage) noNewsMessage.classList.add('d-none');
        
        // Calculate pagination
        const startIndex = 0;
        const endIndex = Math.min(currentNewsPage * newsPerPage, filteredItems.length);
        const displayedItems = filteredItems.slice(startIndex, endIndex);
        
        console.log('Displaying items:', displayedItems.length); // Debug log
        
        // Create and append news items
        displayedItems.forEach(item => {
            try {
                // Add sentiment if not already present
                if (!item.sentiment) {
                    // Basic sentiment analysis
                    const headline = item.Headline ? item.Headline.toLowerCase() : '';
                    if (!headline) {
                        item.sentiment = 'neutral';
                    } else {
                        // Check for positive/negative keywords (similar to above)
                        const positiveWords = ['rise', 'gain', 'grow', 'up', 'bull', 'surge', 'climb', 'jump', 'positive', 'profit'];
                        const negativeWords = ['fall', 'drop', 'decline', 'down', 'bear', 'plunge', 'sink', 'negative', 'loss', 'crash'];
                        
                        let positiveCount = 0;
                        let negativeCount = 0;
                        
                        positiveWords.forEach(word => {
                            if (headline.includes(word)) positiveCount++;
                        });
                        
                        negativeWords.forEach(word => {
                            if (headline.includes(word)) negativeCount++;
                        });
                        
                        if (positiveCount > negativeCount) {
                            item.sentiment = 'positive';
                        } else if (negativeCount > positiveCount) {
                            item.sentiment = 'negative';
                        } else {
                            item.sentiment = 'neutral';
                        }
                    }
                }
                
                // Create news item
                const newsItem = document.createElement('div');
                newsItem.className = 'col-12 mb-3';
                
                // Format date
                let publishedDate = '';
                if (item.PublishedAt) {
                    const date = new Date(item.PublishedAt);
                    publishedDate = date.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                    });
                }
                
                newsItem.innerHTML = `
                    <div class="card shadow-sm news-item ${item.sentiment} bg-dark">
                        <div class="card-body p-3">
                            <h5 class="card-title mb-2 text-light">${item.Headline || 'No headline available'}</h5>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-light opacity-75 small">${item.Company || 'Unknown'} | ${item.Source || 'Unknown source'}</span>
                                <span class="badge ${getSentimentBadgeClass(item.sentiment)}">
                                    ${item.sentiment === 'positive' ? '<i class="fas fa-caret-up me-1"></i>' : 
                                      item.sentiment === 'negative' ? '<i class="fas fa-caret-down me-1"></i>' : ''}
                                    ${capitalizeFirstLetter(item.sentiment)}
                                </span>
                            </div>
                            <div class="text-end">
                                <small class="text-light opacity-50">${publishedDate}</small>
                            </div>
                        </div>
                    </div>
                `;
                
                newsList.appendChild(newsItem);
            } catch (error) {
                console.error('Error creating news item:', error, item);
            }
        });
        
        // Show or hide load more button
        if (loadMoreContainer) {
            if (endIndex < filteredItems.length) {
                loadMoreContainer.classList.remove('d-none');
            } else {
                loadMoreContainer.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Error displaying news items:', error);
        // Add a fallback message in case of error
        if (document.getElementById('news-list')) {
            document.getElementById('news-list').innerHTML = `
                <div class="col-12 text-center py-5">
                    <h3 class="text-light opacity-75">Error loading news. Please try again.</h3>
                </div>
            `;
        }
    }
}

// Get appropriate badge class for sentiment
function getSentimentBadgeClass(sentiment) {
    switch (sentiment) {
        case 'positive':
            return 'percent-change-positive';
        case 'negative':
            return 'percent-change-negative';
        case 'neutral':
        default:
            return 'text-muted';
    }
}

// Format currency values
function formatCurrency(value, symbol = '$') {
    if (typeof value !== 'number') {
        return `${symbol}0.00`;
    }
    return `${symbol}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Format percentage values
function formatPercentage(value) {
    if (typeof value !== 'number') {
        return '0.00%';
    }
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

// Format number values
function formatNumber(value) {
    if (typeof value !== 'number') {
        return '0';
    }
    return value.toLocaleString();
}

// Format number in compact form (e.g., 1.2M, 5.3K)
function formatCompactNumber(value) {
    if (typeof value !== 'number') {
        return '0';
    }
    
    if (value >= 1000000) {
        return (value / 1000000).toLocaleString(undefined, { maximumFractionDigits: 1 }) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 }) + 'K';
    } else {
        return value.toLocaleString();
    }
}

// Capitalize first letter of a string
function capitalizeFirstLetter(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Show error message to user
function showErrorMessage(message) {
    // Use simple alert for now, could be replaced with a nicer UI component
    alert(message);
    
    // Hide loading spinner if it's visible
    document.getElementById('loading-spinner').classList.add('d-none');
}