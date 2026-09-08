document.addEventListener('DOMContentLoaded', () => {
    // 1. Chart Handles
    let charts = {};
    
    // Fetch initial chart data and setup
    fetch('/api/charts/')
        .then(res => res.json())
        .then(data => {
            initializeCharts(data);
        })
        .catch(err => console.error("Error loading charts initial data:", err));
        
    function initializeCharts(data) {
        // Allowed vs Denied Pie Chart
        const ctxPie = document.getElementById('allowedDeniedChart');
        if (ctxPie) {
            charts.pie = new Chart(ctxPie, {
                type: 'pie',
                data: {
                    labels: data.allowed_vs_denied.labels,
                    datasets: [{
                        data: data.allowed_vs_denied.data,
                        backgroundColor: ['#10B981', '#EF4444'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // Pass Utilization Doughnut Chart
        const ctxDoughnut = document.getElementById('passUtilChart');
        if (ctxDoughnut) {
            charts.doughnut = new Chart(ctxDoughnut, {
                type: 'doughnut',
                data: {
                    labels: data.pass_utilization.labels,
                    datasets: [{
                        data: data.pass_utilization.data,
                        backgroundColor: ['#3B82F6', '#94A3B8'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // Top Colleges Bar Chart
        const ctxBar = document.getElementById('topCollegesChart');
        if (ctxBar) {
            charts.bar = new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: data.top_colleges.labels.length ? data.top_colleges.labels : ['No data'],
                    datasets: [{
                        label: 'Passes Checked In',
                        data: data.top_colleges.data.length ? data.top_colleges.data : [0],
                        backgroundColor: '#6366F1',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
    }

    // 2. Real-Time WebSocket Logic
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsScheme}://${window.location.host}/ws/dashboard/`;
    let ws = null;
    let isConnected = false;
    let pollingInterval = null;

    function connectWebSocket() {
        console.log("Connecting WebSocket to URL:", wsUrl);
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("WebSocket connection established.");
            isConnected = true;
            document.getElementById('live-status-indicator').innerHTML = '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1"><span class="pulse-dot"></span> Live (WS)</span>';
            
            // Stop AJAX Polling if active
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.event === 'scan') {
                // Update live feed table
                addLiveTableRow(data.log);
                // Update stats cards counts
                updateStatsCards(data.stats);
                // Play notification sound on dashboard view
                playScanSound(data.log.status === 'Allowed' ? 'success' : 'denied');
                // Show notification toast
                showToast(`New Scan: ${data.log.college_code} is ${data.log.status}!`, data.log.status === 'Allowed' ? 'success' : 'danger');
                // Refresh Chart datasets
                refreshChartData();
            }
        };

        ws.onclose = (e) => {
            console.warn("WebSocket closed. Reconnecting or falling back to polling...", e.reason);
            isConnected = false;
            document.getElementById('live-status-indicator').innerHTML = '<span class="badge bg-warning-subtle text-warning border border-warning-subtle rounded-pill px-2.5 py-1"><span class="pulse-dot-warning"></span> Polling (AJAX)</span>';
            
            // Fall back to AJAX Polling
            startPollingFallback();
            
            // Attempt to reconnect in 5 seconds
            setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (err) => {
            console.error("WebSocket encountered error: ", err.message);
            ws.close();
        };
    }

    // Try starting WebSocket Connection
    connectWebSocket();

    // 3. Fallback AJAX Polling Logic (every 2 seconds)
    function startPollingFallback() {
        if (pollingInterval) return; // Already polling
        
        console.log("Initializing fallback AJAX polling every 2 seconds.");
        pollingInterval = setInterval(() => {
            // Polling stats counts
            fetch('/api/dashboard-stats/')
                .then(res => res.json())
                .then(data => {
                    updateStatsCards(data);
                })
                .catch(err => console.error("Stats polling error:", err));

            // Polling recent logs table
            fetch('/api/recent-entries/')
                .then(res => res.json())
                .then(data => {
                    rebuildTable(data.entries);
                })
                .catch(err => console.error("Table logs polling error:", err));
        }, 2000);
    }

    // Helper: update card numbers
    function updateStatsCards(stats) {
        if (!stats) return;
        updateElementWithPop('count-colleges', stats.total_colleges);
        updateElementWithPop('count-total-passes', stats.total_passes);
        updateElementWithPop('count-used', stats.used_passes);
        updateElementWithPop('count-remaining', stats.remaining_passes);
        updateElementWithPop('count-rejected', stats.rejected_entries);
        updateElementWithPop('count-today', stats.today_entries);
    }

    function updateElementWithPop(id, newValue) {
        const el = document.getElementById(id);
        if (!el) return;
        const currentValue = el.textContent.trim();
        if (currentValue !== String(newValue)) {
            el.textContent = newValue;
            el.classList.remove('pop-number');
            void el.offsetWidth; // Trigger reflow to restart CSS animation
            el.classList.add('pop-number');
        }
    }

    // Helper: prepend row to table
    function addLiveTableRow(log) {
        const tbody = document.getElementById('live-entry-body');
        if (!tbody) return;
        
        // Remove empty row if exists
        const emptyRow = document.getElementById('empty-row-msg');
        if (emptyRow) emptyRow.remove();
        
        const tr = document.createElement('tr');
        tr.className = 'new-scan-row';
        tr.style.backgroundColor = log.status === 'Allowed' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)';
        tr.style.transition = 'background-color 1.5s ease';
        
        const statusBadge = log.status === 'Allowed' 
            ? '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1">Allowed</span>'
            : '<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1">Denied</span>';

        tr.innerHTML = `
            <td class="ps-4 fw-semibold">${log.time}</td>
            <td class="fw-bold">${log.college_name} <small class="text-muted">(${log.college_code})</small></td>
            <td class="text-center">${statusBadge}</td>
            <td>${log.volunteer}</td>
            <td class="text-center pe-4 fw-bold">${log.status === 'Allowed' ? log.remaining : '-'}</td>
        `;
        
        tbody.insertBefore(tr, tbody.firstChild);
        
        // Fade normal row background back after 2 seconds
        setTimeout(() => {
            tr.style.backgroundColor = 'transparent';
        }, 2000);

        // Keep table size limited to 20
        if (tbody.children.length > 20) {
            tbody.removeChild(tbody.lastChild);
        }
    }

    // Helper: rebuild entire table (for polling)
    function rebuildTable(entries) {
        const tbody = document.getElementById('live-entry-body');
        if (!tbody) return;
        
        if (!entries || entries.length === 0) {
            tbody.innerHTML = `
                <tr id="empty-row-msg">
                    <td colspan="5" class="text-center py-4 text-muted">No entry attempts recorded today.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        entries.forEach(log => {
            const tr = document.createElement('tr');
            const statusBadge = log.status === 'Allowed'
                ? '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1">Allowed</span>'
                : '<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1">Denied</span>';

            tr.innerHTML = `
                <td class="ps-4 fw-semibold">${log.time}</td>
                <td class="fw-bold">${log.college_name} <small class="text-muted">(${log.college_code})</small></td>
                <td class="text-center">${statusBadge}</td>
                <td>${log.volunteer}</td>
                <td class="text-center pe-4 fw-bold">${log.status === 'Allowed' ? log.remaining : '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Helper: refresh Chart.js data
    function refreshChartData() {
        fetch('/api/charts/')
            .then(res => res.json())
            .then(data => {
                if (charts.pie) {
                    charts.pie.data.datasets[0].data = data.allowed_vs_denied.data;
                    charts.pie.update();
                }
                if (charts.doughnut) {
                    charts.doughnut.data.datasets[0].data = data.pass_utilization.data;
                    charts.doughnut.update();
                }
                if (charts.bar) {
                    charts.bar.data.labels = data.top_colleges.labels;
                    charts.bar.data.datasets[0].data = data.top_colleges.data;
                    charts.bar.update();
                }
            })
            .catch(err => console.error("Error refreshing chart data:", err));
    }
});
