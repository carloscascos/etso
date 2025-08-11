# OBSERVATORIO ETS - Technical Specifications
## Maritime Carbon Intelligence System

---

## 1. System Overview

### 1.1 Architecture Pattern
- **Type**: Data-driven intelligence system with bidirectional research flow
- **Framework**: LangChain + LangGraph for orchestration
- **Storage**: Hybrid approach with MariaDB (vessel data) + ChromaDB (research & vectors)
- **Processing**: Parallel agent execution with state management

### 1.2 Core Value Propositions
1. **Data-Driven Insights**: Discover patterns in vessel traffic, then research explanations
2. **Research Validation**: Validate all external research against actual vessel movements
3. **Intelligent Retrieval**: Use vector embeddings to find relevant context when building reports
4. **Quarterly Automation**: Generate comprehensive reports combining both data insights and research

---

## 2. Data Architecture

### 2.1 Primary Database (MariaDB/RDS on AWS)

#### Core Tables Structure

```sql
-- Main vessel movement table (linked-list structure)
TABLE escalas (
    start_time      TIMESTAMP,     -- PK component 1
    imo            BIGINT,        -- PK component 2
    end_time       TIMESTAMP,
    portname       VARCHAR(100),
    prev_leg       VARCHAR(50),   -- Link to previous journey
    prev_port      VARCHAR(100),
    next_leg       VARCHAR(50),   -- Link to next journey
    next_port      VARCHAR(100),
    fuel_consumption DECIMAL(10,2),
    PRIMARY KEY (start_time, imo)
);

-- Ports reference table
TABLE ports (
    portname       VARCHAR(100) PRIMARY KEY,
    country        VARCHAR(3),
    zone           VARCHAR(50),   -- Geographic region
    latitude       DECIMAL(10,8),
    longitude      DECIMAL(11,8)
);

-- Vessel registry
TABLE vessels (
    imo            BIGINT PRIMARY KEY,
    vessel_name    VARCHAR(255),
    teu_capacity   INTEGER,
    operator       VARCHAR(255),
    service        VARCHAR(100)
);

-- Research metadata (lightweight reference)
TABLE research_metadata (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    chroma_id      VARCHAR(100),  -- Reference to ChromaDB
    quarter        VARCHAR(10),
    type           VARCHAR(50),
    validation_score DECIMAL(3,2),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Research & Vector Storage (ChromaDB)

#### Storage Strategy
```python
# ChromaDB handles both document storage and vector embeddings
{
    "collection": "observatorio_research",
    "documents": {
        "text": "research_content",      # For vector embedding
        "metadata": {
            "quarter": "2025Q1",
            "type": "eu_ets|routes|geopolitical|carrier|regional",
            "full_content": "complete_research_text",
            "tables": "json_encoded_tables",
            "charts": "json_encoded_chart_configs",
            "images": "base64_or_s3_urls",
            "validation_score": 0.95,
            "confidence": 0.85,
            "timestamp": "2025-01-15T10:30:00Z",
            "sources": ["url1", "url2"],
            "validated_claims": {
                "vessel_movements": true,
                "route_changes": true,
                "fuel_consumption": false
            }
        }
    }
}
```

#### Deployment Options
1. **Local + S3 Backup**: ChromaDB with S3 persistence
2. **EC2 Hosted**: ChromaDB server on EC2 with EFS
3. **Managed Alternative**: AWS OpenSearch with vector capabilities

---

## 3. Agent Architecture

### 3.1 LangGraph Workflow Structure

```python
class ObservatorioState(TypedDict):
    """Global state for workflow orchestration"""
    quarter: str
    user_guidance: List[str]
    data_insights: List[Dict]
    research_findings: List[Dict]
    validated_findings: List[Dict]
    report_sections: Dict[str, Any]
    confidence_scores: Dict[str, float]
```

### 3.2 Agent Nodes

#### 3.2.1 Data Insight Discovery Node
**Purpose**: Analyze vessel traffic patterns
```python
def discover_insights(state: ObservatorioState) -> ObservatorioState:
    """
    Queries:
    - Route deviations using linked-list traversal
    - Service pattern changes
    - Fuel consumption anomalies
    - Port call frequency shifts
    """
```

#### 3.2.2 Research Agent Node
**Purpose**: Conduct guided and insight-driven research
```python
def research_agent(state: ObservatorioState) -> ObservatorioState:
    """
    Research Areas:
    1. EU ETS carbon pricing and compliance
    2. Trade route optimizations
    3. Geopolitical impacts (Suez, Panama)
    4. Carrier strategies (focus: Maersk/GEMINI)
    5. Regional focus (Eastern Mediterranean)
    
    Uses: GPT-4 with specific prompts for each domain
    """
