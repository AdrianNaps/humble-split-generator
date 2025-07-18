"""
WoW Raid Group Splitter
Priority-Based Allocation with Role-First Distribution
Updated to match exact database schema and focus armor balancing on mains only
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
    role_group: str  # 'main', 'alt', 'helper', 'inactive'
    armor_type: str  # 'cloth', 'leather', 'mail', 'plate'
    tier_token: str  # 'Mystic', 'Venerated', 'Zenith', 'Dreadful'
    raid_buff_ids: List[str] = field(default_factory=list)

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
    
    def get_armor_distribution(self, mains_only: bool = False) -> Dict[str, int]:
        """Get armor type distribution, optionally for mains only"""
        armor_count = defaultdict(int)
        
        characters_to_check = self.characters
        if mains_only:
            characters_to_check = [c for c in self.characters if c.role_group == 'main']
        
        for char in characters_to_check:
            armor_count[char.armor_type] += 1
        return dict(armor_count)
    
    def get_tier_distribution(self, mains_only: bool = False) -> Dict[str, int]:
        """Get tier token distribution, optionally for mains only"""
        tier_count = defaultdict(int)
        
        characters_to_check = self.characters
        if mains_only:
            characters_to_check = [c for c in self.characters if c.role_group == 'main']
        
        for char in characters_to_check:
            tier_count[char.tier_token] += 1
        return dict(tier_count)
    
    def get_buffs_provided(self) -> Set[str]:
        """Get all buffs provided by this group"""
        buffs = set()
        for char in self.characters:
            buffs.update(char.raid_buff_ids)
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
        try:
            # First, let's check if we have any characters at all
            total_chars = self.db.characters.count_documents({})
            logger.info(f"Total characters in database: {total_chars}")
            
            if total_chars == 0:
                logger.error("No characters found in database!")
                return []
            
            # Get a sample character to see the actual structure
            sample_char = self.db.characters.find_one()
            logger.info(f"Sample character structure: {sample_char}")
            
            # Check what's actually in the specs and classes collections
            sample_spec = self.db.specs.find_one({"spec_id": sample_char.get("spec_id")})
            logger.info(f"Looking for spec_id '{sample_char.get('spec_id')}', found: {sample_spec}")
            
            sample_class = self.db.classes.find_one({"class_id": sample_char.get("class_id")})
            logger.info(f"Looking for class_id '{sample_char.get('class_id')}', found: {sample_class}")
            
            # Let's see what spec IDs are actually available
            available_specs = list(self.db.specs.find({}, {"spec_id": 1, "spec_name": 1}).limit(5))
            logger.info(f"Available spec IDs (sample): {available_specs}")
            
            # Try a simple aggregation first
            pipeline = [
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
                {
                    "$match": {
                        "class_info": {"$ne": []},
                        "spec_info": {"$ne": []}
                    }
                },
                {"$unwind": "$class_info"},
                {"$unwind": "$spec_info"},
                {
                    "$project": {
                        "name": 1,
                        "player_id": {"$toString": "$player_id"},
                        "class_id": 1,
                        "spec_id": 1,
                        "role_group": 1,
                        # Fix field mapping to match actual database schema
                        "class_name": "$class_info.name",  # Database uses "name", not "class_name"
                        "spec_name": "$spec_info.name",    # Database uses "name", not "spec_name"
                        "role_raid": "$spec_info.role",    # Database uses "role", not "role_raid"
                        "armor_type": "$class_info.armor", # Database uses "armor", not "armor_type"
                        "tier_token": "$class_info.token", # Database uses "token", not "tier_token"
                        "raid_buff_ids": "$class_info.buffs"  # Database uses "buffs", not "raid_buff_ids"
                    }
                }
            ]
            
            logger.info("Running aggregation pipeline...")
            char_results = list(self.db.characters.aggregate(pipeline))
            
            logger.info(f"Pipeline returned {len(char_results)} characters")
            if char_results:
                logger.info(f"Sample character from pipeline: {char_results[0]}")
            else:
                logger.error("Pipeline returned no results! Trying simpler query...")
                
                # Try without aggregation to see what's wrong
                simple_chars = list(self.db.characters.find().limit(5))
                logger.info(f"Simple find() returned {len(simple_chars)} characters")
                if simple_chars:
                    logger.info(f"Sample from simple find: {simple_chars[0]}")
                
                # Check if lookups are working
                logger.info("Testing class lookup...")
                test_class = list(self.db.classes.find().limit(1))
                logger.info(f"Classes available: {len(list(self.db.classes.find()))}")
                if test_class:
                    logger.info(f"Sample class: {test_class[0]}")
                
                logger.info("Testing spec lookup...")
                test_spec = list(self.db.specs.find().limit(1))
                logger.info(f"Specs available: {len(list(self.db.specs.find()))}")
                if test_spec:
                    logger.info(f"Sample spec: {test_spec[0]}")
                
                return []
            
            characters = []
            for char_data in char_results:
                try:
                    character = Character(
                        name=char_data['name'],
                        player_id=char_data['player_id'],
                        class_id=char_data['class_id'],
                        class_name=char_data['class_name'],
                        spec_id=char_data['spec_id'],
                        spec_name=char_data['spec_name'],
                        role_raid=char_data['role_raid'],
                        role_group=char_data['role_group'],
                        armor_type=char_data['armor_type'],
                        tier_token=char_data['tier_token'],
                        raid_buff_ids=char_data.get('raid_buff_ids', [])
                    )
                    characters.append(character)
                except Exception as e:
                    logger.error(f"Error creating character from data {char_data}: {e}")
                    continue
            
            logger.info(f"Successfully created {len(characters)} character objects")
            return characters
            
        except Exception as e:
            logger.error(f"Error in get_all_characters: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
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
        """Distribute tanks across groups (2 per group) - with flexible distribution if not enough"""
        tanks_per_group = 2
        total_tanks_needed = len(groups) * tanks_per_group
        
        if len(tank_chars) < total_tanks_needed:
            logger.warning(f"Not enough tanks! Need {total_tanks_needed}, have {len(tank_chars)}")
            logger.info(f"Will distribute {len(tank_chars)} tanks as evenly as possible")
        
        # Sort tanks by priority (main > alt > helper)
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        tank_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_tanks = []
        
        # Distribute tanks round-robin style for even distribution
        for i, tank in enumerate(tank_chars):
            group_index = i % len(groups)  # Round-robin assignment
            if groups[group_index].add_character(tank):
                used_tanks.append(tank)
                logger.info(f"Assigned tank {tank.name} to Group {group_index + 1}")
        
        # Log final tank distribution
        for i, group in enumerate(groups):
            actual_tanks = len(group.tanks)
            if actual_tanks < tanks_per_group:
                logger.warning(f"Group {i+1} has {actual_tanks} tanks (target was {tanks_per_group})")
        
        return used_tanks
    
    def distribute_healers(self, groups: List[RaidGroup], healer_chars: List[Character], healers_per_group: int) -> List[Character]:
        """Distribute healers across groups - with optimal distribution when not enough"""
        total_healers_needed = len(groups) * healers_per_group
        
        if len(healer_chars) < total_healers_needed:
            logger.warning(f"Not enough healers! Need {total_healers_needed}, have {len(healer_chars)}")
            logger.info(f"Will distribute {len(healer_chars)} healers optimally across {len(groups)} groups")
        
        # Sort healers by priority
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        healer_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_healers = []
        
        # Calculate optimal distribution when we don't have enough healers
        if len(healer_chars) < total_healers_needed:
            # Distribute as evenly as possible
            base_healers_per_group = len(healer_chars) // len(groups)
            extra_healers = len(healer_chars) % len(groups)
            
            healer_index = 0
            for group_idx, group in enumerate(groups):
                # Each group gets base amount, first few groups get one extra
                target_for_this_group = base_healers_per_group + (1 if group_idx < extra_healers else 0)
                
                for _ in range(target_for_this_group):
                    if healer_index < len(healer_chars):
                        healer = healer_chars[healer_index]
                        if group.add_character(healer):
                            used_healers.append(healer)
                            logger.info(f"Assigned healer {healer.name} to Group {group_idx + 1}")
                            healer_index += 1
        else:
            # Standard distribution when we have enough healers
            for i, healer in enumerate(healer_chars[:total_healers_needed]):
                group_index = i // healers_per_group
                if group_index < len(groups):
                    if groups[group_index].add_character(healer):
                        used_healers.append(healer)
                        logger.info(f"Assigned healer {healer.name} to Group {group_index + 1}")
        
        # Log final healer distribution
        for i, group in enumerate(groups):
            actual_healers = len(group.healers)
            logger.info(f"Group {i+1} has {actual_healers} healers")
        
        return used_healers
    
    def ensure_buff_coverage(self, groups: List[RaidGroup], remaining_chars: List[Character], group_size: int) -> List[Character]:
        """Ensure each group has all required buffs - with strict size limit"""
        used_chars = []
        
        for group in groups:
            # Skip if group is already at capacity
            if len(group.characters) >= group_size:
                continue
                
            current_buffs = group.get_buffs_provided()
            missing_buffs = set(self.required_buffs) - current_buffs
            
            for buff in missing_buffs:
                # Skip if group would exceed capacity
                if len(group.characters) >= group_size:
                    break
                    
                # Find character that provides this buff
                buff_provider = None
                for char in remaining_chars:
                    if char not in used_chars and buff in char.raid_buff_ids and group.can_add_character(char):
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
        """Fill remaining slots with available characters - AGGRESSIVE filling to reach target_size"""
        # Remove already used characters
        available_chars = [c for c in remaining_chars if not any(c in group.characters for group in groups)]
        
        # Sort by priority
        priority_order = {'main': 3, 'alt': 2, 'helper': 1}
        available_chars.sort(key=lambda c: priority_order.get(c.role_group, 0), reverse=True)
        
        used_chars = []
        
        logger.info(f"Starting aggressive fill with {len(available_chars)} available characters")
        
        # AGGRESSIVE APPROACH: Fill each group to target_size
        for group in groups:
            current_size = len(group.characters)
            slots_needed = target_size - current_size
            
            if slots_needed <= 0:
                logger.info(f"Group {group.group_id} already at capacity ({current_size}/{target_size})")
                continue
            
            logger.info(f"Group {group.group_id} needs {slots_needed} more characters ({current_size}/{target_size})")
            
            # Find characters that can go in this group
            candidates = []
            for char in available_chars:
                if char not in used_chars and group.can_add_character(char):
                    candidates.append(char)
            
            # Add as many as possible up to the target
            added_to_this_group = 0
            for char in candidates:
                if added_to_this_group >= slots_needed:
                    break
                    
                if group.add_character(char):
                    used_chars.append(char)
                    added_to_this_group += 1
                    logger.info(f"Assigned {char.name} to Group {group.group_id} (size: {len(group.characters)}/{target_size})")
            
            if added_to_this_group > 0:
                logger.info(f"Added {added_to_this_group} characters to Group {group.group_id}")
            else:
                logger.warning(f"Could not add any characters to Group {group.group_id} (player conflicts)")
        
        # Report any unassigned characters
        unassigned_count = len([c for c in available_chars if c not in used_chars])
        if unassigned_count > 0:
            logger.warning(f"⚠️ {unassigned_count} characters could not be assigned due to player conflicts")
        
        # Log final group sizes
        total_assigned = sum(len(group.characters) for group in groups)
        logger.info(f"📊 Final assignment: {total_assigned} characters across {len(groups)} groups")
        for group in groups:
            logger.info(f"Final Group {group.group_id} size: {len(group.characters)}/{target_size}")
        
        return used_chars
    
    def optimize_armor_and_tier_distribution(self, groups: List[RaidGroup]) -> None:
        """Optimize armor type and tier token distribution across groups - MAINS ONLY"""
        logger.info("Optimizing armor and tier distribution (mains only)...")
        
        # Optimization: try to balance armor types and tier tokens among main characters only
        for iteration in range(10):  # Max 10 optimization iterations
            improved = False
            
            for i, group1 in enumerate(groups):
                for j, group2 in enumerate(groups[i+1:], i+1):
                    # Try swapping MAIN characters between groups to improve balance
                    if self._try_armor_and_tier_swap_mains_only(group1, group2):
                        improved = True
            
            if not improved:
                logger.info(f"Distribution optimization converged after {iteration + 1} iterations")
                break
        
        # Log final distributions for mains only
        logger.info("Final distributions for MAIN characters:")
        for group in groups:
            mains_armor = group.get_armor_distribution(mains_only=True)
            mains_tier = group.get_tier_distribution(mains_only=True)
            mains_count = len([c for c in group.characters if c.role_group == 'main'])
            logger.info(f"  Group {group.group_id}: Armor {mains_armor}, Tier {mains_tier} ({mains_count} mains total)")
    
    def _try_armor_and_tier_swap_mains_only(self, group1: RaidGroup, group2: RaidGroup) -> bool:
        """Try to swap MAIN characters between two groups to improve armor and tier balance"""
        # Only consider main characters for swapping
        mains1 = [c for c in group1.characters if c.role_group == 'main']
        mains2 = [c for c in group2.characters if c.role_group == 'main']
        
        # Find main characters that could improve balance if swapped
        for char1 in mains1:
            for char2 in mains2:
                if (char1.role_raid == char2.role_raid and 
                    (char1.armor_type != char2.armor_type or char1.tier_token != char2.tier_token)):
                    
                    # Check if swap would improve balance (considering only mains)
                    if self._would_improve_distribution_mains_only(group1, group2, char1, char2):
                        # Perform swap
                        group1.remove_character(char1)
                        group2.remove_character(char2)
                        
                        if group1.add_character(char2) and group2.add_character(char1):
                            logger.info(f"Swapped MAIN characters {char1.name} and {char2.name} for better distribution")
                            return True
                        else:
                            # Revert if swap failed
                            group1.add_character(char1)
                            group2.add_character(char2)
        
        return False
    
    def _would_improve_distribution_mains_only(self, group1: RaidGroup, group2: RaidGroup, 
                                              char1: Character, char2: Character) -> bool:
        """Check if swapping would improve armor and tier distribution among MAIN characters only"""
        # Only consider main characters for balance calculation
        armor1_before = group1.get_armor_distribution(mains_only=True)
        armor2_before = group2.get_armor_distribution(mains_only=True)
        tier1_before = group1.get_tier_distribution(mains_only=True)
        tier2_before = group2.get_tier_distribution(mains_only=True)
        
        # Calculate combined variance before swap
        armor_variance_before = self._calculate_variance(armor1_before) + self._calculate_variance(armor2_before)
        tier_variance_before = self._calculate_variance(tier1_before) + self._calculate_variance(tier2_before)
        total_variance_before = armor_variance_before + tier_variance_before
        
        # Simulate swap (only if both characters are mains)
        if char1.role_group != 'main' or char2.role_group != 'main':
            return False
        
        # Simulate armor distribution after swap
        armor1_after = armor1_before.copy()
        armor2_after = armor2_before.copy()
        armor1_after[char1.armor_type] = max(0, armor1_after.get(char1.armor_type, 0) - 1)
        armor1_after[char2.armor_type] = armor1_after.get(char2.armor_type, 0) + 1
        armor2_after[char2.armor_type] = max(0, armor2_after.get(char2.armor_type, 0) - 1)
        armor2_after[char1.armor_type] = armor2_after.get(char1.armor_type, 0) + 1
        
        # Simulate tier distribution after swap
        tier1_after = tier1_before.copy()
        tier2_after = tier2_before.copy()
        tier1_after[char1.tier_token] = max(0, tier1_after.get(char1.tier_token, 0) - 1)
        tier1_after[char2.tier_token] = tier1_after.get(char2.tier_token, 0) + 1
        tier2_after[char2.tier_token] = max(0, tier2_after.get(char2.tier_token, 0) - 1)
        tier2_after[char1.tier_token] = tier2_after.get(char1.tier_token, 0) + 1
        
        # Calculate combined variance after swap
        armor_variance_after = self._calculate_variance(armor1_after) + self._calculate_variance(armor2_after)
        tier_variance_after = self._calculate_variance(tier1_after) + self._calculate_variance(tier2_after)
        total_variance_after = armor_variance_after + tier_variance_after
        
        return total_variance_after < total_variance_before
    
    def _calculate_variance(self, distribution: Dict[str, int]) -> float:
        """Calculate variance in distribution (generic for armor or tier)"""
        total = sum(distribution.values())
        if total == 0:
            return 0
        
        target = total / 4  # Ideal is 25% each (4 armor types, 4 tier tokens)
        variance = sum((count - target) ** 2 for count in distribution.values())
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
            used_for_buffs = self.ensure_buff_coverage(groups, remaining_chars, group_size)
            
            # Phase 6: Fill remaining slots with strict size limit
            remaining_chars = [c for c in remaining_chars if c not in used_for_buffs]
            self.fill_remaining_slots(groups, remaining_chars, group_size)
            
            # Phase 7: Optimize armor/tier distribution (mains only)
            self.optimize_armor_and_tier_distribution(groups)
            
            # Phase 8: Validate and report
            self.validate_groups(groups)
            
            return groups
            
        except Exception as e:
            logger.error(f"Error in create_optimal_groups: {str(e)}")
            raise
    
    def validate_groups(self, groups: List[RaidGroup]) -> None:
        """Validate group constraints and report statistics - Updated for mains-only armor focus"""
        logger.info("Validating groups...")
        
        for group in groups:
            mains_count = len([c for c in group.characters if c.role_group == 'main'])
            logger.info(f"Group {group.group_id}: {len(group.characters)} members ({mains_count} mains)")
            logger.info(f"  Tanks: {len(group.tanks)}, Healers: {len(group.healers)}, DPS: {len(group.dps)}")
            
            # Check buff coverage
            provided_buffs = group.get_buffs_provided()
            missing_buffs = set(self.required_buffs) - provided_buffs
            if missing_buffs:
                logger.warning(f"  Missing buffs: {missing_buffs}")
            else:
                logger.info("  All required buffs covered ✓")
            
            # Check armor distribution for mains vs all
            armor_dist_all = group.get_armor_distribution()
            armor_dist_mains = group.get_armor_distribution(mains_only=True)
            logger.info(f"  Armor (all): {armor_dist_all}")
            logger.info(f"  Armor (mains): {armor_dist_mains} ⭐")
            
            # Check tier distribution for mains vs all
            tier_dist_all = group.get_tier_distribution()
            tier_dist_mains = group.get_tier_distribution(mains_only=True)
            logger.info(f"  Tier tokens (all): {tier_dist_all}")
            logger.info(f"  Tier tokens (mains): {tier_dist_mains} ⭐")
            
            # Check priority distribution
            priority_dist = Counter(c.role_group for c in group.characters)
            logger.info(f"  Priority: {dict(priority_dist)}")
    
    def groups_to_dict(self, groups: List[RaidGroup]) -> List[Dict]:
        """Convert groups to dictionary format - Show mains-only counts"""
        result = []
        for group in groups:
            # Get distributions for MAINS ONLY
            mains_armor_dist = group.get_armor_distribution(mains_only=True)
            mains_tier_dist = group.get_tier_distribution(mains_only=True)
            
            # Count mains for context
            mains_count = len([c for c in group.characters if c.role_group == 'main'])
            
            group_dict = {
                'group_id': group.group_id,
                'total_members': len(group.characters),
                'mains_count': mains_count,
                'tanks': len(group.tanks),
                'healers': len(group.healers),
                'dps': len(group.dps),
                'variable_1': mains_count,  # Show mains count as variable 1
                'variable_2': sum(mains_armor_dist.values()),  # Total mains (same as variable_1, for consistency)
                'characters': [
                    {
                        'name': char.name,
                        'class_name': char.class_name,
                        'spec_name': char.spec_name,
                        'role_raid': char.role_raid,
                        'role_group': char.role_group,
                        'armor_type': char.armor_type,
                        'tier_token': char.tier_token,
                        'buffs': char.raid_buff_ids
                    }
                    for char in group.characters
                ],
                'armor_distribution': group.get_armor_distribution(),  # All characters
                'armor_distribution_mains': mains_armor_dist,          # Mains only
                'tier_distribution': group.get_tier_distribution(),    # All characters  
                'tier_distribution_mains': mains_tier_dist,            # Mains only
                'buffs_provided': list(group.get_buffs_provided()),
                'priority_score': group.get_priority_score()
            }
            result.append(group_dict)
        
        return result