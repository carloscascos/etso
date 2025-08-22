# Product Requirements Document (PRD)
# OBSERVATORIO ETS - Maritime Carbon Intelligence System

## 1. Executive Summary

### 1.1 Product Vision
OBSERVATORIO ETS is an automated intelligence system designed to analyze the impact of carbon emission regulations on global container shipping routes. The system aggregates multi-source intelligence, validates findings against real vessel movement data, and produces quarterly reports for stakeholders navigating carbon tax compliance in the maritime sector.

### 1.2 Core Value Proposition
- **Automated Intelligence Gathering**: Continuous monitoring of carbon tax impacts on shipping
- **Data Validation**: Cross-referencing research findings with actual vessel tracking data
- **Quarterly Synthesis**: Professional reports combining multiple intelligence streams
- **Cost Quantification**: Precise calculation of carbon compliance costs per route

### 1.3 Target Users
- Shipping line executives managing carbon compliance strategies
- Port authorities adapting to changing trade patterns
- Freight forwarders optimizing route selection
- Maritime consultants advising on regulatory impacts
- Government agencies monitoring trade flow changes

## 2. System Architecture Overview

### 2.1 Conceptual Framework
The system operates as a distributed intelligence network with specialized research agents, centralized data management, and automated report generation:

```
[Research Layer] → [Storage Layer] → [Validation Layer] → [Publishing Layer]
```

### 2.2 Core Components

#### 2.2.1 Research Engine
- **Multiple Specialized Agents**: Domain-specific intelligence collectors
- **Parallel Processing**: Concurrent research execution
- **Source Diversity**: Web scraping, API integration, document analysis
- **Temporal Coverage**: Real-time to historical trend analysis

#### 2.2.2 Data Management System
- **Centralized Storage**: All research findings in unified repository
- **Semantic Indexing**: Content tagged with metadata for retrieval
- **Vector Embeddings**: Cross-agent knowledge correlation
- **Historical Persistence**: Quarter-over-quarter trend tracking

#### 2.2.3 Validation Engine
- **Database Integration**: Real vessel movement verification
- **Ground Truth Checking**: Research claims vs. actual data
- **Confidence Scoring**: Reliability metrics for all findings
- **Correction Tracking**: Documentation of validated changes

#### 2.2.4 Publishing Pipeline
- **Multi-Format Output**: Word, PDF, web-based dashboards
- **Professional Formatting**: Executive-ready document styling
- **Automated Distribution**: Scheduled delivery to stakeholders
- **Version Control**: Historical report archiving

## 3. Functional Requirements

### 3.1 Research Agent Specifications

#### 3.1.1 Carbon Tax Analysis Agent (EU ETS Specialist)
**Purpose**: Monitor and analyze European Union Emissions Trading System impacts

**Functional Requirements**:
- Track daily carbon allowance (EUA) prices from market sources
- Calculate compliance costs for specific shipping routes
- Monitor regulatory changes and implementation timelines
- Analyze carrier adaptation strategies and service modifications
- Identify cost mitigation approaches and best practices

**Data Sources**:
- Carbon market exchanges (ICE, EEX)
- EU regulatory publications
- Shipping industry reports
- Carrier announcements and earnings calls

**Output Requirements**:
- Daily EUA price updates with trend analysis
- Route-specific compliance cost calculations
- Regulatory change impact assessments
- Carrier strategy summaries

#### 3.1.2 Trade Routes Analysis Agent
**Purpose**: Analyze carbon tax impacts on major shipping corridors

**Coverage Areas**:
- North Europe-Asia routes
- Mediterranean-Asia connections
- Middle East trade lanes
- India subcontinent services
- West Africa corridors
- South America connections

**Functional Requirements**:
- Map service patterns and port rotations
- Calculate emissions per corridor based on distance and vessel size
- Identify route optimization strategies
- Track service restructuring announcements
- Analyze modal shift patterns (rail/sea competition)

**Output Requirements**:
- Corridor-specific emission profiles
- Service change notifications
- Route optimization recommendations
- Competitive positioning analysis

