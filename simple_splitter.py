"""
Simple Raid Splitter
Clean, predictable raid group generation with locking support
"""

import logging
import random
from typing import List, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SimpleCharacter:
    """Simplified character representation"""
    name: str
    player_id: str
    class_id: str
    class_name: str
    spec_id: str
    spec_name: str
    role_raid: str  # 'tank', 'healer', 'mdps', 'rdps'
    role_group: str  # 'main', 'alt', 'helper', 'inactive'
    armor_type: str = ''
    tier_token: str = ''
    raid_buff_ids: List[str] = field(default_factory=list)
    
    # Locking support (future feature)
    is_locked: bool = False
    locked_to_group: int = None

@dataclass
class SimpleGroup:
    """Simple group container with hard size limit"""
    group_id: int
    max_size: int = 30
    characters: List[SimpleCharacter] = field(default_factory=list)
    players_used: Set[str] = field(default_factory=set)
    
    def can_add_character(self, character: SimpleCharacter) -> bool:
        """Check if character can be added"""
        # Check size limit
        if len(self.characters) >= self.max_size:
            return False
            
        # Check if player already in group
        if character.player_id in self.players_used:
            return False
            
        # Check if character is locked to a different group
        if character.is_locked and character.locked_to_group != self.group_id:
            return False
            
        return True
    
    def add_character(self, character: SimpleCharacter) -> bool:
        """Add character to group"""
        if not self.can_add_character(character):
            return False
            
        self.characters.append(character)
        self.players_used.add(character.player_id)
        return True
    
    def get_role_counts(self) -> Dict[str, int]:
        """Get count of each role in group"""
        counts = defaultdict(int)
        for char in self.characters:
            counts[char.role_raid] += 1
        return dict(counts)
    
    def get_priority_counts(self) -> Dict[str, int]:
        """Get count of each priority in group"""
        counts = defaultdict(int)
        for char in self.characters:
            counts[char.role_group] += 1
        return dict(counts)
    
    def get_armor_distribution(self, mains_only: bool = False) -> Dict[str, int]:
        """Get armor type distribution, optionally for mains only"""
        armor_count = defaultdict(int)
        
        characters_to_check = self.characters
        if mains_only:
            characters_to_check = [c for c in self.characters if c.role_group == 'main']
        
        for char in characters_to_check:
            if char.armor_type:  # Only count if armor_type is not empty
                armor_count[char.armor_type] += 1
        return dict(armor_count)
    
    def get_tier_distribution(self, mains_only: bool = False) -> Dict[str, int]:
        """Get tier token distribution, optionally for mains only"""
        tier_count = defaultdict(int)
        
        characters_to_check = self.characters
        if mains_only:
            characters_to_check = [c for c in self.characters if c.role_group == 'main']
        
        for char in characters_to_check:
            if char.tier_token:  # Only count if tier_token is not empty
                tier_count[char.tier_token] += 1
        return dict(tier_count)

