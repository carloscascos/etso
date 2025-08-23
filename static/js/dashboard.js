// Clean, modern dashboard JavaScript v2.0

class ObservatorioApp {
    constructor() {
        this.currentPage = 'overview';
        this.currentTheme = null;
        this.currentClaim = null;
        this.currentQuarter = 'Q1 2025';
        this.init();
    }

    init() {
        // Set up navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.showPage(btn.dataset.page));
        });

        // Set up quarter selector
        document.getElementById('quarter-selector').addEventListener('click', () => {
            document.getElementById('quarter-dialog').classList.add('active');
        });

        document.querySelectorAll('.quarter-grid button').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentQuarter = btn.dataset.quarter;
                document.getElementById('quarter-selector').textContent = this.currentQuarter;
                document.getElementById('quarter-dialog').classList.remove('active');
                this.loadData();
            });
        });

        // Load initial data
        this.loadData();
    }

    showPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        // Show page
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });
        document.getElementById(`page-${page}`).classList.add('active');

        this.currentPage = page;
        this.loadPageData(page);
    }

    async loadData() {
        this.loadOverview();
        this.loadThemes();
    }

    async loadPageData(page) {
        switch(page) {
            case 'overview':
                await this.loadOverview();
                break;
            case 'themes':
                await this.loadThemes();
                break;
            case 'details':
                if (this.currentTheme) {
                    await this.loadDetails(this.currentTheme);
                }
                break;
            case 'claims':
                if (this.currentClaim) {
                    await this.loadClaim(this.currentClaim);
                }
                break;
        }
    }

    async loadOverview() {
        try {
            const response = await fetch('/api/overview');
            const data = await response.json();
            
            document.getElementById('total-themes').textContent = data.total_themes || 0;
            document.getElementById('total-claims').textContent = data.total_claims || 0;
            document.getElementById('avg-confidence').textContent = `${Math.round(data.avg_confidence || 0)}%`;
            document.getElementById('validation-rate').textContent = `${Math.round(data.validation_rate || 0)}%`;
            
            // Load recent activity
            const activityHtml = data.recent_activity?.map(item => `
                <div class="activity-item">
                    <span class="activity-time">${this.formatTime(item.created_at)}</span>
                    <span class="activity-text">${item.description}</span>
                </div>
            `).join('') || '<p>No recent activity</p>';
            
            document.getElementById('recent-activity').innerHTML = activityHtml;
        } catch (error) {
            console.error('Error loading overview:', error);
        }
    }

    async loadThemes() {
        try {
            const response = await fetch('/api/themes');
            const themes = await response.json();
            
            const themesHtml = Object.entries(themes).flatMap(([type, themeList]) => 
                themeList.map(theme => `
                    <div class="theme-card">
                        <div class="theme-header" onclick="app.viewTheme(${theme.id})">
                            <div class="theme-title">${theme.id}: ${theme.theme_title || 'Untitled'}</div>
                            <div class="theme-meta">
                                <span>${theme.quarter}</span>
                                <span>${theme.claim_count} claims</span>
                                <span>${Math.round(theme.overall_confidence * 100)}% confidence</span>
                                <span class="status-badge status-${theme.status}">${theme.status}</span>
                            </div>
                        </div>
                        <div class="theme-actions">
                            <button class="btn-small btn-primary" onclick="app.runTheme(${theme.id}); event.stopPropagation();">▶️ Run</button>
                            <button class="btn-small btn-secondary" onclick="app.editTheme(${theme.id}); event.stopPropagation();">✏️ Edit</button>
                            <button class="btn-small" onclick="app.viewTheme(${theme.id}); event.stopPropagation();">👁️ View</button>
                        </div>
                    </div>
                `)
            ).join('');
            
            document.getElementById('themes-list').innerHTML = themesHtml || '<p>No themes found</p>';
        } catch (error) {
            console.error('Error loading themes:', error);
        }
    }

    async viewTheme(themeId) {
        this.currentTheme = themeId;
        this.showPage('details');
        await this.loadDetails(themeId);
    }

    async loadDetails(themeId) {
        try {
            const response = await fetch(`/api/research/${themeId}`);
            const data = await response.json();
            
            // Update title
            document.getElementById('detail-title').textContent = 
                data.metadata.theme_title || `Theme ${themeId}`;
            
            // 1. Research Guidance
            document.getElementById('research-guidance').innerHTML = 
                data.metadata.user_guidance || '<p class="empty-state">No research guidance provided</p>';
            
            // 2. Research Results
            const researchContent = data.research_content || data.metadata.research_content_preview;
            if (researchContent) {
                document.getElementById('research-results').innerHTML = 
                    this.parseContentWithSources(researchContent);
            } else {
                document.getElementById('research-results').innerHTML = 
                    '<p class="empty-state">No research results generated yet</p>';
            }
            
            // 3. References
            const references = data.metadata.sources || [];
            if (references.length > 0) {
                const referencesHtml = references.map((ref, index) => `
                    <div class="reference-item">
                        <span class="ref-number">[${index + 1}]</span>
                        <a href="${ref.url || '#'}" target="_blank" rel="noopener">
                            ${ref.title || ref.url || 'Unknown source'}
                        </a>
                    </div>
                `).join('');
                document.getElementById('research-references').innerHTML = referencesHtml;
            } else {
                document.getElementById('research-references').innerHTML = 
                    '<p class="empty-state">No references available</p>';
            }
            
            // 4. Display claims
            if (data.claims && data.claims.length > 0) {
                const claimsHtml = data.claims.map(claim => `
                    <div class="claim-card" onclick="app.viewClaim(${claim.id})">
                        <div class="claim-header">
                            <span class="claim-status ${claim.supports_claim ? 'validated' : 'pending'}">
                                ${claim.supports_claim ? 'Validated' : 'Pending'}
                            </span>
                            <span class="claim-weight">${Math.round(claim.validation_weight || 50)}%</span>
                        </div>
                        <div class="claim-preview">${claim.claim_text?.substring(0, 120)}...</div>
                        <div class="claim-meta">
                            Confidence: ${Math.round(claim.confidence_score * 100)}%
                        </div>
                    </div>
                `).join('');
                document.getElementById('claims-list').innerHTML = claimsHtml;
                
                // 5. Validation Summary
                const totalClaims = data.claims.length;
                const validatedClaims = data.claims.filter(c => c.supports_claim).length;
                const avgConfidence = data.claims.reduce((sum, c) => sum + (c.confidence_score || 0), 0) / totalClaims;
                const avgWeight = data.claims.reduce((sum, c) => sum + (c.validation_weight || 50), 0) / totalClaims;
                
                document.getElementById('validation-summary').innerHTML = `
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <span class="stat-label">Total Claims:</span>
                            <span class="stat-value">${totalClaims}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Validated:</span>
                            <span class="stat-value">${validatedClaims} (${Math.round(validatedClaims/totalClaims*100)}%)</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Avg Confidence:</span>
                            <span class="stat-value">${Math.round(avgConfidence * 100)}%</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Avg Weight:</span>
                            <span class="stat-value">${Math.round(avgWeight)}%</span>
                        </div>
                    </div>
                `;
            } else {
                document.getElementById('claims-list').innerHTML = 
                    '<p class="empty-state">No claims generated yet</p>';
                document.getElementById('validation-summary').innerHTML = 
                    '<p class="empty-state">No validation data available</p>';
            }
            
        } catch (error) {
            console.error('Error loading details:', error);
        }
    }

    parseContentWithSources(content) {
        // Convert markdown to HTML
        if (typeof marked !== 'undefined') {
            content = marked.parse(content);
        }
        
        // Convert URLs to clickable links
        content = content.replace(
            /(https?:\/\/[^\s<]+)/g, 
            '<a href="$1" target="_blank" rel="noopener">$1</a>'
        );
        
        // Add source references as superscript links
        content = content.replace(
            /\[(\d+)\]/g,
            '<sup><a href="#source-$1">[$1]</a></sup>'
        );
        
        return content;
    }

    async viewClaim(claimId) {
        this.currentClaim = claimId;
        this.showPage('claims');
        await this.loadClaim(claimId);
    }

    async loadClaim(claimId) {
        try {
            const response = await fetch(`/api/claims/${claimId}`);
            const data = await response.json();
            const claim = data.claim;
            
            // Update breadcrumb
            document.getElementById('claim-title').textContent = `Claim ${claimId}`;
            
            // Display claim details
            document.getElementById('claim-text').textContent = claim.claim_text || '';
            document.getElementById('validation-logic').value = claim.validation_logic || '';
            document.getElementById('claim-sql').textContent = claim.validation_query || 'No SQL generated yet';
            
            // Set weight
            const weight = claim.validation_weight || 50;
            document.getElementById('weight-slider').value = weight;
            document.getElementById('weight-value').textContent = weight;
            
            // Display results
            if (claim.data_points_found) {
                document.getElementById('validation-results').innerHTML = `
                    <div class="results-summary">
                        <p>Data points found: ${claim.data_points_found}</p>
                        <p>Supports claim: ${claim.supports_claim ? 'Yes' : 'No'}</p>
                        <p>Confidence: ${Math.round(claim.confidence_score * 100)}%</p>
                    </div>
                `;
            } else {
                document.getElementById('validation-results').innerHTML = '<p>No validation results yet</p>';
            }
            
            // Display conclusion
            document.getElementById('validation-conclusion').innerHTML = 
                claim.analysis_text || '<p>No conclusion generated yet</p>';
                
        } catch (error) {
            console.error('Error loading claim:', error);
        }
    }

    updateWeight(value) {
        document.getElementById('weight-value').textContent = value;
    }

    async regenerateSQL() {
        const logic = document.getElementById('validation-logic').value;
        if (!logic) {
            alert('Please enter validation logic first');
            return;
        }

        try {
            const response = await fetch('/api/build-sql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ validation_logic: logic })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('claim-sql').textContent = data.query;
            } else {
                alert('Error generating SQL: ' + data.error);
            }
        } catch (error) {
            console.error('Error regenerating SQL:', error);
        }
    }

    async runValidation() {
        const sql = document.getElementById('claim-sql').textContent;
        if (!sql || sql === 'No SQL generated yet') {
            alert('Please generate SQL first');
            return;
        }

        try {
            const response = await fetch('/api/execute-sql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql_query: sql })
            });
            
            const data = await response.json();
            if (data.success) {
                // Display results
                const resultsHtml = `
                    <div class="results-summary">
                        <p>Rows returned: ${data.row_count}</p>
                        <p>Execution time: ${data.execution_time}ms</p>
                    </div>
                    <pre>${JSON.stringify(data.results, null, 2)}</pre>
                `;
                document.getElementById('validation-results').innerHTML = resultsHtml;
                
                // Generate conclusion
                await this.generateConclusion(data.results);
            } else {
                alert('Error executing SQL: ' + data.error);
            }
        } catch (error) {
            console.error('Error running validation:', error);
        }
    }

    async generateConclusion(results) {
        try {
            const response = await fetch('/api/generate-claim-conclusion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    claim_id: this.currentClaim,
                    claim_text: document.getElementById('claim-text').textContent,
                    validation_logic: document.getElementById('validation-logic').value,
                    sql_query: document.getElementById('claim-sql').textContent,
                    query_results: results
                })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('validation-conclusion').innerHTML = 
                    `<div class="conclusion">${data.conclusion}</div>`;
            }
        } catch (error) {
            console.error('Error generating conclusion:', error);
        }
    }

    async saveClaim() {
        try {
            const response = await fetch(`/api/claims/${this.currentClaim}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    validation_logic: document.getElementById('validation-logic').value,
                    validation_weight: document.getElementById('weight-slider').value,
                    validation_query: document.getElementById('claim-sql').textContent
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Claim saved successfully');
            } else {
                alert('Error saving claim: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving claim:', error);
        }
    }

    showNewThemeDialog() {
        document.getElementById('new-theme-dialog').classList.add('active');
    }

    closeDialog() {
        document.querySelectorAll('.dialog').forEach(d => d.classList.remove('active'));
    }

    async runTheme(themeId) {
        try {
            const response = await fetch(`/api/research/${themeId}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quarter: this.currentQuarter })
            });
            
            const data = await response.json();
            if (data.success) {
                await this.loadThemes(); // Refresh to show status
            } else {
                alert('Error running research: ' + data.error);
            }
        } catch (error) {
            console.error('Error running theme:', error);
            alert('Error running research');
        }
    }

    async runCurrentResearch() {
        if (!this.currentTheme) {
            alert('No theme selected');
            return;
        }

        // Update button to show running state
        const runBtn = document.getElementById('run-research-btn');
        const originalText = runBtn.innerHTML;
        runBtn.innerHTML = '⏳ Running...';
        runBtn.disabled = true;

        try {
            const response = await fetch(`/api/research/${this.currentTheme}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    quarter: this.currentQuarter,
                    merge_previous: true // Flag for content merging
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Reload the details to show updated content
                await this.loadDetails(this.currentTheme);
            } else {
                alert('Error running research: ' + data.error);
            }
        } catch (error) {
            console.error('Error running research:', error);
            alert('Error running research');
        } finally {
            // Restore button
            runBtn.innerHTML = originalText;
            runBtn.disabled = false;
        }
    }

    async editTheme(themeId) {
        try {
            const response = await fetch(`/api/research/${themeId}`);
            const data = await response.json();
            
            // Show edit dialog
            document.getElementById('edit-theme-input').value = data.metadata.user_guidance || '';
            document.getElementById('edit-theme-title').value = data.metadata.theme_title || '';
            document.getElementById('edit-theme-dialog').classList.add('active');
            this.editingThemeId = themeId;
        } catch (error) {
            console.error('Error loading theme for edit:', error);
        }
    }

    async saveThemeEdit() {
        try {
            const response = await fetch(`/api/research/${this.editingThemeId}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_guidance: document.getElementById('edit-theme-input').value,
                    theme_title: document.getElementById('edit-theme-title').value
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.closeDialog();
                await this.loadThemes();
                alert('Theme updated successfully');
            } else {
                alert('Error updating theme: ' + data.error);
            }
        } catch (error) {
            console.error('Error updating theme:', error);
        }
    }

    async createTheme() {
        const input = document.getElementById('new-theme-input').value;
        if (!input) return;

        try {
            const response = await fetch('/api/research/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: input, quarter: this.currentQuarter })
            });
            
            const data = await response.json();
            if (data.success) {
                this.closeDialog();
                await this.loadThemes();
                alert('Theme created successfully');
            } else {
                alert('Error creating theme: ' + data.error);
            }
        } catch (error) {
            console.error('Error creating theme:', error);
        }
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

// Initialize app
const app = new ObservatorioApp();