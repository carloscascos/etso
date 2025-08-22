#!/usr/bin/env python3
"""Run validation for research theme 4"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager
from validation import DualDatabaseValidator
from storage import ResearchStorageManager

def run_validation_for_theme_4():
    """Run validation for research theme 4"""
    
    print("🚀 OBSERVATORIO ETS - Research Theme 4 Validation")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    db_manager = DatabaseManager(config)
    llm = ChatOpenAI(
        model_name=config.llm.OPENAI_CONFIG['model'],
        openai_api_key=config.llm.OPENAI_CONFIG['api_key'],
        temperature=0.7
    )
    storage_manager = ResearchStorageManager(db_manager, config)
    validator = DualDatabaseValidator(db_manager, llm)
    
    # First, let's check what research themes we have
    print("\n📋 Checking available research themes...")
    
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get all research metadata
            cursor.execute("""
                SELECT id, quarter, theme_type, user_guidance, 
                       overall_confidence, status, created_at
                FROM research_metadata
                ORDER BY id
            """)
            
            themes = cursor.fetchall()
            
            if not themes:
                print("❌ No research themes found in database")
                return
            
            print(f"\n📊 Found {len(themes)} research themes:")
            for theme in themes:
                print(f"   Theme {theme[0]}: {theme[2]} - Quarter: {theme[1]} - Status: {theme[5]} - Confidence: {theme[4] or 'Not validated'}")
            
            # Check if theme 4 exists
            if len(themes) < 4:
                print(f"\n❌ Theme 4 does not exist. Only {len(themes)} themes found.")
                return
            
            theme_4 = themes[3]  # Index 3 for theme 4
            research_id = theme_4[0]
            theme_type = theme_4[2]
            user_guidance = theme_4[3]
            
            print(f"\n🎯 Selected Theme 4:")
            print(f"   ID: {research_id}")
            print(f"   Type: {theme_type}")
            print(f"   Guidance: {user_guidance[:100]}..." if user_guidance else "   Guidance: None")
            
            # Get the research content from ChromaDB
            print(f"\n🔍 Retrieving research content for theme {research_id}...")
            
            # Get chroma_id from metadata
            cursor.execute("SELECT chroma_id FROM research_metadata WHERE id = %s", (research_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                print("❌ No ChromaDB ID found for this theme")
                return
            
            chroma_id = result[0]
            
            # Retrieve from ChromaDB
            collection = storage_manager.chroma_manager.collection
            results = collection.get(ids=[chroma_id])
            
            if not results['documents']:
                print("❌ No research content found in ChromaDB")
                return
            
            research_content = results['documents'][0]
            print(f"✅ Retrieved research content ({len(research_content)} characters)")
            
            # Define validation targets based on theme type
            validation_targets = []
            if theme_type == 'vessel_movement':
                validation_targets = ['vessel movements', 'route patterns', 'transit times']
            elif theme_type == 'fuel_consumption':
                validation_targets = ['CO2 emissions', 'fuel consumption', 'emission patterns']
            elif theme_type == 'port_frequency':
                validation_targets = ['port calls', 'port activity', 'terminal usage']
            elif theme_type == 'route_optimization':
                validation_targets = ['route efficiency', 'transit times', 'fuel consumption']
            else:
                validation_targets = ['general patterns', 'vessel activity', 'operational metrics']
            
            print(f"\n🎯 Validation targets: {', '.join(validation_targets)}")
            
            # Run validation
            print(f"\n🚀 Starting validation process...")
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
                        print(f"      Data Points: {result.get('analysis', {}).get('data_points', 0)}")
                        if result.get('status') == 'failed':
                            print(f"      Error: {result.get('error', 'Unknown error')}")
            
            # Check if validation was stored
            cursor.execute("""
                SELECT COUNT(*) FROM validation_claims 
                WHERE research_metadata_id = %s
            """, (research_id,))
            claim_count = cursor.fetchone()[0]
            
            print(f"\n💾 Stored {claim_count} validation claims in database")
            
            # Update summary
            cursor.execute("""
                SELECT overall_confidence, status 
                FROM research_metadata 
                WHERE id = %s
            """, (research_id,))
            updated = cursor.fetchone()
            
            print(f"\n📈 Research Theme 4 Status:")
            print(f"   Confidence Score: {updated[0]:.3f}")
            print(f"   Status: {updated[1]}")
            
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    run_validation_for_theme_4()