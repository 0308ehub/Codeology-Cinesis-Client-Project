"""
Demo script showing the complete workflow.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parser.unified_parser import UnifiedParser
from normalization import DataNormalizer
from enrichment import EnrichmentEngine
from database import Database
from load_matching import LoadMatchingEngine
from schema import Load, Lane, Broker, Rate, DataSource, Address
from datetime import datetime


def main():
    print("="*80)
    print("CARRIER DATA PROCESSING SYSTEM - DEMO")
    print("="*80)
    print()
    
    # Step 1: Parse CSV file
    print("Step 1: Parsing brokers.csv...")
    parser = UnifiedParser()
    csv_file = Path(__file__).parent / 'parser' / 'brokers.csv'
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        return
    
    profile = parser.parse_file(str(csv_file))
    print(f"  ✓ Parsed {len(profile.brokers)} brokers")
    print(f"  ✓ Parsed {len(profile.loads)} loads")
    print(f"  ✓ Parsed {len(profile.lanes)} lanes")
    print()
    
    # Step 2: Normalize data
    print("Step 2: Normalizing data...")
    normalizer = DataNormalizer()
    profile = normalizer.normalize_profile(profile)
    stats = normalizer.get_stats()
    print(f"  ✓ Deduplicated {stats['brokers_deduplicated']} brokers")
    print(f"  ✓ Deduplicated {stats['loads_deduplicated']} loads")
    print(f"  ✓ Merged {stats['lanes_merged']} lanes")
    print(f"  ✓ Calculated {stats['rates_calculated']} rates")
    print()
    
    # Step 3: Enrich data
    print("Step 3: Enriching with market data...")
    database = Database()
    enrichment_engine = EnrichmentEngine(database)
    enriched_lanes = enrichment_engine.enrich_lanes(profile.lanes)
    print(f"  ✓ Enriched {len(enriched_lanes)} lanes")
    
    # Fill missing rates
    profile.loads = enrichment_engine.fill_missing_rates(profile.loads, profile.lanes)
    print(f"  ✓ Filled missing rates")
    print()
    
    # Step 4: Extract preferences
    print("Step 4: Extracted preferences...")
    print(f"  ✓ Preferred lanes: {len(profile.preferred_lanes)}")
    if profile.preferred_lanes:
        print(f"    Top lane: {profile.preferred_lanes[0]}")
    print(f"  ✓ Preferred brokers: {len(profile.preferred_brokers)}")
    if profile.preferred_brokers:
        print(f"    Top broker MC: {profile.preferred_brokers[0]}")
    print(f"  ✓ Preferred equipment: {len(profile.preferred_equipment)}")
    if profile.preferred_equipment:
        print(f"    Top equipment: {profile.preferred_equipment[0]}")
    print()
    
    # Step 5: Save to database
    print("Step 5: Saving to database...")
    carrier_id = "demo_carrier_001"
    database.save_carrier_profile(profile, carrier_id)
    print(f"  ✓ Saved with carrier_id: {carrier_id}")
    print()
    
    # Step 6: Load matching demo
    print("Step 6: Load matching demo...")
    
    # Create some sample available loads
    sample_loads = [
        Load(
            load_id="LOAD001",
            broker=Broker(
                mc_id=profile.preferred_brokers[0] if profile.preferred_brokers else "123456",
                company_name="Sample Broker"
            ),
            lane=Lane(
                origin_city_state=profile.preferred_lanes[0].split('→')[0] if profile.preferred_lanes else "Miami, FL",
                destination_city_state=profile.preferred_lanes[0].split('→')[1] if profile.preferred_lanes else "Tampa, FL"
            ),
            rate=Rate(rate_amount=1500.0, rate_per_mile=2.5),
            source=DataSource.MANUAL
        ),
        Load(
            load_id="LOAD002",
            broker=Broker(mc_id="999999", company_name="Other Broker"),
            lane=Lane(
                origin_city_state="New York, NY",
                destination_city_state="Boston, MA"
            ),
            rate=Rate(rate_amount=800.0, rate_per_mile=2.0),
            source=DataSource.MANUAL
        )
    ]
    
    matching_engine = LoadMatchingEngine(profile)
    matches = matching_engine.match_loads(sample_loads, limit=5)
    
    print(f"  ✓ Generated {len(matches)} matches")
    if matches:
        print(f"    Top match: {matches[0].load.load_id} (score: {matches[0].score:.2f})")
        print(f"      Reasons: {', '.join(matches[0].match_reasons[:3])}")
    
    summary = matching_engine.get_match_summary(matches)
    print(f"  ✓ Average match score: {summary['average_score']:.2f}")
    print()
    
    print("="*80)
    print("DEMO COMPLETE!")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Run 'python main.py --mode api' to start the API server")
    print("  2. Use the API to onboard carriers and get matches")
    print("  3. Check the database for saved data")
    print()


if __name__ == '__main__':
    main()