```

#### 3.2.3 Validation Node
**Purpose**: Cross-reference research with vessel data
```python
def validation_node(state: ObservatorioState) -> ObservatorioState:
    """
    Validation Steps:
    1. Extract verifiable claims (vessels, routes, dates)
    2. Query escalas table for matching movements
    3. Calculate confidence scores
    4. Flag discrepancies
    """
```

#### 3.2.4 Report Generation Node
**Purpose**: Create quarterly reports with semantic retrieval
```python
def report_generator(state: ObservatorioState) -> ObservatorioState:
    """
    Report Sections:
    - Executive Summary
    - EU ETS Impact Analysis
    - Trade Route Evolution
    - Carrier Strategies
    - Regional Deep-Dive
    
    Uses: ChromaDB semantic search for relevant findings
    """
```

### 3.3 Workflow Orchestration

```python
# Simplified workflow with parallel execution
workflow = StateGraph(ObservatorioState)

# Add nodes
workflow.add_node("discover", discover_insights)
workflow.add_node("research", research_agent)
workflow.add_node("validate", validation_node)
workflow.add_node("generate", report_generator)

# Define flow
workflow.set_entry_point("discover")
workflow.add_edge("discover", "research")  # Insights inform research
workflow.add_edge("research", "validate")  # Validate all findings
workflow.add_edge("validate", "generate")  # Generate from validated data

# Compile with checkpointing
graph = workflow.compile(
    checkpointer=MemorySaver()  # Or PostgresCheckpointSaver for persistence
)
```

---

## 4. Key Algorithms

### 4.1 Route Deviation Detection
```sql
-- Detect vessels deviating from planned routes
WITH route_analysis AS (
    SELECT 
        e1.imo,
        e1.portname as scheduled_port,
        e1.next_port as planned_next,
        e2.portname as actual_next,
        CASE 
            WHEN e1.next_port != e2.portname THEN 1 
            ELSE 0 
        END as deviation
    FROM escalas e1
    LEFT JOIN escalas e2 
        ON e1.imo = e2.imo 
        AND e1.next_leg = e2.prev_leg
    WHERE QUARTER(e1.start_time) = ?
)
SELECT imo, SUM(deviation) as total_deviations
FROM route_analysis
GROUP BY imo
HAVING total_deviations > 0;
```

### 4.2 Corridor Shift Analysis
```sql
-- Identify vessels changing trade corridors
SELECT 
    imo,
    GROUP_CONCAT(DISTINCT p.zone) as zones_visited,
    COUNT(DISTINCT p.zone) as zone_changes
FROM escalas e
JOIN ports p ON e.portname = p.portname
WHERE QUARTER(e.start_time) = ?
GROUP BY imo
HAVING zone_changes > 3;
```

### 4.3 Validation Confidence Scoring
```python
def calculate_confidence(claim: dict, vessel_data: list) -> float:
    """
    Confidence = weighted average of:
    - Vessel existence (0.3)
    - Route match (0.4)
    - Timing alignment (0.3)
    """
    scores = []
    
    if vessel_exists(claim['vessel'], vessel_data):
        scores.append(1.0 * 0.3)
    
    if route_matches(claim['route'], vessel_data):
        scores.append(1.0 * 0.4)
    
    if dates_align(claim['dates'], vessel_data):
        scores.append(1.0 * 0.3)
    
    return sum(scores)  # 0.0 to 1.0
```

---

## 5. Technology Stack

### 5.1 Core Dependencies
```python
# requirements.txt
langchain==0.3.0           # Core framework
langgraph==0.2.0           # Workflow orchestration
langchain-openai==0.2.0    # GPT-4 integration

# Storage
pymysql==1.1.0            # MariaDB connector
chromadb==0.4.0           # Vector + document storage
boto3==1.28.0             # AWS S3 integration

# Data Processing
pandas==2.1.0             # Data analysis
numpy==1.24.0             # Numerical operations

# Visualization
matplotlib==3.8.0         # Charts
plotly==5.18.0           # Interactive visualizations

