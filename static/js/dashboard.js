// OBSERVATORIO ETS Dashboard JavaScript
class ObservatorioDashboard {
    constructor() {
        this.currentView = 'overview';
        this.currentResearchId = null;
        this.executionStatusInterval = null;
        this.executingThemes = new Set(); // Track themes currently being executed
        this.currentQueryResults = null; // Store current query results for copying
        this.isEditingQuery = false; // Track if query is in edit mode
        this.currentClaimId = null; // Store current claim ID for custom queries
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadOverviewData();
        
        // Auto-refresh data every 30 seconds
        setInterval(() => {
            if (this.currentView === 'overview') {
                this.loadOverviewData();
            }
        }, 30000);
    }
    
    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });
        
        // View themes button
        document.getElementById('view-themes-btn').addEventListener('click', () => {
            this.switchView('themes');
        });
        
        // Back to themes button
        document.getElementById('back-to-themes').addEventListener('click', () => {
            this.switchView('themes');
        });
        
        // Modal close buttons
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.target.closest('.modal').classList.remove('show');
            });
        });
        
        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });
        
        // Theme search and filtering
        document.getElementById('theme-search').addEventListener('input', (e) => {
            this.filterThemes(e.target.value);
        });
        
        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.filterThemes(document.getElementById('theme-search').value, e.target.value);
        });
        
        // Execute query results button
        document.getElementById('execute-query-btn').addEventListener('click', () => {
            const claimId = document.getElementById('execute-query-btn').dataset.claimId;
            if (claimId) {
                this.loadQueryResults(claimId);
            }
        });
        
        // Add validation form handlers
        document.getElementById('test-query-btn').addEventListener('click', () => {
            this.testValidationQuery();
        });
        
        document.getElementById('validation-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createValidationClaim();
        });
        
        // Theme editor event listeners
        document.getElementById('merge-prompts-checkbox').addEventListener('change', () => {
            this.togglePromptMerge();
        });
        
        document.getElementById('preview-merged-btn').addEventListener('click', () => {
            this.togglePromptMerge();
        });
        
        document.getElementById('save-theme-btn').addEventListener('click', () => {
            this.saveThemeChanges();
        });
        
        document.getElementById('generate-claims-btn').addEventListener('click', () => {
            this.generateValidationClaims();
        });
    }
    
    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
        
        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');
        
        this.currentView = viewName;
        
        // Load view-specific data
        switch (viewName) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'themes':
                this.loadThemes();
                break;
            case 'research':
                if (this.currentResearchId) {
                    this.loadResearchDetails(this.currentResearchId);
                }
                break;
        }
    }
    
    async loadOverviewData() {
        try {
            // Load summary stats
            const summary = await this.fetchAPI('/api/summary');
            this.updateSummaryCards(summary);
            
            // Load recent findings
            const findings = await this.fetchAPI('/api/research-findings');
            this.displayFindings(findings);
            
            // Load validation status
            const validations = await this.fetchAPI('/api/validation-status');
            this.displayValidationStatus(validations);
            
            // System health removed - no longer needed
            // const health = await this.fetchAPI('/api/system-health');
            // this.displaySystemHealth(health);
            
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async loadThemes() {
        try {
            const themes = await this.fetchAPI('/api/themes');
            this.displayThemes(themes);
        } catch (error) {
            console.error('Error loading themes:', error);
            this.showError('Failed to load themes');
        }
    }
    
    async loadResearchDetails(researchId) {
        try {
            const research = await this.fetchAPI(`/api/research/${researchId}`);
            this.displayResearchDetails(research);
        } catch (error) {
            console.error('Error loading research details:', error);
            this.showError('Failed to load research details');
        }
    }
    
    updateSummaryCards(summary) {
        document.getElementById('current-quarter').textContent = summary.quarter || 'Q1 2025';
        document.getElementById('total-findings').textContent = summary.total_findings || 0;
        document.getElementById('completed-findings').textContent = summary.completed || 0;
        document.getElementById('validating-findings').textContent = summary.validating || 0;
        document.getElementById('avg-confidence').textContent = `${Math.round((summary.avg_confidence || 0) * 100)}%`;
        
        if (summary.last_research) {
            const lastUpdate = new Date(summary.last_research);
            document.getElementById('last-update').textContent = `Last update: ${lastUpdate.toLocaleString()}`;
        }
    }
    
    displayFindings(findings) {
        const container = document.getElementById('findings-list');
        const countBadge = document.getElementById('findings-count');
        
        countBadge.textContent = findings.length;
        
        if (findings.length === 0) {
            container.innerHTML = '<div class="loading">No research findings found</div>';
            return;
        }
        
        container.innerHTML = findings.map(finding => `
            <div class="finding-item" onclick="dashboard.viewResearch(${finding.id})">
                <div class="finding-header">
                    <span class="finding-theme-mini">${finding.theme_type.toUpperCase()}</span>
                    <span class="finding-status-mini ${finding.status}">${finding.status}</span>
                </div>
                <div class="finding-guidance">${finding.user_guidance || 'No guidance provided'}</div>
                <div class="finding-meta">
                    <span>ID: ${finding.id}</span>
                    <span>Claims: ${finding.claim_count}</span>
                    <span>Confidence: ${Math.round((finding.overall_confidence || 0) * 100)}%</span>
                    <span>${new Date(finding.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    }
    
    displayValidationStatus(validations) {
        // Calculate pending validations
        let totalPending = 0;
        let totalValidated = 0;
        
        // Calculate totals for pending badge
        validations.forEach(validation => {
            if (!validation.avg_confidence || validation.avg_confidence === 0) {
                totalPending += validation.total_claims;
            } else {
                totalValidated += validation.total_claims;
            }
        });
        
        // We removed the validation-stats container, so no need to update it
        
        // Update pending badge
        const pendingBadge = document.getElementById('pending-validations');
        if (pendingBadge) {
            pendingBadge.textContent = `${totalPending} pending`;
            pendingBadge.style.display = totalPending > 0 ? 'inline-block' : 'none';
        }
        
        // Show/hide run validation button
        const runBtn = document.getElementById('run-validation-btn');
        if (runBtn) {
            runBtn.style.display = totalPending > 0 ? 'inline-flex' : 'none';
        }
    }
    
    // System health display removed - no longer needed
    // displaySystemHealth(health) {
    //     const healthMap = {
    //         'traffic-db-status': health.databases?.traffic_db,
    //         'etso-db-status': health.databases?.etso_db,
    //         'chromadb-status': health.databases?.chromadb
    //     };
    //     
    //     Object.entries(healthMap).forEach(([elementId, status]) => {
    //         const indicator = document.getElementById(elementId);
    //         if (indicator) {
    //             indicator.className = `indicator ${status ? 'healthy' : ''}`;
    //         }
    //     });
    // }
    
    displayThemes(themes) {
        const container = document.getElementById('themes-grid');
        
        // Add new research form
        const newResearchHTML = `
            <div class="new-research-section">
                <h4>🔬 Start New Research</h4>
                <div class="new-research-form">
                    <input type="text" id="new-research-input" class="new-research-input" 
                           placeholder="Enter research theme (e.g., 'Impact of Red Sea crisis on container shipping routes')">
                    <button class="btn btn-success" onclick="dashboard.executeNewResearch()">
                        ▶️ Execute Research
                    </button>
                </div>
                <div id="execution-status-container"></div>
            </div>
        `;
        
        // Group themes by category
        const themeCategories = Object.entries(themes).map(([type, themeList]) => `
            <div class="theme-category" data-category="${type}">
                <div class="theme-category-header">
                    <h3>${type.replace('_', ' ').toUpperCase()} Themes</h3>
                    <span class="badge">${themeList.length}</span>
                </div>
                <div class="theme-items">
                    ${themeList.map(theme => this.renderThemeItem(theme)).join('')}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = newResearchHTML + themeCategories;
        
        // Add enter key listener to new research input
        document.getElementById('new-research-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeNewResearch();
            }
        });
    }
    
    renderThemeItem(theme) {
        const confidenceClass = this.getConfidenceLevel(theme.overall_confidence);
        const confidenceText = Math.round((theme.overall_confidence || 0) * 100);
        const isExecuting = this.executingThemes.has(theme.id);
        
        // Determine button state based on theme status and execution state
        let rerunButton = '';
        if (isExecuting) {
            rerunButton = `
                <button class="btn btn-sm btn-warning" disabled>
                    <span class="spinner"></span> Executing...
                </button>
            `;
        } else if (theme.status === 'validating') {
            rerunButton = `
                <button class="btn btn-sm btn-warning" disabled>
                    <span class="spinner"></span> Validating...
                </button>
            `;
        } else if (theme.status === 'completed' || theme.status === 'pending') {
            rerunButton = `
                <button class="btn btn-sm btn-warning" onclick="dashboard.reRunTheme(${theme.id})">
                    🔄 Re-run
                </button>
            `;
        }
        
        return `
            <div class="theme-item" data-theme-id="${theme.id}">
                <div class="theme-item-header">
                    <span class="theme-id">Theme ${theme.id}</span>
                    <div class="theme-actions">
                        <button class="btn btn-sm btn-primary" onclick="dashboard.viewResearch(${theme.id})">
                            🔍 View Details
                        </button>
                        ${rerunButton}
                    </div>
                </div>
                <div class="theme-guidance">${theme.user_guidance || 'No research prompt provided'}</div>
                <div class="theme-stats">
                    <span class="finding-status ${theme.status}">${theme.status}</span>
                    <span class="theme-confidence confidence-${confidenceClass}">${confidenceText}% confidence</span>
                    <span>${theme.claim_count} claims</span>
                    <span>${theme.supported_claims} supported</span>
                    <span>${new Date(theme.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `;
    }
    
    displayResearchDetails(research) {
        const { metadata, claims, research_content } = research;
        
        // Update research title
        document.getElementById('research-title').textContent = 
            `Research ${metadata.id}: ${metadata.theme_type.toUpperCase()}`;
        
        // Display metadata
        const metadataContainer = document.getElementById('research-metadata-content');
        metadataContainer.innerHTML = `
            <div class="metadata-grid">
                <div class="metadata-item">
                    <span class="metadata-label">ID</span>
                    <span class="metadata-value">${metadata.id}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Type</span>
                    <span class="metadata-value">${metadata.theme_type.replace('_', ' ').toUpperCase()}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Status</span>
                    <span class="metadata-value">
                        <span class="finding-status ${metadata.status}">${metadata.status}</span>
                    </span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Confidence</span>
                    <span class="metadata-value confidence-${this.getConfidenceLevel(metadata.overall_confidence)}">
                        ${Math.round((metadata.overall_confidence || 0) * 100)}%
                    </span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Quarter</span>
                    <span class="metadata-value">${metadata.quarter}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Created</span>
                    <span class="metadata-value">${new Date(metadata.created_at).toLocaleString()}</span>
                </div>
            </div>
            
            <div style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top: 16px;">
                <div class="prompt-section">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="metadata-label">Research Prompt</span>
                        <button class="btn btn-sm btn-primary" onclick="dashboard.togglePromptEdit(${metadata.id})">
                            ✏️ Edit
                        </button>
                    </div>
                    <div id="prompt-display-${metadata.id}" class="metadata-value" style="white-space: pre-wrap; position: relative;">
                        ${metadata.user_guidance || 'No research prompt provided'}
                    </div>
                    <div id="prompt-edit-${metadata.id}" style="display: none;">
                        <textarea id="prompt-textarea-${metadata.id}" class="form-textarea" rows="6" 
                                  style="width: 100%; margin: 8px 0; font-family: inherit;"
                                  placeholder="Enter your research prompt...">${metadata.user_guidance || ''}</textarea>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-sm btn-success" onclick="dashboard.savePrompt(${metadata.id})">
                                💾 Save Prompt
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="dashboard.cancelPromptEdit(${metadata.id})">
                                Cancel
                            </button>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: flex-end; margin-top: 12px;">
                        <button class="btn btn-primary" onclick="dashboard.runResearch(${metadata.id}, '${metadata.quarter}')">
                            ▶️ RUN Research
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Display research content
        const contentContainer = document.getElementById('research-full-content');
        if (research_content) {
            // Use marked.js to parse markdown if available, otherwise fallback to basic formatting
            if (window.marked) {
                contentContainer.innerHTML = marked.parse(research_content);
            } else {
                contentContainer.innerHTML = this.formatTextContent(research_content);
            }
        } else if (metadata.research_content_preview) {
            if (window.marked) {
                contentContainer.innerHTML = marked.parse(metadata.research_content_preview);
            } else {
                contentContainer.innerHTML = this.formatTextContent(metadata.research_content_preview);
            }
        } else {
            contentContainer.innerHTML = '<div class="loading">Research content not available</div>';
        }
        
        // Display claims
        this.displayClaims(claims);
    }
    
    displayClaims(claims) {
        const container = document.getElementById('claims-list');
        const countBadge = document.getElementById('claims-count');
        
        countBadge.textContent = claims.length;
        
        if (claims.length === 0) {
            container.innerHTML = '<div class="loading">No validation claims found</div>';
            return;
        }
        
        container.innerHTML = claims.map(claim => `
            <div class="claim-item">
                <div class="claim-header">
                    <span class="claim-type">${claim.claim_type.replace('_', ' ')}</span>
                    <span class="claim-confidence confidence-${this.getConfidenceLevel(claim.confidence_score)}">
                        ${Math.round((claim.confidence_score || 0) * 100)}% confidence
                    </span>
                </div>
                <div class="claim-text">${claim.claim_text}</div>
                ${claim.analysis_text ? `
                    <div class="claim-analysis" style="margin-bottom: 12px; font-size: 0.875rem; color: #6c757d;">
                        <strong>Analysis:</strong> ${claim.analysis_text}
                    </div>
                ` : ''}
                <div class="claim-meta">
                    <div>
                        <span>Data Points: ${claim.data_points_found || 0}</span>
                        <span>Supported: ${claim.supports_claim ? '✅ Yes' : claim.supports_claim === false ? '❌ No' : '⏳ Pending'}</span>
                        ${claim.validation_timestamp ? `<span>Validated: ${new Date(claim.validation_timestamp).toLocaleString()}</span>` : ''}
                    </div>
                    ${claim.validation_query ? `
                        <button class="view-query-btn" onclick="dashboard.showQueryModal(${claim.id}, '${claim.claim_text.replace(/'/g, "\\'")}', ${claim.confidence_score || 0}, ${claim.data_points_found || 0})">
                            View SQL Query
                        </button>
                    ` : ''}
                    ${(!claim.confidence_score || claim.confidence_score === 0) ? `
                        <button class="btn btn-sm btn-info" onclick="dashboard.runSingleValidation(${claim.id})">
                            🔍 Run Analysis
                        </button>
                    ` : ''}
                </div>
                ${claim.vessel_filter || claim.route_filter || claim.period_filter ? `
                    <div style="margin-top: 8px; font-size: 0.75rem; color: #868e96;">
                        Filters: 
                        ${claim.vessel_filter ? `Vessel: ${claim.vessel_filter}` : ''}
                        ${claim.route_filter ? `Route: ${claim.route_filter}` : ''}
                        ${claim.period_filter ? `Period: ${claim.period_filter}` : ''}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    async executeNewResearch() {
        const input = document.getElementById('new-research-input');
        const theme = input.value.trim();
        
        if (!theme) {
            alert('Please enter a research theme');
            return;
        }
        
        const statusContainer = document.getElementById('execution-status-container');
        const executeButton = document.querySelector('.new-research-form .btn-success');
        
        try {
            // Disable execute button and show loading
            executeButton.innerHTML = '<span class="spinner"></span> Executing...';
            executeButton.disabled = true;
            
            // Show execution status
            statusContainer.innerHTML = `
                <div class="execution-status running">
                    <span class="spinner"></span>
                    Executing research for: "${theme}"
                </div>
            `;
            
            // Start research execution
            const response = await fetch('/api/execute-research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme, quarter: '2025Q1' })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Show success and research ID
            statusContainer.innerHTML = `
                <div class="execution-status completed">
                    ✅ Research execution started successfully! 
                    Research ID: ${result.research_id}
                    <button class="btn btn-sm btn-primary" onclick="dashboard.viewResearch(${result.research_id})" style="margin-left: 12px;">
                        View Progress
                    </button>
                </div>
            `;
            
            // Clear input
            input.value = '';
            
            // Start monitoring execution status
            if (result.research_id !== 'pending') {
                this.startExecutionMonitoring(result.research_id);
            }
            
            // Reload themes after a short delay
            setTimeout(() => {
                this.loadThemes();
            }, 2000);
            
        } catch (error) {
            console.error('Error executing research:', error);
            statusContainer.innerHTML = `
                <div class="execution-status error">
                    ❌ Error executing research: ${error.message}
                </div>
            `;
        } finally {
            // Re-enable execute button
            executeButton.innerHTML = '▶️ Execute Research';
            executeButton.disabled = false;
        }
    }
    
    async reRunTheme(themeId) {
        if (!confirm('Are you sure you want to re-run this theme? This will start a new research and validation process.')) {
            return;
        }
        
        try {
            // Mark theme as executing and update UI
            this.executingThemes.add(themeId);
            this.updateThemeButton(themeId, 'executing');
            
            const response = await fetch(`/api/rerun-theme/${themeId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Start monitoring execution status
            if (result.research_id !== 'pending') {
                this.startExecutionMonitoring(result.research_id, themeId);
            }
            
            // Show success message
            this.showSuccessMessage(`Theme ${themeId} re-execution started! Research ID: ${result.research_id}`);
            
            // Reload themes to get updated status
            setTimeout(() => {
                this.loadThemes();
            }, 2000);
            
        } catch (error) {
            console.error('Error re-running theme:', error);
            
            // Remove from executing set on error
            this.executingThemes.delete(themeId);
            this.updateThemeButton(themeId, 'error');
            
            alert(`Error re-running theme: ${error.message}`);
        }
    }
    
    viewResearch(researchId) {
        this.currentResearchId = researchId;
        this.switchView('research');
    }
    
    showQueryModal(claimId, claimText, confidence, dataPoints) {
        // Set modal data
        document.getElementById('modal-claim-text').textContent = claimText;
        document.getElementById('modal-confidence').textContent = `${Math.round((confidence || 0) * 100)}%`;
        document.getElementById('modal-data-points').textContent = dataPoints || 0;
        document.getElementById('execute-query-btn').dataset.claimId = claimId;
        
        // Store current claim ID for custom queries
        this.currentClaimId = claimId;
        
        // Reset edit mode
        this.isEditingQuery = false;
        document.getElementById('query-readonly').classList.remove('hidden');
        document.getElementById('query-editor').classList.add('hidden');
        document.getElementById('execute-custom-btn').classList.add('hidden');
        document.getElementById('edit-query-btn').innerHTML = '✏️ Edit Query';
        
        // Load and display SQL query
        this.loadClaimQuery(claimId);
        
        // Show modal
        document.getElementById('query-modal').classList.add('show');
    }
    
    async loadClaimQuery(claimId) {
        try {
            const response = await fetch(`/api/research/claim/${claimId}`);
            const claim = await response.json();
            
            // Display validation logic
            const validationLogicElement = document.getElementById('modal-validation-logic');
            if (claim.validation_logic) {
                validationLogicElement.textContent = claim.validation_logic;
            } else {
                validationLogicElement.textContent = 'Validation logic not available';
                validationLogicElement.style.fontStyle = 'italic';
                validationLogicElement.style.color = '#868e96';
            }
            
            // Display SQL query
            if (claim.validation_query) {
                const sqlElement = document.getElementById('modal-sql-query');
                sqlElement.textContent = claim.validation_query;
                
                // Apply syntax highlighting if Prism is available
                if (window.Prism) {
                    Prism.highlightElement(sqlElement);
                }
            } else {
                document.getElementById('modal-sql-query').textContent = 'SQL query not available';
            }
            
        } catch (error) {
            console.error('Error loading claim query:', error);
            document.getElementById('modal-sql-query').textContent = 'Error loading query';
            document.getElementById('modal-validation-logic').textContent = 'Error loading validation logic';
        }
    }
    
    async loadQueryResults(claimId) {
        const resultsContainer = document.getElementById('query-results-container');
        const loadingDiv = document.getElementById('results-loading');
        const errorDiv = document.getElementById('results-error');
        const tableContainer = document.getElementById('results-table-container');
        
        // Show loading state
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        tableContainer.classList.add('hidden');
        
        try {
            const response = await fetch(`/api/claim/${claimId}/results`);
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Hide loading
            loadingDiv.classList.add('hidden');
            
            // Update results count
            document.getElementById('results-count').textContent = result.result_count || 0;
            
            // Display results table
            if (result.query_results && result.query_results.length > 0) {
                const table = document.getElementById('results-table');
                const headers = Object.keys(result.query_results[0]);
                
                table.innerHTML = `
                    <thead>
                        <tr>
                            ${headers.map(header => `<th>${header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${result.query_results.map(row => `
                            <tr>
                                ${headers.map(header => `<td>${this.formatCellValue(row[header])}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                `;
                
                // Store results for copying
                this.currentQueryResults = result.query_results;
                
                // Show copy button and table
                document.getElementById('copy-results-btn').classList.remove('hidden');
                tableContainer.classList.remove('hidden');
            } else {
                document.getElementById('copy-results-btn').classList.add('hidden');
                errorDiv.textContent = 'No results returned by the query';
                errorDiv.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('Error loading query results:', error);
            loadingDiv.classList.add('hidden');
            errorDiv.textContent = `Error loading results: ${error.message}`;
            errorDiv.classList.remove('hidden');
        }
    }
    
    filterThemes(searchTerm = '', statusFilter = '') {
        const categories = document.querySelectorAll('.theme-category');
        
        categories.forEach(category => {
            const items = category.querySelectorAll('.theme-item');
            let visibleItems = 0;
            
            items.forEach(item => {
                const guidance = item.querySelector('.theme-guidance').textContent.toLowerCase();
                const status = item.querySelector('.finding-status').textContent;
                
                const matchesSearch = !searchTerm || guidance.includes(searchTerm.toLowerCase());
                const matchesStatus = !statusFilter || status === statusFilter;
                
                if (matchesSearch && matchesStatus) {
                    item.style.display = 'block';
                    visibleItems++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Hide category if no visible items
            category.style.display = visibleItems > 0 ? 'block' : 'none';
        });
    }
    
    // Utility methods
    getConfidenceLevel(confidence) {
        const conf = confidence || 0;
        if (conf >= 0.8) return 'high';
        if (conf >= 0.5) return 'medium';
        return 'low';
    }
    
    formatTextContent(content) {
        // Basic text formatting for when markdown parser isn't available
        if (!content) return '';
        
        return content
            // Convert markdown headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Convert bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // Convert italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            // Convert lists
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            // Wrap consecutive list items in ul tags
            .replace(/((<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>')
            // Convert line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Wrap in paragraphs
            .replace(/^(.)/gm, '<p>$1')
            .replace(/(.)$/gm, '$1</p>')
            // Clean up multiple paragraph tags
            .replace(/<\/p><p>/g, '</p>\n<p>')
            // Fix list items inside paragraphs
            .replace(/<p>(<ul>.*?<\/ul>)<\/p>/gs, '$1')
            .replace(/<p>(<li>.*?<\/li>)<\/p>/g, '$1');
    }
    
    formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<em>null</em>';
        }
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        if (typeof value === 'string' && value.length > 100) {
            return value.substring(0, 100) + '...';
        }
        return String(value);
    }
    
    async fetchAPI(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }
    
    startExecutionMonitoring(researchId, themeId = null) {
        // Poll for research completion every 5 seconds
        const monitoringInterval = setInterval(async () => {
            try {
                const research = await this.fetchAPI(`/api/research/${researchId}`);
                
                if (research.metadata.status === 'completed' || research.metadata.status === 'failed') {
                    // Research completed, stop monitoring
                    clearInterval(monitoringInterval);
                    
                    if (themeId) {
                        this.executingThemes.delete(themeId);
                        this.updateThemeButton(themeId, research.metadata.status);
                    }
                    
                    // Refresh themes view
                    if (this.currentView === 'themes') {
                        this.loadThemes();
                    }
                    
                    // Show completion message
                    const statusText = research.metadata.status === 'completed' ? 'completed successfully' : 'failed';
                    this.showSuccessMessage(`Research ${researchId} ${statusText}!`);
                }
                
            } catch (error) {
                console.error('Error monitoring research:', error);
                // Continue monitoring despite errors
            }
        }, 5000);
        
        // Stop monitoring after 10 minutes
        setTimeout(() => {
            clearInterval(monitoringInterval);
            if (themeId) {
                this.executingThemes.delete(themeId);
                this.loadThemes();
            }
        }, 600000);
    }
    
    updateThemeButton(themeId, status) {
        const themeElement = document.querySelector(`[data-theme-id="${themeId}"]`);
        if (!themeElement) return;
        
        const buttonContainer = themeElement.querySelector('.theme-actions');
        if (!buttonContainer) return;
        
        let rerunButton = '';
        
        switch (status) {
            case 'executing':
                rerunButton = `
                    <button class="btn btn-sm btn-warning" disabled>
                        <span class="spinner"></span> Executing...
                    </button>
                `;
                break;
            case 'validating':
                rerunButton = `
                    <button class="btn btn-sm btn-warning" disabled>
                        <span class="spinner"></span> Validating...
                    </button>
                `;
                break;
            case 'completed':
            case 'pending':
                rerunButton = `
                    <button class="btn btn-sm btn-warning" onclick="dashboard.reRunTheme(${themeId})">
                        🔄 Re-run
                    </button>
                `;
                break;
            case 'error':
            case 'failed':
                rerunButton = `
                    <button class="btn btn-sm btn-danger" onclick="dashboard.reRunTheme(${themeId})">
                        🔄 Retry
                    </button>
                `;
                break;
        }
        
        // Update only the re-run button, keep other buttons
        const editButton = buttonContainer.querySelector('.edit-theme-btn');
        const viewButton = buttonContainer.querySelector('.btn-primary');
        buttonContainer.innerHTML = '';
        if (editButton) {
            buttonContainer.appendChild(editButton.cloneNode(true));
        }
        if (viewButton) {
            buttonContainer.appendChild(viewButton.cloneNode(true));
        }
        if (rerunButton) {
            buttonContainer.insertAdjacentHTML('beforeend', rerunButton);
        }
    }
    
    showSuccessMessage(message) {
        // Create a temporary success message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'execution-status completed';
        messageDiv.innerHTML = `✅ ${message}`;
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.maxWidth = '400px';
        
        document.body.appendChild(messageDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }
    
    async copyQuery() {
        const sqlElement = document.getElementById('modal-sql-query');
        const copyButton = document.getElementById('copy-query-btn');
        
        if (!sqlElement || !sqlElement.textContent) {
            alert('No query to copy');
            return;
        }
        
        try {
            // Use modern clipboard API if available
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(sqlElement.textContent);
            } else {
                // Fallback for older browsers or non-HTTPS
                const textArea = document.createElement('textarea');
                textArea.value = sqlElement.textContent;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            
            // Show success feedback
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '✅ Copied!';
            copyButton.classList.add('btn-success');
            copyButton.classList.remove('btn-secondary');
            
            setTimeout(() => {
                copyButton.innerHTML = originalText;
                copyButton.classList.remove('btn-success');
                copyButton.classList.add('btn-secondary');
            }, 2000);
            
        } catch (error) {
            console.error('Failed to copy query:', error);
            
            // Show error feedback
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '❌ Failed';
            copyButton.classList.add('btn-danger');
            copyButton.classList.remove('btn-secondary');
            
            setTimeout(() => {
                copyButton.innerHTML = originalText;
                copyButton.classList.remove('btn-danger');
                copyButton.classList.add('btn-secondary');
            }, 2000);
        }
    }
    
    async copyResults() {
        const copyButton = document.getElementById('copy-results-btn');
        
        if (!this.currentQueryResults || this.currentQueryResults.length === 0) {
            alert('No results to copy');
            return;
        }
        
        try {
            // Convert results to CSV format
            const headers = Object.keys(this.currentQueryResults[0]);
            const csvContent = [
                headers.join(','),  // Header row
                ...this.currentQueryResults.map(row => 
                    headers.map(header => {
                        const value = row[header];
                        // Escape CSV values that contain commas, quotes, or newlines
                        if (value === null || value === undefined) {
                            return '';
                        }
                        const stringValue = String(value);
                        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                            return `"${stringValue.replace(/"/g, '""')}"`;
                        }
                        return stringValue;
                    }).join(',')
                )
            ].join('\n');
            
            // Use modern clipboard API if available
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(csvContent);
            } else {
                // Fallback for older browsers or non-HTTPS
                const textArea = document.createElement('textarea');
                textArea.value = csvContent;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            
            // Show success feedback
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '✅ Copied as CSV!';
            copyButton.classList.add('btn-success');
            copyButton.classList.remove('btn-secondary');
            
            setTimeout(() => {
                copyButton.innerHTML = originalText;
                copyButton.classList.remove('btn-success');
                copyButton.classList.add('btn-secondary');
            }, 3000);
            
        } catch (error) {
            console.error('Failed to copy results:', error);
            
            // Show error feedback
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '❌ Failed';
            copyButton.classList.add('btn-danger');
            copyButton.classList.remove('btn-secondary');
            
            setTimeout(() => {
                copyButton.innerHTML = originalText;
                copyButton.classList.remove('btn-danger');
                copyButton.classList.add('btn-secondary');
            }, 2000);
        }
    }
    
    async pasteQuery() {
        const pasteButton = document.getElementById('paste-query-btn');
        const queryEditor = document.getElementById('query-editor');
        
        try {
            let clipboardText = '';
            
            // Use modern clipboard API if available
            if (navigator.clipboard && window.isSecureContext) {
                clipboardText = await navigator.clipboard.readText();
            } else {
                // Fallback - just focus the editor for manual paste
                this.toggleEditQuery();
                queryEditor.focus();
                alert('Please paste your query manually in the editor');
                return;
            }
            
            if (!clipboardText.trim()) {
                alert('No text found in clipboard');
                return;
            }
            
            // Switch to edit mode and paste the query
            if (!this.isEditingQuery) {
                this.toggleEditQuery();
            }
            
            queryEditor.value = clipboardText;
            queryEditor.focus();
            
            // Show success feedback
            const originalText = pasteButton.innerHTML;
            pasteButton.innerHTML = '✅ Pasted!';
            pasteButton.classList.add('btn-success');
            pasteButton.classList.remove('btn-info');
            
            setTimeout(() => {
                pasteButton.innerHTML = originalText;
                pasteButton.classList.remove('btn-success');
                pasteButton.classList.add('btn-info');
            }, 2000);
            
        } catch (error) {
            console.error('Failed to paste query:', error);
            
            // Show error feedback or fallback to manual
            const originalText = pasteButton.innerHTML;
            pasteButton.innerHTML = '❌ Paste Manually';
            pasteButton.classList.add('btn-warning');
            pasteButton.classList.remove('btn-info');
            
            // Switch to edit mode for manual paste
            if (!this.isEditingQuery) {
                this.toggleEditQuery();
            }
            queryEditor.focus();
            
            setTimeout(() => {
                pasteButton.innerHTML = originalText;
                pasteButton.classList.remove('btn-warning');
                pasteButton.classList.add('btn-info');
            }, 3000);
        }
    }
    
    toggleEditQuery() {
        const readonlyContainer = document.getElementById('query-readonly');
        const queryEditor = document.getElementById('query-editor');
        const editButton = document.getElementById('edit-query-btn');
        const executeCustomBtn = document.getElementById('execute-custom-btn');
        const sqlElement = document.getElementById('modal-sql-query');
        
        if (!this.isEditingQuery) {
            // Switch to edit mode
            this.isEditingQuery = true;
            
            // Copy current query to editor
            queryEditor.value = sqlElement.textContent || '';
            
            // Show editor, hide readonly
            readonlyContainer.classList.add('hidden');
            queryEditor.classList.remove('hidden');
            executeCustomBtn.classList.remove('hidden');
            
            // Update button text
            editButton.innerHTML = '💾 Save Changes';
            editButton.classList.remove('btn-warning');
            editButton.classList.add('btn-success');
            
            queryEditor.focus();
            
        } else {
            // Switch back to readonly mode
            this.isEditingQuery = false;
            
            // Update the display with edited content
            const editedQuery = queryEditor.value;
            sqlElement.textContent = editedQuery;
            
            // Apply syntax highlighting if available
            if (window.Prism) {
                Prism.highlightElement(sqlElement);
            }
            
            // Show readonly, hide editor
            readonlyContainer.classList.remove('hidden');
            queryEditor.classList.add('hidden');
            executeCustomBtn.classList.add('hidden');
            
            // Update button text
            editButton.innerHTML = '✏️ Edit Query';
            editButton.classList.remove('btn-success');
            editButton.classList.add('btn-warning');
        }
    }
    
    async executeCustomQuery() {
        const queryEditor = document.getElementById('query-editor');
        const customQuery = queryEditor.value.trim();
        
        if (!customQuery) {
            alert('Please enter a SQL query');
            return;
        }
        
        // Use the same results loading logic as the original query
        const resultsContainer = document.getElementById('query-results-container');
        const loadingDiv = document.getElementById('results-loading');
        const errorDiv = document.getElementById('results-error');
        const tableContainer = document.getElementById('results-table-container');
        
        // Show loading state
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        tableContainer.classList.add('hidden');
        
        try {
            const response = await fetch('/api/execute-custom-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: customQuery,
                    claim_id: this.currentClaimId 
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Hide loading
            loadingDiv.classList.add('hidden');
            
            // Update results count
            document.getElementById('results-count').textContent = result.result_count || 0;
            
            // Display results table
            if (result.query_results && result.query_results.length > 0) {
                const table = document.getElementById('results-table');
                const headers = Object.keys(result.query_results[0]);
                
                table.innerHTML = `
                    <thead>
                        <tr>
                            ${headers.map(header => `<th>${header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${result.query_results.map(row => `
                            <tr>
                                ${headers.map(header => `<td>${this.formatCellValue(row[header])}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                `;
                
                // Store results for copying
                this.currentQueryResults = result.query_results;
                
                // Show copy button and table
                document.getElementById('copy-results-btn').classList.remove('hidden');
                tableContainer.classList.remove('hidden');
            } else {
                document.getElementById('copy-results-btn').classList.add('hidden');
                errorDiv.textContent = 'No results returned by the query';
                errorDiv.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('Error executing custom query:', error);
            loadingDiv.classList.add('hidden');
            errorDiv.textContent = `Error executing query: ${error.message}`;
            errorDiv.classList.remove('hidden');
        }
    }
    
    showError(message) {
        // Simple error display - could be enhanced with a toast system
        console.error(message);
        alert(message);
    }
    
    // === NEW VALIDATION WORKFLOW METHODS ===
    
    showAddValidationModal() {
        if (!this.currentResearchId) {
            this.showError('Please select a research theme first');
            return;
        }
        
        // Clear form
        document.getElementById('new-claim-text').value = '';
        document.getElementById('new-validation-logic').value = '';
        document.getElementById('new-validation-query').value = '';
        document.getElementById('new-claim-type').value = 'manual';
        document.getElementById('new-period-filter').value = '';
        
        // Hide test results
        document.getElementById('test-results-section').classList.add('hidden');
        
        // Show modal
        document.getElementById('add-validation-modal').classList.add('show');
    }
    
    async testValidationQuery() {
        const query = document.getElementById('new-validation-query').value.trim();
        
        if (!query) {
            this.showError('Please enter a SQL query first');
            return;
        }
        
        const testResults = document.getElementById('test-results-section');
        const testLoading = document.getElementById('test-loading');
        const testError = document.getElementById('test-error');
        const testSuccess = document.getElementById('test-success');
        
        // Reset states
        testResults.classList.remove('hidden');
        testLoading.classList.remove('hidden');
        testError.classList.add('hidden');
        testSuccess.classList.add('hidden');
        
        try {
            const response = await fetch('/api/execute-custom-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query
                })
            });
            
            const result = await response.json();
            testLoading.classList.add('hidden');
            
            if (response.ok) {
                testSuccess.innerHTML = `
                    <span>✅ Query executed successfully!</span>
                    <span>Records returned: <strong>${result.result_count || 0}</strong></span>
                `;
                testSuccess.classList.remove('hidden');
            } else {
                testError.textContent = result.error || 'Query test failed';
                testError.classList.remove('hidden');
            }
            
        } catch (error) {
            testLoading.classList.add('hidden');
            testError.textContent = `Test failed: ${error.message}`;
            testError.classList.remove('hidden');
        }
    }
    
    async createValidationClaim() {
        const claimText = document.getElementById('new-claim-text').value.trim();
        const validationLogic = document.getElementById('new-validation-logic').value.trim();
        const validationQuery = document.getElementById('new-validation-query').value.trim();
        const claimType = document.getElementById('new-claim-type').value;
        const periodFilter = document.getElementById('new-period-filter').value.trim();
        
        // Validation
        if (!claimText) {
            this.showError('Please enter a claim to validate');
            return;
        }
        
        if (!validationLogic) {
            this.showError('Please explain the validation logic');
            return;
        }
        
        if (!validationQuery) {
            this.showError('Please enter a SQL validation query');
            return;
        }
        
        if (!this.currentResearchId) {
            this.showError('No research selected');
            return;
        }
        
        try {
            const response = await fetch('/api/create-validation-claim', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    research_id: this.currentResearchId,
                    claim_text: claimText,
                    validation_query: validationQuery,
                    validation_logic: validationLogic,
                    claim_type: claimType,
                    period_filter: periodFilter
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Close modal
                document.getElementById('add-validation-modal').classList.remove('show');
                
                // Refresh the claims list
                await this.loadResearchDetail(this.currentResearchId);
                
                // Show success message
                alert(`✅ Validation claim created successfully! Found ${result.data_points_found} data points.`);
            } else {
                this.showError(result.error || 'Failed to create validation claim');
            }
            
        } catch (error) {
            this.showError(`Error creating validation claim: ${error.message}`);
        }
    }
    
    // === THEME EDITOR METHODS ===
    
    async editTheme(themeId) {
        try {
            // Load theme data
            const response = await fetch(`/api/research/${themeId}`);
            const themeData = await response.json();
            
            if (!response.ok) {
                this.showError(themeData.error || 'Failed to load theme data');
                return;
            }
            
            // Populate editor fields
            this.populateThemeEditor(themeData);
            
            // Show editor modal
            document.getElementById('theme-editor-modal').classList.add('show');
            
        } catch (error) {
            this.showError(`Error opening theme editor: ${error.message}`);
        }
    }
    
    populateThemeEditor(themeData) {
        const metadata = themeData.metadata;
        
        // Basic metadata
        document.getElementById('edit-theme-id').value = metadata.id;
        document.getElementById('edit-theme-type').value = metadata.theme_type;
        document.getElementById('edit-theme-quarter').value = metadata.quarter;
        document.getElementById('edit-theme-status').value = metadata.status;
        
        // Status badge
        const statusBadge = document.getElementById('theme-editor-status');
        statusBadge.textContent = metadata.status;
        statusBadge.className = `theme-status-badge ${metadata.status}`;
        
        // Prompts
        document.getElementById('edit-user-guidance').value = metadata.user_guidance || '';
        document.getElementById('edit-enhanced-query').value = metadata.enhanced_query || '';
        
        // Reset prompt view
        document.getElementById('merge-prompts-checkbox').checked = false;
        document.getElementById('separate-prompts-view').classList.remove('hidden');
        document.getElementById('merged-prompt-view').classList.add('hidden');
        
        // Load and display claims
        this.loadClaimsInEditor(themeData.claims);
        
        // Load research content preview
        this.loadResearchContentPreview(themeData.research_content);
        
        // Store current theme data
        this.currentThemeData = themeData;
    }
    
    loadClaimsInEditor(claims) {
        const container = document.getElementById('claims-editor-list');
        const countElement = document.getElementById('claims-count-editor');
        
        countElement.textContent = `${claims.length} claims`;
        
        if (claims.length === 0) {
            container.innerHTML = '<div class="loading">No validation claims found. Use "Generate Validation Claims" to create some.</div>';
            return;
        }
        
        container.innerHTML = claims.map((claim, index) => `
            <div class="claim-editor-item" data-claim-id="${claim.id}">
                <div class="claim-editor-header">
                    <span style="font-weight: 600; color: var(--primary-color);">Claim ${index + 1}</span>
                    <div class="claim-editor-actions">
                        <button class="btn btn-sm btn-info" onclick="dashboard.testClaimQuery(${claim.id})">🧪 Test</button>
                        <button class="btn btn-sm btn-danger" onclick="dashboard.deleteClaim(${claim.id})">🗑️ Delete</button>
                    </div>
                </div>
                
                <label>Claim Text:</label>
                <textarea class="form-textarea" rows="2" data-field="claim_text">${claim.claim_text || ''}</textarea>
                
                <label>Validation Logic:</label>
                <textarea class="form-textarea" rows="2" data-field="validation_logic">${claim.validation_logic || ''}</textarea>
                
                <label>SQL Query:</label>
                <textarea class="query-editor" rows="4" data-field="validation_query">${claim.validation_query || ''}</textarea>
                
                <div class="metadata-grid" style="margin-top: 12px;">
                    <div class="metadata-field">
                        <label>Type:</label>
                        <select class="form-input" data-field="claim_type">
                            <option value="manual" ${claim.claim_type === 'manual' ? 'selected' : ''}>Manual</option>
                            <option value="port_frequency" ${claim.claim_type === 'port_frequency' ? 'selected' : ''}>Port Frequency</option>
                            <option value="transit_time" ${claim.claim_type === 'transit_time' ? 'selected' : ''}>Transit Time</option>
                            <option value="route_pattern" ${claim.claim_type === 'route_pattern' ? 'selected' : ''}>Route Pattern</option>
                            <option value="vessel_movement" ${claim.claim_type === 'vessel_movement' ? 'selected' : ''}>Vessel Movement</option>
                            <option value="fuel_consumption" ${claim.claim_type === 'fuel_consumption' ? 'selected' : ''}>Fuel Consumption</option>
                        </select>
                    </div>
                    <div class="metadata-field">
                        <label>Confidence:</label>
                        <input type="text" class="form-input" value="${Math.round((claim.confidence_score || 0) * 100)}%" readonly>
                    </div>
                    <div class="metadata-field">
                        <label>Data Points:</label>
                        <input type="text" class="form-input" value="${claim.data_points_found || 0}" readonly>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    loadResearchContentPreview(researchContent) {
        const container = document.getElementById('research-content-preview');
        
        if (!researchContent) {
            container.innerHTML = '<div class="loading">No research content available</div>';
            return;
        }
        
        // Use marked.js to render markdown if available
        if (window.marked && researchContent.includes('*') || researchContent.includes('#')) {
            container.innerHTML = marked(researchContent);
        } else {
            // Fallback text formatting
            container.innerHTML = this.formatTextContent(researchContent);
        }
    }
    
    async togglePromptMerge() {
        const checkbox = document.getElementById('merge-prompts-checkbox');
        const separateView = document.getElementById('separate-prompts-view');
        const mergedView = document.getElementById('merged-prompt-view');
        
        if (checkbox.checked) {
            // Show merged view
            separateView.classList.add('hidden');
            mergedView.classList.remove('hidden');
            
            // Merge prompts
            const userGuidance = document.getElementById('edit-user-guidance').value;
            const enhancedQuery = document.getElementById('edit-enhanced-query').value;
            
            const merged = this.mergePrompts(userGuidance, enhancedQuery);
            document.getElementById('edit-merged-prompt').value = merged;
        } else {
            // Show separate view
            separateView.classList.remove('hidden');
            mergedView.classList.add('hidden');
        }
    }
    
    mergePrompts(userGuidance, enhancedQuery) {
        if (!userGuidance && !enhancedQuery) return '';
        if (!userGuidance) return enhancedQuery;
        if (!enhancedQuery) return userGuidance;
        
        return `## Original User Guidance:\n${userGuidance}\n\n## Enhanced Research Query:\n${enhancedQuery}`;
    }
    
    async saveThemeChanges() {
        const themeId = document.getElementById('edit-theme-id').value;
        
        // Collect form data
        const themeData = {
            theme_type: document.getElementById('edit-theme-type').value,
            quarter: document.getElementById('edit-theme-quarter').value,
            status: document.getElementById('edit-theme-status').value,
            user_guidance: document.getElementById('edit-user-guidance').value,
            enhanced_query: document.getElementById('edit-enhanced-query').value
        };
        
        // Handle merged prompts
        const mergeCheckbox = document.getElementById('merge-prompts-checkbox');
        if (mergeCheckbox.checked) {
            const mergedPrompt = document.getElementById('edit-merged-prompt').value;
            themeData.user_guidance = mergedPrompt;
            themeData.enhanced_query = ''; // Clear enhanced query when merged
        }
        
        try {
            const response = await fetch(`/api/update-theme/${themeId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(themeData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Close modal
                document.getElementById('theme-editor-modal').classList.remove('show');
                
                // Refresh themes view if currently active
                if (this.currentView === 'themes') {
                    await this.loadThemes();
                }
                
                alert('✅ Theme updated successfully!');
            } else {
                this.showError(result.error || 'Failed to update theme');
            }
            
        } catch (error) {
            this.showError(`Error saving theme: ${error.message}`);
        }
    }
    
    togglePromptEdit(themeId) {
        const displayDiv = document.getElementById(`prompt-display-${themeId}`);
        const editDiv = document.getElementById(`prompt-edit-${themeId}`);
        
        if (displayDiv && editDiv) {
            displayDiv.style.display = 'none';
            editDiv.style.display = 'block';
        }
    }
    
    cancelPromptEdit(themeId) {
        const displayDiv = document.getElementById(`prompt-display-${themeId}`);
        const editDiv = document.getElementById(`prompt-edit-${themeId}`);
        
        if (displayDiv && editDiv) {
            displayDiv.style.display = 'block';
            editDiv.style.display = 'none';
        }
    }
    
    async runResearch(themeId, quarter) {
        // Get the current prompt text
        const promptDisplay = document.getElementById(`prompt-display-${themeId}`);
        if (!promptDisplay) {
            this.showError('Unable to find research prompt');
            return;
        }
        
        const prompt = promptDisplay.textContent.trim();
        if (!prompt || prompt === 'No research prompt provided') {
            this.showError('Please provide a research prompt before running');
            return;
        }
        
        if (!confirm(`This will run the research with the following prompt:\n\n"${prompt}"\n\nContinue?`)) {
            return;
        }
        
        try {
            // Show loading state on button
            const button = event.target;
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '⏳ Running Research...';
            
            // Execute research
            const response = await fetch('/api/execute-research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    theme: prompt,
                    quarter: quarter || 'Q1 2025'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Research execution started successfully!');
                
                // If we got a research ID, start monitoring
                if (result.research_id && result.research_id !== 'pending') {
                    this.startExecutionMonitoring(result.research_id, themeId);
                }
                
                // Refresh the page after a delay to show updated status
                setTimeout(() => {
                    this.loadResearchDetails(themeId);
                }, 3000);
            } else {
                throw new Error(result.error || 'Failed to execute research');
            }
            
        } catch (error) {
            console.error('Error running research:', error);
            this.showError(`Failed to run research: ${error.message}`);
        } finally {
            // Reset button state
            const button = event.target;
            if (button) {
                button.disabled = false;
                button.innerHTML = '▶️ RUN Research';
            }
        }
    }
    
    async savePrompt(themeId) {
        const textarea = document.getElementById(`prompt-textarea-${themeId}`);
        if (!textarea) return;
        
        const newPrompt = textarea.value.trim();
        if (!newPrompt) {
            this.showError('Research prompt cannot be empty');
            return;
        }
        
        try {
            // Update the prompt in database
            const response = await fetch(`/api/update-theme/${themeId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    user_guidance: newPrompt,
                    // Clear enhanced_query since we're using single prompt now
                    enhanced_query: null
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Research prompt saved successfully!');
                
                // Update the display
                const displayDiv = document.getElementById(`prompt-display-${themeId}`);
                if (displayDiv) {
                    displayDiv.textContent = newPrompt;
                }
                this.cancelPromptEdit(themeId);
            } else {
                throw new Error(result.error || 'Failed to save prompt');
            }
            
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.showError(`Failed to save: ${error.message}`);
        }
    }
    
    async runBulkValidation() {
        if (!confirm('This will run AI analysis on all pending validation claims. This may take a few minutes. Continue?')) {
            return;
        }
        
        const progressDiv = document.getElementById('validation-progress');
        const runBtn = document.getElementById('run-validation-btn');
        
        try {
            // Show progress indicator
            progressDiv.classList.remove('hidden');
            runBtn.disabled = true;
            runBtn.textContent = '⏳ Running...';
            
            const response = await fetch('/api/run-bulk-validation', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Refresh validation status
                await this.loadOverviewData();
                
                // Show success message
                alert(`✅ Validation complete!\n\nProcessed: ${result.results.success + result.results.failed} claims\nSuccessful: ${result.results.success}\nFailed: ${result.results.failed}`);
                
                if (result.results.errors.length > 0) {
                    console.error('Validation errors:', result.results.errors);
                }
            } else {
                this.showError(result.error || 'Validation failed');
            }
            
        } catch (error) {
            this.showError(`Error running validation: ${error.message}`);
        } finally {
            // Hide progress indicator
            progressDiv.classList.add('hidden');
            runBtn.disabled = false;
            runBtn.textContent = '🔄 Run Analysis';
        }
    }
    
    async runSingleValidation(claimId) {
        try {
            const response = await fetch(`/api/run-validation-analysis/${claimId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Show analysis results
                const supported = result.supports_claim ? '✅ SUPPORTED' : '❌ NOT SUPPORTED';
                const confidence = Math.round(result.confidence * 100);
                
                alert(`Validation Analysis Complete!\n\n${supported}\nConfidence: ${confidence}%\nData Points: ${result.data_points}\n\nEvidence: ${result.evidence}\n\nSummary: ${result.summary}`);
                
                // Refresh the current view
                if (this.currentView === 'research' && this.currentResearchId) {
                    await this.loadResearchDetail(this.currentResearchId);
                } else if (this.currentView === 'overview') {
                    await this.loadOverviewData();
                }
                
                return result;
            } else {
                this.showError(result.error || 'Validation analysis failed');
                return null;
            }
            
        } catch (error) {
            this.showError(`Error running validation: ${error.message}`);
            return null;
        }
    }
    
    async generateValidationClaims() {
        const themeId = document.getElementById('edit-theme-id').value;
        
        if (!confirm('This will replace all existing validation claims with AI-generated ones. Continue?')) {
            return;
        }
        
        try {
            // Show loading state
            const generateBtn = document.getElementById('generate-claims-btn');
            const originalText = generateBtn.textContent;
            generateBtn.textContent = '🤖 Generating...';
            generateBtn.disabled = true;
            
            const response = await fetch(`/api/generate-claims/${themeId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Reload the claims in editor
                this.loadClaimsInEditor(result.claims);
                alert(`✅ Generated ${result.claims.length} validation claims!`);
            } else {
                this.showError(result.error || 'Failed to generate claims');
            }
            
            // Reset button
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
            
        } catch (error) {
            this.showError(`Error generating claims: ${error.message}`);
            
            // Reset button
            const generateBtn = document.getElementById('generate-claims-btn');
            generateBtn.textContent = '🤖 Generate Validation Claims';
            generateBtn.disabled = false;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ObservatorioDashboard();
});