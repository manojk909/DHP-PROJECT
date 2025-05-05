// Crypto Comparison JavaScript

// Global variables
let allCryptocurrencies = [];
let selectedCryptocurrencies = [];
const defaultCryptos = ['bitcoin', 'ethereum', 'tether', 'ripple', 'bnb'];
let marketCapChart = null;

// Initialize the comparison page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the comparison page
    if (document.getElementById('crypto-comparison')) {
        initComparisonPage();
    }
});

// Initialize the comparison page
function initComparisonPage() {
    // Load cryptocurrencies
    loadAllCryptocurrencies();
    
    // Set up event listeners for column toggles
    setupColumnToggles();
    
    // Set up search functionality
    setupSearchFunctionality();
}

// Load all available cryptocurrencies
function loadAllCryptocurrencies() {
    fetch('/api/cryptocurrencies?limit=250')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch cryptocurrencies');
            }
            return response.json();
        })
        .then(data => {
            allCryptocurrencies = data;
            populateCryptoDropdown(data);
            
            // Automatically select default cryptocurrencies
            selectDefaultCryptos();
            
            // Create market cap distribution chart for top 10 cryptocurrencies
            createMarketCapDistributionChart(data.slice(0, 10));
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Failed to load cryptocurrency list. Please try again later.');
        })
        .finally(() => {
            // Hide loading spinner
            document.getElementById('loading-spinner').classList.add('d-none');
        });
}

