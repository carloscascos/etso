#!/usr/bin/env python3
"""Check validation results for theme 4"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager

def check_validation_results():
    """Check the validation results for theme 4"""
    
    load_dotenv()
    db_manager = DatabaseManager(config)
    
    print("📊 OBSERVATORIO ETS - Theme 4 Validation Results")
    print("=" * 60)
    
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get theme 4 current status
            cursor.execute("""
                SELECT id, chroma_id, overall_confidence, status, updated_at
                FROM research_metadata 
                WHERE id = 7
            """)
            
            theme = cursor.fetchone()
            if not theme:
                print("❌ Theme 4 (ID 7) not found")
                return
            
            print(f"\n📋 Theme 4 Status:")
            print(f"   ID: {theme[0]}")
            print(f"   ChromaDB ID: {theme[1]}")
            if theme[2] is not None:
                print(f"   Overall Confidence: {theme[2]:.3f}")
            else:
                print(f"   Overall Confidence: Not calculated")
            print(f"   Status: {theme[3]}")
            print(f"   Last Updated: {theme[4]}")
            
            # Get validation claims
            cursor.execute("""
                SELECT 
                    claim_type,
                    claim_text,
                    confidence_score,
                    supports_claim,
                    data_points_found,
                    vessel_filter,
                    route_filter,
                    period_filter
                FROM validation_claims
                WHERE research_metadata_id = 7
                ORDER BY confidence_score DESC
            """)
            
            claims = cursor.fetchall()
            
            if not claims:
                print("\n⚠️ No validation claims found yet")
                print("Validation may still be in progress...")
                return
            
            print(f"\n✅ Found {len(claims)} Validated Claims:")
            print("-" * 60)
            
            supported_count = sum(1 for c in claims if c[3])
            high_confidence_count = sum(1 for c in claims if c[2] >= 0.7)
            
            print(f"📈 Summary:")
            print(f"   Total Claims: {len(claims)}")
            print(f"   Supported Claims: {supported_count} ({supported_count/len(claims)*100:.1f}%)")
            print(f"   High Confidence (≥0.7): {high_confidence_count} ({high_confidence_count/len(claims)*100:.1f}%)")
            print(f"   Average Confidence: {sum(c[2] for c in claims)/len(claims):.3f}")
            
            print(f"\n📝 Individual Claims:")
            for i, claim in enumerate(claims, 1):
                print(f"\n{i}. [{claim[0].upper()}] {claim[1][:100]}...")
                print(f"   Confidence: {claim[2]:.3f}")
                print(f"   Supported: {'✅ Yes' if claim[3] else '❌ No'}")
                print(f"   Data Points Found: {claim[4]}")
                
                # Show filters used
                filters = []
                if claim[5]:  # vessel_filter
                    filters.append(f"Vessel: {claim[5]}")
                if claim[6]:  # route_filter
                    filters.append(f"Route: {claim[6]}")
                if claim[7]:  # period_filter
                    filters.append(f"Period: {claim[7]}")
                
                if filters:
                    print(f"   Filters: {', '.join(filters)}")
            
            # Get sample validation query
            cursor.execute("""
                SELECT validation_query
                FROM validation_claims
                WHERE research_metadata_id = 7
                AND data_points_found > 0
                LIMIT 1
            """)
            
            sample_query = cursor.fetchone()
            if sample_query:
                print(f"\n🔍 Sample Validation Query (first 500 chars):")
                print("-" * 60)
                print(sample_query[0][:500])
                print("-" * 60)
            
            print(f"\n✨ Validation results retrieved successfully!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_validation_results()