"""
Main entry point for the carrier data processing system.
Supports both CLI and API modes.
"""
import sys
import argparse
from pathlib import Path

from parser.unified_parser import UnifiedParser
from normalization import DataNormalizer
from enrichment import EnrichmentEngine
from database import Database
from onboarding import OnboardingFlow


def cli_mode(file_paths: list[str], carrier_name: str = None, carrier_mc: str = None):
    """Run in CLI mode"""
    print("="*80)
    print("CARRIER DATA PROCESSING SYSTEM - CLI MODE")
    print("="*80)
    print()
    
    # Initialize components
    database = Database()
    onboarding_flow = OnboardingFlow(database)
    
    # Process files
    print("Processing files...")
    results = onboarding_flow.process_upload(file_paths, carrier_name, carrier_mc)
    
    # Print results
    print("\n" + "="*80)
    print("PROCESSING RESULTS")
    print("="*80)
    print(f"Carrier ID: {results['carrier_id']}")
    print(f"Files Processed: {len(results['files_processed'])}")
    print()
    
    print("Statistics:")
    stats = results['stats']
    print(f"  - Brokers: {stats.get('final_brokers', 0)}")
    print(f"  - Loads: {stats.get('final_loads', 0)}")
    print(f"  - Lanes: {stats.get('final_lanes', 0)}")
    print(f"  - Preferred Lanes: {stats.get('preferred_lanes', 0)}")
    print(f"  - Preferred Brokers: {stats.get('preferred_brokers', 0)}")
    
    if 'normalization' in stats:
        norm = stats['normalization']
        print(f"\nNormalization:")
        print(f"  - Brokers Deduplicated: {norm.get('brokers_deduplicated', 0)}")
        print(f"  - Loads Deduplicated: {norm.get('loads_deduplicated', 0)}")
        print(f"  - Lanes Merged: {norm.get('lanes_merged', 0)}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print(f"\nWarnings: {len(results['warnings'])}")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "="*80)
    print("Processing complete!")
    print("="*80)
    
    return results


def api_mode(host: str = '0.0.0.0', port: int = 5001):
    """Run in API mode"""
    from api import app
    print(f"Starting API server on {host}:{port}")
    app.run(debug=True, host=host, port=port)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Carrier Data Processing System')
    parser.add_argument('--mode', choices=['cli', 'api'], default='cli',
                       help='Run mode: cli or api')
    parser.add_argument('--files', nargs='+', help='Files to process (CLI mode)')
    parser.add_argument('--carrier-name', help='Carrier name')
    parser.add_argument('--carrier-mc', help='Carrier MC number')
    parser.add_argument('--host', default='0.0.0.0', help='API host (API mode)')
    parser.add_argument('--port', type=int, default=5000, help='API port (API mode)')
    
    args = parser.parse_args()
    
    if args.mode == 'api':
        api_mode(args.host, args.port)
    else:
        if not args.files:
            print("Error: --files required in CLI mode")
            sys.exit(1)
        
        cli_mode(args.files, args.carrier_name, args.carrier_mc)


if __name__ == '__main__':
    main()