// Create market cap distribution chart
function createMarketCapDistributionChart(topCryptos) {
    const ctx = document.getElementById('market-cap-chart');
    if (!ctx) return;
    
    // If a chart already exists, destroy it first
    if (marketCapChart) {
        marketCapChart.destroy();
    }
    
    // Use only top 10 cryptocurrencies by market cap
    const top10Cryptos = topCryptos.slice(0, 10);
    
    // Store crypto info for legend tracking
    const cryptoInfo = [];
    
    // Extract data for the chart
    for (let i = 0; i < top10Cryptos.length; i++) {
        cryptoInfo.push({
            id: top10Cryptos[i].id,
            symbol: top10Cryptos[i].symbol.toUpperCase(),
            marketCap: top10Cryptos[i].market_cap,
            index: i,
            hidden: false
        });
    }
    
    // Calculate total market cap for percentage calculation
    const totalMarketCap = cryptoInfo.reduce((sum, crypto) => sum + crypto.marketCap, 0);
    
    // Calculate percentages and add to the crypto info
    cryptoInfo.forEach(crypto => {
        crypto.percentage = ((crypto.marketCap / totalMarketCap) * 100).toFixed(2);
        crypto.label = `${crypto.symbol} (${crypto.percentage}%)`;
    });
    
    // Prepare data arrays for the chart
    const labels = cryptoInfo.map(crypto => crypto.label);
    const data = cryptoInfo.map(crypto => crypto.marketCap);
    
    // Vibrant color palette for the chart
    const colors = [
        '#1E88E5', // Blue (Bitcoin)
        '#26A69A', // Teal (Ethereum)
        '#FFC107', // Amber (Tether)
        '#EF5350', // Red (XRP)
        '#66BB6A', // Green (BNB)
        '#7E57C2', // Purple (Solana)
        '#F9A825', // Orange (USDC)
        '#EC407A', // Pink (Dogecoin)
        '#5E35B1', // Deep Purple (Cardano)
        '#42A5F5'  // Light Blue (Other)
    ];
    
    // Get the legend container
    const legendContainer = document.getElementById('legend-container');
    if (!legendContainer) return;
    
    // Clear any existing legend content
    legendContainer.innerHTML = '';
    
    // Create a div to hold the legend items
    const legendList = document.createElement('div');
    legendList.id = 'market-cap-legend';
    legendList.className = 'chart-legend d-flex flex-column gap-2 mt-3';
    legendList.style.maxHeight = '350px';
    legendList.style.overflowY = 'auto';
    legendList.style.paddingRight = '10px';
    
    // Add the legend container
    legendContainer.appendChild(legendList);
    
    // Create our own custom legend items
    cryptoInfo.forEach((crypto, index) => {
        const legendItem = document.createElement('div');
        legendItem.className = 'd-flex align-items-center legend-item';
        legendItem.style.cursor = 'pointer';
        legendItem.style.padding = '5px 10px';
        legendItem.style.borderRadius = '4px';
        legendItem.style.transition = 'background-color 0.2s';
        
        legendItem.innerHTML = `
            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: ${colors[index]}; margin-right: 8px;"></div>
            <span>${crypto.label}</span>
        `;
        
        // Add hover effect
        legendItem.addEventListener('mouseenter', () => {
            legendItem.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        });
        
        legendItem.addEventListener('mouseleave', () => {
            legendItem.style.backgroundColor = 'transparent';
        });
        
        // Track crypto index for click handling
        legendItem.dataset.index = index;
        
        // Add click handler to toggle visibility
        legendItem.addEventListener('click', () => {
            const index = parseInt(legendItem.dataset.index);
            
            // Toggle hidden state in our tracking array
            cryptoInfo[index].hidden = !cryptoInfo[index].hidden;
            
            // Update the visual state of the legend item
            if (cryptoInfo[index].hidden) {
                legendItem.style.opacity = '0.5';
                legendItem.style.textDecoration = 'line-through';
            } else {
                legendItem.style.opacity = '1';
                legendItem.style.textDecoration = 'none';
            }
            
            // Apply visibility changes to the chart
            if (marketCapChart) {
                const meta = marketCapChart.getDatasetMeta(0);
                meta.data[index].hidden = cryptoInfo[index].hidden;
                marketCapChart.update();
            }
        });
        
        legendList.appendChild(legendItem);
    });
    
    // Create the chart
    marketCapChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1,
                borderColor: '#121212'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Cryptocurrencies by Market Cap',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false  // Disable built-in legend, we're using our custom one
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const crypto = cryptoInfo[index];
                            return `${crypto.symbol}: $${formatNumber(crypto.marketCap)} (${crypto.percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Populate cryptocurrency dropdown for selection
function populateCryptoDropdown(cryptos) {
    const cryptoList = document.getElementById('crypto-list');
    
    if (!cryptoList) return;
    
    cryptoList.innerHTML = '';
    
    cryptos.forEach(crypto => {
        const item = document.createElement('a');
        item.className = 'dropdown-item d-flex align-items-center';
        item.href = '#';
        item.setAttribute('data-id', crypto.id);
        item.innerHTML = `
            <img src="${crypto.image}" alt="${crypto.name}" class="me-2" width="20" height="20">
            <span>${crypto.name} (${crypto.symbol.toUpperCase()})</span>
        `;
        
        item.addEventListener('click', (e) => {
            e.preventDefault();
            addCryptocurrency(crypto);
        });
        
        cryptoList.appendChild(item);
    });
}

// Setup search functionality for crypto dropdown
function setupSearchFunctionality() {
    const searchInput = document.getElementById('crypto-search');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const cryptoItems = document.querySelectorAll('#crypto-list .dropdown-item');
        
        cryptoItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Prevent dropdown from closing when clicking in search input
    searchInput.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Select default cryptocurrencies
function selectDefaultCryptos() {
    defaultCryptos.forEach(cryptoId => {
        const crypto = allCryptocurrencies.find(c => c.id === cryptoId);
        if (crypto) {
            addCryptocurrency(crypto);
        }
    });
}

// Add a cryptocurrency to the comparison
function addCryptocurrency(crypto) {
    // Check if already selected
    if (selectedCryptocurrencies.some(c => c.id === crypto.id)) {
        return;
    }
    
    // Add to selected list
    selectedCryptocurrencies.push(crypto);
    
    // Create badge
    addCryptoBadge(crypto);
    
    // Update comparison table
    updateComparisonTable();
}

// Remove a cryptocurrency from the comparison
function removeCryptocurrency(cryptoId) {
    // Remove from selected list
    selectedCryptocurrencies = selectedCryptocurrencies.filter(c => c.id !== cryptoId);
    
    // Remove badge
    const badge = document.querySelector(`#selected-cryptos .crypto-badge[data-id="${cryptoId}"]`);
    if (badge) {
        badge.remove();
    }
    
    // Update comparison table
    updateComparisonTable();
}

