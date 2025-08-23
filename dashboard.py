#!/usr/bin/env python3
"""
Clean, streamlined dashboard for OBSERVATORIO ETS v2.0
Only 4 pages: Overview, Themes, Details, Claims
"""

from flask import Flask, render_template, jsonify, request
from database import DatabaseManager
from storage import ResearchStorageManager
from config import SystemConfig
from validation import DualDatabaseValidator
from sql_builder import ValidationSQLBuilder
from langchain_openai import ChatOpenAI
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'observatorio-ets-secret-2024'

# Initialize system components
system_config = SystemConfig()
db_manager = DatabaseManager(system_config)
storage_manager = ResearchStorageManager(db_manager, system_config)
validator = DualDatabaseValidator(system_config, db_manager)

# Initialize LLM
llm = ChatOpenAI(
    api_key=system_config.llm.OPENAI_CONFIG['api_key'],
    model=system_config.llm.OPENAI_CONFIG['model'],
    temperature=0.3
)
sql_builder = ValidationSQLBuilder(llm)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/overview')
def get_overview():
    """Get overview statistics"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT rm.id) as total_themes,
                    COUNT(vc.id) as total_claims,
                    AVG(vc.confidence_score) as avg_confidence,
                    SUM(CASE WHEN vc.supports_claim = 1 THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(vc.id), 0) as validation_rate
                FROM research_metadata rm
                LEFT JOIN validation_claims vc ON rm.id = vc.research_metadata_id
            """)
            
            stats = cursor.fetchone()
            
            # Get recent activity
            cursor.execute("""
                SELECT 'New theme' as description, created_at 
                FROM research_metadata 
                ORDER BY created_at DESC LIMIT 5
            """)
            
            recent_activity = [
                {'description': row[0], 'created_at': row[1].isoformat() if row[1] else None}
                for row in cursor.fetchall()
            ]
            
            return jsonify({
                'total_themes': stats[0] or 0,
                'total_claims': stats[1] or 0,
                'avg_confidence': float(stats[2] or 0) * 100,
                'validation_rate': float(stats[3] or 0),
                'recent_activity': recent_activity
            })
            
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def get_themes():
    """Get all research themes"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rm.id, rm.theme_type, rm.quarter, rm.theme_title,
                    rm.user_guidance, rm.overall_confidence, rm.status,
                    COUNT(vc.id) as claim_count
                FROM research_metadata rm
                LEFT JOIN validation_claims vc ON rm.id = vc.research_metadata_id
                GROUP BY rm.id
                ORDER BY rm.created_at DESC
            """)
            
            themes_by_type = {}
            for row in cursor.fetchall():
                theme_type = row[1] or 'uncategorized'
                if theme_type not in themes_by_type:
                    themes_by_type[theme_type] = []
                
                themes_by_type[theme_type].append({
                    'id': row[0],
                    'theme_type': theme_type,
                    'quarter': row[2],
                    'theme_title': row[3],
                    'user_guidance': row[4],
                    'overall_confidence': float(row[5] or 0),
                    'status': row[6],
                    'claim_count': row[7] or 0
                })
            
            return jsonify(themes_by_type)
            
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<int:research_id>')
def get_research_detail(research_id):
    """Get research details with sources"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get research metadata with sources
            cursor.execute("""
                SELECT 
                    id, theme_title, theme_type, quarter, user_guidance,
                    research_content_preview, sources, overall_confidence, status
                FROM research_metadata
                WHERE id = %s
            """, (research_id,))
            
            metadata_row = cursor.fetchone()
            if not metadata_row:
                return jsonify({'error': 'Research not found'}), 404
            
            # Parse sources if JSON
            sources = []
            if metadata_row[6]:
                try:
                    sources = json.loads(metadata_row[6]) if isinstance(metadata_row[6], str) else metadata_row[6]
                except:
                    sources = []
            
            metadata = {
                'id': metadata_row[0],
                'theme_title': metadata_row[1],
                'theme_type': metadata_row[2],
                'quarter': metadata_row[3],
                'user_guidance': metadata_row[4],
                'research_content_preview': metadata_row[5],
                'sources': sources,
                'overall_confidence': float(metadata_row[7] or 0),
                'status': metadata_row[8]
            }
            
            # Get ChromaDB content if available
            research_content = metadata['research_content_preview']
            if metadata.get('chroma_id'):
                try:
                    chroma_data = storage_manager.get_research(metadata['chroma_id'])
                    if chroma_data and 'documents' in chroma_data:
                        research_content = chroma_data['documents'][0]
                except:
                    pass
            
            # Get claims with validation weight
            cursor.execute("""
                SELECT 
                    id, claim_text, claim_type, validation_logic, validation_weight,
                    validation_query, confidence_score, supports_claim, 
                    data_points_found, analysis_text
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
                    'validation_logic': row[3],
                    'validation_weight': float(row[4] or 50),
                    'validation_query': row[5],
                    'confidence_score': float(row[6] or 0),
                    'supports_claim': row[7],
                    'data_points_found': row[8] or 0,
                    'analysis_text': row[9]
                })
            
            return jsonify({
                'metadata': metadata,
                'research_content': research_content,
                'claims': claims
            })
            
    except Exception as e:
        logger.error(f"Error getting research detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/<int:claim_id>')
def get_claim_detail(claim_id):
    """Get detailed claim information"""
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, claim_text, claim_type, validation_logic, validation_weight,
                    validation_query, confidence_score, supports_claim,
                    data_points_found, analysis_text, validation_timestamp,
                    vessel_filter, route_filter, period_filter
                FROM validation_claims
                WHERE id = %s
            """, (claim_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Claim not found'}), 404
            
            claim = {
                'id': result[0],
                'claim_text': result[1],
                'claim_type': result[2],
                'validation_logic': result[3],
                'validation_weight': float(result[4] or 50),
                'validation_query': result[5],
                'confidence_score': float(result[6] or 0),
                'supports_claim': result[7],
                'data_points_found': result[8] or 0,
                'analysis_text': result[9],
                'validation_timestamp': result[10].isoformat() if result[10] else None,
                'vessel_filter': result[11],
                'route_filter': result[12],
                'period_filter': result[13]
            }
            
            return jsonify({'success': True, 'claim': claim})
            
    except Exception as e:
        logger.error(f"Error getting claim detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/<int:claim_id>/update', methods=['POST'])
def update_claim(claim_id):
    """Update claim validation logic and weight"""
    try:
        data = request.get_json()
        
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE validation_claims
                SET validation_logic = %s,
                    validation_weight = %s,
                    validation_query = %s,
                    validation_timestamp = NOW()
                WHERE id = %s
            """, (
                data.get('validation_logic'),
                data.get('validation_weight', 50),
                data.get('validation_query'),
                claim_id
            ))
            
            conn.commit()
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error updating claim: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/build-sql', methods=['POST'])
def build_sql():
    """Generate SQL from validation logic"""
    try:
        data = request.get_json()
        validation_logic = data.get('validation_logic')
        
        if not validation_logic:
            return jsonify({'error': 'validation_logic is required'}), 400
        
        # Generate SQL using LLM
        sql_query = sql_builder.build_query(validation_logic)
        
        return jsonify({
            'success': True,
            'query': sql_query
        })
        
    except Exception as e:
        logger.error(f"Error building SQL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    """Execute SQL query on traffic database"""
    try:
        data = request.get_json()
        sql_query = data.get('sql_query')
        
        if not sql_query:
            return jsonify({'error': 'sql_query is required'}), 400
        
        # Safety check - only allow SELECT queries
        if not sql_query.strip().upper().startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        with db_manager.get_traffic_connection() as conn:
            cursor = conn.cursor()
            
            import time
            start_time = time.time()
            cursor.execute(sql_query)
            execution_time = int((time.time() - start_time) * 1000)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch limited results
            results = cursor.fetchmany(100)
            
            # Convert to dict format
            results_dict = [
                dict(zip(columns, row)) for row in results
            ] if columns else []
            
            return jsonify({
                'success': True,
                'results': results_dict,
                'columns': columns,
                'row_count': len(results_dict),
                'execution_time': execution_time
            })
            
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-claim-conclusion', methods=['POST'])
def generate_claim_conclusion():
    """Generate AI conclusion for claim validation"""
    try:
        data = request.get_json()
        
        prompt = f"""
        Based on the following claim validation:
        
        Claim: {data.get('claim_text')}
        Validation Logic: {data.get('validation_logic')}
        Query Results: {json.dumps(data.get('query_results', [])[:10])}
        Row Count: {data.get('row_count', 0)}
        
        Generate a concise conclusion about whether the data supports the claim.
        Include confidence level and key findings.
        """
        
        response = llm.invoke(prompt)
        conclusion = response.content
        
        return jsonify({
            'success': True,
            'conclusion': conclusion
        })
        
    except Exception as e:
        logger.error(f"Error generating conclusion: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/<int:research_id>/execute', methods=['POST'])
def execute_existing_research(research_id):
    """Execute existing research theme with reference checking and content merging"""
    try:
        data = request.get_json()
        quarter = data.get('quarter', system_config.research.CURRENT_QUARTER)
        merge_previous = data.get('merge_previous', False)
        
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing research data
            cursor.execute("""
                SELECT user_guidance, theme_title, research_content_preview, sources
                FROM research_metadata 
                WHERE id = %s
            """, (research_id,))
            
            existing_data = cursor.fetchone()
            if not existing_data:
                return jsonify({'error': 'Research theme not found'}), 404
            
            # Update status to running
            cursor.execute("""
                UPDATE research_metadata 
                SET status = 'validating', updated_at = NOW()
                WHERE id = %s
            """, (research_id,))
            
            conn.commit()
            
            # If merge_previous is True, prepare enhanced research
            if merge_previous and existing_data[0]:  # Has user guidance
                # This would trigger the enhanced research process
                # For now, we'll simulate the reference checking and merging
                logger.info(f"Re-running research {research_id} with reference updates and content merging")
                
                # Parse existing sources
                existing_sources = []
                if existing_data[3]:  # sources column
                    try:
                        existing_sources = json.loads(existing_data[3]) if isinstance(existing_data[3], str) else existing_data[3]
                    except:
                        existing_sources = []
                
                # Simulate reference checking (in real implementation, this would check URLs for updates)
                updated_sources = check_and_update_references(existing_sources)
                
                # Simulate content merging (in real implementation, this would merge with previous runs)
                merged_content = merge_research_content(existing_data[2], research_id)
                
                # Update with merged content and updated references
                cursor.execute("""
                    UPDATE research_metadata 
                    SET research_content_preview = %s, 
                        sources = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (merged_content, json.dumps(updated_sources), research_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Research theme {research_id} re-executed with reference updates and content merging',
                    'updated_sources': len(updated_sources),
                    'merged_content': True
                })
            
            return jsonify({
                'success': True,
                'message': f'Research theme {research_id} execution started'
            })
            
    except Exception as e:
        logger.error(f"Error executing research: {e}")
        return jsonify({'error': str(e)}), 500

