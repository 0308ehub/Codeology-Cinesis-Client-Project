"""
Legacy parser module - DEPRECATED

This module is kept for backward compatibility but is no longer used.
All functionality has been moved to:
- parser/csv_parser.py - Enhanced CSV parser
- parser/unified_parser.py - Unified parser interface
- schema.py - Data models

For new code, use:
    from parser.unified_parser import UnifiedParser
    from schema import Broker, Load, Lane, Rate, CarrierProfile
"""

# This file is kept for reference only
# All new code should use the modules listed above

if __name__ == "__main__":
    """
    Example usage with the new system.
    """
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Use new unified system
    from parser.unified_parser import UnifiedParser
    from normalization import DataNormalizer
    from enrichment import EnrichmentEngine
    from database import Database
    
    print("="*80)
    print("CARRIER DATA PROCESSING SYSTEM")
    print("="*80)
    print()
    print("Note: This is a legacy entry point. Use 'python demo.py' or 'python main.py' instead.")
    print()
    
    # Initialize components
    parser = UnifiedParser()
    normalizer = DataNormalizer()
    database = Database()
    enrichment_engine = EnrichmentEngine(database)
    
    # Parse the CSV file
    print("Parsing brokers.csv...")
    profile = parser.parse_file('brokers.csv')
    
    print(f"\nParsed {len(profile.brokers)} brokers, {len(profile.loads)} loads, {len(profile.lanes)} lanes")
    
    # Normalize data
    print("\nNormalizing data...")
    profile = normalizer.normalize_profile(profile)
    norm_stats = normalizer.get_stats()
    print(f"Normalization stats: {norm_stats}")
    
    # Enrich data
    print("\nEnriching data...")
    enriched_lanes = enrichment_engine.enrich_lanes(profile.lanes)
    print(f"Enriched {len(enriched_lanes)} lanes")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Brokers: {len(profile.brokers)}")
    print(f"Loads: {len(profile.loads)}")
    print(f"Lanes: {len(profile.lanes)}")
    print(f"Preferred Lanes: {len(profile.preferred_lanes)}")
    print(f"Preferred Brokers: {len(profile.preferred_brokers)}")
    print(f"Preferred Equipment: {len(profile.preferred_equipment)}")
    
    # Save to database
    print("\nSaving to database...")
    carrier_id = "demo_carrier_001"
    database.save_carrier_profile(profile, carrier_id)
    print(f"Saved to database with carrier_id: {carrier_id}")
    
    print("\n" + "="*80)
    print("Processing complete!")
    print("="*80)
