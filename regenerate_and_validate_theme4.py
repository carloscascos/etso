#!/usr/bin/env python3
"""Re-run research generation for theme 4 and then validate it"""

import os
import sys
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager
from storage import ResearchStorageManager, ResearchFinding
from validation import DualDatabaseValidator

def generate_research_content(theme_guidance: str, llm: ChatOpenAI) -> str:
    """Generate research content for the given theme"""
    
    system_prompt = """You are a maritime industry research analyst specializing in container shipping 
    and carbon emissions regulations. Generate a comprehensive research report based on the given theme.
    
    Focus on:
    1. Current state and trends
    2. Specific vessels, routes, or ports affected
    3. Quantifiable impacts and metrics
    4. Time periods and seasonal variations
    5. Regulatory compliance implications
    
    Provide specific, verifiable claims with details about:
    - Vessel names or types
    - Specific routes (origin -> destination)
    - Time periods (quarters, months)
    - Percentage changes or absolute numbers
    - Port activities and frequencies"""
    
    user_prompt = f"""Generate a detailed research report on the following theme:
    
    {theme_guidance}
    
    Provide at least 5-8 specific, verifiable claims with concrete details about vessels, 
    routes, ports, time periods, and measurable impacts. Focus on container shipping operations
    and their response to this situation."""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        return response.content
        
    except Exception as e:
        print(f"Error generating research: {e}")
        return None

