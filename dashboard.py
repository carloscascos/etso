"""
OBSERVATORIO ETS - Research Dashboard
Real-time monitoring of research findings, validations, and reports
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from database import create_database_manager, ETSODataAccess
from storage import ResearchStorageManager
from config import config as system_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database and storage managers
db_manager = create_database_manager(system_config)
etso_access = ETSODataAccess(db_manager)
storage_manager = ResearchStorageManager(db_manager, system_config)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/summary')
def get_summary():
    """Get overall system summary"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get current quarter stats
            current_quarter = system_config.research.CURRENT_QUARTER
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_findings,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'validating' THEN 1 END) as validating,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    AVG(overall_confidence) as avg_confidence,
                    MAX(created_at) as last_research
                FROM research_metadata
                WHERE quarter = %s
            """, (current_quarter,))
            
            result = cursor.fetchone()
            
            return jsonify({
                'quarter': current_quarter,
                'total_findings': result[0] or 0,
                'completed': result[1] or 0,
                'validating': result[2] or 0,
                'pending': result[3] or 0,
                'avg_confidence': float(result[4] or 0),
                'last_research': result[5].isoformat() if result[5] else None
            })
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-findings')
def get_research_findings():
    """Get recent research findings with details"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rm.id,
                    rm.chroma_id,
                    rm.quarter,
                    rm.theme_type,
                    rm.user_guidance,
                    rm.enhanced_query,
                    rm.overall_confidence,
                    rm.status,
                    rm.created_at,
                    COUNT(vc.id) as claim_count,
                    AVG(vc.confidence_score) as avg_claim_confidence
                FROM research_metadata rm
                LEFT JOIN validation_claims vc ON rm.id = vc.research_metadata_id
                GROUP BY rm.id
                ORDER BY rm.created_at DESC
                LIMIT 20
            """)
            
            findings = []
            for row in cursor.fetchall():
                findings.append({
                    'id': row[0],
                    'chroma_id': row[1],
                    'quarter': row[2],
                    'theme_type': row[3],
                    'user_guidance': row[4],
                    'enhanced_query': row[5],
                    'overall_confidence': float(row[6] or 0),
                    'status': row[7],
                    'created_at': row[8].isoformat() if row[8] else None,
                    'claim_count': row[9] or 0,
                    'avg_claim_confidence': float(row[10] or 0)
                })
            
            return jsonify(findings)
    except Exception as e:
        logger.error(f"Error getting research findings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validation-status')
def get_validation_status():
    """Get validation status and results"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    vc.claim_type,
                    COUNT(*) as total_claims,
                    AVG(vc.confidence_score) as avg_confidence,
                    SUM(CASE WHEN vc.supports_claim = 1 THEN 1 ELSE 0 END) as supported,
                    SUM(CASE WHEN vc.supports_claim = 0 THEN 1 ELSE 0 END) as rejected,
                    AVG(vc.data_points_found) as avg_data_points
                FROM validation_claims vc
                JOIN research_metadata rm ON vc.research_metadata_id = rm.id
                WHERE rm.quarter = %s
                GROUP BY vc.claim_type
            """, (system_config.research.CURRENT_QUARTER,))
            
            validations = []
            for row in cursor.fetchall():
                validations.append({
                    'claim_type': row[0],
                    'total_claims': row[1],
                    'avg_confidence': float(row[2] or 0),
                    'supported': row[3] or 0,
                    'rejected': row[4] or 0,
                    'avg_data_points': float(row[5] or 0)
                })
            
            return jsonify(validations)
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quarterly-reports')
def get_quarterly_reports():
    """Get quarterly report summaries"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    quarter,
                    total_findings,
                    high_confidence_findings,
                    average_confidence,
                    created_at
                FROM quarterly_reports
                ORDER BY quarter DESC
                LIMIT 8
            """)
            
            reports = []
            for row in cursor.fetchall():
                reports.append({
                    'quarter': row[0],
                    'total_findings': row[1],
                    'high_confidence_findings': row[2],
                    'average_confidence': float(row[3] or 0),
                    'created_at': row[4].isoformat() if row[4] else None
                })
            
            return jsonify(reports)
    except Exception as e:
        logger.error(f"Error getting quarterly reports: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-insights')
def get_data_insights():
    """Get data insights and patterns"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    insight_type,
                    category,
                    metric_value,
                    metric_unit,
                    description,
                    created_at
                FROM data_insights
                WHERE quarter = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (system_config.research.CURRENT_QUARTER,))
            
            insights = []
            for row in cursor.fetchall():
                insights.append({
                    'insight_type': row[0],
                    'category': row[1],
                    'metric_value': float(row[2]) if row[2] else None,
                    'metric_unit': row[3],
                    'description': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return jsonify(insights)
    except Exception as e:
        logger.error(f"Error getting data insights: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def get_themes():
    """Get all research themes grouped by type"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rm.id,
                    rm.theme_type,
                    rm.quarter,
                    rm.user_guidance,
                    rm.overall_confidence,
                    rm.status,
                    rm.created_at,
                    rm.updated_at,
                    COUNT(vc.id) as claim_count,
                    AVG(vc.confidence_score) as avg_claim_confidence,
                    SUM(CASE WHEN vc.supports_claim = 1 THEN 1 ELSE 0 END) as supported_claims
                FROM research_metadata rm
                LEFT JOIN validation_claims vc ON rm.id = vc.research_metadata_id
                GROUP BY rm.id
                ORDER BY rm.theme_type, rm.created_at DESC
            """)
            
            themes_by_type = {}
            for row in cursor.fetchall():
                theme_type = row[1]
                if theme_type not in themes_by_type:
                    themes_by_type[theme_type] = []
                
                themes_by_type[theme_type].append({
                    'id': row[0],
                    'quarter': row[2],
                    'user_guidance': row[3],
                    'overall_confidence': float(row[4] or 0),
                    'status': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'updated_at': row[7].isoformat() if row[7] else None,
                    'claim_count': row[8] or 0,
                    'avg_claim_confidence': float(row[9] or 0),
                    'supported_claims': row[10] or 0
                })
            
            return jsonify(themes_by_type)
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<int:research_id>')
def get_research_detail(research_id):
    """Get detailed information about a specific research finding"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get research metadata
            cursor.execute("""
                SELECT 
                    id, chroma_id, quarter, theme_type, user_guidance, 
                    enhanced_query, research_content_preview, overall_confidence, 
                    status, created_at, updated_at
                FROM research_metadata
                WHERE id = %s
            """, (research_id,))
            
            metadata_row = cursor.fetchone()
            if not metadata_row:
                return jsonify({'error': 'Research not found'}), 404
            
            metadata = {
                'id': metadata_row[0],
                'chroma_id': metadata_row[1],
                'quarter': metadata_row[2],
                'theme_type': metadata_row[3],
                'user_guidance': metadata_row[4],
                'enhanced_query': metadata_row[5],
                'research_content_preview': metadata_row[6],
                'overall_confidence': float(metadata_row[7] or 0),
                'status': metadata_row[8],
                'created_at': metadata_row[9].isoformat() if metadata_row[9] else None,
                'updated_at': metadata_row[10].isoformat() if metadata_row[10] else None
            }
            
            # Get validation claims with SQL queries
            cursor.execute("""
                SELECT 
                    id, claim_text, claim_type, vessel_filter, route_filter, 
                    period_filter, validation_query, validation_logic, confidence_score, 
                    supports_claim, data_points_found, analysis_text, 
                    validation_timestamp
                FROM validation_claims
                WHERE research_metadata_id = %s
                ORDER BY id
            """, (research_id,))
            
            claims = []
            for row in cursor.fetchall():
                claims.append({
                    'id': row[0],
                    'claim_text': row[1],
                    'claim_type': row[2],
                    'vessel_filter': row[3],
                    'route_filter': row[4],
                    'period_filter': row[5],
                    'validation_query': row[6],
                    'validation_logic': row[7],
                    'confidence_score': float(row[8] or 0),
                    'supports_claim': row[9],
                    'data_points_found': row[10] or 0,
                    'analysis_text': row[11],
                    'validation_timestamp': row[12].isoformat() if row[12] else None
                })
        
        # Get research content from ChromaDB if available
        research_content = None
        if metadata['chroma_id']:
            try:
                import chromadb
                from chromadb.config import Settings
                import os
                
                client = chromadb.PersistentClient(
                    path=os.getenv('CHROMA_PERSIST_DIR', './chroma_data'),
                    settings=Settings(anonymized_telemetry=False)
                )
                collection = client.get_collection(name=os.getenv('CHROMA_COLLECTION', 'observatorio_research'))
                
                result = collection.get(
                    ids=[metadata['chroma_id']],
                    include=['documents']
                )
                if result['documents']:
                    research_content = result['documents'][0]
            except Exception as e:
                logger.warning(f"Could not retrieve ChromaDB content: {e}")
        
        return jsonify({
            'metadata': metadata,
            'claims': claims,
            'research_content': research_content
        })
    except Exception as e:
        logger.error(f"Error getting research detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/claim/<int:claim_id>/results')
def get_claim_results(claim_id):
    """Get the actual SQL query results for a validation claim"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get the claim and its validation query
            cursor.execute("""
                SELECT validation_query, claim_text, data_points_found
                FROM validation_claims
                WHERE id = %s
            """, (claim_id,))
            
            result = cursor.fetchone()
            if not result or not result[0]:
                return jsonify({'error': 'Validation query not found'}), 404
            
            validation_query = result[0]
            claim_text = result[1]
            data_points_found = result[2]
            
        # Execute the validation query on traffic database
        query_results = []
        try:
            with db_manager.get_traffic_connection() as traffic_conn:
                traffic_cursor = traffic_conn.cursor()
                traffic_cursor.execute(validation_query)
                
                # Get column names
                columns = [desc[0] for desc in traffic_cursor.description]
                
                # Fetch results (limit to prevent overwhelming response)
                rows = traffic_cursor.fetchmany(100)
                
                for row in rows:
                    query_results.append(dict(zip(columns, row)))
        
        except Exception as e:
            logger.error(f"Error executing validation query: {e}")
            return jsonify({
                'error': f'Query execution failed: {str(e)}',
                'query': validation_query,
                'claim_text': claim_text
            }), 500
        
        return jsonify({
            'claim_text': claim_text,
            'validation_query': validation_query,
            'data_points_found': data_points_found,
            'query_results': query_results,
            'result_count': len(query_results)
        })
    
    except Exception as e:
        logger.error(f"Error getting claim results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-research', methods=['POST'])
def execute_research():
    """Execute new research theme"""
    try:
        data = request.get_json()
        theme = data.get('theme')
        quarter = data.get('quarter', '2025Q1')
        start_date = data.get('startDate', '2022-01-01')
        end_date = data.get('endDate', '2025-03-31')
        quarter_display = data.get('quarterDisplay', 'Q1 2025')
        research_period = data.get('researchPeriod', 'January 2022 to March 2025')
        
        if not theme:
            return jsonify({'error': 'Theme is required'}), 400
            
        # Enhance theme with date range context
        enhanced_theme = f"""
Research Theme: {theme}

Research Period: {research_period}
Analysis Timeframe: {start_date} to {end_date}
Target Quarter: {quarter_display}

Context: This research should analyze maritime carbon regulations and container shipping data within the specified timeframe, focusing on trends, patterns, and regulatory impacts from {start_date} through {end_date}."""
        
        # Import here to avoid circular imports
        from main import ObservatorioETS
        import asyncio
        import threading
        
        # Store the research ID that will be returned
        research_result = {'research_id': None, 'error': None}
        
        def run_research():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Initialize OBSERVATORIO ETS
                observatorio = ObservatorioETS(system_config)
                
                # Run research with enhanced theme containing date range
                result = loop.run_until_complete(
                    observatorio.run_quarterly_analysis(quarter, [enhanced_theme])
                )
                
                # Extract research ID from result
                if result and 'research_findings' in result.get('summary', {}):
                    # Get the latest research ID from database
                    with db_manager.get_etso_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id FROM research_metadata 
                            WHERE user_guidance = %s AND quarter = %s
                            ORDER BY created_at DESC LIMIT 1
                        """, (theme, quarter))
                        row = cursor.fetchone()
                        if row:
                            research_result['research_id'] = row[0]
                        
                loop.close()
                
            except Exception as e:
                research_result['error'] = str(e)
                logger.error(f"Research execution error: {e}")
        
        # Start research in background thread
        thread = threading.Thread(target=run_research)
        thread.daemon = True
        thread.start()
        
        # Wait a moment to see if we can get the research ID quickly
        thread.join(timeout=2.0)
        
        if research_result['error']:
            return jsonify({'error': research_result['error']}), 500
        
        if research_result['research_id']:
            return jsonify({
                'success': True,
                'research_id': research_result['research_id'],
                'message': 'Research execution started successfully'
            })
        else:
            # Research is still running, return a placeholder ID
            return jsonify({
                'success': True,
                'research_id': 'pending',
                'message': 'Research execution started in background'
            })
        
    except Exception as e:
        logger.error(f"Error executing research: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rerun-theme/<int:theme_id>', methods=['POST'])
def rerun_theme(theme_id):
    """Re-run existing research theme"""
    try:
        # Get existing theme details
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_guidance, quarter FROM research_metadata
                WHERE id = %s
            """, (theme_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Theme not found'}), 404
            
            theme, quarter = result
        
        # Execute the research using the same logic as execute_research
        from main import ObservatorioETS
        import asyncio
        import threading
        
        research_result = {'research_id': None, 'error': None}
        
        def run_research():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                observatorio = ObservatorioETS(system_config)
                
                result = loop.run_until_complete(
                    observatorio.run_quarterly_analysis(quarter, [theme])
                )
                
                # Get the latest research ID
                with db_manager.get_etso_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id FROM research_metadata 
                        WHERE user_guidance = %s AND quarter = %s
                        ORDER BY created_at DESC LIMIT 1
                    """, (theme, quarter))
                    row = cursor.fetchone()
                    if row:
                        research_result['research_id'] = row[0]
                        
                loop.close()
                
            except Exception as e:
                research_result['error'] = str(e)
                logger.error(f"Theme re-run error: {e}")
        
        thread = threading.Thread(target=run_research)
        thread.daemon = True
        thread.start()
        thread.join(timeout=2.0)
        
        if research_result['error']:
            return jsonify({'error': research_result['error']}), 500
        
        return jsonify({
            'success': True,
            'research_id': research_result['research_id'] or 'pending',
            'message': f'Theme {theme_id} re-execution started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error re-running theme {theme_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/claim/<int:claim_id>')
def get_claim_details(claim_id):
    """Get detailed information about a specific validation claim"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    claim_text, claim_type, vessel_filter, route_filter,
                    period_filter, validation_query, validation_logic, confidence_score,
                    supports_claim, data_points_found, analysis_text
                FROM validation_claims
                WHERE id = %s
            """, (claim_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Claim not found'}), 404
            
            claim = {
                'claim_text': result[0],
                'claim_type': result[1],
                'vessel_filter': result[2],
                'route_filter': result[3],
                'period_filter': result[4],
                'validation_query': result[5],
                'validation_logic': result[6],
                'confidence_score': float(result[7] or 0),
                'supports_claim': result[8],
                'data_points_found': result[9] or 0,
                'analysis_text': result[10]
            }
            
            return jsonify(claim)
            
    except Exception as e:
        logger.error(f"Error getting claim details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-health')
def get_system_health():
    """Get system health and status"""
    try:
        health = {
            'databases': {
                'traffic_db': False,
                'etso_db': False,
                'chromadb': False
            },
            'services': {
                'research_processor': True,
                'validator': True,
                'storage_manager': True
            }
        }
        
        # Test database connections
        try:
            with db_manager.get_traffic_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                health['databases']['traffic_db'] = True
        except:
            pass
        
        try:
            with db_manager.get_etso_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                health['databases']['etso_db'] = True
        except:
            pass
        
        try:
            # Test ChromaDB
            storage_manager.collection.count()
            health['databases']['chromadb'] = True
        except:
            pass
        
        return jsonify(health)
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<int:research_id>/status')
def get_research_status(research_id):
    """Get quick status of a research item"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, overall_confidence, updated_at
                FROM research_metadata
                WHERE id = %s
            """, (research_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Research not found'}), 404
            
            return jsonify({
                'status': result[0],
                'overall_confidence': float(result[1] or 0),
                'updated_at': result[2].isoformat() if result[2] else None
            })
            
    except Exception as e:
        logger.error(f"Error getting research status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-validation-claim', methods=['POST'])
def create_validation_claim():
    """Create a new validation claim with user-entered query and logic"""
    try:
        data = request.get_json()
        research_id = data.get('research_id')
        claim_text = data.get('claim_text')
        validation_query = data.get('validation_query') 
        validation_logic = data.get('validation_logic')
        claim_type = data.get('claim_type', 'manual')
        
        if not all([research_id, claim_text, validation_query, validation_logic]):
            return jsonify({'error': 'Missing required fields: research_id, claim_text, validation_query, validation_logic'}), 400
        
        # Basic security checks - only allow SELECT statements  
        query_upper = validation_query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return jsonify({'error': 'Query contains forbidden operations'}), 400
        
        # Test the query first by executing it
        try:
            with db_manager.get_traffic_connection() as traffic_conn:
                traffic_cursor = traffic_conn.cursor()
                traffic_cursor.execute('SET SESSION wait_timeout = 30')
                traffic_cursor.execute(validation_query)
                results = traffic_cursor.fetchmany(10)  # Test with limited results
                data_points_found = len(results)
                
        except Exception as e:
            return jsonify({
                'error': f'Query validation failed: {str(e)}',
                'query': validation_query[:200] + ('...' if len(validation_query) > 200 else '')
            }), 400
        
        # Store the validation claim
        claim_data = {
            'research_metadata_id': research_id,
            'claim_text': claim_text,
            'claim_type': claim_type,
            'vessel_filter': data.get('vessel_filter', ''),
            'route_filter': data.get('route_filter', ''),
            'period_filter': data.get('period_filter', ''),
            'validation_query': validation_query,
            'validation_logic': validation_logic,
            'confidence_score': None,  # To be set later by analysis
            'supports_claim': None,    # To be set later by analysis
            'data_points_found': data_points_found,
            'analysis_text': 'Manual validation query created by user'
        }
        
        claim_id = etso_access.store_validation_claim(claim_data)
        
        return jsonify({
            'success': True,
            'claim_id': claim_id,
            'data_points_found': data_points_found,
            'message': 'Validation claim created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating validation claim: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-custom-query', methods=['POST'])
def execute_custom_query():
    """Execute a custom SQL query on the traffic database"""
    try:
        data = request.get_json()
        custom_query = data.get('query', '').strip()
        claim_id = data.get('claim_id')
        
        if not custom_query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Basic security checks - only allow SELECT statements
        query_upper = custom_query.upper().strip()
        if not query_upper.startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return jsonify({'error': 'Query contains forbidden operations'}), 400
        
        # Execute the custom query on traffic database
        query_results = []
        try:
            with db_manager.get_traffic_connection() as traffic_conn:
                traffic_cursor = traffic_conn.cursor()
                
                # Set a reasonable timeout
                traffic_cursor.execute('SET SESSION wait_timeout = 30')
                traffic_cursor.execute(custom_query)
                
                # Get column names
                columns = [desc[0] for desc in traffic_cursor.description] if traffic_cursor.description else []
                
                # Fetch results (limit to prevent overwhelming response)
                rows = traffic_cursor.fetchmany(500)  # Increased limit for custom queries
                
                for row in rows:
                    # Convert any datetime objects to strings
                    converted_row = []
                    for value in row:
                        if hasattr(value, 'isoformat'):  # datetime object
                            converted_row.append(value.isoformat())
                        else:
                            converted_row.append(value)
                    query_results.append(dict(zip(columns, converted_row)))
        
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return jsonify({
                'error': f'Query execution failed: {str(e)}',
                'query': custom_query[:200] + ('...' if len(custom_query) > 200 else '')
            }), 400
        
        return jsonify({
            'query': custom_query,
            'claim_id': claim_id,
            'query_results': query_results,
            'result_count': len(query_results)
        })
    
    except Exception as e:
        logger.error(f"Error in execute_custom_query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regenerate-enhanced-query/<int:theme_id>', methods=['POST'])
def regenerate_enhanced_query(theme_id):
    """Regenerate enhanced query with deep research approach (Gemini-style)"""
    try:
        data = request.get_json()
        user_guidance = data.get('user_guidance', '')
        
        if not user_guidance:
            return jsonify({'error': 'User guidance is required'}), 400
        
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        # Use GPT-4 for deep research enhancement
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        enhancement_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a maritime research strategist creating comprehensive research plans.
            Generate a deep, multi-layered research query similar to Google Gemini's deep research approach.
            
            Your enhanced query should include:
            1. PRIMARY RESEARCH QUESTIONS (3-5 core questions)
            2. SUPPORTING INVESTIGATIONS (5-8 detailed sub-queries)
            3. DATA ANALYSIS REQUIREMENTS
               - Vessel movement patterns
               - Port call statistics
               - Route optimization metrics
               - Fuel consumption analysis
               - Time-based comparisons
            4. CROSS-VALIDATION POINTS
               - Historical baseline comparisons
               - Regional impact assessments
               - Carrier-specific analysis
            5. QUANTITATIVE METRICS TO EXTRACT
               - Specific KPIs and thresholds
               - Statistical significance tests
               - Trend identification parameters
            
            Format the output as a structured, comprehensive research plan that can guide multiple research agents.
            Be specific about data sources, time periods, and geographic regions.
            Include both broad strategic questions and detailed tactical investigations."""),
            ("human", """Original Research Theme: {user_guidance}
            
            Generate a comprehensive, deep research query that will thoroughly investigate this theme.
            Make it detailed, actionable, and data-driven.""")
        ])
        
        # Generate enhanced query
        response = llm.invoke(
            enhancement_prompt.format_messages(user_guidance=user_guidance)
        )
        
        enhanced_query = response.content
        
        # Update the database with new enhanced query
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE research_metadata SET
                    user_guidance = %s,
                    enhanced_query = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (user_guidance, enhanced_query, theme_id))
            conn.commit()
        
        return jsonify({
            'success': True,
            'theme_id': theme_id,
            'user_guidance': user_guidance,
            'enhanced_query': enhanced_query
        })
        
    except Exception as e:
        logger.error(f"Error regenerating enhanced query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-theme/<int:theme_id>', methods=['PUT'])
def update_theme(theme_id):
    """Update research theme metadata and prompts"""
    try:
        data = request.get_json()
        
        # Update research metadata
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE research_metadata SET
                    theme_type = COALESCE(%s, theme_type),
                    quarter = COALESCE(%s, quarter),
                    status = COALESCE(%s, status),
                    user_guidance = COALESCE(%s, user_guidance),
                    enhanced_query = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                data.get('theme_type'),
                data.get('quarter'),
                data.get('status'),
                data.get('user_guidance'),
                data.get('enhanced_query'),
                theme_id
            ))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Theme not found'}), 404
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Theme updated successfully'
            })
        
    except Exception as e:
        logger.error(f"Error updating theme {theme_id}: {e}")
        return jsonify({'error': str(e)}), 500

