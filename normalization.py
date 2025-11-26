"""
Data normalization and cleaning module.
Handles deduplication, standardization, and data quality improvements.
"""
from typing import List, Dict, Set, Optional
from datetime import datetime
import re
from collections import defaultdict

from schema import (
    Broker, Load, Lane, Rate, Address, CarrierProfile,
    DataSource
)


class DataNormalizer:
    """Normalizes and cleans carrier data"""
    
    def __init__(self):
        self.normalization_stats = {
            'brokers_deduplicated': 0,
            'loads_deduplicated': 0,
            'lanes_merged': 0,
            'addresses_normalized': 0,
            'rates_calculated': 0
        }
    
    def normalize_profile(self, profile: CarrierProfile) -> CarrierProfile:
        """
        Normalize a carrier profile by deduplicating and cleaning data.
        
        Args:
            profile: CarrierProfile to normalize
            
        Returns:
            Normalized CarrierProfile
        """
        # Normalize brokers
        profile.brokers = self._deduplicate_brokers(profile.brokers)
        
        # Normalize addresses
        for broker in profile.brokers:
            if broker.company_address:
                broker.company_address = self._normalize_address(broker.company_address)
        
        # Normalize lanes
        profile.lanes = self._deduplicate_lanes(profile.lanes)
        
        # Normalize loads
        profile.loads = self._deduplicate_loads(profile.loads)
        
        # Calculate missing rates
        self._calculate_missing_rates(profile.loads)
        
        # Extract preferences from historical data
        self._extract_preferences(profile)
        
        return profile
    
    def _deduplicate_brokers(self, brokers: List[Broker]) -> List[Broker]:
        """Deduplicate brokers by MC number and company name"""
        seen_mc = {}
        seen_company = {}
        unique_brokers = []
        
        for broker in brokers:
            # Skip if no identifying information
            if not broker.mc_id and not broker.company_name:
                continue
            
            # Check by MC number (most reliable)
            if broker.mc_id:
                normalized_mc = self._normalize_mc_id(broker.mc_id)
                if normalized_mc in seen_mc:
                    # Merge with existing broker
                    existing = seen_mc[normalized_mc]
                    self._merge_brokers(existing, broker)
                    continue
                seen_mc[normalized_mc] = broker
            
            # Check by company name (if no MC)
            elif broker.company_name:
                normalized_name = self._normalize_company_name(broker.company_name)
                if normalized_name in seen_company:
                    existing = seen_company[normalized_name]
                    self._merge_brokers(existing, broker)
                    continue
                seen_company[normalized_name] = broker
            
            unique_brokers.append(broker)
        
        self.normalization_stats['brokers_deduplicated'] = len(brokers) - len(unique_brokers)
        return unique_brokers
    
    def _deduplicate_loads(self, loads: List[Load]) -> List[Load]:
        """Deduplicate loads by load ID"""
        seen_loads = {}
        unique_loads = []
        
        for load in loads:
            if not load.load_id:
                # Try to generate ID from other fields
                load.load_id = self._generate_load_id(load)
            
            if load.load_id:
                normalized_id = load.load_id.strip().upper()
                if normalized_id not in seen_loads:
                    seen_loads[normalized_id] = load
                    unique_loads.append(load)
                else:
                    # Merge load data
                    existing = seen_loads[normalized_id]
                    self._merge_loads(existing, load)
            else:
                unique_loads.append(load)
        
        self.normalization_stats['loads_deduplicated'] = len(loads) - len(unique_loads)
        return unique_loads
    
    def _deduplicate_lanes(self, lanes: List[Lane]) -> List[Lane]:
        """Deduplicate and merge lanes"""
        lane_map = {}
        
        for lane in lanes:
            # Create lane key
            origin = self._normalize_city_state(lane.origin_city_state) if lane.origin_city_state else ""
            destination = self._normalize_city_state(lane.destination_city_state) if lane.destination_city_state else ""
            
            if not origin or not destination:
                continue
            
            lane_key = f"{origin}→{destination}"
            
            if lane_key in lane_map:
                # Merge lane data
                existing = lane_map[lane_key]
                if not existing.distance_miles and lane.distance_miles:
                    existing.distance_miles = lane.distance_miles
                if not existing.estimated_duration_hours and lane.estimated_duration_hours:
                    existing.estimated_duration_hours = lane.estimated_duration_hours
            else:
                lane_map[lane_key] = lane
        
        self.normalization_stats['lanes_merged'] = len(lanes) - len(lane_map)
        return list(lane_map.values())
    
    def _normalize_address(self, address: Address) -> Address:
        """Normalize address format"""
        if address.raw_address:
            # Try to extract components
            raw = address.raw_address
            
            # Extract state
            if not address.state:
                state_match = re.search(r'\b([A-Z]{2})\b', raw)
                if state_match:
                    address.state = state_match.group(1)
            
            # Extract ZIP
            if not address.zip_code:
                zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', raw)
                if zip_match:
                    address.zip_code = zip_match.group(1)
            
            # Extract city (text before state)
            if not address.city and address.state:
                parts = raw.split(address.state)
                if parts:
                    city_part = parts[0].strip().rstrip(',').strip()
                    city_parts = city_part.split(',')
                    if city_parts:
                        address.city = city_parts[-1].strip()
        
        self.normalization_stats['addresses_normalized'] += 1
        return address
    
    def _normalize_mc_id(self, mc_id: str) -> str:
        """Normalize MC number"""
        if not mc_id:
            return ""
        # Remove all non-numeric characters
        return re.sub(r'[^\d]', '', str(mc_id))
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ""
        # Remove common suffixes and normalize
        name = name.upper().strip()
        name = re.sub(r'\s+(LLC|INC|CORP|LTD|LP|LLP)\s*$', '', name)
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name
    
    def _normalize_city_state(self, city_state: str) -> str:
        """Normalize city-state string"""
        if not city_state:
            return ""
        # Remove extra whitespace, normalize format
        city_state = city_state.strip()
        city_state = re.sub(r'\s+', ' ', city_state)
        # Ensure state is uppercase
        parts = city_state.split(',')
        if len(parts) == 2:
            city, state = parts
            return f"{city.strip()}, {state.strip().upper()}"
        return city_state
    
    def _merge_brokers(self, existing: Broker, new: Broker):
        """Merge new broker data into existing broker"""
        # Fill in missing fields
        if not existing.broker_name and new.broker_name:
            existing.broker_name = new.broker_name
        if not existing.company_name and new.company_name:
            existing.company_name = new.company_name
        if not existing.mc_id and new.mc_id:
            existing.mc_id = new.mc_id
        if not existing.broker_phone_number and new.broker_phone_number:
            existing.broker_phone_number = new.broker_phone_number
        if not existing.broker_email and new.broker_email:
            existing.broker_email = new.broker_email
        if not existing.company_address and new.company_address:
            existing.company_address = new.company_address
        if not existing.notes and new.notes:
            existing.notes = new.notes
        elif new.notes and existing.notes and new.notes not in existing.notes:
            existing.notes = f"{existing.notes}; {new.notes}"
    
    def _merge_loads(self, existing: Load, new: Load):
        """Merge new load data into existing load"""
        if not existing.pickup_date and new.pickup_date:
            existing.pickup_date = new.pickup_date
        if not existing.delivery_date and new.delivery_date:
            existing.delivery_date = new.delivery_date
        if not existing.rate and new.rate:
            existing.rate = new.rate
        if not existing.equipment_type and new.equipment_type:
            existing.equipment_type = new.equipment_type
    
    def _generate_load_id(self, load: Load) -> Optional[str]:
        """Generate a load ID from available data"""
        if load.broker and load.broker.mc_id and load.pickup_date:
            return f"{load.broker.mc_id}-{load.pickup_date.strftime('%Y%m%d')}"
        return None
    
    def _calculate_missing_rates(self, loads: List[Load]):
        """Calculate rate per mile for loads missing this information"""
        calculated = 0
        
        for load in loads:
            if load.rate and load.rate.rate_amount:
                # Calculate rate per mile if we have distance
                if load.lane and load.lane.distance_miles:
                    if not load.rate.rate_per_mile:
                        load.rate.rate_per_mile = load.rate.rate_amount / load.lane.distance_miles
                        calculated += 1
                # Calculate distance if we have rate per mile
                elif load.rate.rate_per_mile and load.lane:
                    if not load.lane.distance_miles and load.rate.rate_amount:
                        load.lane.distance_miles = load.rate.rate_amount / load.rate.rate_per_mile
        
        self.normalization_stats['rates_calculated'] = calculated
    
    def _extract_preferences(self, profile: CarrierProfile):
        """Extract carrier preferences from historical data"""
        # Extract preferred lanes (most frequent)
        lane_counts = defaultdict(int)
        for lane in profile.lanes:
            if lane.origin_city_state and lane.destination_city_state:
                lane_key = f"{lane.origin_city_state}→{lane.destination_city_state}"
                lane_counts[lane_key] += 1
        
        # Get top 10 lanes
        profile.preferred_lanes = [
            lane for lane, _ in sorted(lane_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Extract preferred brokers (most frequent)
        broker_counts = defaultdict(int)
        for load in profile.loads:
            if load.broker and load.broker.mc_id:
                broker_counts[load.broker.mc_id] += 1
        
        profile.preferred_brokers = [
            mc_id for mc_id, _ in sorted(broker_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Extract preferred equipment types
        equipment_counts = defaultdict(int)
        for load in profile.loads:
            if load.equipment_type:
                equipment_counts[load.equipment_type] += 1
        
        profile.preferred_equipment = [
            eq for eq, _ in sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get normalization statistics"""
        return self.normalization_stats.copy()

