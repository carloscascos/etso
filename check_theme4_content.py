#!/usr/bin/env python3
"""Check the content of research theme 4"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import DatabaseManager
from storage import ResearchStorageManager

def check_theme_4_content():
    """Check what's stored for theme 4"""
    
    load_dotenv()
    db_manager = DatabaseManager(config)
    storage_manager = ResearchStorageManager(db_manager, config)
    
    try:
        with db_manager.get_etso_connection() as conn:
            cursor = conn.cursor()
            
            # Get theme 4 (which is ID 7 based on the output)
            cursor.execute("""
                SELECT id, chroma_id, quarter, theme_type, user_guidance, 
                       enhanced_query, overall_confidence, status
                FROM research_metadata
                WHERE id = 7
            """)
            
            result = cursor.fetchone()
            if not result:
                print("Theme 4 (ID 7) not found")
                return
            
            print("Theme 4 Details:")
            print(f"  ID: {result[0]}")
            print(f"  ChromaDB ID: {result[1]}")
            print(f"  Quarter: {result[2]}")
            print(f"  Type: {result[3]}")
            print(f"  User Guidance: {result[4]}")
            print(f"  Enhanced Query: {result[5]}")
            print(f"  Confidence: {result[6]}")
            print(f"  Status: {result[7]}")
            
            # Get content from ChromaDB
            if result[1]:
                collection = storage_manager.chroma_manager.collection
                chroma_results = collection.get(ids=[result[1]], include=['documents', 'metadatas'])
                
                if chroma_results['documents']:
                    print(f"\nChromaDB Content:")
                    print(f"  Document length: {len(chroma_results['documents'][0])} chars")
                    print(f"  Content preview:")
                    print("-" * 50)
                    print(chroma_results['documents'][0][:1000])
                    print("-" * 50)
                    
                    if chroma_results['metadatas']:
                        print(f"\nMetadata:")
                        for key, value in chroma_results['metadatas'][0].items():
                            print(f"  {key}: {value}")
                else:
                    print("\nNo content found in ChromaDB")
            else:
                print("\nNo ChromaDB ID associated with this theme")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_theme_4_content()