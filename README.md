# OBSERVATORIO ETS
## Maritime Carbon Intelligence System

A dual-database intelligence system that analyzes carbon emission regulations' impact on global container shipping routes, validates research findings against real vessel movement data, and produces automated quarterly reports.

## 🏗️ System Architecture

### Core Components
- **Dual Database**: Traffic DB (read-only vessel data) + ETSO DB (research findings)
- **LangChain/LangGraph**: Multi-agent research orchestration
- **ChromaDB**: Vector storage for semantic search and retrieval
- **Validation Engine**: Cross-references research with actual vessel movements

### Data Flow
```
User Guidance → Research Enhancement → LLM Research → 
Data Validation → Confidence Scoring → Report Generation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MariaDB/MySQL databases (traffic + etso)
- OpenAI API key
- 8GB+ RAM recommended

### Installation

1. **Clone and setup**
   ```bash
   git clone <repository>
   cd etso
   python setup.py
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

3. **Initialize database**
   ```bash
   python schema_setup.py
   ```

4. **Test the system**
   ```bash
   python main.py
   ```

## 📊 Usage

### Basic Quarterly Analysis
```python
from main import ObservatorioETS
from config import config

# Initialize system
observatorio = ObservatorioETS(config)

# Define research themes
themes = [
    "Red Sea crisis impact on Asia-Europe routes",
    "EU ETS compliance costs for major carriers",
    "Eastern Mediterranean transshipment growth"
]

# Run analysis
results = await observatorio.run_quarterly_analysis("2025Q1", themes)
```

### Research Theme Processing
The system enhances user input into structured research themes:

**Input:** `"Red Sea situation impact"`

**Enhanced Output:**
- **Query**: Analyze Red Sea security crisis impact on container shipping routes...
- **Expected Outputs**: Percentage of vessels avoiding Suez, alternative routing patterns...
- **Validation Targets**: Port call sequences, transit time changes, fuel consumption increases...

### Data Validation
All research findings are validated against your vessel traffic database:
- Extract verifiable claims from research
- Generate SQL queries against `escalas`, `vessels`, `ports` tables
- Calculate confidence scores based on data matches
- Store validation results with supporting evidence

## 🗄️ Database Schema

### Traffic Database (Read-Only)
```sql
-- Your existing vessel traffic data
escalas (start_time, imo, portname, next_port, fuel_consumption, ...)
vessels (imo, vessel_name, teu_capacity, operator, ...)
ports (portname, country, zone, ...)
```

### ETSO Database (Full Access)
```sql
-- Research findings metadata
research_metadata (id, chroma_id, quarter, theme_type, overall_confidence, ...)

-- Validation results for individual claims
validation_claims (id, research_metadata_id, claim_text, confidence_score, ...)

-- Quarterly report metadata
quarterly_reports (id, quarter, total_findings, average_confidence, ...)
```

## 🔧 Configuration

### Environment Variables
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

### System Settings
```python
CURRENT_QUARTER=2025Q1
VALIDATION_THRESHOLD=0.7  # Minimum confidence for validated findings
MAX_RESEARCH_TOPICS=10
```

## 📈 Features

### ✅ Implemented
- **Dual-database architecture** with proper access controls
- **Enhanced research themes** from user input
- **Multi-domain research agents** (EU ETS, Routes, Geopolitical, Carrier, Regional)
- **Vessel data validation** with confidence scoring
- **Semantic storage and retrieval** using ChromaDB
- **Data insight discovery** from traffic patterns
- **Comprehensive logging and monitoring**

### 🔄 Research Domains
1. **EU ETS Analysis**: Carbon pricing, compliance costs, carrier strategies
2. **Trade Routes**: Service patterns, route optimizations, corridor shifts  
3. **Geopolitical**: Red Sea, Suez Canal, Panama Canal impacts
4. **Carrier Intelligence**: Maersk/GEMINI focus, fleet strategies
5. **Regional Analysis**: Eastern Mediterranean, transshipment hubs

### 🔍 Validation Capabilities
- **Vessel Movement**: Confirm reported vessel locations and routes
- **Fuel Consumption**: Validate efficiency claims and consumption patterns  
- **Transit Times**: Verify route duration and delay reports
- **Port Frequencies**: Check service pattern and call frequency changes
- **Route Patterns**: Confirm service modifications and diversions

## 🏃‍♂️ Performance

### Target Metrics
- Research execution: <5 minutes per theme
- Validation accuracy: 95% for vessel movements
- Database queries: <30 seconds per validation
- Report generation: <10 minutes quarterly
- System availability: 99.5%

### Scalability
- Supports 10+ concurrent research themes
- Handles 100,000+ stored research findings
- Processes 1,000+ validations per day
- Maintains 2+ years historical data

## 🔒 Security

### Access Control
- **Traffic DB**: Read-only access via `traffic_readonly` user
- **ETSO DB**: Full access via `etso` user with transaction control
- **API Keys**: Stored in environment variables
- **Database**: SSL/TLS encryption in transit

### Data Protection
- No vessel tracking data stored outside original database
- Research findings encrypted at rest in ChromaDB
- Audit logging for all database operations
- Configurable data retention policies

## 📝 File Structure

```
etso/
├── main.py                 # Main application entry point
├── config.py              # System configuration
├── database.py            # Database connection management
├── storage.py             # ChromaDB + ETSO storage manager
├── validation.py          # Dual-database validation system
├── schema.sql            # ETSO database schema
├── schema_setup.py       # Database initialization
├── setup.py              # System installation
├── requirements.txt      # Python dependencies
├── .env.example         # Environment configuration template
└── README.md            # This file
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check credentials in .env
# Verify database accessibility
python -c "from database import create_database_manager; create_database_manager().test_connections()"
```

**ChromaDB Issues**
```bash
# Reset ChromaDB storage
rm -rf ./chroma_data
mkdir chroma_data
```

**OpenAI API Errors**
```bash
# Verify API key and check usage limits
python -c "from langchain_openai import ChatOpenAI; ChatOpenAI().invoke('test')"
```

### Performance Optimization
- Use database connection pooling for high throughput
- Implement query result caching for repeated validations
- Batch validation queries where possible
- Monitor ChromaDB index size and optimize embeddings

## 📊 Monitoring

### Key Metrics
- Research execution time per quarter
- Validation success rate and confidence distribution
- Database query performance
- OpenAI API token usage
- System resource utilization

### Logging
```python
# Enable debug logging
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

## 🚀 Development

### Adding New Research Domains
1. Extend `_classify_theme_type()` in `main.py`
2. Add domain-specific validation queries in `validation.py`
3. Update theme type enum in `schema.sql`

### Custom Validation Logic
1. Inherit from `ValidationQueryGenerator` 
2. Implement domain-specific query methods
3. Register new claim types in validation system

## 📞 Support

### Getting Help
- Check logs in `./logs/` directory
- Review database schema in `schema.sql`
- Validate configuration with `python setup.py`

### Contributing
1. Follow existing code patterns and structure
2. Add comprehensive logging to new features
3. Update database schema version when modifying tables
4. Test with both small and large datasets

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**License**: Proprietary