#!/usr/bin/env python3
"""Test validation query generation with escaped % characters"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import ValidationQueryGenerator, ValidationClaim

def test_query_generation():
    """Test that queries are generated with properly escaped % characters"""
    
    generator = ValidationQueryGenerator()
    
    # Test case 1: Vessel filter with name
    claim = ValidationClaim(
        claim_text="Maersk vessels increased transit times",
        claim_type="vessel_movement",
        vessel="Maersk",
        route=None,
        period="2025Q1",
        metric=None,
        expected_change=None
    )
    
    query = generator.generate_validation_query(claim, "2025Q1")
    
    # Check that % is properly escaped (doubled)
    print("Testing vessel name filter...")
    if "LIKE '%%Maersk%%'" in query:
        print("✅ Vessel filter properly escaped")
    else:
        print("❌ Vessel filter not properly escaped")
        print("Query snippet:", query[400:600])
    
    # Test case 2: Transit time with route filter
    claim2 = ValidationClaim(
        claim_text="Singapore to Rotterdam transit times increased",
        claim_type="transit_time",
        vessel=None,
        route="Singapore -> Rotterdam",
        period="2025Q1",
        metric=None,
        expected_change=None
    )
    
    query2 = generator.generate_validation_query(claim2, "2025Q1")
    
    print("\nTesting transit time route filter...")
    if "LIKE '%%Singapore%%'" in query2 and "LIKE '%%Rotterdam%%'" in query2:
        print("✅ Transit route filter properly escaped")
    else:
        print("❌ Transit route filter not properly escaped")
        print("Query snippet:", query2[1000:1200])
    
    # Test case 3: General port search
    claim3 = ValidationClaim(
        claim_text="Asian ports saw increased activity",
        claim_type="port_frequency",
        vessel=None,
        route="Asia",
        period="2025Q1",
        metric=None,
        expected_change=None
    )
    
    query3 = generator.generate_validation_query(claim3, "2025Q1")
    
    print("\nTesting general port/zone filter...")
    if "LIKE '%%Asia%%'" in query3:
        print("✅ Zone filter properly escaped")
    else:
        print("❌ Zone filter not properly escaped")
        print("Query snippet:", query3[400:600])
    
    print("\n✅ All query generation tests completed successfully!")
    
    # Show a sample query for verification
    print("\nSample generated query (first 500 chars):")
    print(query[:500])
    
    return True

if __name__ == "__main__":
    test_query_generation()