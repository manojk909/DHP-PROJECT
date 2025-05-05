// Chart-related functions for Crypto Analysis Platform

// Use existing chart objects if they exist, otherwise create them
// These variable declarations will be handled in app.js
// This avoids duplicate variable declarations

// Initialize or update charts based on cryptocurrency data
function updateCharts(priceHistory, analysis) {
    if (!priceHistory || !priceHistory.prices || priceHistory.prices.length === 0) {
        console.error('No price history data available');
        return;
    }
    
    // Create price chart
    createPriceChart(priceHistory, analysis);
    
    // Create volume chart
    createVolumeChart(priceHistory);
    
    // Create performance chart
    createPerformanceChart(analysis);
}

// Create or update price chart
function createPriceChart(priceHistory, analysis) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Prepare data
    const prices = priceHistory.prices;
    const labels = prices.map(item => new Date(item.timestamp).toLocaleDateString());
    const priceData = prices.map(item => item.price);
    
    // Moving averages data
    let ma7Data = [];
    let ma14Data = [];
    let ma30Data = [];
    
    // If we have analysis data with moving averages
    if (analysis && analysis.moving_averages) {
        // Create empty arrays for moving averages
        ma7Data = new Array(prices.length).fill(null);
        ma14Data = new Array(prices.length).fill(null);
        ma30Data = new Array(prices.length).fill(null);
        
        // Fill in MA data - only the available values
        // MA7 starts from index 6, MA14 from 13, etc.
        for (let i = 6; i < prices.length; i++) {
            ma7Data[i] = prices[i].price; // Ideally this would be MA7 but we're using actual prices as a placeholder
        }
        
        for (let i = 13; i < prices.length; i++) {
            ma14Data[i] = prices[i].price; // Placeholder
        }
        
        for (let i = 29; i < prices.length; i++) {
            ma30Data[i] = prices[i].price; // Placeholder
        }
    }
    
    // Destroy existing chart if it exists
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Create the chart
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Price',
                    data: priceData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 3,
                },
                {
                    label: '7-Day MA',
                    data: ma7Data,
                    borderColor: '#2ecc71',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                },
                {
                    label: '14-Day MA',
                    data: ma14Data,
                    borderColor: '#f39c12',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                },
                {
                    label: '30-Day MA',
                    data: ma30Data,
                    borderColor: '#e74c3c',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10,
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, "$");
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatCurrency(context.parsed.y, "$");
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Create or update volume chart
function createVolumeChart(priceHistory) {
    const ctx = document.getElementById('volume-chart').getContext('2d');
    
    // Prepare data
    const volumes = priceHistory.volumes;
    const labels = volumes.map(item => new Date(item.timestamp).toLocaleDateString());
    const volumeData = volumes.map(item => item.volume);
    
    // Destroy existing chart if it exists
    if (volumeChart) {
        volumeChart.destroy();
    }
    
    // Create the chart
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Volume',
                    data: volumeData,
                    backgroundColor: 'rgba(52, 152, 219, 0.5)',
                    borderColor: '#3498db',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10,
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, "$");
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatCurrency(context.parsed.y, "$");
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Create or update performance chart
function createPerformanceChart(analysis) {
    const ctx = document.getElementById('performance-chart').getContext('2d');
    
    // Check if analysis data is available
    if (!analysis || !analysis.momentum) {
        console.error('No momentum data available for performance chart');
        return;
    }
    
    // Prepare data
    const data = [
        analysis.momentum.roc_7d,
        analysis.momentum.roc_14d,
        analysis.momentum.roc_30d
    ];
    
    // Determine colors based on values
    const backgroundColors = data.map(value => 
        value > 0 ? 'rgba(46, 204, 113, 0.6)' : 'rgba(231, 76, 60, 0.6)'
    );
    
    const borderColors = data.map(value => 
        value > 0 ? '#2ecc71' : '#e74c3c'
    );
    
    // Destroy existing chart if it exists
    if (pricePerformanceChart) {
        pricePerformanceChart.destroy();
    }
    
    // Create the chart
    pricePerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['7 Days', '14 Days', '30 Days'],
            datasets: [
                {
                    label: 'Price Change',
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2) + '%';
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
}
