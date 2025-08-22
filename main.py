#!/usr/bin/env python3
"""
OBSERVATORIO ETS - Main Application
Maritime Carbon Intelligence System with dual-database architecture
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Local imports
from config import SystemConfig, config
from database import create_database_manager, DatabaseManager
from storage import create_storage_manager, ResearchStorageManager, ResearchFinding
from validation import DualDatabaseValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResearchTheme:
    """Enhanced research theme with user guidance"""
    original_input: str
    enhanced_query: str
    expected_outputs: List[str]
    validation_targets: List[str]
    research_scope: Dict[str, Any]

class ResearchThemeProcessor:
    """Processes user guidance into enhanced research themes"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.theme_prompt = self._create_theme_prompt()
    
    def _create_theme_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a maritime industry research specialist. Transform user research 
            requests into structured, actionable research themes for container shipping analysis.
            
            Focus on quantifiable, vessel-trackable impacts related to:
            - Carbon compliance and EU ETS
            - Trade route optimizations  
            - Vessel movements and service patterns
            - Fuel consumption and emissions
            - Port operations and congestion
            
            Structure your response as JSON with these fields:
            - enhanced_query: Improved research query with maritime terminology
            - expected_outputs: List of specific findings to discover  
            - validation_targets: What vessel data could confirm/deny findings
            - research_scope: Timeframe, geography, vessel types, focus areas"""),
            ("human", """User research request: {user_input}
            
            Context: Container shipping analysis with vessel traffic validation capability.
            Database contains: vessel movements (escalas), port calls, fuel consumption, routes.
            
            Transform into structured research theme (JSON format).""")
        ])
    
    def process_user_theme(self, user_input: str) -> ResearchTheme:
        """Convert user input into structured research theme"""
        
        try:
            logger.info(f"🔄 Processing research theme: {user_input[:50]}...")
            
            response = self.llm.invoke(
                self.theme_prompt.format_messages(user_input=user_input)
            )
            
            # Parse JSON response (simplified parsing)
            import json
            theme_data = self._extract_json_from_response(response.content)
            
            theme = ResearchTheme(
                original_input=user_input,
                enhanced_query=theme_data.get('enhanced_query', user_input),
                expected_outputs=theme_data.get('expected_outputs', []),
                validation_targets=theme_data.get('validation_targets', []),
                research_scope=theme_data.get('research_scope', {})
            )
            
            logger.info(f"✅ Research theme processed: {theme.enhanced_query[:100]}...")
            return theme
            
        except Exception as e:
            logger.error(f"❌ Theme processing failed: {e}")
            # Fallback to basic theme
            return ResearchTheme(
                original_input=user_input,
                enhanced_query=user_input,
                expected_outputs=[],
                validation_targets=[],
                research_scope={}
            )
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        import json
        import re
        
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback: create basic structure
            return {
                'enhanced_query': response_text[:500],
                'expected_outputs': [],
                'validation_targets': [],
                'research_scope': {}
            }

class ResearchAgent:
    """Conducts research based on enhanced themes"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.research_prompt = self._create_research_prompt()
    
    def _create_research_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a maritime carbon intelligence researcher specializing in container shipping.
            
            Research focus areas:
            - EU ETS compliance costs and carrier strategies
            - Trade route optimizations due to carbon regulations
            - Geopolitical impacts on shipping lanes (Red Sea, Suez, Panama)
            - Carrier-specific strategies (especially Maersk/GEMINI alliance)
            - Regional shipping developments (Eastern Mediterranean focus)
            
            Provide specific, quantifiable information including:
            - Vessel names and IMO numbers when available
            - Specific route details (port sequences, corridors)
            - Quantified impacts (costs, time, fuel consumption)
            - Dates and timeframes
            - Source references
            
            Make claims that can be validated against vessel movement data."""),
            ("human", """Research Query: {enhanced_query}
            
            Quarter: {quarter}
            Research Scope: {research_scope}
            
            Expected Findings:
            {expected_outputs}
            
            Conduct comprehensive research and provide detailed findings with specific examples.""")
        ])
    
    async def conduct_research(self, theme: ResearchTheme, quarter: str) -> str:
        """Conduct research based on enhanced theme"""
        
        logger.info(f"🔍 Conducting research: {theme.enhanced_query[:50]}...")
        
        try:
            response = await self.llm.ainvoke(
                self.research_prompt.format_messages(
                    enhanced_query=theme.enhanced_query,
                    quarter=quarter,
                    research_scope=theme.research_scope,
                    expected_outputs='\n'.join(f"- {output}" for output in theme.expected_outputs)
                )
            )
            
            logger.info(f"✅ Research completed: {len(response.content)} characters")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            return f"Research failed: {e}"

class DataInsightDiscovery:
    """Discovers insights from vessel traffic data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def discover_insights(self, quarter: str) -> List[Dict[str, Any]]:
        """Discover patterns and anomalies in vessel traffic data"""
        
        logger.info(f"📊 Discovering data insights for {quarter}")
        
        insights = []
        
        try:
            # Route deviation analysis
            route_insights = await self._analyze_route_deviations(quarter)
            insights.extend(route_insights)
            
            # Fuel consumption anomalies
            fuel_insights = await self._analyze_fuel_patterns(quarter)
            insights.extend(fuel_insights)
            
            # Port frequency changes
            port_insights = await self._analyze_port_patterns(quarter)
            insights.extend(port_insights)
            
            logger.info(f"✅ Discovered {len(insights)} data insights")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Data insight discovery failed: {e}")
            return []
    
    async def _analyze_route_deviations(self, quarter: str) -> List[Dict[str, Any]]:
        """Analyze route deviations and pattern changes"""
        
        query = """
        SELECT 
            e.imo,
            v.name as vessel_name,
            COUNT(DISTINCT e.next_port) as unique_destinations,
            COUNT(*) as total_calls,
            GROUP_CONCAT(DISTINCT p.zone) as zones_visited
        FROM escalas e
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN v_fleet v ON e.imo = v.imo
        LEFT JOIN ports p ON e.portname = p.portname
        WHERE CONCAT(YEAR(e.start), 'Q', QUARTER(e.start)) = %s
        AND e.next_port IS NOT NULL
        GROUP BY e.imo, v.name
        HAVING total_calls >= 5 AND unique_destinations >= 3
        ORDER BY unique_destinations DESC, total_calls DESC
        LIMIT 10
        """
        
        try:
            results = self.db_manager.execute_traffic_query(query, (quarter,))
            
            insights = []
            for row in results:
                insights.append({
                    'type': 'route_diversity',
                    'title': f'High route diversity detected for {row[1]}',
                    'description': f'Vessel {row[1]} (IMO: {row[0]}) visited {row[2]} different destinations in {row[3]} port calls',
                    'data': {
                        'imo': row[0],
                        'vessel_name': row[1],
                        'unique_destinations': row[2],
                        'total_calls': row[3],
                        'zones_visited': row[4]
                    },
                    'research_prompt': f'Research why {row[1]} shows high route diversity - possible service flexibility or market optimization?'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Route deviation analysis failed: {e}")
            return []
    
    async def _analyze_fuel_patterns(self, quarter: str) -> List[Dict[str, Any]]:
        """Analyze CO2 emissions patterns by zone"""
        
        query = """
        SELECT 
            p.zone,
            AVG(m.co2nm) as avg_co2_per_nm,
            STDDEV(m.co2nm) as co2_deviation,
            COUNT(DISTINCT e.imo) as vessel_count,
            COUNT(*) as total_port_calls
        FROM escalas e
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN ports p ON e.portname = p.portname
        JOIN v_MRV m ON e.imo = m.imo
        WHERE CONCAT(YEAR(e.start), 'Q', QUARTER(e.start)) = %s
        AND m.co2nm > 0
        GROUP BY p.zone
        HAVING vessel_count >= 5 AND co2_deviation > avg_co2_per_nm * 0.4
        ORDER BY co2_deviation DESC
        LIMIT 5
        """
        
        try:
            results = self.db_manager.execute_traffic_query(query, (quarter,))
            
            insights = []
            for row in results:
                insights.append({
                    'type': 'co2_emissions_anomaly',
                    'title': f'CO2 emissions variation in {row[0]}',
                    'description': f'Zone {row[0]} shows high CO2/nm variation (std dev: {row[2]:.2f} kg, avg: {row[1]:.2f} kg per nautical mile)',
                    'data': {
                        'zone': row[0],
                        'avg_co2_per_nm': row[1],
                        'co2_deviation': row[2],
                        'vessel_count': row[3],
                        'total_port_calls': row[4]
                    },
                    'research_prompt': f'Investigate CO2 emissions variations in {row[0]} - possible route diversions or fuel efficiency changes affecting carbon intensity?'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ CO2 emissions analysis failed: {e}")
            return []
    
    async def _analyze_port_patterns(self, quarter: str) -> List[Dict[str, Any]]:
        """Analyze port call frequency changes"""
        
        # This is a simplified version - in practice would compare with previous quarters
        query = """
        SELECT 
            e.portname,
            p.country,
            p.zone,
            COUNT(*) as call_frequency,
            COUNT(DISTINCT e.imo) as unique_vessels
        FROM escalas e
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN ports p ON e.portname = p.portname
        WHERE CONCAT(YEAR(e.start), 'Q', QUARTER(e.start)) = %s
        GROUP BY e.portname, p.country, p.zone
        HAVING call_frequency >= 50
        ORDER BY call_frequency DESC
        LIMIT 10
        """
        
        try:
            results = self.db_manager.execute_traffic_query(query, (quarter,))
            
            insights = []
            # Focus on ports with unusually high activity
            for row in results[:3]:  # Top 3 most active ports
                insights.append({
                    'type': 'port_activity',
                    'title': f'High activity at {row[0]}',
                    'description': f'Port {row[0]} ({row[1]}) handled {row[3]} calls from {row[4]} unique vessels',
                    'data': {
                        'port_name': row[0],
                        'country': row[1],
                        'zone': row[2],
                        'call_frequency': row[3],
                        'unique_vessels': row[4]
                    },
                    'research_prompt': f'Research growth drivers for {row[0]} port - new services, transshipment hub development?'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Port pattern analysis failed: {e}")
            return []

class ObservatorioETS:
    """Main OBSERVATORIO ETS application"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        
        # Initialize components
        self.db_manager = create_database_manager(config)
        self.storage_manager = create_storage_manager(self.db_manager, config)
        
        # Initialize LLM
        llm_config = config.llm.OPENAI_CONFIG
        self.llm = ChatOpenAI(
            api_key=llm_config['api_key'],
            model=llm_config['model'],
            temperature=llm_config['temperature'],
            max_tokens=llm_config['max_tokens']
        )
        
        # Initialize processors
        self.theme_processor = ResearchThemeProcessor(self.llm)
        self.research_agent = ResearchAgent(self.llm)
        self.validator = DualDatabaseValidator(self.db_manager, self.llm)
        self.insight_discovery = DataInsightDiscovery(self.db_manager)
        
        logger.info("🚀 OBSERVATORIO ETS initialized successfully")
    
    async def run_quarterly_analysis(self, quarter: str, user_themes: List[str]) -> Dict[str, Any]:
        """Run complete quarterly analysis with user guidance"""
        
        logger.info(f"🎯 Starting quarterly analysis for {quarter}")
        logger.info(f"📋 User themes: {user_themes}")
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Discover data insights
            logger.info("🔄 Phase 1: Data insight discovery")
            data_insights = await self.insight_discovery.discover_insights(quarter)
            
            # Phase 2: Process user themes
            logger.info("🔄 Phase 2: Processing user research themes")
            processed_themes = []
            for theme_input in user_themes:
                theme = self.theme_processor.process_user_theme(theme_input)
                processed_themes.append(theme)
            
            # Phase 3: Conduct research
            logger.info("🔄 Phase 3: Conducting research")
            research_results = []
            
            # Research user-guided themes
            for theme in processed_themes:
                research_content = await self.research_agent.conduct_research(theme, quarter)
                
                # Create research finding
                finding = ResearchFinding(
                    quarter=quarter,
                    theme_type=self._classify_theme_type(theme),
                    user_guidance=theme.original_input,
                    enhanced_query=theme.enhanced_query,
                    research_content=research_content,
                    validation_targets=theme.validation_targets,
                    expected_outputs=theme.expected_outputs,
                    research_scope=theme.research_scope
                )
                
                # Store research finding
                chroma_id, research_id = self.storage_manager.store_research_finding(finding)
                
                research_results.append({
                    'theme': theme,
                    'research_content': research_content,
                    'chroma_id': chroma_id,
                    'research_id': research_id
                })
            
            # Phase 4: Validate research findings
            logger.info("🔄 Phase 4: Validating research findings")
            validation_results = []
            
            for result in research_results:
                logger.info(f"🔎 Validating research ID: {result['research_id']}")
                
                validation_result = self.validator.validate_research_finding(
                    research_metadata_id=result['research_id'],
                    research_content=result['research_content'],
                    validation_targets=result['theme'].validation_targets
                )
                
                # Update confidence in storage
                if validation_result.get('overall_confidence', 0) > 0:
                    self.storage_manager.update_research_confidence(
                        result['research_id'],
                        validation_result['overall_confidence']
                    )
                
                validation_results.append(validation_result)
            
            # Phase 5: Generate summary
            logger.info("🔄 Phase 5: Generating quarterly summary")
            summary = await self._generate_quarterly_summary(
                quarter, data_insights, research_results, validation_results
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Quarterly analysis completed in {execution_time:.1f} seconds")
            
            return {
                'quarter': quarter,
                'execution_time_seconds': execution_time,
                'data_insights': data_insights,
                'research_results': research_results,
                'validation_results': validation_results,
                'summary': summary,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Quarterly analysis failed: {e}")
            return {
                'quarter': quarter,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _classify_theme_type(self, theme: ResearchTheme) -> str:
        """Classify theme type based on content"""
        
        query_lower = theme.enhanced_query.lower()
        
        if 'ets' in query_lower or 'carbon' in query_lower or 'emission' in query_lower:
            return 'eu_ets'
        elif 'route' in query_lower or 'corridor' in query_lower or 'service' in query_lower:
            return 'routes'
        elif 'geopolit' in query_lower or 'red sea' in query_lower or 'suez' in query_lower or 'panama' in query_lower:
            return 'geopolitical'
        elif 'maersk' in query_lower or 'carrier' in query_lower or 'alliance' in query_lower:
            return 'carrier'
        elif 'mediterranean' in query_lower or 'egypt' in query_lower or 'regional' in query_lower:
            return 'regional'
        else:
            return 'general'
    
    async def _generate_quarterly_summary(self, quarter: str, data_insights: List[Dict],
                                        research_results: List[Dict], 
                                        validation_results: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive quarterly summary"""
        
        total_research_findings = len(research_results)
        total_validations = len(validation_results)
        
        # Calculate validation metrics
        validated_findings = sum(1 for v in validation_results if v.get('overall_confidence', 0) >= 0.7)
        avg_confidence = sum(v.get('overall_confidence', 0) for v in validation_results) / total_validations if total_validations > 0 else 0
        
        # Count by theme type
        theme_distribution = {}
        for result in research_results:
            theme_type = self._classify_theme_type(result['theme'])
            theme_distribution[theme_type] = theme_distribution.get(theme_type, 0) + 1
        
        return {
            'quarter': quarter,
            'data_insights': {
                'total_discovered': len(data_insights),
                'by_type': self._count_by_type(data_insights, 'type')
            },
            'research_findings': {
                'total_findings': total_research_findings,
                'by_theme': theme_distribution
            },
            'validation_metrics': {
                'total_validations': total_validations,
                'validated_findings': validated_findings,
                'validation_rate': validated_findings / total_validations if total_validations > 0 else 0,
                'average_confidence': avg_confidence
            },
            'key_insights': data_insights[:5],  # Top 5 insights
            'high_confidence_findings': [
                v for v in validation_results 
                if v.get('overall_confidence', 0) >= 0.8
            ][:3]  # Top 3 high-confidence findings
        }
    
    def _count_by_type(self, items: List[Dict], type_field: str) -> Dict[str, int]:
        """Count items by type field"""
        counts = {}
        for item in items:
            item_type = item.get(type_field, 'unknown')
            counts[item_type] = counts.get(item_type, 0) + 1
        return counts

async def main():
    """Main execution function"""
    
    # Validate configuration
    if not config.validate_config():
        logger.error("❌ Configuration validation failed")
        return False
    
    # Initialize OBSERVATORIO ETS
    observatorio = ObservatorioETS(config)
    
    # Example usage
    quarter = "2025Q1"
    user_themes = [
        "Red Sea crisis impact on Asia-Europe container routes",
        "Maersk GEMINI alliance carbon compliance strategy",
        "Eastern Mediterranean transshipment hub development",
        "Transpacific trade Asia-America container volumes focusing on Long Beach port"
    ]
    
    # Run analysis
    results = await observatorio.run_quarterly_analysis(quarter, user_themes)
    
    # Display results summary
    logger.info("📊 ANALYSIS RESULTS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Quarter: {results['quarter']}")
    logger.info(f"Execution Time: {results.get('execution_time_seconds', 0):.1f}s")
    
    if 'error' in results:
        logger.error(f"❌ Analysis failed: {results['error']}")
        return False
    
    summary = results['summary']
    logger.info(f"Data Insights: {summary['data_insights']['total_discovered']}")
    logger.info(f"Research Findings: {summary['research_findings']['total_findings']}")
    logger.info(f"Validation Rate: {summary['validation_metrics']['validation_rate']:.1%}")
    logger.info(f"Average Confidence: {summary['validation_metrics']['average_confidence']:.3f}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)