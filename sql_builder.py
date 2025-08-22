#!/usr/bin/env python3
"""
SQL Query Builder from Validation Logic
Generates SQL queries based on natural language validation descriptions
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

@dataclass
class QueryComponents:
    """Components needed to build a SQL query"""
    claim_type: str
    vessel_filter: Optional[str] = None
    route_filter: Optional[str] = None
    port_filter: Optional[str] = None
    period_filter: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    comparison: Optional[str] = None

@dataclass
class SQLQueryResult:
    """Result of SQL query generation"""
    query: str
    explanation: str
    components: QueryComponents
    confidence: float
    query_type: str

class ValidationLogicParser:
    """Parses natural language validation logic into query components"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.parsing_prompt = self._create_parsing_prompt()
    
    def _create_parsing_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a maritime data analyst expert at converting validation logic into structured query components.

DATABASE SCHEMA CONTEXT:

## Core Tables:
- **escalas**: Main port call records (start, end, imo, portname, prev_port, next_port, prev_leg, next_leg)
- **port_trace**: Container vessel filter (PRIMARY KEY: imo) - ALWAYS JOIN with escalas
- **v_fleet**: Fleet info (imo, name, stype, group, fleet) - where fleet='containers' and group=shipping company
- **ports**: Port info (portname, country, zone, portcode)
- **v_MRV**: CO2 emissions (imo, co2nm=CO2 kg/nautical mile, foctd=fuel consumption)

## Required Query Pattern:
```sql
FROM escalas e
JOIN port_trace pt ON pt.imo = e.imo  -- REQUIRED for container vessels
JOIN v_fleet f ON e.imo = f.imo
WHERE f.fleet = 'containers'
```

## Vessel Identification Methods:
1. By IMO (most reliable): e.imo = 1016654
2. By Shipping Company: f.group LIKE '%MSC%' or '%Maersk%'
3. By Vessel Name: f.name LIKE '%MSC LEILA%'

## Analysis Patterns:
- Route sequences: prev_port → portname → next_port
- Distance: prev_leg, next_leg (nautical miles)
- Time: start/end timestamps for port call duration
- Geographic: JOIN ports for country/zone grouping
- Emissions: LEFT JOIN v_MRV for CO2 analysis

CRITICAL: You must respond with ONLY valid JSON - no explanations, no markdown, no additional text.

Parse the validation logic and identify:
1. claim_type: vessel_movement, transit_time, port_frequency, route_pattern, fuel_consumption
2. vessel_filter: specific vessel names, IMO numbers, or shipping companies (Maersk, MSC, etc.)
3. route_filter: trade routes, port pairs, or geographic regions
4. port_filter: specific ports mentioned (Rotterdam, Singapore, etc.)
5. period_filter: time periods (quarters, years, date ranges)
6. metric: what to measure (delays, frequency, emissions, transit time, etc.)
7. aggregation: how to aggregate (COUNT, AVG, SUM, MIN, MAX)
8. comparison: comparative terms (increase, decrease, higher, lower, vs previous period)