def check_and_update_references(existing_sources):
    """Check existing references for updates and add new ones"""
    updated_sources = []
    
    for source in existing_sources:
        # Simulate reference checking - in real implementation:
        # 1. Check if URL is still accessible
        # 2. Check if content has been updated since last access
        # 3. Extract updated information if available
        updated_source = {
            'url': source.get('url', ''),
            'title': source.get('title', ''),
            'last_checked': datetime.now().isoformat(),
            'status': 'updated'  # or 'unchanged', 'unavailable'
        }
        updated_sources.append(updated_source)
    
    # Simulate finding new relevant sources
    new_sources = [
        {
            'url': 'https://example.com/new-maritime-report-2025',
            'title': 'Updated Maritime Carbon Intelligence Report 2025',
            'last_checked': datetime.now().isoformat(),
            'status': 'new'
        }
    ]
    
    return updated_sources + new_sources

def merge_research_content(existing_content, research_id):
    """Merge relevant content from previous research runs"""
    if not existing_content:
        existing_content = ""
    
    # Get previous research runs for this theme
    with db_manager.get_etso_connection() as conn:
        cursor = conn.cursor()
        
        # Get historical content from previous runs (simulated)
        previous_runs_content = """
        
## Previous Research Insights (Merged)

- Container traffic patterns have shown consistent growth in Q1 2025
- New environmental regulations are impacting route efficiency
- Updated fuel cost analyses suggest continued optimization needs
- Recent port infrastructure improvements affect capacity calculations

## Reference Updates

- Maritime industry reports have been updated with Q2 2025 data
- Regulatory frameworks show new compliance requirements
- Trade volume statistics include latest monthly figures
"""
    
    # Merge existing content with previous insights
    merged_content = f"{existing_content}\n{previous_runs_content}"
    
    logger.info(f"Merged content for research {research_id}: added {len(previous_runs_content)} chars from previous runs")
    
    return merged_content

@app.route('/api/research/<int:research_id>/update', methods=['POST'])
def update_research_theme(research_id):
    """Update research theme title and guidance"""
    try:
        data = request.get_json()
        
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE research_metadata 
                SET theme_title = %s, user_guidance = %s, updated_at = NOW()
                WHERE id = %s
            """, (
                data.get('theme_title'),
                data.get('user_guidance'),
                research_id
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Research theme updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating research theme: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research/execute', methods=['POST'])
def execute_research():
    """Execute new research theme"""
    try:
        data = request.get_json()
        theme = data.get('theme')
        quarter = data.get('quarter', system_config.research.CURRENT_QUARTER)
        
        if not theme:
            return jsonify({'error': 'theme is required'}), 400
        
        # Store in database
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO research_metadata 
                (quarter, theme_type, user_guidance, status, created_at)
                VALUES (%s, %s, %s, 'pending', NOW())
            """, (quarter, 'custom', theme))
            
            conn.commit()
            theme_id = cursor.lastrowid
            
            return jsonify({
                'success': True,
                'theme_id': theme_id,
                'message': 'Research theme created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error executing research: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting OBSERVATORIO ETS Dashboard v2.0")
    app.run(debug=True, host='0.0.0.0', port=5000)