#### 3.1.3 Geopolitical Intelligence Agent
**Purpose**: Analyze geopolitical events affecting shipping with carbon cost implications

**Functional Requirements**:
- Monitor conflict zones impacting shipping lanes
- Track trade sanctions and their routing effects
- Analyze infrastructure developments (new ports, canals)
- Assess weather/climate impacts on routing
- Evaluate political decisions affecting trade flows

**Special Focus Areas**:
- Red Sea/Suez Canal security situations
- Panama Canal restrictions
- Arctic route viability
- Strait chokepoint monitoring

**Output Requirements**:
- Risk assessment matrices
- Alternative routing cost analyses
- Timeline projections for disruptions
- Carbon cost implications of diversions

#### 3.1.4 Carrier Intelligence Agent (Maersk Focus)
**Purpose**: Track major carrier performance and carbon compliance strategies

**Functional Requirements**:
- Monitor fleet deployment and vessel movements
- Track alliance formations and service agreements
- Analyze carbon reduction initiatives
- Calculate carrier-specific compliance costs
- Document green technology adoption

**Specific Tracking**:
- GEMINI Alliance operations
- Vessel efficiency improvements
- Alternative fuel adoption
- Carbon offset programs

**Output Requirements**:
- Carrier scorecards with emission metrics
- Alliance network analysis
- Technology adoption timelines
- Compliance cost comparisons

#### 3.1.5 Regional Specialist Agent (Eastern Mediterranean)
**Purpose**: Deep-dive analysis of specific regional shipping dynamics

**Geographic Coverage**:
- Egypt (Suez Canal, Port Said, Alexandria)
- Israel (Haifa, Ashdod)
- Turkey (Istanbul, Mersin, Izmir)

**Functional Requirements**:
- Track port congestion and capacity
- Monitor infrastructure investments
- Analyze transshipment patterns
- Assess regional carrier strategies
- Calculate regional carbon advantages/disadvantages

**Output Requirements**:
- Port performance metrics
- Infrastructure development timelines
- Regional competitive analysis
- Carbon cost differentials

### 3.2 Data Management Agent (Datagent) Requirements

#### 3.2.1 Core Functionality
**Purpose**: Centralized hub for all research content with intelligent storage and retrieval

**Storage Requirements**:
- Accept content from all research agents
- Maintain data integrity and versioning
- Support concurrent write operations
- Handle various content types (text, tables, charts)
- Preserve temporal context (timestamps, quarters)

**Indexing Requirements**:
- Semantic tagging of all content
- Multi-dimensional categorization:
  - Agent source
  - Topic/theme
  - Geographic region
  - Time period
  - Confidence level
  - Validation status

**Retrieval Requirements**:
- Full-text search capability
- Semantic similarity search
- Cross-agent correlation queries
- Temporal range filtering
- Confidence-based filtering

#### 3.2.2 Vector Embedding System
**Purpose**: Enable intelligent content correlation across agents

**Requirements**:
- Generate embeddings for all stored content
- Support similarity searches
- Identify related findings across agents
- Detect duplicate or contradictory information
- Enable trend identification

#### 3.2.3 Metadata Management
**Required Metadata Fields**:
- Source agent identifier
- Creation timestamp
- Geographic relevance
- Topic categories
- Validation status
- Confidence score
- Related content links
- Quarterly assignment

### 3.3 Validation Agent Requirements

#### 3.3.1 Database Integration
**Purpose**: Validate research findings against vessel tracking database is optional, the user will write a query to validate the findings, the sytem will execute the query and interpret the results and dtermine if the findings are validated or not.

**Core Database Tables Required**:
- Vessel registry (IMO, name, capacity, owner)
- Port calls (arrival/departure times, port names)
- Vessel tracks (position history, speed, draft)
- Route segments (origin, destination, distance)
- Container capacity (TEU data)

**Validation Operations**:
- Verify reported vessel movements
- Confirm service pattern claims
- Calculate actual distances sailed
- Compute precise emission figures
- Validate capacity utilizations

