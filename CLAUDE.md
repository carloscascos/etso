# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**OBSERVATORIO ETS** is a Maritime Carbon Intelligence System that analyzes carbon emission regulations' impact on global container shipping routes. It features a dual-database architecture with LangChain/LangGraph orchestration, validating research findings against real vessel movement data.

## Key Commands

### Setup and Installation
```bash
# Full system setup (checks Python version, installs dependencies, initializes databases)
python setup/setup.py

# Initialize ETSO database schema
python setup/schema_setup.py

# Test database connections
python test/test_connections.py

# Complete setup verification
python test/test_complete_setup.py
```

### Running the Application
```bash
# Main application entry point
python main.py

# Web dashboard (comprehensive frontend interface)
uv run python dashboard.py
# Access at: http://172.31.40.23:5000 (external URL)

# Test specific database connection
python test/test_traffic_connection.py
```

### Deployment
```bash
# Deploy with automatic version increment and git push
uv run python deploy.py [major|minor|patch]

# Examples:
uv run python deploy.py patch    # 1.0.0 -> 1.0.1 (default)
uv run python deploy.py minor    # 1.0.0 -> 1.1.0  
uv run python deploy.py major    # 1.0.0 -> 2.0.0

# The /deploy command does: version bump + git commit + git push
# Version number appears in dashboard top-right corner
```

### Development and Maintenance
```bash
# Install/update dependencies using modern Python tooling
uv sync  # Uses uv.lock for reproducible installs
# Or traditional approach:
pip install -r requirements.txt

# Reset ChromaDB vector storage (if needed)
rm -rf ./chroma_data && mkdir chroma_data
```

## Development Recommendations

- Always run Python using `uv run` for consistent and reproducible environments

## Architecture Overview

### Dual-Database Pattern
- **Traffic DB** (read-only): Existing vessel movement data (`escalas`, `vessels`, `ports` tables)
- **ETSO DB** (full access): Research findings and validation metadata

### Core Components
- **main.py**: `ObservatorioETS` orchestration with `ResearchThemeProcessor` for LLM-enhanced research
- **database.py**: `DatabaseManager` with context managers for dual database connections
- **storage.py**: `ResearchStorageManager` combining ChromaDB vector storage with structured metadata in ETSO DB
- **validation.py**: `DualDatabaseValidator` that cross-references research claims with vessel data
- **config.py**: `SystemConfig` with environment-based configuration management
- **dashboard.py**: Flask web application providing comprehensive research management interface

### Research Processing Flow
1. User provides research themes → `ResearchThemeProcessor` enhances with LLM
2. Multi-agent research execution via LangChain/LangGraph
3. **Manual Validation Workflow**: Users enter validation queries with semantic meaning through dashboard interface
4. `DualDatabaseValidator` validates findings against traffic database (or user-provided queries)
5. `ResearchStorageManager` stores in ChromaDB + ETSO DB with confidence scores
6. Quarterly report generation with validated findings

## Database Schema

### Traffic Database (Read-Only)
```sql
escalas: (start, end, imo, portname, next_port, speed, ...)
v_fleet: (imo, name, stype, GT, DWT, owner, ...)
v_MRV: (imo, name, type, co2nm, foctd, GT) - CO2 kg per nautical mile
ports: (portname, country, zone, portcode, ...)
port_trace: (imo) - Container vessels only (PRIMARY KEY)
```

**Container Vessel Focus:** All queries join with `port_trace.imo = escalas.imo` to analyze only container vessels.

### ETSO Database (Full Access)
```sql
research_metadata: (id, chroma_id, quarter, theme_type, overall_confidence, ...)
validation_claims: (id, research_metadata_id, claim_text, validation_query, validation_logic, confidence_score, ...)
quarterly_reports: (id, quarter, total_findings, average_confidence, ...)
```

**New Manual Validation Workflow**: The `validation_claims` table now includes `validation_logic` field for users to provide semantic meaning alongside their SQL validation queries.

## Configuration

### Environment Variables Required
```bash
# Database connections
TRAFFIC_DB_HOST=your-traffic-rds-endpoint
TRAFFIC_DB_PASSWORD=readonly_password
ETSO_DB_HOST=your-etso-rds-endpoint  
ETSO_DB_PASSWORD=etso_password

# OpenAI
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION=observatorio_research
```

### Key Settings in config.py
- `CURRENT_QUARTER`: Active research quarter (e.g., "2025Q1")
- `VALIDATION_THRESHOLD`: Minimum confidence score (default: 0.7)
- Dual database configurations with proper access controls

