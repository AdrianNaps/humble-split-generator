"""
Database Structure and Schema Setup
Handles MongoDB collections, static data, and core database operations
"""

from pymongo import MongoClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WoWRosterDB:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        """Initialize MongoDB connection and collections"""
        self.client = MongoClient(connection_string)
        self.db = self.client['wow_roster']
        
        # Define collections
        self.players = self.db.players
        self.characters = self.db.characters
        self.classes = self.db.classes
        self.specs = self.db.specs
        self.raid_buffs = self.db.raid_buffs
    
    def clear_all_collections(self):
        """Clear all collections (but keep the database structure)"""
        logger.info("🗑️ Clearing all collections...")
        self.db.drop_collection('players')
        self.db.drop_collection('characters')
        self.db.drop_collection('classes')
        self.db.drop_collection('specs')
        self.db.drop_collection('raid_buffs')
        logger.info("✅ All collections cleared!")
    
    def clear_character_data(self):
        """Clear only players and characters (keep static data)"""
        logger.info("🗑️ Clearing player and character data...")
        self.db.drop_collection('players')
        self.db.drop_collection('characters')
        logger.info("✅ Player and character data cleared!")
    
    def setup_static_data(self):
        """Set up classes, specs, and raid buffs - the core game data"""
        logger.info("📊 Setting up static WoW data...")
        
        # Raid Buffs - Required for optimal group composition
        raid_buffs = [
            {"buff_id": "arcane_intellect", "name": "Arcane Intellect", "required": True},
            {"buff_id": "battle_shout", "name": "Battle Shout", "required": True},
            {"buff_id": "mark_of_the_wild", "name": "Mark of the Wild", "required": True},
            {"buff_id": "power_word_fortitude", "name": "Power Word: Fortitude", "required": True},
            {"buff_id": "mystic_touch", "name": "Mystic Touch", "required": True},
            {"buff_id": "chaos_brand", "name": "Chaos Brand", "required": True},
            {"buff_id": "hunters_mark", "name": "Hunter's Mark", "required": True},
            {"buff_id": "atrophic_poison", "name": "Atrophic Poison", "required": True},
            {"buff_id": "windfury_totem", "name": "Windfury Totem", "required": False},
            {"buff_id": "blessing_of_the_bronze", "name": "Blessing of the Bronze", "required": False},
            {"buff_id": "skyfury", "name": "Skyfury", "required": True}
        ]
        self.raid_buffs.insert_many(raid_buffs)
        
        # Classes with armor types, tier tokens, and buffs provided
        classes = [
            {"class_id": "death_knight", "class_name": "Death Knight", "armor_type": "plate", "tier_token": "Dreadful", "raid_buff_ids": []},
            {"class_id": "demon_hunter", "class_name": "Demon Hunter", "armor_type": "leather", "tier_token": "Venerated", "raid_buff_ids": ["chaos_brand"]},
            {"class_id": "druid", "class_name": "Druid", "armor_type": "leather", "tier_token": "Venerated", "raid_buff_ids": ["mark_of_the_wild"]},
            {"class_id": "evoker", "class_name": "Evoker", "armor_type": "mail", "tier_token": "Zenith", "raid_buff_ids": ["blessing_of_the_bronze"]},
            {"class_id": "hunter", "class_name": "Hunter", "armor_type": "mail", "tier_token": "Zenith", "raid_buff_ids": ["hunters_mark"]},
            {"class_id": "mage", "class_name": "Mage", "armor_type": "cloth", "tier_token": "Mystic", "raid_buff_ids": ["arcane_intellect"]},
            {"class_id": "monk", "class_name": "Monk", "armor_type": "leather", "tier_token": "Venerated", "raid_buff_ids": ["mystic_touch"]},
            {"class_id": "paladin", "class_name": "Paladin", "armor_type": "plate", "tier_token": "Dreadful", "raid_buff_ids": []},
            {"class_id": "priest", "class_name": "Priest", "armor_type": "cloth", "tier_token": "Mystic", "raid_buff_ids": ["power_word_fortitude"]},
            {"class_id": "rogue", "class_name": "Rogue", "armor_type": "leather", "tier_token": "Venerated", "raid_buff_ids": ["atrophic_poison"]},
            {"class_id": "shaman", "class_name": "Shaman", "armor_type": "mail", "tier_token": "Zenith", "raid_buff_ids": ["windfury_totem", "skyfury"]},
            {"class_id": "warlock", "class_name": "Warlock", "armor_type": "cloth", "tier_token": "Mystic", "raid_buff_ids": []},
            {"class_id": "warrior", "class_name": "Warrior", "armor_type": "plate", "tier_token": "Dreadful", "raid_buff_ids": ["battle_shout"]}
        ]
        self.classes.insert_many(classes)
        
        # Specializations with their roles and main stats
        specs = [
            # Death Knight
            {"spec_id": "death_knight_blood", "spec_name": "Blood", "class_id": "death_knight", "role_raid": "tank", "main_stat": "str"},
            {"spec_id": "death_knight_frost", "spec_name": "Frost", "class_id": "death_knight", "role_raid": "mdps", "main_stat": "str"},
            {"spec_id": "death_knight_unholy", "spec_name": "Unholy", "class_id": "death_knight", "role_raid": "mdps", "main_stat": "str"},
            
            # Demon Hunter
            {"spec_id": "demon_hunter_havoc", "spec_name": "Havoc", "class_id": "demon_hunter", "role_raid": "mdps", "main_stat": "agi"},
            {"spec_id": "demon_hunter_vengeance", "spec_name": "Vengeance", "class_id": "demon_hunter", "role_raid": "tank", "main_stat": "agi"},
            
            # Druid
            {"spec_id": "druid_balance", "spec_name": "Balance", "class_id": "druid", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "druid_feral", "spec_name": "Feral", "class_id": "druid", "role_raid": "mdps", "main_stat": "agi"},
            {"spec_id": "druid_guardian", "spec_name": "Guardian", "class_id": "druid", "role_raid": "tank", "main_stat": "agi"},
            {"spec_id": "druid_restoration", "spec_name": "Restoration", "class_id": "druid", "role_raid": "healer", "main_stat": "int"},
            
            # Evoker
            {"spec_id": "evoker_devastation", "spec_name": "Devastation", "class_id": "evoker", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "evoker_preservation", "spec_name": "Preservation", "class_id": "evoker", "role_raid": "healer", "main_stat": "int"},
            {"spec_id": "evoker_augmentation", "spec_name": "Augmentation", "class_id": "evoker", "role_raid": "rdps", "main_stat": "int"},
            
            # Hunter
            {"spec_id": "hunter_beast_mastery", "spec_name": "Beast Mastery", "class_id": "hunter", "role_raid": "rdps", "main_stat": "agi"},
            {"spec_id": "hunter_marksmanship", "spec_name": "Marksmanship", "class_id": "hunter", "role_raid": "rdps", "main_stat": "agi"},
            {"spec_id": "hunter_survival", "spec_name": "Survival", "class_id": "hunter", "role_raid": "mdps", "main_stat": "agi"},
            
            # Mage
            {"spec_id": "mage_arcane", "spec_name": "Arcane", "class_id": "mage", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "mage_fire", "spec_name": "Fire", "class_id": "mage", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "mage_frost", "spec_name": "Frost", "class_id": "mage", "role_raid": "rdps", "main_stat": "int"},
            
            # Monk
            {"spec_id": "monk_brewmaster", "spec_name": "Brewmaster", "class_id": "monk", "role_raid": "tank", "main_stat": "agi"},
            {"spec_id": "monk_mistweaver", "spec_name": "Mistweaver", "class_id": "monk", "role_raid": "healer", "main_stat": "int"},
            {"spec_id": "monk_windwalker", "spec_name": "Windwalker", "class_id": "monk", "role_raid": "mdps", "main_stat": "agi"},
            
            # Paladin
            {"spec_id": "paladin_holy", "spec_name": "Holy", "class_id": "paladin", "role_raid": "healer", "main_stat": "int"},
            {"spec_id": "paladin_protection", "spec_name": "Protection", "class_id": "paladin", "role_raid": "tank", "main_stat": "str"},
            {"spec_id": "paladin_retribution", "spec_name": "Retribution", "class_id": "paladin", "role_raid": "mdps", "main_stat": "str"},
            
            # Priest
            {"spec_id": "priest_discipline", "spec_name": "Discipline", "class_id": "priest", "role_raid": "healer", "main_stat": "int"},
            {"spec_id": "priest_holy", "spec_name": "Holy", "class_id": "priest", "role_raid": "healer", "main_stat": "int"},
            {"spec_id": "priest_shadow", "spec_name": "Shadow", "class_id": "priest", "role_raid": "rdps", "main_stat": "int"},
            
            # Rogue
            {"spec_id": "rogue_assassination", "spec_name": "Assassination", "class_id": "rogue", "role_raid": "mdps", "main_stat": "agi"},
            {"spec_id": "rogue_outlaw", "spec_name": "Outlaw", "class_id": "rogue", "role_raid": "mdps", "main_stat": "agi"},
            {"spec_id": "rogue_subtlety", "spec_name": "Subtlety", "class_id": "rogue", "role_raid": "mdps", "main_stat": "agi"},
            
            # Shaman
            {"spec_id": "shaman_elemental", "spec_name": "Elemental", "class_id": "shaman", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "shaman_enhancement", "spec_name": "Enhancement", "class_id": "shaman", "role_raid": "mdps", "main_stat": "agi"},
            {"spec_id": "shaman_restoration", "spec_name": "Restoration", "class_id": "shaman", "role_raid": "healer", "main_stat": "int"},
            
            # Warlock
            {"spec_id": "warlock_affliction", "spec_name": "Affliction", "class_id": "warlock", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "warlock_demonology", "spec_name": "Demonology", "class_id": "warlock", "role_raid": "rdps", "main_stat": "int"},
            {"spec_id": "warlock_destruction", "spec_name": "Destruction", "class_id": "warlock", "role_raid": "rdps", "main_stat": "int"},
            
            # Warrior
            {"spec_id": "warrior_arms", "spec_name": "Arms", "class_id": "warrior", "role_raid": "mdps", "main_stat": "str"},
            {"spec_id": "warrior_fury", "spec_name": "Fury", "class_id": "warrior", "role_raid": "mdps", "main_stat": "str"},
            {"spec_id": "warrior_protection", "spec_name": "Protection", "class_id": "warrior", "role_raid": "tank", "main_stat": "str"}
        ]
        self.specs.insert_many(specs)
        
        logger.info(f"✅ Created {len(raid_buffs)} raid buffs")
        logger.info(f"✅ Created {len(classes)} classes")
        logger.info(f"✅ Created {len(specs)} specs")
    
    def get_available_specs_by_role(self):
        """Get specs organized by role - useful for data generation"""
        specs = list(self.specs.find())
        
        organized = {
            'tank': [],
            'healer': [],
            'mdps': [],
            'rdps': []
        }
        
        for spec in specs:
            role = spec['role_raid']
            if role in organized:
                organized[role].append((spec['class_id'], spec['spec_id']))
        
        return organized
    
    def initialize_schema(self):
        """Initialize the database schema with static data"""
        logger.info("🚀 Initializing WoW Roster Database Schema...")
        self.clear_all_collections()
        self.setup_static_data()
        logger.info("✅ Database schema initialization complete!")
    
    def get_stats(self):
        """Get current database statistics"""
        return {
            "players": self.players.count_documents({}),
            "characters": self.characters.count_documents({}),
            "classes": self.classes.count_documents({}),
            "specs": self.specs.count_documents({}),
            "raid_buffs": self.raid_buffs.count_documents({})
        }