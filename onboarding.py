"""
MVP Onboarding Flow
Handles the complete flow: upload → parsing → enrichment → match generation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pathlib import Path

from schema import CarrierProfile, DataSource
from parser.unified_parser import UnifiedParser
from normalization import DataNormalizer
from enrichment import EnrichmentEngine
from load_matching import LoadMatchingEngine, LoadMatch
from database import Database
from schema import Load


class OnboardingFlow:
    """Complete onboarding flow for carriers"""
    
    def __init__(self, database: Optional[Database] = None):
        self.parser = UnifiedParser()
        self.normalizer = DataNormalizer()
        self.enrichment_engine = EnrichmentEngine(database)
        self.database = database
    
    def process_upload(self, file_paths: List[str], carrier_name: Optional[str] = None,
                      carrier_mc: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete onboarding flow: parse → normalize → enrich → save
        
        Args:
            file_paths: List of file paths to process
            carrier_name: Optional carrier name
            carrier_mc: Optional carrier MC number
            
        Returns:
            Dictionary with processing results and carrier profile
        """
        results = {
            'carrier_id': str(uuid.uuid4()),
            'files_processed': [],
            'errors': [],
            'warnings': [],
            'stats': {},
            'profile': None
        }
        
        # Step 1: Parse files
        print("Step 1: Parsing files...")
        try:
            if len(file_paths) == 1:
                profile = self.parser.parse_file(file_paths[0])
            else:
                profile = self.parser.parse_multiple_files(file_paths)
            
            results['files_processed'] = file_paths
            results['stats']['parsed_brokers'] = len(profile.brokers)
            results['stats']['parsed_loads'] = len(profile.loads)
            results['stats']['parsed_lanes'] = len(profile.lanes)
            
        except Exception as e:
            results['errors'].append(f"Parsing error: {str(e)}")
            return results
        
        # Set carrier information
        profile.carrier_name = carrier_name
        profile.mc_number = carrier_mc
        profile.carrier_id = results['carrier_id']
        
        # Step 2: Normalize data
        print("Step 2: Normalizing data...")
        try:
            profile = self.normalizer.normalize_profile(profile)
            norm_stats = self.normalizer.get_stats()
            results['stats']['normalization'] = norm_stats
            
        except Exception as e:
            results['warnings'].append(f"Normalization warning: {str(e)}")
        
        # Step 3: Enrich data
        print("Step 3: Enriching data...")
        try:
            # Enrich lanes
            enriched_lanes = self.enrichment_engine.enrich_lanes(profile.lanes)
            results['stats']['enriched_lanes'] = len(enriched_lanes)
            
            # Fill missing rates
            profile.loads = self.enrichment_engine.fill_missing_rates(
                profile.loads,
                profile.lanes
            )
            
            # Enrich rates
            for load in profile.loads:
                if load.rate and load.lane:
                    load.rate = self.enrichment_engine.enrich_rate(load.rate, load.lane)
            
            results['stats']['enriched_rates'] = len([l for l in profile.loads if l.rate and l.rate.enrichment_source])
            
        except Exception as e:
            results['warnings'].append(f"Enrichment warning: {str(e)}")
        
        # Step 4: Save to database
        if self.database:
            print("Step 4: Saving to database...")
            try:
                self.database.save_carrier_profile(profile, results['carrier_id'])
                results['stats']['saved'] = True
            except Exception as e:
                results['warnings'].append(f"Database save warning: {str(e)}")
        
        results['profile'] = profile
        results['stats']['final_brokers'] = len(profile.brokers)
        results['stats']['final_loads'] = len(profile.loads)
        results['stats']['final_lanes'] = len(profile.lanes)
        results['stats']['preferred_lanes'] = len(profile.preferred_lanes)
        results['stats']['preferred_brokers'] = len(profile.preferred_brokers)
        
        return results
    
    def generate_matches(self, carrier_id: str, available_loads: List[Load],
                        limit: int = 10) -> Dict[str, Any]:
        """
        Generate load matches for a carrier.
        
        Args:
            carrier_id: Carrier ID
            available_loads: List of available loads to match
            limit: Maximum number of matches
            
        Returns:
            Dictionary with matches and summary
        """
        # Load carrier profile from database
        if not self.database:
            raise ValueError("Database required for match generation")
        
        # For now, we'll need to reconstruct profile from database
        # In production, this would be a proper query
        profile = self.database.get_carrier_profile(carrier_id)
        
        if not profile:
            raise ValueError(f"Carrier profile not found: {carrier_id}")
        
        # Create matching engine
        # Note: This is simplified - in production, reconstruct full profile
        carrier_profile = CarrierProfile(carrier_id=carrier_id)
        # ... reconstruct from database ...
        
        matching_engine = LoadMatchingEngine(carrier_profile)
        matches = matching_engine.match_loads(available_loads, limit)
        summary = matching_engine.get_match_summary(matches)
        
        return {
            'carrier_id': carrier_id,
            'matches': [m.to_dict() for m in matches],
            'summary': summary
        }
    
    def get_onboarding_status(self, carrier_id: str) -> Dict[str, Any]:
        """Get onboarding status for a carrier"""
        if not self.database:
            return {'status': 'unknown', 'message': 'Database not available'}
        
        profile = self.database.get_carrier_profile(carrier_id)
        
        if not profile:
            return {'status': 'not_found', 'message': 'Carrier not found'}
        
        # Determine completeness
        has_brokers = len(profile.brokers) > 0 if hasattr(profile, 'brokers') else False
        has_loads = len(profile.loads) > 0 if hasattr(profile, 'loads') else False
        has_lanes = len(profile.lanes) > 0 if hasattr(profile, 'lanes') else False
        
        if has_loads and has_lanes:
            status = 'complete'
            message = 'Onboarding complete - ready for matching'
        elif has_brokers or has_loads:
            status = 'partial'
            message = 'Partial data - enrichment recommended'
        else:
            status = 'incomplete'
            message = 'Insufficient data - upload more files'
        
        return {
            'status': status,
            'message': message,
            'has_brokers': has_brokers,
            'has_loads': has_loads,
            'has_lanes': has_lanes,
            'carrier_id': carrier_id
        }