## Development Patterns

### Research Domain Extensions
- Add new theme types in `_classify_theme_type()` in main.py:712
- Extend validation logic in `validation.py` for domain-specific queries
- Update theme type enum in `schema.sql`

### Database Access Patterns
```python
# Traffic DB (read-only)
with db_manager.get_traffic_connection() as conn:
    # Read vessel movement data

# ETSO DB (full access with transactions)
with db_manager.get_etso_connection() as conn:
    # Store research findings and validation results
```

### Testing Approach
- Connection tests: `test/test_connections.py`, `test/test_traffic_connection.py`
- Complete setup verification: `test/test_complete_setup.py`
- No pytest framework - uses direct database connection testing

## Technology Stack

- **Python 3.13+** with modern async/await patterns
- **LangChain/LangGraph**: Multi-agent research orchestration
- **ChromaDB**: Vector storage for semantic search
- **OpenAI GPT-4**: Research processing and theme enhancement
- **PyMySQL**: Dual database connectivity (MariaDB/MySQL)
- **Pydantic**: Data validation and settings management
- **Rich/Structlog**: Enhanced logging and console output
- **Flask + CORS**: Web dashboard backend
- **Modern JavaScript ES6**: Frontend with Chart.js, Axios, Prism.js, Marked.js

## Web Dashboard Interface

### Overview
The Flask-based web dashboard provides a comprehensive frontend for the OBSERVATORIO ETS system, accessible at `http://localhost:5000` or externally via server IP.

### Dashboard Features

#### Main Navigation
- **Overview**: System statistics, recent findings, validation status, and health monitoring
- **Research Themes**: Browse and manage 34+ themes categorized by EU_ETS, ROUTES, and REGIONAL
- **Research Details**: Deep-dive into individual research findings with full content and claims

#### Key Capabilities
- **Theme Management**: View themes by category with search/filter functionality
- **Research Execution**: Trigger new research or re-run existing themes with real-time progress monitoring
- **Content Display**: Markdown-rendered research content with proper formatting
- **SQL Query Interface**: Interactive modal with copy/paste/edit capabilities for validation queries
- **Manual Validation Workflow**: Users can create validation queries with semantic explanations
- **Results Visualization**: Tabular display of query results with CSV export functionality
- **Dynamic Status Updates**: Real-time monitoring of research execution progress

#### SQL Query Modal Features
```javascript
// Copy existing queries to clipboard
dashboard.copyQuery()

// Paste queries from external sources  
dashboard.pasteQuery()

// Toggle between read-only and edit modes
dashboard.toggleEditQuery()

// Execute custom queries with security validation
dashboard.executeCustomQuery()

// Export results as CSV format
dashboard.copyResults()
```

#### API Endpoints
- `GET /api/themes` - Retrieve all research themes grouped by type
- `GET /api/research/<id>` - Get detailed research information including claims
- `GET /api/claim/<id>/results` - Execute validation query and return results
- `POST /api/execute-research` - Trigger new research theme execution
- `POST /api/rerun-theme/<id>` - Re-run existing research theme
- `POST /api/execute-custom-query` - Execute custom SQL with injection protection
- `POST /api/create-validation-claim` - **NEW**: Create user-entered validation queries with logic
- `GET /api/system-health` - Check database and service health status

#### Security Features
- SQL injection protection (SELECT queries only)
- CORS enabled for cross-origin requests
- Query timeout limits (30 seconds)
- Result set limits (500 records max for custom queries)
- Dangerous keyword filtering (DROP, DELETE, INSERT, UPDATE, etc.)

#### Frontend Technologies
- **CSS**: Modern responsive design with maritime theme colors
- **JavaScript**: ES6 class-based architecture (ObservatorioDashboard)
- **Libraries**: Chart.js (visualization), Prism.js (syntax highlighting), Marked.js (markdown)
- **Real-time Updates**: Polling-based execution monitoring with dynamic UI states

### Dashboard File Structure
```
static/
├── css/dashboard.css     # Complete styling with responsive design
└── js/dashboard.js       # Main application logic and API interactions

templates/
└── dashboard.html        # Single-page application template

dashboard.py             # Flask backend with comprehensive API
```

## Performance Targets

- Research execution: <5 minutes per theme
- Database queries: <30 seconds per validation
- Dashboard response time: <2 seconds for most operations
- System handles 10+ concurrent research themes
- Maintains 100,000+ stored research findings with 2+ years historical data
- always show the public url
- mem show public urls only