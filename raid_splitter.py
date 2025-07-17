"""
WoW Raid Group Splitter
Priority-Based Allocation with Role-First Distribution
"""

import random
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Character:
    """Represents a WoW character with all relevant attributes"""
    name: str
    player_id: str
    class_id: str
    class_name: str
    spec_id: str
    spec_name: str
    role_raid: str  # 'tank', 'healer', 'mdps', 'rdps'
    role_group: str  # 'main', 'alt', 'helper'
    armor_type: str  # 'cloth', 'leather', 'mail', 'plate'
    tier_token: str  # 'Mystic', 'Venerated', 'Zenith', 'Dreadful'
    buffs: List[str] = field(default_factory=list)

@dataclass
class RaidGroup:
    """Represents a single raid group with constraints and members"""
    group_id: int
    characters: List[Character] = field(default_factory=list)
    players_used: Set[str] = field(default_factory=set)
    tanks: List[Character] = field(default_factory=list)
    healers: List[Character] = field(default_factory=list)
    dps: List[Character] = field(default_factory=list)
    
    def can_add_character(self, character: Character) -> bool:
        """Check if character can be added (player not already in group)"""
        return character.player_id not in self.players_used
    
    def add_character(self, character: Character) -> bool:
        """Add character to appropriate role list"""
        if not self.can_add_character(character):
            return False
        
        self.characters.append(character)
        self.players_used.add(character.player_id)
        
        # Add to role-specific list
        if character.role_raid == 'tank':
            self.tanks.append(character)
        elif character.role_raid == 'healer':
            self.healers.append(character)
        else:  # mdps or rdps
            self.dps.append(character)
        
        return True
    
    def remove_character(self, character: Character) -> bool:
        """Remove character from group"""
        if character not in self.characters:
            return False
        
        self.characters.remove(character)
        self.players_used.discard(character.player_id)
        
        # Remove from role-specific list
        if character.role_raid == 'tank':
            self.tanks.remove(character)
        elif character.role_raid == 'healer':
            self.healers.remove(character)
        else:
            self.dps.remove(character)
        
        return True
    
    def get_armor_distribution(self) -> Dict[str, int]:
        """Get armor type distribution"""
        armor_count = defaultdict(int)
        for char in self.characters:
            armor_count[char.armor_type] += 1
        return dict(armor_count)
    
    def get_tier_distribution(self) -> Dict[str, int]:
        """Get tier token distribution"""
        tier_count = defaultdict(int)
        for char in self.characters:
            tier_count[char.tier_token] += 1
        return dict(tier_count)
    
    def get_buffs_provided(self) -> Set[str]:
        """Get all buffs provided by this group"""
        buffs = set()
        for char in self.characters:
            buffs.update(char.buffs)
        return buffs
    
    def get_priority_score(self) -> float:
        """Calculate priority score (higher is better)"""
        main_count = sum(1 for c in self.characters if c.role_group == 'main')
        alt_count = sum(1 for c in self.characters if c.role_group == 'alt')
        helper_count = sum(1 for c in self.characters if c.role_group == 'helper')
        
        return (main_count * 3) + (alt_count * 2) + (helper_count * 1)

