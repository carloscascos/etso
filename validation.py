"""
OBSERVATORIO ETS - Dual Database Validation System
Validates research findings against vessel traffic data
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from database import DatabaseManager, TrafficDataAccess, ETSODataAccess

logger = logging.getLogger(__name__)

@dataclass
class ValidationClaim:
    """Structure for a verifiable claim extracted from research"""
    claim_text: str
    claim_type: str
    vessel: Optional[str] = None
    route: Optional[str] = None  
    period: Optional[str] = None
    metric: Optional[str] = None
    expected_change: Optional[str] = None
    confidence: float = 0.0

class ClaimExtractor:
    """Extracts verifiable claims from research findings"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.extraction_prompt = self._create_extraction_prompt()
    
    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a maritime data analyst. Extract specific, verifiable claims 
            from research findings that can be validated against vessel movement data.
            
            For each claim, identify:
            1. Claim text (exact statement)
            2. Claim type (vessel_movement, fuel_consumption, transit_time, route_pattern, port_frequency)
            3. Vessel name or IMO (if mentioned)
            4. Route description (ports, corridors, regions)
            5. Time period (quarter, year, date range)
            6. Metric (what is being measured)
            7. Expected change (increase, decrease, pattern)
            
            Only extract claims that mention specific vessels, routes, or measurable changes.
            Return as JSON array."""),
            ("human", """Research finding to analyze:
            {research_content}
            
            Expected validation targets:
            {validation_targets}
            
            Extract verifiable claims as JSON array with format:
            [{
                "claim_text": "exact claim from research",
                "claim_type": "vessel_movement|fuel_consumption|transit_time|route_pattern|port_frequency",
                "vessel": "vessel name or IMO if mentioned",
                "route": "route description",
                "period": "time period",
                "metric": "what is measured",
                "expected_change": "expected pattern or change"
            }]""")
        ])
    
    def extract_claims(self, research_content: str, validation_targets: List[str]) -> List[ValidationClaim]:
        """Extract verifiable claims from research content"""
        try:
            response = self.llm.invoke(
                self.extraction_prompt.format_messages(
                    research_content=research_content,
                    validation_targets=validation_targets
                )
            )
            
            # Parse JSON response
            claims_data = self._parse_json_response(response.content)
            
            # Convert to ValidationClaim objects
            claims = []
            for claim_dict in claims_data:
                claim = ValidationClaim(
                    claim_text=claim_dict.get('claim_text', ''),
                    claim_type=claim_dict.get('claim_type', 'general'),
                    vessel=claim_dict.get('vessel'),
                    route=claim_dict.get('route'),
                    period=claim_dict.get('period'),
                    metric=claim_dict.get('metric'),
                    expected_change=claim_dict.get('expected_change')
                )
                claims.append(claim)
            
            logger.info(f"✅ Extracted {len(claims)} verifiable claims")
            return claims
            
        except Exception as e:
            logger.error(f"❌ Failed to extract claims: {e}")
            return []
    
    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """Parse LLM JSON response, handling potential formatting issues"""
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback: manual parsing
            logger.warning("Failed to parse JSON response, using fallback parsing")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> List[Dict]:
        """Fallback parsing when JSON parsing fails"""
        # Simple fallback - extract basic claim information
        claims = []
        lines = text.split('\n')
        
        current_claim = {}
        for line in lines:
            line = line.strip()
            if 'claim_text' in line.lower():
                current_claim['claim_text'] = line.split(':', 1)[1].strip().strip('"')
            elif 'claim_type' in line.lower():
                current_claim['claim_type'] = line.split(':', 1)[1].strip().strip('"')
            elif 'vessel' in line.lower():
                current_claim['vessel'] = line.split(':', 1)[1].strip().strip('"')
            elif 'route' in line.lower():
                current_claim['route'] = line.split(':', 1)[1].strip().strip('"')
            elif len(current_claim) >= 2 and line == '':
                claims.append(current_claim)
                current_claim = {}
        
        if current_claim:
            claims.append(current_claim)
        
        return claims

class ValidationQueryGenerator:
    """Generates SQL queries to validate claims against traffic data"""
    
    def generate_validation_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate appropriate SQL query based on claim type"""
        
        query_generators = {
            'fuel_consumption': self._fuel_consumption_query,
            'transit_time': self._transit_time_query,
            'route_pattern': self._route_pattern_query,
            'port_frequency': self._port_frequency_query,
            'vessel_movement': self._vessel_movement_query
        }
        
        generator = query_generators.get(claim.claim_type, self._general_movement_query)
        return generator(claim, quarter)
    
    def _fuel_consumption_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate fuel consumption validation query"""
        vessel_filter = self._build_vessel_filter(claim.vessel)
        route_filter = self._build_route_filter(claim.route)
        period_filter = self._build_period_filter(claim.period, quarter)
        
        return f"""
        SELECT 
            e.imo,
            v.vessel_name,
            AVG(e.fuel_consumption) as avg_fuel_consumption,
            STDDEV(e.fuel_consumption) as fuel_deviation,
            COUNT(*) as voyage_count,
            MIN(e.start_time) as period_start,
            MAX(e.start_time) as period_end
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        LEFT JOIN ports p_start ON e.portname = p_start.portname
        LEFT JOIN ports p_end ON e.next_port = p_end.portname
        WHERE e.fuel_consumption IS NOT NULL
        AND e.fuel_consumption > 0
        {vessel_filter}
        {route_filter}
        {period_filter}
        GROUP BY e.imo, v.vessel_name
        HAVING voyage_count >= 2
        ORDER BY avg_fuel_consumption DESC
        LIMIT 50
        """
    
    def _transit_time_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate transit time validation query"""
        vessel_filter = self._build_vessel_filter(claim.vessel)
        route_filter = self._build_route_filter(claim.route)
        period_filter = self._build_period_filter(claim.period, quarter)
        
        return f"""
        WITH transit_calculations AS (
            SELECT 
                e1.imo,
                v.vessel_name,
                e1.portname as origin_port,
                e2.portname as destination_port,
                TIMESTAMPDIFF(DAY, e1.end_time, e2.start_time) as transit_days,
                e1.start_time as voyage_start
            FROM escalas e1
            JOIN escalas e2 ON e1.imo = e2.imo AND e1.next_leg = e2.prev_leg
            JOIN vessels v ON e1.imo = v.imo
            WHERE e1.next_port = e2.portname
            AND TIMESTAMPDIFF(DAY, e1.end_time, e2.start_time) BETWEEN 1 AND 60
            {vessel_filter.replace('e.', 'e1.')}
            {period_filter.replace('e.', 'e1.')}
        )
        SELECT 
            imo,
            vessel_name,
            origin_port,
            destination_port,
            AVG(transit_days) as avg_transit_days,
            STDDEV(transit_days) as transit_deviation,
            COUNT(*) as voyage_count,
            MIN(voyage_start) as period_start,
            MAX(voyage_start) as period_end
        FROM transit_calculations
        WHERE 1=1 {self._build_route_filter_transit(claim.route)}
        GROUP BY imo, vessel_name, origin_port, destination_port
        HAVING voyage_count >= 2
        ORDER BY avg_transit_days DESC
        LIMIT 30
        """
    
    def _route_pattern_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate route pattern validation query"""
        vessel_filter = self._build_vessel_filter(claim.vessel)
        period_filter = self._build_period_filter(claim.period, quarter)
        
        return f"""
        SELECT 
            e.imo,
            v.vessel_name,
            GROUP_CONCAT(
                DISTINCT CONCAT(e.portname, '->', COALESCE(e.next_port, 'END'))
                ORDER BY e.start_time 
                SEPARATOR ' | '
            ) as route_pattern,
            COUNT(DISTINCT e.portname) as unique_ports,
            COUNT(*) as total_calls,
            GROUP_CONCAT(DISTINCT p.zone) as zones_visited,
            AVG(e.fuel_consumption) as avg_fuel_consumption
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        LEFT JOIN ports p ON e.portname = p.portname
        WHERE 1=1
        {vessel_filter}
        {period_filter}
        GROUP BY e.imo, v.vessel_name
        HAVING total_calls >= 3
        ORDER BY unique_ports DESC, total_calls DESC
        LIMIT 25
        """
    
    def _port_frequency_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate port frequency validation query"""
        vessel_filter = self._build_vessel_filter(claim.vessel)
        route_filter = self._build_route_filter(claim.route)
        period_filter = self._build_period_filter(claim.period, quarter)
        
        return f"""
        SELECT 
            e.portname,
            p.country,
            p.zone,
            COUNT(DISTINCT e.imo) as unique_vessels,
            COUNT(*) as total_calls,
            AVG(e.fuel_consumption) as avg_fuel_consumption,
            COUNT(DISTINCT v.operator) as unique_operators
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        LEFT JOIN ports p ON e.portname = p.portname
        WHERE 1=1
        {vessel_filter}
        {route_filter}
        {period_filter}
        GROUP BY e.portname, p.country, p.zone
        HAVING total_calls >= 5
        ORDER BY total_calls DESC
        LIMIT 20
        """
    
    def _vessel_movement_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Generate general vessel movement query"""
        vessel_filter = self._build_vessel_filter(claim.vessel)
        route_filter = self._build_route_filter(claim.route)
        period_filter = self._build_period_filter(claim.period, quarter)
        
        return f"""
        SELECT 
            e.imo,
            v.vessel_name,
            e.portname,
            e.next_port,
            e.start_time,
            e.end_time,
            e.fuel_consumption,
            p.country,
            p.zone
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        LEFT JOIN ports p ON e.portname = p.portname
        WHERE 1=1
        {vessel_filter}
        {route_filter}
        {period_filter}
        ORDER BY e.start_time DESC
        LIMIT 100
        """
    
    def _general_movement_query(self, claim: ValidationClaim, quarter: str) -> str:
        """Fallback general movement query"""
        return self._vessel_movement_query(claim, quarter)
    
    def _build_vessel_filter(self, vessel_info: Optional[str]) -> str:
        """Build vessel filter clause"""
        if not vessel_info:
            return ""
        
        # Check if it looks like an IMO number (7 digits)
        if vessel_info.isdigit() and len(vessel_info) == 7:
            return f"AND e.imo = {vessel_info}"
        elif vessel_info.strip():
            # Search by vessel name (partial match)
            return f"AND v.vessel_name LIKE '%{vessel_info}%'"
        
        return ""
    
    def _build_route_filter(self, route_info: Optional[str]) -> str:
        """Build route filter clause"""
        if not route_info:
            return ""
        
        route_info = route_info.strip()
        
        # Handle specific port-to-port routes
        if '->' in route_info:
            ports = [p.strip() for p in route_info.split('->')]
            if len(ports) >= 2:
                origin, destination = ports[0], ports[1]
                return f"""
                AND (e.portname LIKE '%{origin}%' OR e.portname LIKE '%{destination}%')
                AND (e.next_port LIKE '%{origin}%' OR e.next_port LIKE '%{destination}%')
                """
        
        # Handle regional routes like "Asia-Europe"
        elif '-' in route_info and not route_info.replace('-', '').isdigit():
            regions = [r.strip() for r in route_info.split('-')]
            if len(regions) >= 2:
                region1, region2 = regions[0], regions[1]
                return f"""
                AND (p_start.zone LIKE '%{region1}%' OR p_start.zone LIKE '%{region2}%'
                     OR p_end.zone LIKE '%{region1}%' OR p_end.zone LIKE '%{region2}%')
                """
        
        # General port/region search
        else:
            return f"""
            AND (e.portname LIKE '%{route_info}%' 
                 OR e.next_port LIKE '%{route_info}%'
                 OR p.zone LIKE '%{route_info}%')
            """
        
        return ""
    
    def _build_route_filter_transit(self, route_info: Optional[str]) -> str:
        """Build route filter for transit time queries"""
        if not route_info:
            return ""
        
        if '->' in route_info:
            ports = [p.strip() for p in route_info.split('->')]
            if len(ports) >= 2:
                origin, destination = ports[0], ports[1]
                return f"""
                AND origin_port LIKE '%{origin}%'
                AND destination_port LIKE '%{destination}%'
                """
        
        return f"AND (origin_port LIKE '%{route_info}%' OR destination_port LIKE '%{route_info}%')"
    
    def _build_period_filter(self, period_info: Optional[str], default_quarter: str) -> str:
        """Build time period filter clause"""
        target_period = period_info or default_quarter
        
        if not target_period:
            return ""
        
        # Handle quarter format like "2024Q1"
        if 'Q' in target_period.upper():
            return f"AND CONCAT(YEAR(e.start_time), 'Q', QUARTER(e.start_time)) = '{target_period.upper()}'"
        
        # Handle year format like "2024"
        elif len(target_period) == 4 and target_period.isdigit():
            return f"AND YEAR(e.start_time) = {target_period}"
        
        # Handle date format (basic)
        else:
            return f"AND e.start_time >= '{target_period}'"

class ValidationAnalyzer:
    """Analyzes validation results using LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_analysis_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a maritime data analyst validating research claims against vessel traffic data.
            
            Analyze the database results and determine:
            1. Does the data support the claim? (Yes/No/Partially)
            2. Confidence level (0.0 to 1.0)
            3. Key evidence from the data
            4. Any contradictions or data limitations
            
            Be objective and quantitative in your analysis."""),
            ("human", """
            Original Claim: {claim}
            
            Database Query Results ({num_results} records):
            {results}
            
            Analyze whether the data supports this claim and provide:
            - Support Level: Yes/No/Partially
            - Confidence: 0.0-1.0
            - Evidence: Key supporting data points
            - Limitations: Any data gaps or contradictions
            
            Format as:
            SUPPORT: [Yes/No/Partially]
            CONFIDENCE: [0.0-1.0]
            EVIDENCE: [Key supporting evidence]
            LIMITATIONS: [Any limitations or contradictions]
            """)
        ])
    
    def analyze_validation_results(self, claim: ValidationClaim, query_results: List[tuple]) -> Dict[str, Any]:
        """Analyze validation query results"""
        try:
            # Format results for LLM analysis
            results_text = self._format_results_for_analysis(query_results)
            
            response = self.llm.invoke(
                self.analysis_prompt.format_messages(
                    claim=claim.claim_text,
                    num_results=len(query_results),
                    results=results_text
                )
            )
            
            # Parse analysis response
            analysis = self._parse_analysis_response(response.content)
            
            return {
                'supports_claim': analysis.get('support', 'No').lower() in ['yes', 'partially'],
                'confidence': float(analysis.get('confidence', 0.0)),
                'evidence': analysis.get('evidence', ''),
                'limitations': analysis.get('limitations', ''),
                'analysis_text': response.content,
                'data_points': len(query_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return {
                'supports_claim': False,
                'confidence': 0.0,
                'evidence': '',
                'limitations': f'Analysis error: {e}',
                'analysis_text': '',
                'data_points': len(query_results)
            }
    
    def _format_results_for_analysis(self, results: List[tuple]) -> str:
        """Format query results for LLM analysis"""
        if not results:
            return "No matching data found"
        
        # Show up to 10 results for analysis
        formatted_results = []
        for i, row in enumerate(results[:10]):
            formatted_results.append(f"Record {i+1}: {row}")
        
        if len(results) > 10:
            formatted_results.append(f"... and {len(results) - 10} more records")
        
        return '\n'.join(formatted_results)
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, str]:
        """Parse structured analysis response"""
        analysis = {}
        
        # Extract structured fields
        patterns = {
            'support': r'SUPPORT:\s*(.+?)(?:\n|$)',
            'confidence': r'CONFIDENCE:\s*([0-9.]+)',
            'evidence': r'EVIDENCE:\s*(.+?)(?:\nLIMITATIONS:|$)',
            'limitations': r'LIMITATIONS:\s*(.+?)(?:\n|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                analysis[key] = match.group(1).strip()
        
        return analysis

class DualDatabaseValidator:
    """Main validation system using both databases"""
    
    def __init__(self, db_manager: DatabaseManager, llm: ChatOpenAI):
        self.db_manager = db_manager
        self.traffic_access = TrafficDataAccess(db_manager)
        self.etso_access = ETSODataAccess(db_manager)
        
        self.claim_extractor = ClaimExtractor(llm)
        self.query_generator = ValidationQueryGenerator()
        self.analyzer = ValidationAnalyzer(llm)
        
        logger.info("✅ Dual database validator initialized")
    
    def validate_research_finding(self, research_metadata_id: int, research_content: str, 
                                validation_targets: List[str]) -> Dict[str, Any]:
        """Complete validation process for a research finding"""
        
        logger.info(f"🔍 Starting validation for research ID: {research_metadata_id}")
        
        try:
            # 1. Extract verifiable claims
            claims = self.claim_extractor.extract_claims(research_content, validation_targets)
            
            if not claims:
                logger.warning("⚠️  No verifiable claims extracted")
                return {'overall_confidence': 0.0, 'validation_results': []}
            
            # 2. Validate each claim
            validation_results = []
            for i, claim in enumerate(claims):
                logger.info(f"🔎 Validating claim {i+1}/{len(claims)}: {claim.claim_type}")
                result = self._validate_single_claim(claim, research_metadata_id)
                validation_results.append(result)
            
            # 3. Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(validation_results)
            
            # 4. Update research metadata
            self.etso_access.update_research_confidence(research_metadata_id, overall_confidence)
            
            logger.info(f"✅ Validation completed. Overall confidence: {overall_confidence:.3f}")
            
            return {
                'research_metadata_id': research_metadata_id,
                'validation_results': validation_results,
                'overall_confidence': overall_confidence,
                'total_claims': len(claims),
                'supported_claims': sum(1 for r in validation_results if r.get('supports_claim', False))
            }
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return {'overall_confidence': 0.0, 'validation_results': [], 'error': str(e)}
    
    def _validate_single_claim(self, claim: ValidationClaim, research_metadata_id: int) -> Dict[str, Any]:
        """Validate a single claim against traffic database"""
        
        try:
            # Generate validation query
            query = self.query_generator.generate_validation_query(claim, claim.period or "2025Q1")
            
            # Execute query against traffic database
            results = self.db_manager.execute_traffic_query(query)
            
            # Analyze results with LLM
            analysis = self.analyzer.analyze_validation_results(claim, results)
            
            # Store validation result in ETSO database
            claim_data = {
                'research_metadata_id': research_metadata_id,
                'claim_text': claim.claim_text,
                'claim_type': claim.claim_type,
                'vessel_filter': claim.vessel or '',
                'route_filter': claim.route or '',
                'period_filter': claim.period or '',
                'validation_query': query,
                'confidence_score': analysis['confidence'],
                'supports_claim': analysis['supports_claim'],
                'data_points_found': analysis['data_points'],
                'analysis_text': analysis['analysis_text']
            }
            
            self.etso_access.store_validation_claim(claim_data)
            
            return {
                'claim': claim,
                'query': query,
                'data_results': results[:5],  # Store only first 5 results
                'analysis': analysis,
                'confidence': analysis['confidence'],
                'supports_claim': analysis['supports_claim'],
                'status': 'validated'
            }
            
        except Exception as e:
            logger.error(f"❌ Single claim validation failed: {e}")
            return {
                'claim': claim,
                'error': str(e),
                'confidence': 0.0,
                'supports_claim': False,
                'status': 'failed'
            }
    
    def _calculate_overall_confidence(self, validation_results: List[Dict]) -> float:
        """Calculate overall confidence from individual validations"""
        
        if not validation_results:
            return 0.0
        
        # Weight by data points and support
        total_weight = 0
        weighted_confidence = 0
        
        for result in validation_results:
            if result['status'] == 'validated':
                # Weight by number of data points (more data = higher weight)
                data_weight = min(result['analysis']['data_points'] * 0.1 + 1.0, 3.0)
                
                # Boost weight if claim is supported
                support_weight = 1.5 if result.get('supports_claim', False) else 1.0
                
                final_weight = data_weight * support_weight
                
                weighted_confidence += result['confidence'] * final_weight
                total_weight += final_weight
        
        return min(weighted_confidence / total_weight if total_weight > 0 else 0.0, 1.0)