// Add a cryptocurrency badge to the selected area
function addCryptoBadge(crypto) {
    const selectedArea = document.getElementById('selected-cryptos');
    
    if (!selectedArea) return;
    
    const badge = document.createElement('div');
    badge.className = `crypto-badge bg-primary text-white`;
    badge.setAttribute('data-id', crypto.id);
    
    badge.innerHTML = `
        <img src="${crypto.image}" alt="${crypto.name}" width="18" height="18" class="me-1">
        ${crypto.symbol.toUpperCase()}
        <span class="remove-btn" title="Remove">×</span>
    `;
    
    // Add click handler for remove button
    badge.querySelector('.remove-btn').addEventListener('click', () => {
        removeCryptocurrency(crypto.id);
    });
    
    selectedArea.appendChild(badge);
}

// Update the comparison table with selected cryptocurrencies
function updateComparisonTable() {
    const tableBody = document.getElementById('comparison-tbody');
    
    if (!tableBody) return;
    
    // Clear table
    tableBody.innerHTML = '';
    
    // Show message if no cryptos selected
    if (selectedCryptocurrencies.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="11" class="text-center py-4">
                <p>Select cryptocurrencies to compare</p>
            </td>
        `;
        tableBody.appendChild(emptyRow);
        return;
    }
    
    // Add rows for each cryptocurrency
    selectedCryptocurrencies.forEach(crypto => {
        const row = document.createElement('tr');
        
        // Name column with icon
        const nameCell = document.createElement('td');
        nameCell.innerHTML = `
            <div class="d-flex align-items-center">
                <img src="${crypto.image}" alt="${crypto.name}" width="24" height="24" class="me-2">
                <span>${crypto.name}</span>
                <button class="btn btn-sm text-danger ms-2" title="Remove" onclick="removeCryptocurrency('${crypto.id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Symbol
        const symbolCell = document.createElement('td');
        symbolCell.className = 'col-symbol';
        symbolCell.textContent = crypto.symbol.toUpperCase();
        
        // Price
        const priceCell = document.createElement('td');
        priceCell.className = 'col-price';
        priceCell.textContent = formatCurrency(crypto.current_price);
        
        // Market Cap
        const marketCapCell = document.createElement('td');
        marketCapCell.className = 'col-market-cap';
        marketCapCell.textContent = formatCurrency(crypto.market_cap);
        
        // 24h Change
        const change24hCell = document.createElement('td');
        change24hCell.className = `col-24h-change ${crypto.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`;
        change24hCell.textContent = formatPercentage(crypto.price_change_percentage_24h);
        
        // 7d Change
        const change7dCell = document.createElement('td');
        change7dCell.className = 'col-7d-change';
        if (crypto.price_change_percentage_7d_in_currency) {
            change7dCell.className += crypto.price_change_percentage_7d_in_currency >= 0 ? ' positive' : ' negative';
            change7dCell.textContent = formatPercentage(crypto.price_change_percentage_7d_in_currency);
        } else {
            change7dCell.textContent = 'N/A';
        }
        
        // 30d Change
        const change30dCell = document.createElement('td');
        change30dCell.className = 'col-30d-change';
        if (crypto.price_change_percentage_30d_in_currency) {
            change30dCell.className += crypto.price_change_percentage_30d_in_currency >= 0 ? ' positive' : ' negative';
            change30dCell.textContent = formatPercentage(crypto.price_change_percentage_30d_in_currency);
        } else {
            change30dCell.textContent = 'N/A';
        }
        
        // Volume
        const volumeCell = document.createElement('td');
        volumeCell.className = 'col-volume d-none';
        volumeCell.textContent = formatCurrency(crypto.total_volume);
        
        // Circulating Supply
        const supplyCell = document.createElement('td');
        supplyCell.className = 'col-supply d-none';
        supplyCell.textContent = formatNumber(crypto.circulating_supply);
        
        // Max Supply
        const maxSupplyCell = document.createElement('td');
        maxSupplyCell.className = 'col-max-supply d-none';
        maxSupplyCell.textContent = crypto.max_supply ? formatNumber(crypto.max_supply) : 'N/A';
        
        // All-Time High
        const athCell = document.createElement('td');
        athCell.className = 'col-ath d-none';
        athCell.textContent = crypto.ath ? formatCurrency(crypto.ath) : 'N/A';
        
        // Append all cells
        row.appendChild(nameCell);
        row.appendChild(symbolCell);
        row.appendChild(priceCell);
        row.appendChild(marketCapCell);
        row.appendChild(change24hCell);
        row.appendChild(change7dCell);
        row.appendChild(change30dCell);
        row.appendChild(volumeCell);
        row.appendChild(supplyCell);
        row.appendChild(maxSupplyCell);
        row.appendChild(athCell);
        
        tableBody.appendChild(row);
    });
}