#### 3.3.2 Validation Workflow
**Process Requirements**:
1. Receive research finding flagged for validation
2. Parse claim into verifiable components
3. User writes Query against vessel database for relevant data
4. Sytem Compars research claim with database facts
5. Calculate confidence score
6. Document discrepancies
7. Store validation results with original research

**Validation Metrics**:
- Accuracy percentage
- Data completeness
- Temporal alignment
- Geographic precision
- Capacity correlation

### 3.4 Report Generation Agent (Formatter) Requirements

#### 3.4.1 Content Aggregation
**Purpose**: Synthesize all validated research into professional reports

**Aggregation Requirements**:
- Query datagent for quarterly content
- Prioritize validated over unvalidated findings
- Cross-correlate findings from multiple agents
- Identify key themes and trends
- Generate executive summaries

**Synthesis Rules**:
- Combine related findings into coherent narratives
- Resolve contradictions using validation scores
- Highlight consensus findings
- Flag areas of uncertainty
- Quantify impacts where possible

#### 3.4.2 Document Formatting
**Professional Styling Requirements**:
- Executive summary (1-2 pages)
- Table of contents with hyperlinks
- Hierarchical heading structure
- Professional typography:
  - Title: 24pt, bold, centered
  - Section headers: 18pt, bold
  - Subsections: 14pt, bold
  - Body text: 11pt, regular
