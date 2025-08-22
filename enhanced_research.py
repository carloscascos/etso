#!/usr/bin/env python3
"""
Enhanced Research Agent - Comprehensive source tracking and report generation
Maritime Carbon Intelligence System with detailed source attribution
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.memory import ConversationBufferMemory

# Local imports
from database import DatabaseManager
from validation import DualDatabaseValidator

logger = logging.getLogger(__name__)

@dataclass
class ResearchSource:
    """Tracks individual research sources"""
    source_type: str  # 'database_query', 'web_search', 'analysis', 'inference'
    content: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ResearchStep:
    """Tracks individual research steps"""
    step_number: int
    description: str
    sources: List[ResearchSource] = field(default_factory=list)
    findings: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ComprehensiveResearchResult:
    """Enhanced research result with full source tracking"""
    theme: str
    quarter: str
    start_date: str
    end_date: str
    research_steps: List[ResearchStep] = field(default_factory=list)
    final_findings: str = ""
    all_sources: List[ResearchSource] = field(default_factory=list)
    confidence_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    related_themes: List[str] = field(default_factory=list)

class EnhancedMaritimeResearchAgent:
    """Comprehensive research agent with detailed source tracking"""
    
    def __init__(self, db_manager: DatabaseManager, llm: ChatOpenAI):
        self.db_manager = db_manager
        self.llm = llm
        self.validator = DualDatabaseValidator(db_manager, llm)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        
        # Create tools for the agent
        self.tools = self._create_tools()
        
        # Initialize agent
        self.agent = initialize_agent(
            self.tools, 
            llm, 
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, 
            memory=self.memory,
            verbose=True,
            max_iterations=10
        )
        
        # Research prompts
        self.research_prompt = self._create_research_prompt()
        self.synthesis_prompt = self._create_synthesis_prompt()
        
    def _create_tools(self) -> List[Tool]:
        """Create research tools for the agent"""
        return [
            Tool(
                name="vessel_movement_analysis",
                description="Analyze vessel movement patterns, port calls, and route changes from the escalas and port_trace tables",
                func=self._analyze_vessel_movements
            ),
            Tool(
                name="fleet_analysis", 
                description="Analyze fleet composition, ownership, and vessel characteristics from v_fleet table",
                func=self._analyze_fleet_data
            ),
            Tool(
                name="emissions_analysis",
                description="Analyze CO2 emissions and fuel consumption from MRV data",
                func=self._analyze_emissions_data
            ),
            Tool(
                name="port_analysis",
                description="Analyze port performance, traffic patterns, and regional trends",
                func=self._analyze_port_data
            ),
            Tool(
                name="time_series_analysis",
                description="Analyze trends over time periods and quarters",
                func=self._analyze_time_series
            ),
            Tool(
                name="comparative_analysis",
                description="Compare different periods, regions, or vessel segments",
                func=self._comparative_analysis
            )
        ]
    
    def _create_research_prompt(self) -> ChatPromptTemplate:
        """Create comprehensive research prompt"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert maritime industry research analyst with deep knowledge of container shipping, carbon regulations, and vessel operations.

Your task is to conduct comprehensive research on the given theme, utilizing all available data sources and analytical methods. 

RESEARCH METHODOLOGY:
1. Break down the research theme into specific investigable questions
2. Use multiple analytical approaches to gather evidence
3. Cross-reference findings from different data sources
4. Track ALL sources of information with confidence scores
5. Synthesize findings into actionable insights

DATA SOURCES AVAILABLE:
- escalas: Vessel port calls, arrival/departure times, vessel speeds
- port_trace: Container vessel tracking (filters for container vessels only)
- v_fleet: Vessel specifications, ownership, vessel types
- v_MRV: CO2 emissions per nautical mile, fuel consumption
- ports: Port details, locations, operational data

ANALYSIS FOCUS AREAS:
- EU ETS carbon regulation impacts on routing and operations
- Container vessel efficiency and emission patterns
- Port congestion and operational changes
- Trade route modifications and frequency changes
- Carrier strategy adaptations

Remember: Always join escalas with port_trace.imo to focus on container vessels only.
"""),
            ("user", """
Research Theme: {theme}
Research Period: {start_date} to {end_date}
Target Quarter: {quarter}

Conduct comprehensive research following these steps:
1. Identify key research questions
2. Plan analytical approach 
3. Execute analysis using available tools
4. Synthesize findings with source attribution
5. Provide actionable insights