class RaidSplitter:
    """Main class for splitting characters into raid groups"""
    
    def __init__(self, wow_db):
        self.db = wow_db
        self.required_buffs = [
            'arcane_intellect', 'battle_shout', 'mark_of_the_wild',
            'power_word_fortitude', 'mystic_touch', 'chaos_brand',
            'hunters_mark', 'atrophic_poison', 'skyfury'
        ]
        self.armor_types = ['cloth', 'leather', 'mail', 'plate']
        self.tier_tokens = ['Mystic', 'Venerated', 'Zenith', 'Dreadful']
    
    def get_all_characters(self) -> List[Character]:
        """Fetch all characters from database with full info"""
        pipeline = [
            {
                "$lookup": {
                    "from": "players",
                    "localField": "player_id",
                    "foreignField": "_id",
                    "as": "player"
                }
            },
            {
                "$lookup": {
                    "from": "classes",
                    "localField": "class_id",
                    "foreignField": "class_id",
                    "as": "class_info"
                }
            },
            {
                "$lookup": {
                    "from": "specs",
                    "localField": "spec_id",
                    "foreignField": "spec_id",
                    "as": "spec_info"
                }
            },
            {"$unwind": "$player"},
            {"$unwind": "$class_info"},
            {"$unwind": "$spec_info"},
            {
                "$project": {
                    "name": 1,
                    "player_id": 1,
                    "role_group": 1,
                    "class_id": 1,
                    "class_name": "$class_info.name",
                    "spec_id": 1,
                    "spec_name": "$spec_info.name",
                    "role_raid": "$spec_info.role",
                    "armor_type": "$class_info.armor",
                    "tier_token": "$class_info.token",
                    "buffs": "$class_info.buffs"
                }
            }
        ]
        
        characters = []
        for char_data in self.db.characters.aggregate(pipeline):
            character = Character(
                name=char_data['name'],
                player_id=str(char_data['player_id']),
                class_id=char_data['class_id'],
                class_name=char_data['class_name'],
                spec_id=char_data['spec_id'],
                spec_name=char_data['spec_name'],
                role_raid=char_data['role_raid'],
                role_group=char_data['role_group'],
                armor_type=char_data['armor_type'],
                tier_token=char_data['tier_token'],
                buffs=char_data.get('buffs', [])
            )
            characters.append(character)
        
        return characters
    
    def categorize_characters(self, characters: List[Character]) -> Dict[str, List[Character]]:
        """Categorize characters by role and priority"""
        categorized = {
            'tanks': [],
            'healers': [],
            'dps': []
        }
        
        for char in characters:
            try:
                # Normalize role - convert mdps/rdps to dps
                if char.role_raid == 'tank':
                    categorized['tanks'].append(char)
                elif char.role_raid == 'healer':
                    categorized['healers'].append(char)
                elif char.role_raid in ['mdps', 'rdps', 'dps']:
                    categorized['dps'].append(char)
                else:
                    logger.warning(f"Unknown role '{char.role_raid}' for character {char.name}, treating as DPS")
                    categorized['dps'].append(char)
            except Exception as e:
                logger.error(f"Error categorizing character {char.name}: {e}")
                # Default to DPS if there's an error
                categorized['dps'].append(char)
        
        return categorized
    
    def distribute_tanks(self, groups: List[RaidGroup], tank_chars: List[Character]) -> List[Character]:
        """Distribute tanks across groups (2 per group)"""
        tanks_per_group = 2
        total_tanks_needed = len(groups) * tanks_per_group
        
        if len(tank_chars) < total_tanks_needed:
            logger.warning(f"Not enough tanks! Need {total_tanks_needed}, have {len(tank_chars)}")
        
        # Sort tanks by priority (main > alt > helper)
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        tank_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_tanks = []
        for i, tank in enumerate(tank_chars[:total_tanks_needed]):
            group_index = i // tanks_per_group
            if group_index < len(groups):
                if groups[group_index].add_character(tank):
                    used_tanks.append(tank)
                    logger.info(f"Assigned tank {tank.name} to Group {group_index + 1}")
        
        return used_tanks
    
    def distribute_healers(self, groups: List[RaidGroup], healer_chars: List[Character], healers_per_group: int) -> List[Character]:
        """Distribute healers across groups"""
        total_healers_needed = len(groups) * healers_per_group
        
        if len(healer_chars) < total_healers_needed:
            logger.warning(f"Not enough healers! Need {total_healers_needed}, have {len(healer_chars)}")
        
        # Sort healers by priority
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        healer_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_healers = []
        for i, healer in enumerate(healer_chars[:total_healers_needed]):
            group_index = i // healers_per_group
            if group_index < len(groups):
                if groups[group_index].add_character(healer):
                    used_healers.append(healer)
                    logger.info(f"Assigned healer {healer.name} to Group {group_index + 1}")
        
        return used_healers
    
    def ensure_buff_coverage(self, groups: List[RaidGroup], remaining_chars: List[Character]) -> List[Character]:
        """Ensure each group has all required buffs"""
        used_chars = []
        
        for group in groups:
            current_buffs = group.get_buffs_provided()
            missing_buffs = set(self.required_buffs) - current_buffs
            
            for buff in missing_buffs:
                # Find character that provides this buff
                buff_provider = None
                for char in remaining_chars:
                    if char not in used_chars and buff in char.buffs and group.can_add_character(char):
                        buff_provider = char
                        break
                
                if buff_provider:
                    if group.add_character(buff_provider):
                        used_chars.append(buff_provider)
                        logger.info(f"Assigned {buff_provider.name} to Group {group.group_id} for {buff}")
                else:
                    logger.warning(f"Could not find provider for {buff} in Group {group.group_id}")
        
        return used_chars
    
    def fill_remaining_slots(self, groups: List[RaidGroup], remaining_chars: List[Character], target_size: int) -> List[Character]:
        """Fill remaining slots with available characters"""
        # Remove already used characters
        available_chars = [c for c in remaining_chars if not any(c in group.characters for group in groups)]
        
        # Sort by priority
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        available_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_chars = []
        
        for char in available_chars:
            # Find group with space that can accept this character
            best_group = None
            min_size = float('inf')
            
            for group in groups:
                if len(group.characters) < target_size and group.can_add_character(char):
                    if len(group.characters) < min_size:
                        min_size = len(group.characters)
                        best_group = group
            
            if best_group:
                if best_group.add_character(char):
                    used_chars.append(char)
                    logger.info(f"Assigned {char.name} to Group {best_group.group_id}")
        
        return used_chars
    
    def optimize_armor_distribution(self, groups: List[RaidGroup]) -> None:
        """Optimize armor type distribution across groups"""
        logger.info("Optimizing armor distribution...")
        
        # Simple optimization: try to balance armor types
        for _ in range(10):  # Max 10 optimization iterations
            improved = False
            
            for i, group1 in enumerate(groups):
                for j, group2 in enumerate(groups[i+1:], i+1):
                    # Try swapping characters between groups to improve balance
                    if self._try_armor_swap(group1, group2):
                        improved = True
            
            if not improved:
                break
    
    def _try_armor_swap(self, group1: RaidGroup, group2: RaidGroup) -> bool:
        """Try to swap characters between two groups to improve armor balance"""
        armor1 = group1.get_armor_distribution()
        armor2 = group2.get_armor_distribution()
        
        # Find characters that could improve balance if swapped
        for char1 in group1.characters:
            for char2 in group2.characters:
                if (char1.role_raid == char2.role_raid and 
                    char1.armor_type != char2.armor_type):
                    
                    # Check if swap would improve balance
                    if self._would_improve_armor_balance(group1, group2, char1, char2):
                        # Perform swap
                        group1.remove_character(char1)
                        group2.remove_character(char2)
                        
                        if group1.add_character(char2) and group2.add_character(char1):
                            logger.info(f"Swapped {char1.name} and {char2.name} for armor balance")
                            return True
                        else:
                            # Revert if swap failed
                            group1.add_character(char1)
                            group2.add_character(char2)
        
        return False
    
    def _would_improve_armor_balance(self, group1: RaidGroup, group2: RaidGroup, 
                                   char1: Character, char2: Character) -> bool:
        """Check if swapping would improve armor balance"""
        # Simple heuristic: reduce variance in armor distribution
        armor1_before = group1.get_armor_distribution()
        armor2_before = group2.get_armor_distribution()
        
        # Calculate variance before swap
        variance_before = self._calculate_armor_variance(armor1_before) + self._calculate_armor_variance(armor2_before)
        
        # Simulate swap
        armor1_after = armor1_before.copy()
        armor2_after = armor2_before.copy()
        
        armor1_after[char1.armor_type] -= 1
        armor1_after[char2.armor_type] = armor1_after.get(char2.armor_type, 0) + 1
        
        armor2_after[char2.armor_type] -= 1
        armor2_after[char1.armor_type] = armor2_after.get(char1.armor_type, 0) + 1
        
        # Calculate variance after swap
        variance_after = self._calculate_armor_variance(armor1_after) + self._calculate_armor_variance(armor2_after)
        
        return variance_after < variance_before
    
    def _calculate_armor_variance(self, armor_dist: Dict[str, int]) -> float:
        """Calculate variance in armor distribution"""
        total = sum(armor_dist.values())
        if total == 0:
            return 0
        
        target = total / 4  # Ideal is 25% each
        variance = sum((count - target) ** 2 for count in armor_dist.values())
        return variance / total
    
    def create_optimal_groups(self, num_groups: int = 3, group_size: int = 30, 
                            healers_per_group: int = 5) -> List[RaidGroup]:
        """Main method to create optimized raid groups"""
        logger.info(f"Creating {num_groups} groups of {group_size} with {healers_per_group} healers each")
        
        try:
            # Phase 1: Get all characters
            all_characters = self.get_all_characters()
            logger.info(f"Loaded {len(all_characters)} characters")
            
            if not all_characters:
                raise ValueError("No characters found in database")
            
            # Phase 2: Categorize characters
            categorized = self.categorize_characters(all_characters)
            
            tanks = categorized['tanks']
            healers = categorized['healers']
            dps = categorized['dps']
            
            logger.info(f"Available: {len(tanks)} tanks, {len(healers)} healers, {len(dps)} dps")
            
            # Check minimum requirements
            tanks_needed = num_groups * 2
            healers_needed = num_groups * healers_per_group
            
            if len(tanks) < tanks_needed:
                logger.warning(f"Not enough tanks! Need {tanks_needed}, have {len(tanks)}")
            if len(healers) < healers_needed:
                logger.warning(f"Not enough healers! Need {healers_needed}, have {len(healers)}")
            
            # Phase 3: Initialize groups
            groups = [RaidGroup(group_id=i+1) for i in range(num_groups)]
            
            # Phase 4: Role-First Distribution
            used_tanks = self.distribute_tanks(groups, tanks)
            used_healers = self.distribute_healers(groups, healers, healers_per_group)
            
            # Phase 5: Ensure buff coverage
            remaining_chars = [c for c in all_characters if c not in used_tanks and c not in used_healers]
            used_for_buffs = self.ensure_buff_coverage(groups, remaining_chars)
            
            # Phase 6: Fill remaining slots
            remaining_chars = [c for c in remaining_chars if c not in used_for_buffs]
            self.fill_remaining_slots(groups, remaining_chars, group_size)
            
            # Phase 7: Optimize armor/tier distribution
            self.optimize_armor_distribution(groups)
            
            # Phase 8: Validate and report
            self.validate_groups(groups)
            
            return groups
            
        except Exception as e:
            logger.error(f"Error in create_optimal_groups: {str(e)}")
            raise
    
    def validate_groups(self, groups: List[RaidGroup]) -> None:
        """Validate group constraints and report statistics"""
        logger.info("Validating groups...")
        
        for group in groups:
            logger.info(f"Group {group.group_id}: {len(group.characters)} members")
            logger.info(f"  Tanks: {len(group.tanks)}, Healers: {len(group.healers)}, DPS: {len(group.dps)}")
            
            # Check buff coverage
            provided_buffs = group.get_buffs_provided()
            missing_buffs = set(self.required_buffs) - provided_buffs
            if missing_buffs:
                logger.warning(f"  Missing buffs: {missing_buffs}")
            else:
                logger.info("  All required buffs covered ✓")
            
            # Check armor distribution
            armor_dist = group.get_armor_distribution()
            logger.info(f"  Armor: {armor_dist}")
            
            # Check tier distribution
            tier_dist = group.get_tier_distribution()
            logger.info(f"  Tier tokens: {tier_dist}")
            
            # Check priority distribution
            priority_dist = Counter(c.role_group for c in group.characters)
            logger.info(f"  Priority: {dict(priority_dist)}")
    
    def groups_to_dict(self, groups: List[RaidGroup]) -> List[Dict]:
        """Convert groups to dictionary format for JSON serialization"""
        result = []
        for group in groups:
            # Calculate meaningful variables for display
            armor_dist = group.get_armor_distribution()
            armor_balance_score = self._calculate_armor_balance_score(armor_dist)
            
            tier_dist = group.get_tier_distribution()
            tier_balance_score = self._calculate_tier_balance_score(tier_dist)
            
            group_dict = {
                'group_id': group.group_id,
                'total_members': len(group.characters),
                'tanks': len(group.tanks),
                'healers': len(group.healers),
                'dps': len(group.dps),
                'variable_1': round(armor_balance_score, 1),  # Armor balance score
                'variable_2': round(tier_balance_score, 1),   # Tier balance score
                'characters': [
                    {
                        'name': char.name,
                        'class_name': char.class_name,
                        'spec_name': char.spec_name,
                        'role_raid': char.role_raid,
                        'role_group': char.role_group,
                        'armor_type': char.armor_type,
                        'tier_token': char.tier_token,
                        'buffs': char.buffs
                    }
                    for char in group.characters
                ],
                'armor_distribution': armor_dist,
                'tier_distribution': tier_dist,
                'buffs_provided': list(group.get_buffs_provided()),
                'priority_score': group.get_priority_score()
            }
            result.append(group_dict)
        
        return result
    
    def _calculate_armor_balance_score(self, armor_dist: Dict[str, int]) -> float:
        """Calculate armor balance score (0-100, higher is better)"""
        total = sum(armor_dist.values())
        if total == 0:
            return 100.0
        
        target = total / 4  # Ideal is 25% each
        variance = sum((count - target) ** 2 for count in armor_dist.values())
        
        # Convert to 0-100 score (100 = perfect balance)
        max_variance = target * target * 4  # Maximum possible variance
        balance_score = max(0, 100 - (variance / max_variance * 100))
        return balance_score
    
    def _calculate_tier_balance_score(self, tier_dist: Dict[str, int]) -> float:
        """Calculate tier token balance score (0-100, higher is better)"""
        total = sum(tier_dist.values())
        if total == 0:
            return 100.0
        
        target = total / 4  # Ideal is 25% each
        variance = sum((count - target) ** 2 for count in tier_dist.values())
        
        # Convert to 0-100 score
        max_variance = target * target * 4
        balance_score = max(0, 100 - (variance / max_variance * 100))
        return balance_score