def run_single_claim_validation(claim_id):
    """Core validation logic for a single claim"""
    try:
        # Get claim details
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    vc.claim_text, vc.validation_query, vc.validation_logic,
                    vc.claim_type, vc.research_metadata_id
                FROM validation_claims vc
                WHERE vc.id = %s
            """, (claim_id,))
            
            claim_data = cursor.fetchone()
            if not claim_data:
                return {'success': False, 'error': 'Claim not found'}
            
            claim_text, validation_query, validation_logic, claim_type, research_id = claim_data
        
        # Execute the validation query
        query_results = []
        column_names = []
        try:
            with db_manager.get_traffic_connection() as traffic_conn:
                traffic_cursor = traffic_conn.cursor()
                traffic_cursor.execute(validation_query)
                query_results = traffic_cursor.fetchall()
                column_names = [desc[0] for desc in traffic_cursor.description] if traffic_cursor.description else []
                logger.info(f"Query returned {len(query_results)} results")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            # Update claim with failed status
            with db_manager.get_etso_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE validation_claims SET
                        confidence_score = 0.0,
                        supports_claim = 0,
                        data_points_found = 0,
                        analysis_text = %s
                    WHERE id = %s
                """, (f"Query execution failed: {str(e)}", claim_id))
                conn.commit()
            return {'success': False, 'error': f'Query execution failed: {str(e)}'}
        
        # Analyze results using LLM
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a maritime data analyst validating research claims against vessel traffic data.
            
            Analyze the database results and determine:
            1. Does the data support the claim? (Yes/No/Partially)
            2. Confidence level (0.0 to 1.0)
            3. Key evidence from the data
            4. Any contradictions or data limitations
            
            Be objective and quantitative in your analysis.
            Consider the validation logic provided to understand what the query is measuring."""),
            ("human", """
            Original Claim: {claim}
            
            Validation Logic: {logic}
            
            Database Query Results ({num_results} records):
            {results}
            
            Analyze whether the data supports this claim and provide:
            - Support Level: Yes/No/Partially
            - Confidence: 0.0-1.0
            - Evidence: Key supporting data points
            - Summary: Brief analysis summary
            
            Format your response as:
            SUPPORT: [Yes/No/Partially]
            CONFIDENCE: [0.0-1.0]
            EVIDENCE: [Key supporting evidence]
            SUMMARY: [Brief analysis summary]
            """)
        ])
        
        # Format results for LLM (limit to first 20 rows for analysis)
        results_text = ""
        if query_results:
            # Use stored column names
            results_text = f"Columns: {', '.join(column_names)}\n"
            for i, row in enumerate(query_results[:20]):
                results_text += f"Row {i+1}: {row}\n"
            if len(query_results) > 20:
                results_text += f"... and {len(query_results) - 20} more records\n"
        else:
            results_text = "No matching data found"
        
        # Get LLM analysis
        response = llm.invoke(
            analysis_prompt.format_messages(
                claim=claim_text,
                logic=validation_logic or "Validate if the claim is supported by the data",
                num_results=len(query_results),
                results=results_text
            )
        )
        
        # Parse LLM response
        analysis_text = response.content
        
        # Extract structured data from response
        import re
        
        support_match = re.search(r'SUPPORT:\s*(\w+)', analysis_text, re.IGNORECASE)
        confidence_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', analysis_text, re.IGNORECASE)
        evidence_match = re.search(r'EVIDENCE:\s*(.+?)(?:\n|SUMMARY:|$)', analysis_text, re.DOTALL | re.IGNORECASE)
        summary_match = re.search(r'SUMMARY:\s*(.+?)(?:\n|$)', analysis_text, re.DOTALL | re.IGNORECASE)
        
        # Determine support status
        support_text = support_match.group(1).lower() if support_match else 'no'
        supports_claim = 1 if support_text in ['yes', 'partially'] else 0
        
        # Get confidence score
        try:
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            confidence = max(0.0, min(1.0, confidence))  # Ensure between 0 and 1
        except:
            confidence = 0.5
        
        # Get evidence and summary
        evidence = evidence_match.group(1).strip() if evidence_match else "No specific evidence extracted"
        summary = summary_match.group(1).strip() if summary_match else analysis_text[:500]
        
        # Update the claim with analysis results
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE validation_claims SET
                    confidence_score = %s,
                    supports_claim = %s,
                    data_points_found = %s,
                    analysis_text = %s,
                    validation_timestamp = NOW()
                WHERE id = %s
            """, (
                confidence,
                supports_claim,
                len(query_results),
                f"Support: {support_text.upper()}\nConfidence: {confidence:.2f}\nEvidence: {evidence}\n\nSummary: {summary}",
                claim_id
            ))
            conn.commit()
        
        # Update overall confidence for the research theme
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE research_metadata rm
                SET overall_confidence = (
                    SELECT AVG(confidence_score)
                    FROM validation_claims
                    WHERE research_metadata_id = rm.id
                    AND confidence_score IS NOT NULL
                )
                WHERE rm.id = %s
            """, (research_id,))
            conn.commit()
        
        return {
            'success': True,
            'claim_id': claim_id,
            'supports_claim': supports_claim,
            'confidence': confidence,
            'data_points': len(query_results),
            'evidence': evidence,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error running validation analysis: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/api/run-validation-analysis/<int:claim_id>', methods=['POST'])
def run_validation_analysis(claim_id):
    """Run actual validation analysis on a claim using LLM"""
    result = run_single_claim_validation(claim_id)
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({'error': result['error']}), 500

@app.route('/api/run-bulk-validation', methods=['POST'])
def run_bulk_validation():
    """Run validation analysis on all pending claims"""
    try:
        # Get all claims that need validation
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM validation_claims
                WHERE confidence_score IS NULL 
                   OR confidence_score = 0
                   OR supports_claim IS NULL
            """)
            pending_claims = cursor.fetchall()
        
        if not pending_claims:
            return jsonify({
                'success': True,
                'message': 'No claims need validation',
                'processed': 0
            })
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for (claim_id,) in pending_claims:
            try:
                # Call validation logic directly instead of HTTP request
                validation_result = run_single_claim_validation(claim_id)
                if validation_result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Claim {claim_id}: {validation_result.get('error', 'Unknown error')}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Claim {claim_id}: {str(e)}")
                logger.error(f"Failed to validate claim {claim_id}: {e}")
        
        return jsonify({
            'success': True,
            'message': f"Processed {len(pending_claims)} claims",
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in bulk validation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-claims/<int:theme_id>', methods=['POST'])
def generate_claims(theme_id):
    """Generate AI validation claims for a research theme"""
    try:
        # Get theme data
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_guidance, enhanced_query, chroma_id
                FROM research_metadata
                WHERE id = %s
            """, (theme_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Theme not found'}), 404
            
            user_guidance, enhanced_query, chroma_id = result
        
        # Get research content from ChromaDB
        research_content = ""
        if chroma_id:
            try:
                import chromadb
                from chromadb.config import Settings
                import os
                
                client = chromadb.PersistentClient(
                    path=os.getenv('CHROMA_PERSIST_DIR', './chroma_data'),
                    settings=Settings(anonymized_telemetry=False)
                )
                collection = client.get_collection(name=os.getenv('CHROMA_COLLECTION', 'observatorio_research'))
                
                result = collection.get(
                    ids=[chroma_id],
                    include=['documents']
                )
                if result['documents']:
                    research_content = result['documents'][0]
            except Exception as e:
                logger.warning(f"Could not retrieve ChromaDB content: {e}")
        
        # Use existing validation system to generate claims
        from validation import DualDatabaseValidator
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        validator = DualDatabaseValidator(db_manager, llm)
        
        # Create validation targets from prompts
        validation_targets = []
        if user_guidance:
            validation_targets.append(user_guidance)
        if enhanced_query:
            validation_targets.append(enhanced_query)
        
        # Extract claims using the existing ClaimExtractor
        claims = validator.claim_extractor.extract_claims(
            research_content or (user_guidance + "\n" + enhanced_query), 
            validation_targets
        )
        
        # Delete existing claims
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM validation_claims WHERE research_metadata_id = %s", (theme_id,))
            conn.commit()
        
        # Generate validation queries and store claims
        generated_claims = []
        for claim in claims:
            try:
                # Generate validation query
                query = validator.query_generator.generate_validation_query(claim, "2025Q1")
                
                # Test query execution
                try:
                    results = db_manager.execute_traffic_query(query)
                    data_points = len(results)
                except Exception as e:
                    logger.warning(f"Query test failed for claim: {e}")
                    data_points = 0
                
                # Store claim
                claim_data = {
                    'research_metadata_id': theme_id,
                    'claim_text': claim.claim_text,
                    'claim_type': claim.claim_type,
                    'vessel_filter': claim.vessel or '',
                    'route_filter': claim.route or '',
                    'period_filter': claim.period or '',
                    'validation_query': query,
                    'validation_logic': f'AI-generated query to validate: {claim.claim_text}',
                    'confidence_score': None,
                    'supports_claim': None,
                    'data_points_found': data_points,
                    'analysis_text': 'AI-generated validation claim'
                }
                
                claim_id = etso_access.store_validation_claim(claim_data)
                
                generated_claims.append({
                    'id': claim_id,
                    'claim_text': claim.claim_text,
                    'claim_type': claim.claim_type,
                    'validation_query': query,
                    'validation_logic': claim_data['validation_logic'],
                    'data_points_found': data_points,
                    'confidence_score': 0.0,
                    'supports_claim': None,
                    'analysis_text': 'AI-generated validation claim',
                    'validation_timestamp': None
                })
                
            except Exception as e:
                logger.error(f"Error generating claim: {e}")
                continue
        
        return jsonify({
            'success': True,
            'claims': generated_claims,
            'message': f'Generated {len(generated_claims)} validation claims'
        })
        
    except Exception as e:
        logger.error(f"Error generating claims for theme {theme_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting OBSERVATORIO ETS Dashboard on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)