Begin your research:
""")
        ])
    
    def _create_synthesis_prompt(self) -> ChatPromptTemplate:
        """Create synthesis prompt for final report"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are synthesizing comprehensive maritime research findings into a final report.

SYNTHESIS REQUIREMENTS:
- Integrate all research steps and findings
- Maintain source attribution for all claims
- Highlight key insights and trends
- Provide quantitative evidence where available
- Address research objectives directly
- Note any limitations or data gaps

FORMAT:
# Executive Summary
[Key findings and implications]

# Detailed Analysis
[Comprehensive findings with source attribution]

# Data Sources
[List all sources used with confidence ratings]

# Recommendations
[Actionable insights based on findings]
"""),
            ("user", """
Research Theme: {theme}
Research Steps: {research_steps}
All Sources: {sources}

Synthesize these findings into a comprehensive final report:
""")
        ])
    
    async def conduct_comprehensive_research(
        self, 
        theme: str, 
        quarter: str, 
        start_date: str, 
        end_date: str
    ) -> ComprehensiveResearchResult:
        """Conduct comprehensive research with full source tracking"""
        
        logger.info(f"🔬 Starting comprehensive research: {theme[:50]}...")
        
        result = ComprehensiveResearchResult(
            theme=theme,
            quarter=quarter,
            start_date=start_date,
            end_date=end_date
        )
        
        try:
            # Step 1: Initialize research with theme analysis
            step1 = await self._analyze_research_theme(theme, quarter, start_date, end_date)
            result.research_steps.append(step1)
            result.all_sources.extend(step1.sources)
            
            # Step 2: Execute agent-based research
            agent_response = await self._run_agent_research(theme, quarter, start_date, end_date)
            step2 = ResearchStep(
                step_number=2,
                description="Agent-based comprehensive analysis",
                findings=agent_response,
                sources=[ResearchSource(
                    source_type="agent_analysis",
                    content=agent_response,
                    confidence=0.8,
                    metadata={"agent_type": "conversational_react", "tools_used": [tool.name for tool in self.tools]}
                )]
            )
            result.research_steps.append(step2)
            result.all_sources.extend(step2.sources)
            
            # Step 3: Validate key claims
            validation_step = await self._validate_research_claims(result)
            result.research_steps.append(validation_step)
            result.all_sources.extend(validation_step.sources)
            
            # Step 4: Synthesize final findings
            final_findings = await self._synthesize_findings(result)
            result.final_findings = final_findings
            
            # Calculate overall confidence
            result.confidence_score = self._calculate_confidence(result.all_sources)
            
            # Extract keywords and related themes
            result.keywords = self._extract_keywords(theme, final_findings)
            result.related_themes = self._identify_related_themes(theme, final_findings)
            
            logger.info(f"✅ Comprehensive research completed. {len(result.research_steps)} steps, {len(result.all_sources)} sources")
            
        except Exception as e:
            logger.error(f"❌ Comprehensive research failed: {e}")
            result.final_findings = f"Research failed: {e}"
            result.confidence_score = 0.0
        
        return result
    
    async def _analyze_research_theme(self, theme: str, quarter: str, start_date: str, end_date: str) -> ResearchStep:
        """Analyze and break down the research theme"""
        
        theme_analysis_prompt = f"""
        Analyze this maritime research theme and create a research plan:
        
        Theme: {theme}
        Period: {start_date} to {end_date}
        Quarter: {quarter}
        
        Provide:
        1. Key research questions (5-7 specific questions)
        2. Data requirements and sources needed
        3. Expected analytical approaches
        4. Potential challenges and limitations
        """
        
        try:
            response = await self.llm.ainvoke(theme_analysis_prompt)
            
            source = ResearchSource(
                source_type="theme_analysis",
                content=response.content,
                confidence=0.9,
                metadata={"prompt_type": "theme_decomposition", "quarter": quarter}
            )
            
            return ResearchStep(
                step_number=1,
                description="Research theme analysis and planning",
                findings=response.content,
                sources=[source]
            )
            
        except Exception as e:
            logger.error(f"Theme analysis failed: {e}")
            return ResearchStep(
                step_number=1,
                description="Research theme analysis and planning",
                findings=f"Theme analysis failed: {e}",
                sources=[]
            )
    
    async def _run_agent_research(self, theme: str, quarter: str, start_date: str, end_date: str) -> str:
        """Run agent-based research using tools"""
        
        research_query = f"""
        Research Theme: {theme}
        Research Period: {start_date} to {end_date}
        Target Quarter: {quarter}
        
        Using the available tools, conduct comprehensive research on this theme. 
        Focus on container vessels (join with port_trace) and provide specific quantitative findings.
        Use multiple tools to gather evidence from different perspectives.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.agent.run(research_query)
            )
            return response
        except Exception as e:
            logger.error(f"Agent research failed: {e}")
            return f"Agent research failed: {e}"
    
    async def _validate_research_claims(self, result: ComprehensiveResearchResult) -> ResearchStep:
        """Validate key research claims using the validation system"""
        
        claims_to_validate = self._extract_claims_from_findings(result.final_findings if result.final_findings else "")
        
        validation_sources = []
        validation_findings = []
        
        for claim in claims_to_validate[:5]:  # Validate top 5 claims
            try:
                # Use existing validator to create validation query
                validation_result = await self.validator.validate_claim(
                    claim, 
                    result.quarter, 
                    claim_type="research_validation"
                )
                
                source = ResearchSource(
                    source_type="database_validation",
                    content=f"Claim: {claim}\nValidation: {validation_result}",
                    confidence=0.8 if "confirmed" in str(validation_result).lower() else 0.6,
                    metadata={"validation_type": "dual_database", "claim": claim}
                )
                
                validation_sources.append(source)
                validation_findings.append(f"Validated: {claim}")
                
            except Exception as e:
                logger.warning(f"Validation failed for claim: {claim[:50]}... Error: {e}")
                continue
        
        return ResearchStep(
            step_number=len(result.research_steps) + 1,
            description="Research claim validation",
            findings="\n".join(validation_findings),
            sources=validation_sources
        )
    
    def _extract_claims_from_findings(self, findings: str) -> List[str]:
        """Extract testable claims from research findings"""
        # Simple extraction - could be enhanced with NLP
        lines = findings.split('\n')
        claims = []
        
        for line in lines:
            line = line.strip()
            # Look for statements that could be validated
            if any(keyword in line.lower() for keyword in ['increase', 'decrease', 'trend', 'pattern', 'more', 'less', 'higher', 'lower']):
                if len(line) > 20 and len(line) < 200:  # Reasonable claim length
                    claims.append(line)
        
        return claims[:10]  # Return top 10 potential claims
    
    async def _synthesize_findings(self, result: ComprehensiveResearchResult) -> str:
        """Synthesize all research steps into final findings"""
        
        research_steps_text = "\n\n".join([
            f"Step {step.step_number}: {step.description}\n{step.findings}" 
            for step in result.research_steps
        ])
        
        sources_text = "\n".join([
            f"- {source.source_type}: {source.content[:100]}... (confidence: {source.confidence})"
            for source in result.all_sources
        ])
        
        try:
            response = await self.llm.ainvoke(
                self.synthesis_prompt.format_messages(
                    theme=result.theme,
                    research_steps=research_steps_text,
                    sources=sources_text
                )
            )
            return response.content
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return f"Synthesis failed: {e}"
    
    def _calculate_confidence(self, sources: List[ResearchSource]) -> float:
        """Calculate overall confidence score based on sources"""
        if not sources:
            return 0.0
        
        weighted_sum = sum(source.confidence for source in sources)
        return min(weighted_sum / len(sources), 1.0)
    
    def _extract_keywords(self, theme: str, findings: str) -> List[str]:
        """Extract relevant keywords from theme and findings"""
        # Simple keyword extraction - could be enhanced
        text = f"{theme} {findings}".lower()
        
        maritime_keywords = [
            'container', 'vessel', 'port', 'shipping', 'ets', 'carbon', 'emission',
            'route', 'cargo', 'freight', 'maritime', 'oceanic', 'trade', 'transport',
            'fuel', 'efficiency', 'regulation', 'compliance'
        ]
        
        found_keywords = [keyword for keyword in maritime_keywords if keyword in text]
        return found_keywords[:10]
    
    def _identify_related_themes(self, theme: str, findings: str) -> List[str]:
        """Identify related research themes"""
        # Simple theme identification - could be enhanced
        related = []
        
        if 'port' in theme.lower() or 'port' in findings.lower():
            related.append('Port Performance Analysis')
        if 'carbon' in theme.lower() or 'emission' in findings.lower():
            related.append('Carbon Emission Optimization')
        if 'route' in theme.lower() or 'route' in findings.lower():
            related.append('Route Optimization Studies')
        if 'carrier' in theme.lower() or 'line' in findings.lower():
            related.append('Carrier Strategy Analysis')
            
        return related[:5]
    
    # Tool implementation methods (simplified for space)
    def _analyze_vessel_movements(self, query: str) -> str:
        """Analyze vessel movement patterns"""
        # This would connect to database and run queries
        return f"Vessel movement analysis for: {query}"
    
    def _analyze_fleet_data(self, query: str) -> str:
        """Analyze fleet composition and characteristics"""
        return f"Fleet analysis for: {query}"
    
    def _analyze_emissions_data(self, query: str) -> str:
        """Analyze emissions and fuel consumption"""
        return f"Emissions analysis for: {query}"
    
    def _analyze_port_data(self, query: str) -> str:
        """Analyze port performance and traffic"""
        return f"Port analysis for: {query}"
    
    def _analyze_time_series(self, query: str) -> str:
        """Analyze time series trends"""
        return f"Time series analysis for: {query}"
    
    def _comparative_analysis(self, query: str) -> str:
        """Perform comparative analysis"""
        return f"Comparative analysis for: {query}"