# Report Generation
markdown==3.5.0          # Markdown processing
weasyprint==60.0         # HTML to PDF conversion
jinja2==3.1.0           # Template rendering
```

### 5.2 Infrastructure Requirements

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **MariaDB RDS** | db.t3.medium, 100GB | Vessel traffic data |
| **Application Server** | t3.large EC2 or ECS Fargate | Run agents |
| **ChromaDB Storage** | S3 bucket or EFS | Research persistence |
| **Memory** | 8GB minimum | LLM operations |
| **API Rate Limits** | 10,000 TPM for GPT-4 | Research operations |

---

## 6. API Integrations

### 6.1 Required External APIs
- **OpenAI GPT-4**: Research and analysis
- **Carbon Market Data**: ICE/EEX for EUA prices (optional)
- **Shipping APIs**: MarineTraffic or similar (optional)

### 6.2 Internal API Endpoints
```python
# FastAPI endpoints for system interaction
GET  /api/insights/{quarter}      # Get discovered insights
POST /api/research                # Trigger research with guidance
GET  /api/findings/{quarter}       # Retrieve validated findings
POST /api/report/generate         # Generate quarterly report
GET  /api/report/{quarter}        # Retrieve generated report
```

---

## 7. Performance Specifications

### 7.1 Processing Metrics
| Operation | Target | Maximum |
|-----------|--------|---------|
| Data insight discovery | < 2 min | 5 min |
| Research per topic | < 1 min | 3 min |
| Validation per finding | < 10 sec | 30 sec |
| Report generation | < 5 min | 10 min |
| Vector search | < 500 ms | 2 sec |

### 7.2 Scalability Targets
- Concurrent research topics: 5-10
- Stored findings: 100,000+
- Quarterly reports: 50+
- Historical data: 2+ years

### 7.3 Accuracy Requirements
- Vessel movement validation: 95%
- Route matching accuracy: 90%
- Confidence scoring precision: 85%

---

## 8. Data Flow

### 8.1 Bidirectional Research Flow
```
1. Data → Insights → Research
   MariaDB → Pattern Detection → LLM Research → Validation

2. Guidance → Research → Validation
   User Topics → LLM Research → Traffic Validation → Storage

3. Storage → Retrieval → Report
   ChromaDB → Semantic Search → Context Building → Generation
```

### 8.2 Validation Pipeline
```
Research Finding 
    → Claim Extraction
    → SQL Query Generation
    → MariaDB Lookup
    → Confidence Calculation
    → ChromaDB Storage with Score
```

---

## 9. Security & Compliance

### 9.1 Data Security
- MariaDB: SSL/TLS encryption in transit
- ChromaDB: Encrypted at rest (S3 SSE)
- API Keys: AWS Secrets Manager
- Access Control: IAM roles for AWS resources

### 9.2 Rate Limiting
- OpenAI API: 10,000 TPM limit
- Database queries: Connection pooling
- ChromaDB: Batch operations for efficiency

---

## 10. Deployment Architecture

### 10.1 AWS Deployment (Recommended)
```yaml
Components:
  Database:
    - RDS MariaDB (existing)
    - Multi-AZ for high availability
  
  Application:
    - ECS Fargate or EC2
    - Auto-scaling group
    - Application Load Balancer
  
  Storage:
    - S3 for ChromaDB persistence
    - S3 for report archives
  
  Monitoring:
    - CloudWatch for logs
    - CloudWatch metrics for performance
```

### 10.2 Local Development
```yaml
Components:
  Database:
    - Local MariaDB or Docker container
    - Sample vessel data subset
  
  Application:
    - Python 3.10+ virtual environment
    - Local ChromaDB instance
  
  Storage:
    - Local filesystem for ChromaDB
    - Local report output directory
```

---

## 11. Monitoring & Observability

### 11.1 Key Metrics
- Research execution time per quarter
- Validation success rate
- Confidence score distribution
- API token usage
- Database query performance

### 11.2 Logging Strategy
```python
logging_config = {
    "agent_operations": "INFO",
    "validation_results": "INFO",
    "database_queries": "DEBUG",
    "api_calls": "INFO",
    "errors": "ERROR"
}
```

---

## 12. Development Roadmap

### Phase 1: MVP (Week 1-2)
- Basic MariaDB integration
- Single research agent
- Simple validation
- Markdown report output

### Phase 2: Full Agents (Week 3)
- All 5 research domains
- ChromaDB integration
- Semantic search
- Validation pipeline

### Phase 3: Production (Week 4)
- AWS deployment
- PDF generation
- Monitoring setup
- Performance optimization

---

## 13. Cost Analysis

### Monthly Operational Costs (Estimated)
| Service | Cost | Notes |
|---------|------|-------|
| RDS MariaDB | Existing | Already provisioned |
| EC2/Fargate | $50-100 | t3.large or equivalent |
| S3 Storage | $10-20 | Research + reports |
| OpenAI API | $200-400 | ~10K requests/month |
| **Total** | **$260-520** | Excluding existing RDS |

---

## 14. Success Criteria

### Technical KPIs
- System uptime: ≥99.5%
- Validation accuracy: ≥95%
- Report generation: 100% on schedule
- Query response time: <2 seconds

### Business KPIs
- Insights discovered per quarter: >20
- Validated findings: >80%
- Report adoption rate: >90%
- Decision influence: Documented impact

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-15  
**Status**: Final Technical Specification