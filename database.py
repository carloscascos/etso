"""
OBSERVATORIO ETS - Database Connection Manager
Handles dual database connections: traffic_db (readonly) + etso_db (full access)
"""

import pymysql
import logging
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from config import SystemConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages connections to both traffic and ETSO databases"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.traffic_config = config.database.TRAFFIC_DB
        self.etso_config = config.database.ETSO_DB
        
        # Test connections on initialization
        self.test_connections()
    
    @contextmanager
    def get_traffic_connection(self) -> Generator[pymysql.Connection, None, None]:
        """Get read-only connection to traffic database"""
        conn = None
        try:
            logger.debug("Connecting to traffic database (readonly)")
            conn = pymysql.connect(**self.traffic_config)
            yield conn
        except Exception as e:
            logger.error(f"Traffic database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Traffic database connection closed")
    
    @contextmanager
    def get_etso_connection(self) -> Generator[pymysql.Connection, None, None]:
        """Get full access connection to ETSO database"""
        conn = None
        try:
            logger.debug("Connecting to ETSO database (full access)")
            conn = pymysql.connect(**self.etso_config)
            yield conn
        except Exception as e:
            logger.error(f"ETSO database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("ETSO database connection closed")
    
    def test_connections(self) -> bool:
        """Test both database connections"""
        try:
            # Test traffic database
            with self.get_traffic_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM escalas LIMIT 1")
                traffic_result = cursor.fetchone()
                logger.info(f"✅ Traffic DB connected: {traffic_result[0] if traffic_result else 0} records accessible")
            
            # Test ETSO database
            with self.get_etso_connection() as conn:
                cursor = conn.cursor()
                # Check if research_metadata table exists
                cursor.execute("SHOW TABLES LIKE 'research_metadata'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM research_metadata")
                    etso_result = cursor.fetchone()
                    logger.info(f"✅ ETSO DB connected: {etso_result[0] if etso_result else 0} research records")
                else:
                    logger.warning("⚠️  ETSO DB connected but schema not initialized")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def execute_traffic_query(self, query: str, params: tuple = None) -> list:
        """Execute read-only query on traffic database"""
        with self.get_traffic_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_etso_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[list]:
        """Execute query on ETSO database with transaction support"""
        with self.get_etso_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                else:
                    result = cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
                
                conn.commit()
                return result
                
            except Exception as e:
                conn.rollback()
                logger.error(f"ETSO query failed: {e}")
                raise

class TrafficDataAccess:
    """Specialized class for traffic database queries"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_vessel_movements(self, imo: int, start_date: str, end_date: str) -> list:
        """Get vessel movements for specific IMO and date range"""
        query = """
        SELECT e.imo, v.vessel_name, e.portname, e.next_port, 
               e.start_time, e.end_time, e.fuel_consumption,
               p.country as port_country, p.zone as port_zone
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        LEFT JOIN ports p ON e.portname = p.portname
        WHERE e.imo = %s 
        AND e.start_time BETWEEN %s AND %s
        ORDER BY e.start_time
        """
        return self.db_manager.execute_traffic_query(query, (imo, start_date, end_date))
    
    def get_route_patterns(self, quarter: str, limit: int = 100) -> list:
        """Get route patterns for specific quarter"""
        query = """
        SELECT e.imo, v.vessel_name,
               GROUP_CONCAT(
                   CONCAT(e.portname, '->', COALESCE(e.next_port, 'END'))
                   ORDER BY e.start_time SEPARATOR ' | '
               ) as route_pattern,
               COUNT(*) as port_calls,
               AVG(e.fuel_consumption) as avg_fuel_consumption
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        WHERE CONCAT(YEAR(e.start_time), 'Q', QUARTER(e.start_time)) = %s
        GROUP BY e.imo, v.vessel_name
        HAVING port_calls >= 3
        ORDER BY port_calls DESC
        LIMIT %s
        """
        return self.db_manager.execute_traffic_query(query, (quarter, limit))
    
    def get_fuel_consumption_analysis(self, quarter: str) -> list:
        """Analyze fuel consumption patterns by route/zone"""
        query = """
        SELECT p.zone,
               COUNT(DISTINCT e.imo) as unique_vessels,
               COUNT(*) as total_calls,
               AVG(e.fuel_consumption) as avg_fuel_consumption,
               STDDEV(e.fuel_consumption) as fuel_deviation
        FROM escalas e
        JOIN ports p ON e.portname = p.portname
        WHERE CONCAT(YEAR(e.start_time), 'Q', QUARTER(e.start_time)) = %s
        AND e.fuel_consumption IS NOT NULL
        AND e.fuel_consumption > 0
        GROUP BY p.zone
        HAVING unique_vessels >= 5
        ORDER BY avg_fuel_consumption DESC
        """
        return self.db_manager.execute_traffic_query(query, (quarter,))

class ETSODataAccess:
    """Specialized class for ETSO database queries"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def store_research_metadata(self, metadata: Dict[str, Any]) -> int:
        """Store research metadata and return the ID"""
        query = """
        INSERT INTO research_metadata (
            chroma_id, quarter, theme_type, user_guidance,
            enhanced_query, status
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db_manager.execute_etso_query(
            query,
            (
                metadata['chroma_id'],
                metadata['quarter'],
                metadata['theme_type'],
                metadata.get('user_guidance', ''),
                metadata.get('enhanced_query', ''),
                metadata.get('status', 'pending')
            ),
            fetch=False
        )
    
    def get_research_metadata(self, research_id: int) -> Optional[dict]:
        """Get research metadata by ID"""
        query = """
        SELECT id, chroma_id, quarter, theme_type, user_guidance,
               enhanced_query, validation_score, overall_confidence,
               status, created_at, updated_at
        FROM research_metadata
        WHERE id = %s
        """
        result = self.db_manager.execute_etso_query(query, (research_id,))
        
        if result:
            row = result[0]
            return {
                'id': row[0],
                'chroma_id': row[1],
                'quarter': row[2],
                'theme_type': row[3],
                'user_guidance': row[4],
                'enhanced_query': row[5],
                'validation_score': row[6],
                'overall_confidence': row[7],
                'status': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            }
        return None
    
    def update_research_confidence(self, research_id: int, confidence: float, status: str = 'completed'):
        """Update research confidence score and status"""
        query = """
        UPDATE research_metadata 
        SET overall_confidence = %s, status = %s, updated_at = NOW()
        WHERE id = %s
        """
        return self.db_manager.execute_etso_query(
            query, (confidence, status, research_id), fetch=False
        )
    
    def store_validation_claim(self, claim_data: Dict[str, Any]) -> int:
        """Store validation claim result"""
        query = """
        INSERT INTO validation_claims (
            research_metadata_id, claim_text, claim_type,
            vessel_filter, route_filter, period_filter,
            validation_query, confidence_score, supports_claim,
            data_points_found, analysis_text
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db_manager.execute_etso_query(
            query,
            (
                claim_data['research_metadata_id'],
                claim_data['claim_text'],
                claim_data['claim_type'],
                claim_data['vessel_filter'],
                claim_data['route_filter'],
                claim_data['period_filter'],
                claim_data['validation_query'],
                claim_data['confidence_score'],
                claim_data['supports_claim'],
                claim_data['data_points_found'],
                claim_data['analysis_text']
            ),
            fetch=False
        )
    
    def get_quarterly_summary(self, quarter: str) -> dict:
        """Get quarterly research summary"""
        query = """
        SELECT 
            COUNT(*) as total_findings,
            COUNT(CASE WHEN overall_confidence >= 0.7 THEN 1 END) as high_confidence,
            AVG(overall_confidence) as avg_confidence,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
        FROM research_metadata
        WHERE quarter = %s
        """
        result = self.db_manager.execute_etso_query(query, (quarter,))
        
        if result:
            row = result[0]
            return {
                'quarter': quarter,
                'total_findings': row[0],
                'high_confidence_findings': row[1],
                'average_confidence': float(row[2]) if row[2] else 0.0,
                'completed_findings': row[3]
            }
        return {}

# Convenience function to create database manager
def create_database_manager(config: SystemConfig = None) -> DatabaseManager:
    """Create database manager with configuration"""
    if config is None:
        from config import config as default_config
        config = default_config
    
    return DatabaseManager(config)