"""
Load matching algorithm.
Ranks loads based on carrier's past booking history and preferences.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from schema import CarrierProfile, Load, Lane, Broker


@dataclass
class LoadMatch:
    """Represents a matched load with score"""
    load: Load
    score: float
    match_reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'load': self.load.to_dict(),
            'score': self.score,
            'match_reasons': self.match_reasons
        }


class LoadMatchingEngine:
    """Engine for matching loads to carriers based on historical data"""
    
    def __init__(self, carrier_profile: CarrierProfile):
        self.carrier_profile = carrier_profile
        self.match_weights = {
            'past_broker': 0.3,      # Matched with past broker
            'past_lane': 0.4,         # Matched with past lane
            'preferred_lane': 0.2,    # Matched with preferred lane
            'preferred_equipment': 0.1, # Matched with preferred equipment
            'rate_quality': 0.1,      # Rate quality vs market
            'enrichment_confidence': 0.05  # Confidence in enriched data
        }
    
    def match_loads(self, available_loads: List[Load], limit: int = 10) -> List[LoadMatch]:
        """
        Match available loads to carrier profile.
        
        Args:
            available_loads: List of available loads to match
            limit: Maximum number of matches to return
            
        Returns:
            List of LoadMatch objects sorted by score (highest first)
        """
        matches = []
        
        for load in available_loads:
            score, reasons = self._calculate_match_score(load)
            matches.append(LoadMatch(
                load=load,
                score=score,
                match_reasons=reasons
            ))
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x.score, reverse=True)
        
        return matches[:limit]
    
    def _calculate_match_score(self, load: Load) -> tuple:
        """
        Calculate match score for a load.
        
        Returns:
            Tuple of (score, list of match reasons)
        """
        score = 0.0
        reasons = []
        
        # Check past broker match
        if load.broker and load.broker.mc_id:
            if load.broker.mc_id in self.carrier_profile.preferred_brokers:
                broker_rank = self.carrier_profile.preferred_brokers.index(load.broker.mc_id)
                # Higher score for higher rank (more frequent)
                broker_score = (len(self.carrier_profile.preferred_brokers) - broker_rank) / len(self.carrier_profile.preferred_brokers)
                score += self.match_weights['past_broker'] * broker_score
                reasons.append(f"Past broker match: {load.broker.company_name}")
            
            # Also check if broker appears in historical loads
            for past_load in self.carrier_profile.loads:
                if past_load.broker and past_load.broker.mc_id == load.broker.mc_id:
                    score += self.match_weights['past_broker'] * 0.5
                    reasons.append(f"Historical broker: {load.broker.company_name}")
                    break
        
        # Check lane match
        if load.lane and load.lane.origin_city_state and load.lane.destination_city_state:
            lane_key = f"{load.lane.origin_city_state}→{load.lane.destination_city_state}"
            
            # Check preferred lanes
            if lane_key in self.carrier_profile.preferred_lanes:
                lane_rank = self.carrier_profile.preferred_lanes.index(lane_key)
                lane_score = (len(self.carrier_profile.preferred_lanes) - lane_rank) / len(self.carrier_profile.preferred_lanes)
                score += self.match_weights['preferred_lane'] * lane_score
                reasons.append(f"Preferred lane: {lane_key}")
            
            # Check past lanes (exact match)
            for past_lane in self.carrier_profile.lanes:
                if (past_lane.origin_city_state == load.lane.origin_city_state and
                    past_lane.destination_city_state == load.lane.destination_city_state):
                    score += self.match_weights['past_lane']
                    reasons.append(f"Exact lane match: {lane_key}")
                    break
            
            # Check reverse lane (return trip)
            reverse_key = f"{load.lane.destination_city_state}→{load.lane.origin_city_state}"
            for past_lane in self.carrier_profile.lanes:
                if (past_lane.origin_city_state == load.lane.destination_city_state and
                    past_lane.destination_city_state == load.lane.origin_city_state):
                    score += self.match_weights['past_lane'] * 0.7  # Slightly lower for reverse
                    reasons.append(f"Reverse lane match: {reverse_key}")
                    break
        
        # Check equipment type match
        if load.equipment_type and load.equipment_type in self.carrier_profile.preferred_equipment:
            eq_rank = self.carrier_profile.preferred_equipment.index(load.equipment_type)
            eq_score = (len(self.carrier_profile.preferred_equipment) - eq_rank) / len(self.carrier_profile.preferred_equipment)
            score += self.match_weights['preferred_equipment'] * eq_score
            reasons.append(f"Preferred equipment: {load.equipment_type}")
        
        # Check rate quality
        if load.rate and load.rate.rate_amount and load.lane and load.lane.distance_miles:
            # Calculate rate per mile
            rate_per_mile = load.rate.rate_amount / load.lane.distance_miles
            
            # Compare with historical rates
            historical_rates = []
            for past_load in self.carrier_profile.loads:
                if (past_load.rate and past_load.rate.rate_per_mile and
                    past_load.lane and past_load.lane.distance_miles):
                    historical_rates.append(past_load.rate.rate_per_mile)
            
            if historical_rates:
                avg_rate = sum(historical_rates) / len(historical_rates)
                # Score based on how close to average (within 20% is good)
                rate_diff = abs(rate_per_mile - avg_rate) / avg_rate
                if rate_diff <= 0.2:
                    rate_score = 1.0 - (rate_diff / 0.2)
                    score += self.match_weights['rate_quality'] * rate_score
                    reasons.append(f"Rate quality: ${rate_per_mile:.2f}/mile (avg: ${avg_rate:.2f})")
        
        # Normalize score to 0-1 range
        score = min(1.0, score)
        
        # If no specific matches, give a base score for sparse data scenarios
        if score < 0.1 and len(self.carrier_profile.loads) < 5:
            score = 0.3  # Base score for new carriers
            reasons.append("New carrier - base match score")
        
        return score, reasons
    
    def get_match_summary(self, matches: List[LoadMatch]) -> Dict[str, Any]:
        """Get summary statistics for matches"""
        if not matches:
            return {
                'total_matches': 0,
                'average_score': 0,
                'high_confidence_matches': 0,
                'match_distribution': {}
            }
        
        scores = [m.score for m in matches]
        high_confidence = len([s for s in scores if s >= 0.7])
        
        # Count match types
        match_types = {}
        for match in matches:
            for reason in match.match_reasons:
                match_type = reason.split(':')[0] if ':' in reason else reason
                match_types[match_type] = match_types.get(match_type, 0) + 1
        
        return {
            'total_matches': len(matches),
            'average_score': sum(scores) / len(scores),
            'high_confidence_matches': high_confidence,
            'match_distribution': match_types
        }