- Color scheme:
  - Primary: Blue (#2145A5)
  - Secondary: Dark gray gradients
  - Accent: Green for positive, red for negative

**Content Elements**:
- Charts and visualizations
- Data tables with formatting
- Callout boxes for key findings
- Footnotes and references
- Appendices with detailed data

#### 3.4.3 Output Formats
**Supported Formats**:
- Microsoft Word (.docx)
- PDF with embedded charts
- Web-based dashboards
- Interactive spreadsheets
- Executive presentations

**Format-Specific Requirements**:
- Word: Maintain styles, support track changes
- PDF: Preserve formatting, embed fonts
- Web: Responsive design, interactive elements
- Spreadsheets: Linked data, pivot tables
- Presentations: Speaker notes, animations

### 3.5 System Integration Requirements

#### 3.5.1 Agent Communication
**Inter-Agent Messaging**:
- Asynchronous message passing
- Event-driven triggers
- Status broadcasting
- Error propagation
- Completion notifications

**Workflow Orchestration**:
- Research phase coordination
- Validation queue management
- Publishing pipeline control
- Retry mechanisms
- Failure recovery

#### 3.5.2 Data Flow Management
**Pipeline Requirements**:
```
Research Agent → Datagent Storage → Validation Queue → Traffic Validator → 
Datagent Update → Formatter Query → Report Generation → Distribution
```

**Flow Control**:
- Batch processing capabilities
- Stream processing for real-time data
- Queue management for validation
- Parallel processing where applicable
- Sequential dependencies handling

## 4. Data Requirements

### 4.1 Container Ship Focus
**Critical Requirement**: System exclusively analyzes container vessel traffic

**Data Filtering**:
- Only vessels with TEU capacity > 0
- Exclude bulk carriers, tankers, passenger vessels
- Focus on liner services (scheduled operations)
- Include feeder and mainline vessels

### 4.2 Temporal Requirements
**Update Frequencies**:
- Carbon prices: Daily
- Vessel movements: Real-time where available
- Service changes: Weekly
- Regulatory updates: As announced
- Quarterly reports: Every 3 months

**Historical Data**:
- Minimum 2 years historical comparison
- Quarter-over-quarter trending
- Year-over-year analysis
- Seasonal pattern detection

### 4.3 Geographic Coverage
**Primary Regions**:
- European Union ports (ETS coverage)
- United Kingdom (Brexit implications)
- Major Asian hubs (Singapore, Shanghai, Hong Kong)
- Middle East transshipment (Dubai, Jeddah)
- North American gateways

**Route Prioritization**:
1. Asia-North Europe (highest volume)
2. Asia-Mediterranean
3. Transatlantic
4. Middle East-Europe
5. Africa-Europe
6. South America-Europe

## 5. Performance Requirements

### 5.1 Processing Metrics
- Research agent execution: < 5 minutes per query
- Database validation: < 30 seconds per claim
- Report generation: < 10 minutes for quarterly report
- Content storage: < 1 second per item
- Search retrieval: < 2 seconds for complex queries

### 5.2 Accuracy Requirements
- Vessel movement validation: 95% accuracy
- Carbon cost calculations: ± 5% margin
- Service pattern detection: 90% precision
- Trend identification: 85% confidence

### 5.3 Scalability Requirements
- Support 10+ concurrent research agents
- Handle 100,000+ stored research items
- Process 1,000+ validation requests/day
- Generate 50+ reports/quarter
- Maintain 2+ years of historical data

## 6. Quality Assurance

### 6.1 Validation Protocols
- Automated fact-checking against database
- Cross-agent contradiction detection
- Source reliability scoring
- Temporal consistency checking
- Geographic accuracy validation

### 6.2 Report Quality
- Grammar and spell checking
- Formatting consistency validation
- Data accuracy verification
- Chart/table integrity checking
- Reference link validation

## 7. Security and Compliance

### 7.1 Data Protection
- Encrypted storage for sensitive data
- Access control by user role
- Audit logging of all operations
- Data retention policies
- GDPR compliance where applicable

### 7.2 System Security
- API authentication required
- Rate limiting on external queries
- Input validation and sanitization
- Output filtering for sensitive data
- Regular security updates

## 8. User Interface Requirements

### 8.1 Command Interface
**Natural Language Commands**:
- Research initiation: "Analyze carbon costs for Asia-Europe routes"
- Validation requests: "Verify Maersk service changes with database"
- Report generation: "Create Q1 2025 quarterly report"
- Status queries: "Show pending validations"

### 8.2 Output Interface
**Report Delivery**:
- Email distribution lists
- Cloud storage integration
- Web portal access
- API endpoints for data
- Scheduled delivery options

## 9. Success Metrics

### 9.1 Business Metrics
- Report adoption rate by stakeholders
- Decision influence tracking
- Cost savings identified
- Risk mitigation value
- User satisfaction scores

### 9.2 Technical Metrics
- System uptime: 99.5%
- Data accuracy: 95%
- Report delivery: 100% on schedule
- Agent success rate: 90%
- Validation coverage: 80% of claims

## 10. Future Enhancements

### 10.1 Phase 2 Capabilities
- Real-time alerting system
- Predictive modeling integration
- Machine learning for pattern detection
- Automated trading recommendations
- Mobile application interface

### 10.2 Phase 3 Expansion
- Coverage of additional regulations (FuelEU, IMO 2030)
- Expansion to bulk and tanker sectors
- Integration with booking platforms
- Carbon credit trading analysis
- Supply chain optimization

## Appendix A: Glossary

- **ETS**: Emissions Trading System
- **EUA**: European Union Allowance (carbon credit)
- **TEU**: Twenty-foot Equivalent Unit (container measure)
- **IMO**: International Maritime Organization vessel identifier
- **kTEUmile**: Thousand TEU-miles (capacity-distance metric)
- **Transshipment**: Transfer between vessels at intermediate port
- **Liner Service**: Scheduled container shipping route
- **Alliance**: Carrier cooperation agreement
- **Feeder**: Smaller vessel serving regional ports
- **Mainline**: Large vessel on primary trade routes

## Appendix B: Sample Calculations

### Carbon Emission Formula
```
Emissions (tonnes CO2) = Distance (nm) × Capacity (TEU) × Emission Factor (kg/TEU/nm) / 1000
```

### ETS Cost Calculation
```
ETS Cost (EUR) = Emissions × Coverage Factor × Carbon Price
Where:
- Coverage Factor = 0.5 for EU ports (50% of emissions)
- Coverage Factor = 0.0 for UK ports (no ETS)
- Carbon Price = Current EUA price (e.g., 80 EUR/tonne)
```

### Validation Score
```
Confidence = (Matching_Data_Points / Total_Data_Points) × 100
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-10  
**Status**: Complete  
**Classification**: Product Requirements