class SimpleRaidSplitter:
    """
    Simple, predictable raid group generator
    
    Algorithm:
    1. Distribute mains by role (tank → healer → rdps → mdps)
    2. Distribute alts by role (same order)
    3. Fill remaining slots with helpers
    4. Hard cap at group_size per group
    """
    
    def __init__(self, wow_db):
        self.db = wow_db
        self.role_priority = ['tank', 'healer', 'rdps', 'mdps']
        self.group_priority = ['main', 'alt', 'helper', 'inactive']
    
    def create_groups(self, num_groups: int = 3, group_size: int = 30, character_locks: List[Dict] = None) -> List[SimpleGroup]:
        """
        Create raid groups using simple distribution logic
        
        Args:
            num_groups: Number of groups to create
            group_size: Maximum characters per group (hard cap)
            character_locks: List of locked character assignments
            
        Returns:
            List of SimpleGroup objects
        """
        logger.info(f"🎯 Creating {num_groups} groups with max {group_size} characters each")
        
        # Process character locks
        locks_map = {}
        if character_locks:
            for lock in character_locks:
                locks_map[lock['characterName']] = lock['groupId']
            logger.info(f"🔒 Processing {len(locks_map)} character locks")
        
        # Get all characters organized by priority
        all_characters = self._get_all_characters()
        
        # Apply locks to characters
        for char in all_characters:
            if char.name in locks_map:
                char.is_locked = True
                char.locked_to_group = locks_map[char.name]
                logger.info(f"🔒 {char.name} locked to Group {char.locked_to_group}")
        
        characters_by_priority = self._organize_by_priority(all_characters)
        
        # Initialize empty groups
        groups = [SimpleGroup(group_id=i+1, max_size=group_size) for i in range(num_groups)]
        
        # Apply locked character assignments first
        self._apply_locked_assignments(groups, all_characters)
        
        # Phase 1: Distribute mains by role
        logger.info("📋 Phase 1: Distributing main characters")
        self._distribute_priority_group(groups, characters_by_priority.get('main', []))
        
        # Phase 2: Distribute alts by role  
        logger.info("📋 Phase 2: Distributing alt characters")
        self._distribute_priority_group(groups, characters_by_priority.get('alt', []))
        
        # Phase 3: Fill remaining slots with helpers
        logger.info("📋 Phase 3: Filling with helper characters")
        self._distribute_priority_group(groups, characters_by_priority.get('helper', []))
        
        # Phase 4: Fill any remaining slots with inactive characters
        logger.info("📋 Phase 4: Adding inactive characters if space available")
        self._distribute_priority_group(groups, characters_by_priority.get('inactive', []))
        
        # Log final results
        self._log_final_results(groups)
        
        return groups
    
    def _get_all_characters(self) -> List[SimpleCharacter]:
        """Get all characters from database as SimpleCharacter objects"""
        try:
            # Pipeline using the exact field names from debug output
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
                        "localField": "spec_id",  # Characters have spec_id
                        "foreignField": "spec_id",  # Specs have spec_id
                        "as": "spec_info"
                    }
                },
                {"$unwind": "$class_info"},
                {"$unwind": "$spec_info"},
                {
                    "$project": {
                        "name": 1,
                        "player_id": {"$toString": "$player_id"},  # Convert ObjectId to string
                        "class_id": 1,
                        "spec_id": 1,
                        "role_group": 1,  # Characters have role_group
                        "class_name": "$class_info.class_name",
                        "spec_name": "$spec_info.spec_name",
                        "role_raid": "$spec_info.role_raid",  # Get role from specs
                        "armor_type": "$class_info.armor_type",
                        "tier_token": "$class_info.tier_token",
                        "raid_buff_ids": {"$ifNull": ["$class_info.raid_buff_ids", []]}
                    }
                }
            ]
            
            logger.info("🔍 Running character aggregation pipeline...")
            
            # First, let's test each step of the pipeline
            logger.info("Testing aggregation steps...")
            
            # Step 1: Get raw characters
            raw_chars = list(self.db.characters.find().limit(3))
            logger.info(f"📊 Raw characters sample: {len(raw_chars)} found")
            for i, char in enumerate(raw_chars):
                logger.info(f"  {i+1}. {char.get('name', 'Unknown')} - spec_id: {char.get('spec_id', 'Missing')}")
            
            # Step 2: Test class lookup
            test_class_lookup = list(self.db.characters.aggregate([
                {"$lookup": {"from": "classes", "localField": "class_id", "foreignField": "class_id", "as": "class_info"}},
                {"$limit": 1}
            ]))
            logger.info(f"📊 Class lookup test: {len(test_class_lookup)} results")
            if test_class_lookup:
                logger.info(f"  Class info found: {len(test_class_lookup[0].get('class_info', []))} classes")
            
            # Step 3: Test spec lookup  
            test_spec_lookup = list(self.db.characters.aggregate([
                {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec_info"}},
                {"$limit": 1}
            ]))
            logger.info(f"📊 Spec lookup test: {len(test_spec_lookup)} results")
            if test_spec_lookup:
                logger.info(f"  Spec info found: {len(test_spec_lookup[0].get('spec_info', []))} specs")
                if test_spec_lookup[0].get('spec_info'):
                    logger.info(f"  Sample spec: {test_spec_lookup[0]['spec_info'][0]}")
            
            # Now run the full pipeline
            char_results = list(self.db.characters.aggregate(pipeline))
            logger.info(f"📊 Full pipeline returned {len(char_results)} character records")
            
            if not char_results:
                logger.error("❌ No characters returned from database!")
                # Let's try a simple query to see what's in the characters collection
                simple_count = self.db.characters.count_documents({})
                logger.info(f"📊 Simple count shows {simple_count} characters in collection")
                return []
            
            characters = []
            for i, char_data in enumerate(char_results):
                try:
                    logger.info(f"🔍 Processing character {i+1}: {char_data.get('name', 'Unknown')}")
                    character = SimpleCharacter(
                        name=char_data['name'],
                        player_id=char_data['player_id'],
                        class_id=char_data['class_id'],
                        class_name=char_data.get('class_name', ''),
                        spec_id=char_data['spec_id'],  # Back to spec_id
                        spec_name=char_data.get('spec_name', ''),
                        role_raid=char_data.get('role_raid', ''),
                        role_group=char_data['role_group'],  # Back to role_group
                        armor_type=char_data.get('armor_type', ''),
                        tier_token=char_data.get('tier_token', ''),
                        raid_buff_ids=char_data.get('raid_buff_ids', [])
                    )
                    characters.append(character)
                    
                    if i < 3:  # Log first few characters for debugging
                        logger.info(f"   ✅ Created: {character.name} ({character.role_raid} {character.role_group})")
                        
                except KeyError as e:
                    logger.error(f"❌ Missing field in character data: {e}")
                    logger.error(f"   Character data: {char_data}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error creating character from data: {e}")
                    logger.error(f"   Character data: {char_data}")
                    continue
            
            logger.info(f"✅ Successfully created {len(characters)} character objects")
            
            # Log role distribution for debugging
            role_counts = {}
            priority_counts = {}
            for char in characters:
                role_counts[char.role_raid] = role_counts.get(char.role_raid, 0) + 1
                priority_counts[char.role_group] = priority_counts.get(char.role_group, 0) + 1
            
            logger.info(f"📊 Role distribution: {role_counts}")
            logger.info(f"📊 Priority distribution: {priority_counts}")
            
            return characters
            
        except Exception as e:
            logger.error(f"❌ Error loading characters: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _organize_by_priority(self, characters: List[SimpleCharacter]) -> Dict[str, List[SimpleCharacter]]:
        """Organize characters by priority group"""
        organized = defaultdict(list)
        
        for char in characters:
            organized[char.role_group].append(char)
        
        # Log distribution
        for priority in self.group_priority:
            count = len(organized[priority])
            logger.info(f"   {priority}: {count} characters")
            
        return dict(organized)
    
    def _apply_locked_assignments(self, groups: List[SimpleGroup], all_characters: List[SimpleCharacter]):
        """Apply any locked character assignments (future feature)"""
        locked_chars = [char for char in all_characters if char.is_locked]
        
        if not locked_chars:
            return
            
        logger.info(f"🔒 Applying {len(locked_chars)} locked character assignments")
        
        for char in locked_chars:
            if char.locked_to_group and 1 <= char.locked_to_group <= len(groups):
                target_group = groups[char.locked_to_group - 1]
                if target_group.add_character(char):
                    logger.info(f"   🔒 {char.name} locked to Group {char.locked_to_group}")
                else:
                    logger.warning(f"   ⚠️ Could not lock {char.name} to Group {char.locked_to_group}")
    
    def _distribute_priority_group(self, groups: List[SimpleGroup], characters: List[SimpleCharacter]):
        """Distribute characters of a specific priority by role"""
        if not characters:
            return
            
        # Organize by role
        chars_by_role = defaultdict(list)
        for char in characters:
            # Skip if already assigned (locked characters)
            if any(char in group.characters for group in groups):
                continue
            chars_by_role[char.role_raid].append(char)
        
        # Distribute each role in priority order
        for role in self.role_priority:
            role_chars = chars_by_role[role]
            if role_chars:
                self._distribute_role_round_robin(groups, role_chars, role)
    
    def _distribute_role_round_robin(self, groups: List[SimpleGroup], characters: List[SimpleCharacter], role: str):
        """Distribute characters of a specific role using round-robin with randomization"""
        if not characters:
            return
            
        logger.info(f"   Distributing {len(characters)} {role} characters")
        
        # Randomize the order of characters to add variance
        shuffled_characters = characters.copy()
        random.shuffle(shuffled_characters)
        
        # Sort groups by current size (fill smaller groups first), then randomize ties
        available_groups = sorted(groups, key=lambda g: (len(g.characters), random.random()))
        
        assigned_count = 0
        group_index = 0
        
        for char in shuffled_characters:
            # Skip if already assigned (locked characters)
            if any(char in group.characters for group in groups):
                continue
                
            attempts = 0
            assigned = False
            
            # Try to assign to groups, starting from current index
            while attempts < len(available_groups) and not assigned:
                group = available_groups[group_index]
                
                if group.add_character(char):
                    logger.info(f"     ✅ {char.name} → Group {group.group_id}")
                    assigned = True
                    assigned_count += 1
                
                # Move to next group
                group_index = (group_index + 1) % len(available_groups)
                attempts += 1
            
            if not assigned:
                logger.warning(f"     ⚠️ Could not assign {char.name} - groups may be full")
        
        logger.info(f"   📊 Assigned {assigned_count}/{len(characters)} {role} characters")
    
    def _log_final_results(self, groups: List[SimpleGroup]):
        """Log final group composition"""
        logger.info("\n📊 Final Group Composition:")
        
        total_chars = 0
        for group in groups:
            role_counts = group.get_role_counts()
            priority_counts = group.get_priority_counts()
            
            tanks = role_counts.get('tank', 0)
            healers = role_counts.get('healer', 0) 
            mdps = role_counts.get('mdps', 0)
            rdps = role_counts.get('rdps', 0)
            
            mains = priority_counts.get('main', 0)
            alts = priority_counts.get('alt', 0)
            helpers = priority_counts.get('helper', 0)
            
            logger.info(f"   Group {group.group_id}: {len(group.characters)}/{group.max_size} members")
            logger.info(f"     Roles: {tanks}T / {healers}H / {mdps}M / {rdps}R")
            logger.info(f"     Priority: {mains} mains, {alts} alts, {helpers} helpers")
            
            total_chars += len(group.characters)
        
        logger.info(f"\n✅ Successfully distributed {total_chars} characters across {len(groups)} groups")
    
    def groups_to_dict(self, groups: List[SimpleGroup]) -> List[Dict]:
        """Convert groups to dictionary format for API responses"""
        result = []
        
        for group in groups:
            role_counts = group.get_role_counts()
            priority_counts = group.get_priority_counts()
            
            # Get distributions for MAINS ONLY
            mains_armor_dist = group.get_armor_distribution(mains_only=True)
            mains_tier_dist = group.get_tier_distribution(mains_only=True)
            
            group_dict = {
                'group_id': group.group_id,
                'total_members': len(group.characters),
                'tanks': role_counts.get('tank', 0),
                'healers': role_counts.get('healer', 0),
                'dps': role_counts.get('mdps', 0) + role_counts.get('rdps', 0),
                'mains_count': priority_counts.get('main', 0),
                'priority_score': self._calculate_priority_score(group),
                'variable_1': priority_counts.get('main', 0),  # Main count for display
                'variable_2': len(group.characters),  # Total count for display
                
                # Add armor and tier distributions for mains
                'armor_distribution_mains': mains_armor_dist,
                'tier_distribution_mains': mains_tier_dist,
                
                # Keep all distributions for backwards compatibility
                'armor_distribution': group.get_armor_distribution(),
                'tier_distribution': group.get_tier_distribution(),
                
                'characters': [
                    {
                        'name': char.name,
                        'class_name': char.class_name,
                        'spec_name': char.spec_name,
                        'role_raid': char.role_raid,
                        'role_group': char.role_group,
                        'armor_type': char.armor_type,
                        'tier_token': char.tier_token,
                        'buffs': char.raid_buff_ids,
                        'is_locked': char.is_locked  # Include lock status
                    }
                    for char in group.characters
                ]
            }
            result.append(group_dict)
        
        return result
    
    def _calculate_priority_score(self, group: SimpleGroup) -> float:
        """Calculate priority score for group"""
        priority_counts = group.get_priority_counts()
        
        main_count = priority_counts.get('main', 0)
        alt_count = priority_counts.get('alt', 0)
        helper_count = priority_counts.get('helper', 0)
        
        return (main_count * 3) + (alt_count * 2) + (helper_count * 1)

# Convenience function for easy integration
def create_simple_raid_groups(db, num_groups: int = 3, group_size: int = 30) -> List[Dict]:
    """
    Simple function to create raid groups
    
    Args:
        db: Database connection
        num_groups: Number of groups to create (default: 3)
        group_size: Maximum size per group (default: 30)
        
    Returns:
        List of group dictionaries ready for API response
    """
    splitter = SimpleRaidSplitter(db)
    groups = splitter.create_groups(num_groups, group_size)
    return splitter.groups_to_dict(groups)