class ReportGenerationSystem:
    """Enhanced report generation with previous report review"""
    
    def __init__(self, db_manager: DatabaseManager, llm: ChatOpenAI):
        self.db_manager = db_manager
        self.llm = llm
        
    async def generate_quarterly_report_with_history(
        self, 
        quarter: str, 
        research_results: List[ComprehensiveResearchResult]
    ) -> Dict[str, Any]:
        """Generate quarterly report reviewing previous reports for continuity"""
        
        logger.info(f"📊 Generating quarterly report for {quarter} with historical context")
        
        # Get previous reports
        previous_reports = await self._get_previous_reports(quarter)
        
        # Extract relevant information from previous reports
        historical_context = self._extract_historical_context(previous_reports)
        
        # Generate report with historical context
        report = await self._generate_enhanced_report(
            quarter, 
            research_results, 
            historical_context
        )
        
        return report
    
    async def _get_previous_reports(self, current_quarter: str) -> List[Dict[str, Any]]:
        """Retrieve previous quarterly reports"""
        try:
            with self.db_manager.get_etso_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT quarter, report_content, key_findings, created_at
                    FROM quarterly_reports
                    WHERE quarter < %s
                    ORDER BY created_at DESC
                    LIMIT 4
                """, (current_quarter,))
                
                return [
                    {
                        'quarter': row[0],
                        'content': row[1],
                        'findings': row[2],
                        'date': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to retrieve previous reports: {e}")
            return []
    
    def _extract_historical_context(self, previous_reports: List[Dict[str, Any]]) -> str:
        """Extract relevant context from previous reports"""
        if not previous_reports:
            return "No previous reports available for historical context."
        
        context_parts = []
        for report in previous_reports:
            context_parts.append(f"Quarter {report['quarter']}: {report['findings'][:200]}...")
        
        return "\n\n".join(context_parts)
    
    async def _generate_enhanced_report(
        self, 
        quarter: str, 
        research_results: List[ComprehensiveResearchResult], 
        historical_context: str
    ) -> Dict[str, Any]:
        """Generate enhanced report with historical continuity"""
        
        report_prompt = f"""
        Generate a comprehensive quarterly report for {quarter} that:
        
        1. Synthesizes current quarter findings
        2. References relevant historical trends from previous quarters
        3. Identifies continuing patterns and new developments
        4. Provides forward-looking insights
        
        CURRENT QUARTER FINDINGS:
        {self._format_research_results(research_results)}
        
        HISTORICAL CONTEXT:
        {historical_context}
        
        Create a professional quarterly report with:
        - Executive Summary
        - Key Findings (with historical comparison)
        - Trend Analysis
        - Source Attribution
        - Recommendations
        """
        
        try:
            response = await self.llm.ainvoke(report_prompt)
            
            return {
                'quarter': quarter,
                'report_content': response.content,
                'research_count': len(research_results),
                'total_sources': sum(len(result.all_sources) for result in research_results),
                'average_confidence': sum(result.confidence_score for result in research_results) / len(research_results) if research_results else 0,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                'quarter': quarter,
                'report_content': f"Report generation failed: {e}",
                'error': str(e)
            }
    
    def _format_research_results(self, results: List[ComprehensiveResearchResult]) -> str:
        """Format research results for report generation"""
        formatted_parts = []
        
        for i, result in enumerate(results, 1):
            formatted_parts.append(f"""
Research Theme {i}: {result.theme}
Confidence Score: {result.confidence_score:.2f}
Sources Used: {len(result.all_sources)}
Key Findings: {result.final_findings[:300]}...
Keywords: {', '.join(result.keywords)}
""")
        
        return "\n".join(formatted_parts)