// Setup column toggle functionality
// Function added below to avoid duplication

// Set up correlation period listeners
function setupCorrelationPeriodListeners() {
    const correlationRadios = document.querySelectorAll('input[name="correlation-period"]');
    correlationRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.checked && selectedCryptocurrencies.length >= 2) {
                updateCorrelationAnalysis(radio.value);
            }
        });
    });
}

// Update the performance chart based on the selected period
function updatePerformanceChart(period) {
    const chartTitle = document.getElementById('performance-chart-title');
    const periodMap = {
        '24h': {
            title: '24H Price Change Comparison',
            dataKey: 'price_change_percentage_24h'
        },
        '7d': {
            title: '7 Day Price Change Comparison',
            dataKey: 'price_change_percentage_7d_in_currency'
        },
        '30d': {
            title: '30 Day Price Change Comparison',
            dataKey: 'price_change_percentage_30d_in_currency'
        }
    };
    
    if (chartTitle) {
        chartTitle.textContent = periodMap[period].title;
    }
    
    createPerformanceChart(selectedCryptocurrencies, periodMap[period].dataKey, period);
    createMarketCapComparisonChart(selectedCryptocurrencies);
}

// Create price performance comparison chart
function createPerformanceChart(cryptos, dataKey, period) {
    if (cryptos.length === 0) return;
    
    const ctx = document.getElementById('performance-chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (comparisonPerformanceChart) {
        comparisonPerformanceChart.destroy();
    }
    
    // Extract data
    const labels = cryptos.map(crypto => crypto.symbol.toUpperCase());
    const data = cryptos.map(crypto => crypto[dataKey] || 0);
    
    // Generate color gradient for values
    const colors = data.map(value => {
        if (value > 0) {
            // Green gradient based on positivity (higher values = deeper green)
            const intensity = Math.min(value * 3, 100) / 100;
            return `rgba(40, 167, 69, ${0.6 + intensity * 0.4})`;
        } else if (value < 0) {
            // Red gradient based on negativity (more negative = deeper red)
            const intensity = Math.min(Math.abs(value) * 3, 100) / 100;
            return `rgba(220, 53, 69, ${0.6 + intensity * 0.4})`;
        } else {
            // Yellow/neutral for zero or tiny changes
            return `rgba(255, 193, 7, 0.8)`;
        }
    });
    
    // Get period title for chart
    const periodTitles = {
        '24h': '24H Price Change Comparison',
        '7d': '7 Day Price Change Comparison',
        '30d': '30 Day Price Change Comparison'
    };
    
    // Create chart
    comparisonPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `${period} Price Change (%)`,
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(0, 0, 0, 0.1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'x',
            plugins: {
                title: {
                    display: true,
                    text: periodTitles[period] || `Price Change Comparison`,
                    color: '#ffffff',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: {
                        bottom: 30
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toFixed(2)}%`;
                        },
                        title: function(context) {
                            return context[0].label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '%';
                        },
                        color: '#fff'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#fff'
                    }
                }
            }
        }
    });
}

// Create market cap comparison chart
function createMarketCapComparisonChart(cryptos) {
    if (cryptos.length === 0) return;
    
    const ctx = document.getElementById('market-cap-comparison-chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (marketCapComparisonChart) {
        marketCapComparisonChart.destroy();
    }
    
    // Extract data
    const labels = cryptos.map(crypto => crypto.symbol.toUpperCase());
    const data = cryptos.map(crypto => crypto.market_cap);
    
    // Define a vibrant color palette
    const colors = [
        '#4285F4', // Google Blue
        '#34A853', // Google Green
        '#FBBC05', // Google Yellow
        '#EA4335', // Google Red
        '#8F00FF', // Violet
        '#00C6FF', // Sky Blue
        '#FF5722', // Deep Orange
        '#00BFA5', // Teal
        '#FF4081', // Pink
        '#FFD600'  // Amber
    ];
    
    // Create chart
    marketCapComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Market Cap (USD)',
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Market Cap Comparison',
                    color: '#ffffff',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: {
                        bottom: 30
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `Market Cap: $${formatNumber(value)}`;
                        },
                        title: function(context) {
                            return context[0].label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + formatShortNumber(value);
                        },
                        color: '#fff'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#fff'
                    }
                }
            }
        }
    });
}

// Helper function to format large numbers in a readable way (e.g., 1.2B, 345M)
function formatShortNumber(num) {
    if (!num) return '0';
    
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function setupColumnToggles() {
    const toggles = {
        'toggle-symbol': '.col-symbol',
        'toggle-price': '.col-price',
        'toggle-market-cap': '.col-market-cap',
        'toggle-24h-change': '.col-24h-change',
        'toggle-7d-change': '.col-7d-change',
        'toggle-30d-change': '.col-30d-change',
        'toggle-volume': '.col-volume',
        'toggle-supply': '.col-supply',
        'toggle-max-supply': '.col-max-supply',
        'toggle-ath': '.col-ath'
    };
    
    // Add event listeners to toggles
    Object.keys(toggles).forEach(toggleId => {
        const toggle = document.getElementById(toggleId);
        
        if (!toggle) return;
        
        toggle.addEventListener('change', () => {
            const columns = document.querySelectorAll(toggles[toggleId]);
            
            columns.forEach(col => {
                if (toggle.checked) {
                    col.classList.remove('d-none');
                } else {
                    col.classList.add('d-none');
                }
            });
        });
    });
}

// Update the correlation analysis based on the selected period
function updateCorrelationAnalysis(days) {
    // Make sure we have at least 2 cryptocurrencies selected
    if (selectedCryptocurrencies.length < 2) {
        document.getElementById('correlation-info').classList.remove('d-none');
        return;
    }
    
    // Hide info message
    document.getElementById('correlation-info').classList.add('d-none');
    
    // Show loading spinner
    document.getElementById('correlation-loading').classList.remove('d-none');
    
    // Get coin IDs from selected cryptocurrencies
    const coinIds = selectedCryptocurrencies.map(crypto => crypto.id).join(',');
    
    // Fetch correlation data from the API
    fetch(`/api/price-correlation?coins=${coinIds}&days=${days}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch correlation data');
            }
            return response.json();
        })
        .then(data => {
            // Store correlation data globally
            correlationData = data;
            
            // Check if we're using demo data
            if (data.demo_data) {
                // Show a demo data notification
                const infoEl = document.getElementById('correlation-info');
                infoEl.innerHTML = `
                    <i class="fas fa-info-circle me-2"></i>
                    Using representative correlation data. The CoinGecko API has rate limits that prevent fetching real-time correlation data at this moment.
                `;
                infoEl.classList.remove('d-none');
                infoEl.classList.remove('alert-danger');
                infoEl.classList.add('alert-warning');
            }
            
            // Create the correlation matrix chart
            createCorrelationMatrixChart(data);
            
            // Update the correlation table
            updateCorrelationTable(data);
        })
        .catch(error => {
            console.error('Error:', error);
            // Show error message
            const infoEl = document.getElementById('correlation-info');
            infoEl.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                Error fetching correlation data: ${error.message}. Please try again later.
            `;
            infoEl.classList.remove('d-none');
            infoEl.classList.remove('alert-warning');
            infoEl.classList.add('alert-danger');
        })
        .finally(() => {
            // Hide loading spinner
            document.getElementById('correlation-loading').classList.add('d-none');
        });
}

// Create a correlation matrix heatmap chart
function createCorrelationMatrixChart(data) {
    const ctx = document.getElementById('correlation-matrix-chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (correlationMatrixChart) {
        correlationMatrixChart.destroy();
    }
    
    // Extract correlation matrix data
    const matrix = data.correlation_matrix;
    const coinDetails = data.coin_details;
    
    // Get list of coin IDs
    const coinIds = Object.keys(matrix);
    
    // Get symbols for labels
    const labels = coinIds.map(id => coinDetails[id].symbol.toUpperCase());
    
    // Create datasets for the heatmap
    const datasets = [];
    
    coinIds.forEach((coinId, rowIndex) => {
        // Get correlation values for this coin
        const values = coinIds.map(id => matrix[coinId][id]);
        
        datasets.push({
            label: coinDetails[coinId].symbol.toUpperCase(),
            data: values,
            backgroundColor: function(context) {
                const value = context.dataset.data[context.dataIndex];
                
                // Return color based on correlation value
                if (value === 1) {
                    // Perfect positive correlation (self-correlation)
                    return 'rgba(80, 80, 80, 0.8)';
                } else if (value >= 0.7) {
                    // Strong positive correlation (green)
                    return `rgba(40, 167, 69, ${0.5 + value * 0.5})`;
                } else if (value >= 0.3) {
                    // Moderate positive correlation (light green)
                    return `rgba(0, 255, 0, ${0.3 + value * 0.4})`;
                } else if (value >= -0.3) {
                    // Weak or no correlation (yellow)
                    return `rgba(255, 193, 7, ${0.4 + Math.abs(value) * 0.3})`;
                } else if (value >= -0.7) {
                    // Moderate negative correlation (orange)
                    return `rgba(255, 145, 0, ${0.5 + Math.abs(value) * 0.3})`;
                } else {
                    // Strong negative correlation (red)
                    return `rgba(220, 53, 69, ${0.5 + Math.abs(value) * 0.5})`;
                }
            },
            borderColor: 'rgba(0, 0, 0, 0.1)',
            borderWidth: 1
        });
    });
    
    // Create chart
    correlationMatrixChart = new Chart(ctx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: 'Correlation Matrix',
                data: [],
                backgroundColor: function(context) {
                    // Get the value from the matrix
                    const rowIndex = context.dataIndex % coinIds.length;
                    const colIndex = Math.floor(context.dataIndex / coinIds.length);
                    const value = matrix[coinIds[rowIndex]][coinIds[colIndex]];
                    
                    // Return color based on correlation value
                    if (rowIndex === colIndex) {
                        // Perfect positive correlation (self-correlation)
                        return 'rgba(80, 80, 80, 0.8)';
                    } else if (value >= 0.7) {
                        // Strong positive correlation (green)
                        return `rgba(40, 167, 69, ${0.5 + value * 0.5})`;
                    } else if (value >= 0.3) {
                        // Moderate positive correlation (light green)
                        return `rgba(0, 255, 0, ${0.3 + value * 0.4})`;
                    } else if (value >= -0.3) {
                        // Weak or no correlation (yellow)
                        return `rgba(255, 193, 7, ${0.4 + Math.abs(value) * 0.3})`;
                    } else if (value >= -0.7) {
                        // Moderate negative correlation (orange)
                        return `rgba(255, 145, 0, ${0.5 + Math.abs(value) * 0.3})`;
                    } else {
                        // Strong negative correlation (red)
                        return `rgba(220, 53, 69, ${0.5 + Math.abs(value) * 0.5})`;
                    }
                },
                borderColor: 'rgba(0, 0, 0, 0.1)',
                borderWidth: 1,
                width: coinIds.length,
                height: coinIds.length
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const i = context[0].dataIndex;
                            const rowIndex = i % coinIds.length;
                            const colIndex = Math.floor(i / coinIds.length);
                            
                            const coin1 = labels[rowIndex];
                            const coin2 = labels[colIndex];
                            
                            return `${coin1} vs ${coin2}`;
                        },
                        label: function(context) {
                            const i = context.dataIndex;
                            const rowIndex = i % coinIds.length;
                            const colIndex = Math.floor(i / coinIds.length);
                            
                            const value = matrix[coinIds[rowIndex]][coinIds[colIndex]];
                            
                            return `Correlation: ${value.toFixed(2)}`;
                        }
                    }
                },
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: `Cryptocurrency Price Correlation (${data.days} days)`,
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: labels,
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: labels,
                    offset: true,
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Update the correlation table with correlation data
function updateCorrelationTable(data) {
    const table = document.getElementById('correlation-table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Extract correlation matrix data
    const matrix = data.correlation_matrix;
    const coinDetails = data.coin_details;
    
    // Get list of coin IDs
    const coinIds = Object.keys(matrix);
    
    // Generate pairs (excluding self-correlations)
    const pairs = [];
    
    for (let i = 0; i < coinIds.length; i++) {
        for (let j = i + 1; j < coinIds.length; j++) {
            const coin1 = coinIds[i];
            const coin2 = coinIds[j];
            const correlation = matrix[coin1][coin2];
            
            pairs.push({
                coin1,
                coin2,
                correlation
            });
        }
    }
    
    // Sort pairs by absolute correlation value (strongest correlation first)
    pairs.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
    
    // Add rows to the table
    pairs.forEach(pair => {
        const row = document.createElement('tr');
        
        // Get symbols for display
        const symbol1 = coinDetails[pair.coin1].symbol.toUpperCase();
        const symbol2 = coinDetails[pair.coin2].symbol.toUpperCase();
        
        // Create pair cell
        const pairCell = document.createElement('td');
        pairCell.innerHTML = `${symbol1} / ${symbol2}`;
        
        // Create correlation cell
        const correlationCell = document.createElement('td');
        const correlationValue = pair.correlation.toFixed(2);
        correlationCell.textContent = correlationValue;
        
        // Add class based on correlation strength
        if (pair.correlation >= 0.7) {
            correlationCell.className = 'positive';
        } else if (pair.correlation <= -0.7) {
            correlationCell.className = 'negative';
        }
        
        // Create strength cell
        const strengthCell = document.createElement('td');
        
        let strength;
        let strengthClass;
        
        if (pair.correlation >= 0.7) {
            strength = 'Strong Positive';
            strengthClass = 'positive';
        } else if (pair.correlation >= 0.3) {
            strength = 'Moderate Positive';
            strengthClass = 'positive';
        } else if (pair.correlation > -0.3) {
            strength = 'Weak/None';
            strengthClass = '';
        } else if (pair.correlation > -0.7) {
            strength = 'Moderate Negative';
            strengthClass = 'negative';
        } else {
            strength = 'Strong Negative';
            strengthClass = 'negative';
        }
        
        strengthCell.textContent = strength;
        strengthCell.className = strengthClass;
        
        // Append cells to the row
        row.appendChild(pairCell);
        row.appendChild(correlationCell);
        row.appendChild(strengthCell);
        
        // Append row to the table body
        tbody.appendChild(row);
    });
    
    // Show message if no pairs
    if (pairs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="3" class="text-center">
                Select at least two cryptocurrencies to view correlations
            </td>
        `;
        tbody.appendChild(row);
    }
}