Response format:
{
    "claim_type": "vessel_movement",
    "vessel_filter": "Maersk vessels",
    "route_filter": "Asia-Europe trade lane", 
    "port_filter": "Rotterdam",
    "period_filter": "Q1 2025",
    "metric": "port call frequency",
    "aggregation": "COUNT",
    "comparison": "increase vs Q4 2024"
}"""),
            ("user", "Parse this validation logic: {validation_logic}")
        ])
    
    async def parse_validation_logic(self, validation_logic: str) -> QueryComponents:
        """Parse natural language validation logic into structured components"""
        
        try:
            response = await self.llm.ainvoke(
                self.parsing_prompt.format_messages(validation_logic=validation_logic)
            )
            
            # Parse JSON response
            import json
            components_dict = json.loads(response.content)
            
            return QueryComponents(
                claim_type=components_dict.get('claim_type', 'vessel_movement'),
                vessel_filter=components_dict.get('vessel_filter'),
                route_filter=components_dict.get('route_filter'),
                port_filter=components_dict.get('port_filter'),
                period_filter=components_dict.get('period_filter'),
                metric=components_dict.get('metric'),
                aggregation=components_dict.get('aggregation'),
                comparison=components_dict.get('comparison')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse validation logic: {e}")
            # Return basic components
            return QueryComponents(claim_type='vessel_movement')

class SQLQueryBuilder:
    """Builds SQL queries from parsed validation components"""
    
    def __init__(self):
        self.template_queries = {
            'vessel_movement': self._build_vessel_movement_query,
            'transit_time': self._build_transit_time_query,
            'port_frequency': self._build_port_frequency_query,
            'route_pattern': self._build_route_pattern_query,
            'fuel_consumption': self._build_fuel_consumption_query
        }
    
    def build_query(self, components: QueryComponents) -> SQLQueryResult:
        """Build SQL query from components"""
        
        query_builder = self.template_queries.get(
            components.claim_type, 
            self._build_vessel_movement_query
        )
        
        query, explanation, confidence = query_builder(components)
        
        return SQLQueryResult(
            query=query,
            explanation=explanation,
            components=components,
            confidence=confidence,
            query_type=components.claim_type
        )
    
    def _build_vessel_movement_query(self, components: QueryComponents) -> Tuple[str, str, float]:
        """Build vessel movement analysis query"""
        
        # Base query structure with required container vessel filtering
        select_clause = "SELECT e.imo, f.name as vessel_name, f.stype as vessel_type, f.group as shipping_company"
        from_clause = """FROM escalas e 
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN v_fleet f ON e.imo = f.imo"""
        where_conditions = ["f.fleet = 'containers'"]
        group_by = ""
        order_by = "ORDER BY e.start DESC"
        
        # Add specific fields based on metric
        if components.metric:
            if 'port' in components.metric.lower():
                select_clause += ", e.portname, COUNT(*) as port_calls"
                group_by = "GROUP BY e.imo, v.name, v.stype, e.portname"
                order_by = "ORDER BY port_calls DESC"
            elif 'route' in components.metric.lower():
                select_clause += ", e.portname, e.next_port, COUNT(*) as route_frequency"
                group_by = "GROUP BY e.imo, v.name, v.stype, e.portname, e.next_port"
                order_by = "ORDER BY route_frequency DESC"
            elif 'time' in components.metric.lower():
                select_clause += ", e.start, e.end, TIMESTAMPDIFF(HOUR, e.start, e.end) as port_time_hours"
        
        # Add filters
        if components.vessel_filter:
            vessel_condition = self._build_vessel_condition(components.vessel_filter)
            if vessel_condition:
                where_conditions.append(vessel_condition)
        
        if components.port_filter:
            port_condition = self._build_port_condition(components.port_filter)
            if port_condition:
                where_conditions.append(port_condition)
        
        if components.period_filter:
            period_condition = self._build_period_condition(components.period_filter)
            if period_condition:
                where_conditions.append(period_condition)
        
        if components.route_filter:
            route_condition = self._build_route_condition(components.route_filter)
            if route_condition:
                from_clause += " LEFT JOIN ports p_start ON e.portname = p_start.portname LEFT JOIN ports p_end ON e.next_port = p_end.portname"
                where_conditions.append(route_condition)
        
        # Build final query
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query_parts = [select_clause, from_clause, where_clause]
        if group_by:
            query_parts.append(group_by)
        query_parts.append(order_by)
        query_parts.append("LIMIT 100")
        
        query = "\n".join(query_parts)
        
        explanation = f"Analyzing vessel movement patterns"
        if components.vessel_filter:
            explanation += f" for {components.vessel_filter}"
        if components.port_filter:
            explanation += f" at {components.port_filter}"
        if components.period_filter:
            explanation += f" during {components.period_filter}"
        
        confidence = 0.8
        
        return query, explanation, confidence
    
    def _build_transit_time_query(self, components: QueryComponents) -> Tuple[str, str, float]:
        """Build transit time analysis query"""
        
        select_clause = """SELECT 
            e.imo,
            f.name as vessel_name,
            f.group as shipping_company,
            e.portname as departure_port,
            e.next_port as arrival_port,
            AVG(TIMESTAMPDIFF(HOUR, e.start, e.end)) as avg_port_time_hours,
            AVG(e.prev_leg) as avg_distance_nm,
            COUNT(*) as journey_count"""
        
        from_clause = """FROM escalas e 
        JOIN port_trace pt ON pt.imo = e.imo 
        JOIN v_fleet f ON e.imo = f.imo"""
        
        where_conditions = [
            "f.fleet = 'containers'",
            "e.next_port IS NOT NULL",
            "e.start IS NOT NULL",
            "e.end IS NOT NULL",
            "TIMESTAMPDIFF(HOUR, e.start, e.end) BETWEEN 1 AND 720"  # 1 hour to 30 days
        ]
        
        # Add specific filters
        if components.vessel_filter:
            vessel_condition = self._build_vessel_condition(components.vessel_filter)
            if vessel_condition:
                where_conditions.append(vessel_condition)
        
        if components.route_filter:
            route_condition = self._build_route_condition(components.route_filter)
            if route_condition:
                from_clause += " LEFT JOIN ports p_start ON e.portname = p_start.portname LEFT JOIN ports p_end ON e.next_port = p_end.portname"
                where_conditions.append(route_condition)
        
        if components.period_filter:
            period_condition = self._build_period_condition(components.period_filter)
            if period_condition:
                where_conditions.append(period_condition)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        group_by = "GROUP BY e.imo, v.name, e.portname, e.next_port"
        having = "HAVING journey_count >= 3"
        order_by = "ORDER BY avg_port_time_hours DESC"
        
        query = "\n".join([
            select_clause, from_clause, where_clause, 
            group_by, having, order_by, "LIMIT 50"
        ])
        
        explanation = f"Analyzing transit times between ports"
        if components.route_filter:
            explanation += f" for {components.route_filter} routes"
        if components.period_filter:
            explanation += f" during {components.period_filter}"
        
        return query, explanation, 0.9
    
    def _build_port_frequency_query(self, components: QueryComponents) -> Tuple[str, str, float]:
        """Build port frequency analysis query"""
        
        select_clause = """SELECT 
            e.portname,
            p.country,
            p.zone,
            COUNT(DISTINCT e.imo) as unique_vessels,
            COUNT(*) as total_calls,
            AVG(e.speed) as avg_speed"""
        
        from_clause = """FROM escalas e 
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN v_fleet f ON e.imo = f.imo
        LEFT JOIN ports p ON e.portname = p.portname"""
        
        where_conditions = ["f.fleet = 'containers'"]
        
        if components.vessel_filter:
            vessel_condition = self._build_vessel_condition(components.vessel_filter)
            if vessel_condition:
                where_conditions.append(vessel_condition)
        
        if components.port_filter:
            port_condition = self._build_port_condition(components.port_filter)
            if port_condition:
                where_conditions.append(port_condition)
        
        if components.period_filter:
            period_condition = self._build_period_condition(components.period_filter)
            if period_condition:
                where_conditions.append(period_condition)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        group_by = "GROUP BY e.portname, p.country"
        having = "HAVING total_calls >= 5"
        order_by = "ORDER BY total_calls DESC"
        
        query = "\n".join([
            select_clause, from_clause, where_clause,
            group_by, having, order_by, "LIMIT 30"
        ])
        
        explanation = f"Analyzing port call frequency"
        if components.port_filter:
            explanation += f" for {components.port_filter}"
        if components.period_filter:
            explanation += f" during {components.period_filter}"
        
        return query, explanation, 0.85
    
    def _build_route_pattern_query(self, components: QueryComponents) -> Tuple[str, str, float]:
        """Build route pattern analysis query"""
        
        select_clause = """SELECT 
            e.portname as origin_port,
            e.next_port as destination_port,
            p1.country as origin_country,
            p2.country as destination_country,
            p1.zone as origin_zone,
            p2.zone as destination_zone,
            COUNT(*) as route_frequency,
            COUNT(DISTINCT e.imo) as unique_vessels,
            AVG(e.speed) as avg_speed,
            AVG(e.next_leg) as avg_distance_nm"""
        
        from_clause = """FROM escalas e 
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN v_fleet f ON e.imo = f.imo
        LEFT JOIN ports p1 ON e.portname = p1.portname
        LEFT JOIN ports p2 ON e.next_port = p2.portname"""
        
        where_conditions = ["f.fleet = 'containers'", "e.next_port IS NOT NULL"]
        
        if components.vessel_filter:
            vessel_condition = self._build_vessel_condition(components.vessel_filter)
            if vessel_condition:
                where_conditions.append(vessel_condition)
        
        if components.route_filter:
            route_condition = self._build_route_condition(components.route_filter)
            if route_condition:
                where_conditions.append(route_condition)
        
        if components.period_filter:
            period_condition = self._build_period_condition(components.period_filter)
            if period_condition:
                where_conditions.append(period_condition)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        group_by = "GROUP BY e.portname, e.next_port, p1.country, p2.country"
        having = "HAVING route_frequency >= 3"
        order_by = "ORDER BY route_frequency DESC"
        
        query = "\n".join([
            select_clause, from_clause, where_clause,
            group_by, having, order_by, "LIMIT 40"
        ])
        
        explanation = f"Analyzing shipping route patterns"
        if components.route_filter:
            explanation += f" for {components.route_filter}"
        if components.period_filter:
            explanation += f" during {components.period_filter}"
        
        return query, explanation, 0.88
    
    def _build_fuel_consumption_query(self, components: QueryComponents) -> Tuple[str, str, float]:
        """Build fuel consumption analysis query"""
        
        select_clause = """SELECT 
            e.imo,
            f.name as vessel_name,
            f.stype as vessel_type,
            f.group as shipping_company,
            m.co2nm as co2_per_nautical_mile,
            m.foctd as fuel_consumption_tonnes_day,
            COUNT(*) as voyage_count,
            AVG(e.speed) as avg_speed,
            AVG(e.next_leg) as avg_distance_nm"""
        
        from_clause = """FROM escalas e 
        JOIN port_trace pt ON pt.imo = e.imo
        JOIN v_fleet f ON e.imo = f.imo
        LEFT JOIN v_MRV m ON e.imo = m.imo"""
        
        where_conditions = [
            "f.fleet = 'containers'",
            "m.co2nm IS NOT NULL",
            "m.co2nm > 0"
        ]
        
        if components.vessel_filter:
            vessel_condition = self._build_vessel_condition(components.vessel_filter)
            if vessel_condition:
                where_conditions.append(vessel_condition)
        
        if components.period_filter:
            period_condition = self._build_period_condition(components.period_filter)
            if period_condition:
                where_conditions.append(period_condition)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        group_by = "GROUP BY e.imo, v.name, v.stype, m.co2nm, m.foctd"
        having = "HAVING voyage_count >= 2"
        order_by = "ORDER BY m.co2nm DESC"
        
        query = "\n".join([
            select_clause, from_clause, where_clause,
            group_by, having, order_by, "LIMIT 50"
        ])
        
        explanation = f"Analyzing vessel fuel consumption and CO2 emissions"
        if components.vessel_filter:
            explanation += f" for {components.vessel_filter}"
        if components.period_filter:
            explanation += f" during {components.period_filter}"
        
        return query, explanation, 0.92
    
    def _build_vessel_condition(self, vessel_filter: str) -> str:
        """Build vessel filter condition using proper schema patterns"""
        vessel_lower = vessel_filter.lower()
        
        conditions = []
        
        # Check for IMO numbers (most reliable - all digits)
        if vessel_filter.isdigit() and len(vessel_filter) >= 7:
            conditions.append(f"e.imo = {vessel_filter}")
        elif any(char.isdigit() for char in vessel_filter) and len([c for c in vessel_filter if c.isdigit()]) >= 7:
            # Extract IMO if present
            import re
            imo_match = re.search(r'\d{7,}', vessel_filter)
            if imo_match:
                conditions.append(f"e.imo = {imo_match.group()}")
        
        # Check for shipping companies (use f.group - shipping company field)
        companies = {
            'maersk': 'f.group LIKE "%MAERSK%"',
            'msc': 'f.group LIKE "%MSC%"', 
            'cosco': 'f.group LIKE "%COSCO%"',
            'cma': 'f.group LIKE "%CMA%"',
            'hapag': 'f.group LIKE "%HAPAG%"',
            'evergreen': 'f.group LIKE "%EVERGREEN%"',
            'yang ming': 'f.group LIKE "%YANG MING%"',
            'oocl': 'f.group LIKE "%OOCL%"',
            'one': 'f.group LIKE "%ONE%"',
            'zim': 'f.group LIKE "%ZIM%"'
        }
        
        for company, condition in companies.items():
            if company in vessel_lower:
                conditions.append(condition)
        
        # Check for specific vessel names (less reliable)
        if not conditions:
            conditions.append(f'f.name LIKE "%{vessel_filter}%"')
        
        return "(" + " OR ".join(conditions) + ")"
    
    def _build_port_condition(self, port_filter: str) -> str:
        """Build port filter condition"""
        # Handle multiple ports
        ports = [p.strip() for p in port_filter.split(',')]
        port_conditions = [f"e.portname LIKE '%{port}%'" for port in ports]
        return "(" + " OR ".join(port_conditions) + ")"
    
    def _build_route_condition(self, route_filter: str) -> str:
        """Build route filter condition"""
        route_lower = route_filter.lower()
        
        # Define major trade routes
        route_conditions = {
            'asia-europe': "(p1.zone LIKE '%Asia%' AND p2.zone LIKE '%Europe%') OR (p1.zone LIKE '%Europe%' AND p2.zone LIKE '%Asia%')",
            'transpacific': "(p1.zone LIKE '%Asia%' AND p2.zone LIKE '%America%') OR (p1.zone LIKE '%America%' AND p2.zone LIKE '%Asia%')",
            'transatlantic': "(p1.zone LIKE '%Europe%' AND p2.zone LIKE '%America%') OR (p1.zone LIKE '%America%' AND p2.zone LIKE '%Europe%')",
            'intra-asia': "p1.zone LIKE '%Asia%' AND p2.zone LIKE '%Asia%'",
            'mediterranean': "p1.zone LIKE '%Mediterranean%' OR p2.zone LIKE '%Mediterranean%'"
        }
        
        for route_name, condition in route_conditions.items():
            if route_name.replace('-', '').replace(' ', '') in route_lower.replace('-', '').replace(' ', ''):
                return condition
        
        # Default: treat as region filter
        return f"(p1.zone LIKE '%{route_filter}%' OR p2.zone LIKE '%{route_filter}%')"
    
    def _build_period_condition(self, period_filter: str) -> str:
        """Build period filter condition"""
        period_lower = period_filter.lower()
        
        # Handle quarters
        if 'q1' in period_lower:
            year = '2025'
            if any(y in period_lower for y in ['2024', '2025', '2026', '2027']):
                year = next(y for y in ['2024', '2025', '2026', '2027'] if y in period_lower)
            return f"e.start >= '{year}-01-01' AND e.start < '{year}-04-01'"
        elif 'q2' in period_lower:
            year = '2025'
            if any(y in period_lower for y in ['2024', '2025', '2026', '2027']):
                year = next(y for y in ['2024', '2025', '2026', '2027'] if y in period_lower)
            return f"e.start >= '{year}-04-01' AND e.start < '{year}-07-01'"
        elif 'q3' in period_lower:
            year = '2025'
            if any(y in period_lower for y in ['2024', '2025', '2026', '2027']):
                year = next(y for y in ['2024', '2025', '2026', '2027'] if y in period_lower)
            return f"e.start >= '{year}-07-01' AND e.start < '{year}-10-01'"
        elif 'q4' in period_lower:
            year = '2025'
            if any(y in period_lower for y in ['2024', '2025', '2026', '2027']):
                year = next(y for y in ['2024', '2025', '2026', '2027'] if y in period_lower)
            return f"e.start >= '{year}-10-01' AND e.start < '{int(year)+1}-01-01'"
        
        # Handle years
        if '2024' in period_lower:
            return "e.start >= '2024-01-01' AND e.start < '2025-01-01'"
        elif '2025' in period_lower:
            return "e.start >= '2025-01-01' AND e.start < '2026-01-01'"
        elif '2026' in period_lower:
            return "e.start >= '2026-01-01' AND e.start < '2027-01-01'"
        elif '2027' in period_lower:
            return "e.start >= '2027-01-01' AND e.start < '2028-01-01'"
        
        # Default: last year
        return "e.start >= DATE_SUB(NOW(), INTERVAL 1 YEAR)"

class ValidationSQLBuilder:
    """Main class for building SQL from validation logic"""
    
    def __init__(self, llm: ChatOpenAI):
        self.parser = ValidationLogicParser(llm)
        self.builder = SQLQueryBuilder()
    
    async def build_sql_from_validation_logic(self, validation_logic: str) -> SQLQueryResult:
        """Build SQL query from natural language validation logic"""
        
        logger.info(f"🔧 Building SQL from validation logic: {validation_logic[:50]}...")
        
        try:
            # Parse validation logic into components
            components = await self.parser.parse_validation_logic(validation_logic)
            
            # Build SQL query from components
            result = self.builder.build_query(components)
            
            logger.info(f"✅ SQL query generated: {result.query_type} query with confidence {result.confidence}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to build SQL from validation logic: {e}")
            
            # Return fallback query
            fallback_components = QueryComponents(claim_type='vessel_movement')
            fallback_result = self.builder.build_query(fallback_components)
            fallback_result.explanation = f"Fallback query generated due to parsing error: {e}"
            fallback_result.confidence = 0.3
            
            return fallback_result
    
    def get_example_validation_logics(self) -> List[Dict[str, str]]:
        """Get example validation logics for testing"""
        
        return [
            {
                "logic": "Check if Maersk vessels increased port calls to Rotterdam in Q1 2025 compared to Q4 2024",
                "type": "port_frequency"
            },
            {
                "logic": "Analyze transit times for Asia-Europe trade routes to identify delays",
                "type": "transit_time"
            },
            {
                "logic": "Validate CO2 emissions increase for container vessels operating transpacific routes",
                "type": "fuel_consumption"
            },
            {
                "logic": "Examine route pattern changes for MSC vessels avoiding Suez Canal",
                "type": "route_pattern"
            },
            {
                "logic": "Verify increased vessel movements around Singapore hub during 2025",
                "type": "vessel_movement"
            },
            {
                "logic": "Check port congestion at Long Beach affecting container vessel schedules",
                "type": "port_frequency"
            }
        ]