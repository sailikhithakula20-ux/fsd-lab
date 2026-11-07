/**
 * AuraHealth AI - Dashboard Visual Analytics
 * Powered by Chart.js 4.4
 * Custom Clinical Palette: Deep Forest, Emerald, Sage, Soft Olive
 */

document.addEventListener('DOMContentLoaded', () => {
    const calorieCanvas = document.getElementById('calorieTrendsChart');
    const macroCanvas = document.getElementById('macroBreakdownChart');
    const lifestyleCanvas = document.getElementById('lifestyleTrendsChart');

    if (!calorieCanvas || typeof Chart === 'undefined') return;

    // Fetch dynamic 7-day data from Flask REST API
    fetch('/api/v1/dashboard/summary')
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') return;

            const trends = data.trends;
            const summary = data.summary;

            // --- 1. Calorie Consumption vs Target (7-Day Combo Chart) ---
            const calCtx = calorieCanvas.getContext('2d');
            const calGradient = calCtx.createLinearGradient(0, 0, 0, 300);
            calGradient.addColorStop(0, 'rgba(16, 76, 53, 0.35)');
            calGradient.addColorStop(1, 'rgba(16, 76, 53, 0.02)');

            new Chart(calCtx, {
                type: 'line',
                data: {
                    labels: trends.labels,
                    datasets: [
                        {
                            label: 'Calories Consumed (kcal)',
                            data: trends.calories,
                            backgroundColor: calGradient,
                            borderColor: '#104C35',
                            borderWidth: 2.5,
                            pointBackgroundColor: '#104C35',
                            pointBorderColor: '#fff',
                            pointHoverRadius: 6,
                            fill: true,
                            tension: 0.35
                        },
                        {
                            label: 'Target TDEE Goal (kcal)',
                            data: trends.target_calories_line,
                            borderColor: '#8A9A5B',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            pointRadius: 0,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                                usePointStyle: true,
                                boxWidth: 8
                            }
                        },
                        tooltip: {
                            backgroundColor: '#0B291B',
                            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 'bold' },
                            padding: 12,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(226, 232, 228, 0.6)' },
                            ticks: {
                                callback: val => `${val} kcal`,
                                font: { family: "'JetBrains Mono', monospace", size: 11 }
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } }
                        }
                    }
                }
            });

            // --- 2. Today's Macronutrient Distribution (Doughnut Chart) ---
            if (macroCanvas) {
                const macroCtx = macroCanvas.getContext('2d');
                const p = summary.nutrition.protein.consumed;
                const c = summary.nutrition.carbs.consumed;
                const f = summary.nutrition.fat.consumed;

                // Fallback to placeholder ratio if no food logged yet today
                const hasData = (p + c + f) > 0;
                const chartData = hasData ? [p, c, f] : [20, 55, 25];

                new Chart(macroCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Protein (g)', 'Carbohydrates (g)', 'Fats (g)'],
                        datasets: [{
                            data: chartData,
                            backgroundColor: ['#104C35', '#8A9A5B', '#6A8E7F'],
                            hoverOffset: 6,
                            borderWidth: 2,
                            borderColor: '#FFFFFF'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '72%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
                                    usePointStyle: true,
                                    padding: 16
                                }
                            },
                            tooltip: {
                                backgroundColor: '#0B291B',
                                padding: 10,
                                cornerRadius: 8
                            }
                        }
                    }
                });
            }

            // --- 3. Lifestyle Activity (Steps) & Sleep Trends ---
            if (lifestyleCanvas) {
                const lifeCtx = lifestyleCanvas.getContext('2d');

                new Chart(lifeCtx, {
                    type: 'bar',
                    data: {
                        labels: trends.labels,
                        datasets: [
                            {
                                label: 'Daily Steps',
                                data: trends.steps,
                                backgroundColor: 'rgba(16, 76, 53, 0.75)',
                                borderRadius: 6,
                                yAxisID: 'ySteps'
                            },
                            {
                                label: 'Sleep Hours',
                                data: trends.sleep_hours,
                                type: 'line',
                                borderColor: '#8A9A5B',
                                borderWidth: 2.5,
                                pointBackgroundColor: '#8A9A5B',
                                yAxisID: 'ySleep',
                                tension: 0.3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                                    usePointStyle: true,
                                    boxWidth: 8
                                }
                            },
                            tooltip: {
                                backgroundColor: '#0B291B',
                                padding: 12,
                                cornerRadius: 8
                            }
                        },
                        scales: {
                            ySteps: {
                                type: 'linear',
                                position: 'left',
                                beginAtZero: true,
                                grid: { color: 'rgba(226, 232, 228, 0.6)' },
                                ticks: { font: { family: "'JetBrains Mono', monospace", size: 11 } }
                            },
                            ySleep: {
                                type: 'linear',
                                position: 'right',
                                min: 0,
                                max: 12,
                                grid: { display: false },
                                ticks: {
                                    callback: val => `${val}h`,
                                    font: { family: "'JetBrains Mono', monospace", size: 11 }
                                }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error("Error loading dashboard analytics:", err));
});