def regenerate_and_validate_theme_4():
    """Re-run research generation and validation for theme 4"""
    
    print("🚀 OBSERVATORIO ETS - Regenerate & Validate Theme 4")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = config.llm.OPENAI_CONFIG['api_key']
    if not api_key or api_key.startswith('ysk-proj'):
        print("❌ Invalid or missing OpenAI API key")
        print("Please set a valid OPENAI_API_KEY in your .env file")
        return
    
    print(f"✅ Using OpenAI API key: {api_key[:10]}...")
    
    # Initialize components
    db_manager = DatabaseManager(config)
    llm = ChatOpenAI(
        model_name=config.llm.OPENAI_CONFIG['model'],
        openai_api_key=api_key,
        temperature=0.7
    )
    storage_manager = ResearchStorageManager(db_manager, config)
    validator = DualDatabaseValidator(db_manager, llm)
    
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get theme 4 details (ID 7)
            cursor.execute("""
                SELECT id, chroma_id, quarter, theme_type, user_guidance, enhanced_query
                FROM research_metadata
                WHERE id = 7
            """)
            
            theme = cursor.fetchone()
            if not theme:
                print("❌ Theme 4 (ID 7) not found")
                return
            
            research_id = theme[0]
            old_chroma_id = theme[1]
            quarter = theme[2]
            theme_type = theme[3]
            user_guidance = theme[4] or "Red Sea crisis impact on Asia-Europe container routes"
            
            print(f"\n📋 Theme 4 Details:")
            print(f"   ID: {research_id}")
            print(f"   Type: {theme_type}")
            print(f"   Quarter: {quarter}")
            print(f"   Guidance: {user_guidance}")
            print(f"   Old ChromaDB ID: {old_chroma_id}")
            
            # Step 1: Generate new research content
            print(f"\n🔬 Generating new research content...")
            research_content = generate_research_content(user_guidance, llm)
            
            if not research_content:
                print("❌ Failed to generate research content")
                return
            
            print(f"✅ Generated {len(research_content)} characters of research")
            print(f"\n📄 Research Preview (first 500 chars):")
            print("-" * 50)
            print(research_content[:500])
            print("-" * 50)
            
            # Step 2: Update ChromaDB with new content
            print(f"\n💾 Updating ChromaDB with new research content...")
            
            # Prepare validation targets based on theme
            validation_targets = []
            expected_outputs = []
            
            if 'route' in theme_type or 'Red Sea' in user_guidance:
                validation_targets = [
                    'vessel movements through Red Sea',
                    'alternative routes via Cape of Good Hope',
                    'Asia-Europe container services',
                    'transit time changes',
                    'fuel consumption impacts'
                ]
                expected_outputs = [
                    'specific vessel diversions',
                    'increased transit times',
                    'additional fuel costs',
                    'port congestion patterns'
                ]
            else:
                validation_targets = ['vessel movements', 'route patterns', 'operational metrics']
                expected_outputs = ['quantifiable impacts', 'specific examples']
            
            # Create new research finding
            finding = ResearchFinding(
                quarter=quarter,
                theme_type=theme_type,
                user_guidance=user_guidance,
                enhanced_query=user_guidance,
                research_content=research_content,
                validation_targets=validation_targets,
                expected_outputs=expected_outputs,
                research_scope={
                    'geographic': 'Asia-Europe',
                    'vessel_type': 'container',
                    'time_period': quarter
                },
                confidence=0.0,
                status='pending'
            )
            
            # Store the new research content
            new_chroma_id = storage_manager.chroma_manager.store_research_finding(finding)
            
            # Update the database with new chroma_id
            cursor.execute("""
                UPDATE research_metadata 
                SET chroma_id = %s, status = 'validating', updated_at = NOW()
                WHERE id = %s
            """, (new_chroma_id, research_id))
            conn.commit()
            
            print(f"✅ Updated with new ChromaDB ID: {new_chroma_id}")
            
            # Step 3: Run validation
            print(f"\n🔍 Starting validation process...")
            
            validation_result = validator.validate_research_finding(
                research_metadata_id=research_id,
                research_content=research_content,
                validation_targets=validation_targets
            )
            
            # Display results
            print(f"\n✅ Validation Complete!")
            print(f"   Overall Confidence: {validation_result['overall_confidence']:.3f}")
            print(f"   Total Claims Validated: {len(validation_result['validation_results'])}")
            
            # Show individual claim results
            if validation_result['validation_results']:
                print(f"\n📊 Individual Claim Results:")
                for i, result in enumerate(validation_result['validation_results'], 1):
                    claim = result.get('claim')
                    if claim:
                        print(f"\n   Claim {i}: {claim.claim_text[:100]}...")
                        print(f"      Type: {claim.claim_type}")
                        print(f"      Confidence: {result.get('confidence', 0):.3f}")
                        print(f"      Supported: {'✅ Yes' if result.get('supports_claim') else '❌ No'}")
                        
                        analysis = result.get('analysis', {})
                        print(f"      Data Points: {analysis.get('data_points', 0)}")
                        
                        if analysis.get('evidence'):
                            print(f"      Evidence: {analysis['evidence'][:200]}...")
                        
                        if result.get('status') == 'failed':
                            print(f"      ⚠️ Error: {result.get('error', 'Unknown error')}")
            
            # Final summary
            cursor.execute("""
                SELECT overall_confidence, status,
                       (SELECT COUNT(*) FROM validation_claims WHERE research_metadata_id = %s)
                FROM research_metadata 
                WHERE id = %s
            """, (research_id, research_id))
            
            final = cursor.fetchone()
            
            print(f"\n📈 Final Theme 4 Status:")
            print(f"   Confidence Score: {final[0]:.3f if final[0] else 0:.3f}")
            print(f"   Status: {final[1]}")
            print(f"   Validation Claims Stored: {final[2]}")
            
            # Show sample validation queries
            cursor.execute("""
                SELECT claim_type, claim_text, confidence_score, supports_claim, data_points_found
                FROM validation_claims
                WHERE research_metadata_id = %s
                ORDER BY confidence_score DESC
                LIMIT 3
            """, (research_id,))
            
            top_claims = cursor.fetchall()
            if top_claims:
                print(f"\n🏆 Top Validated Claims:")
                for claim in top_claims:
                    print(f"   • [{claim[0]}] {claim[1][:60]}...")
                    print(f"     Confidence: {claim[2]:.3f}, Supported: {claim[3]}, Data Points: {claim[4]}")
            
            print(f"\n✨ Theme 4 regeneration and validation completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_and_validate_theme_4()