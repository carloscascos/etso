#!/usr/bin/env python3
"""Complete the validation for theme 4"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager
from storage import ResearchStorageManager
from validation import DualDatabaseValidator

def complete_theme4_validation():
    """Complete validation for theme 4"""
    
    print("🔄 Completing Theme 4 Validation")
    print("=" * 60)
    
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
    
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get theme 4 ChromaDB content
            cursor.execute("SELECT chroma_id FROM research_metadata WHERE id = 7")
            chroma_id = cursor.fetchone()[0]
            
            # Retrieve research content
            collection = storage_manager.chroma_manager.collection
            results = collection.get(ids=[chroma_id], include=['documents'])
            
            if not results['documents']:
                print("❌ No research content found")
                return
            
            research_content = results['documents'][0]
            print(f"✅ Retrieved research content: {len(research_content)} chars")
            
            # Define specific validation targets
            validation_targets = [
                'vessel route diversions via Cape of Good Hope',
                'increased transit times for Asia-Europe routes',
                'fuel consumption increases',
                'specific container vessels affected',
                'port congestion impacts'
            ]
            
            print(f"\n🎯 Validation targets: {len(validation_targets)}")
            
            # Check current validation status
            cursor.execute("""
                SELECT COUNT(*) FROM validation_claims 
                WHERE research_metadata_id = 7
            """)
            existing_claims = cursor.fetchone()[0]
            print(f"📊 Existing validated claims: {existing_claims}")
            
            if existing_claims < 2:
                print("\n🚀 Running full validation...")
                
                # Run validation
                result = validator.validate_research_finding(
                    research_metadata_id=7,
                    research_content=research_content,
                    validation_targets=validation_targets
                )
                
                print(f"\n✅ Validation completed!")
                print(f"   Overall Confidence: {result['overall_confidence']:.3f}")
                print(f"   Claims Validated: {len(result['validation_results'])}")
                
                # Show summary of results
                for i, val_result in enumerate(result['validation_results'], 1):
                    if val_result.get('claim'):
                        claim = val_result['claim']
                        print(f"\n   {i}. {claim.claim_text[:80]}...")
                        print(f"      Confidence: {val_result.get('confidence', 0):.3f}")
                        print(f"      Supported: {'Yes' if val_result.get('supports_claim') else 'No'}")
            
            # Update status to completed
            cursor.execute("""
                UPDATE research_metadata 
                SET status = 'completed'
                WHERE id = 7
            """)
            conn.commit()
            
            # Final check
            cursor.execute("""
                SELECT 
                    overall_confidence,
                    (SELECT COUNT(*) FROM validation_claims WHERE research_metadata_id = 7),
                    (SELECT AVG(confidence_score) FROM validation_claims WHERE research_metadata_id = 7)
                FROM research_metadata 
                WHERE id = 7
            """)
            
            final = cursor.fetchone()
            print(f"\n📈 Final Theme 4 Status:")
            print(f"   Overall Confidence: {final[0]:.3f if final[0] else 0:.3f}")
            print(f"   Total Claims: {final[1]}")
            print(f"   Average Claim Confidence: {final[2]:.3f if final[2] else 0:.3f}")
            
            print("\n✨ Theme 4 validation completed!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    complete_theme4_validation()