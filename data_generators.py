"""
Mock Data Generators for WoW Roster Testing
Multiple data generation strategies for different testing scenarios
"""

import random
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self, db):
        self.db = db
        
        # Character name pools (max 12 characters per schema)
        self.character_names = [
            'Thunder', 'Shadow', 'Frost', 'Flame', 'Moon',
            'Storm', 'Night', 'Ice', 'Fire', 'Dark',
            'Light', 'Wild', 'Blood', 'Star', 'Iron',
            'Mystic', 'Ash', 'Void', 'Sun', 'Grim',
            'Swift', 'Earth', 'Dream', 'Soul', 'Bright',
            'Wind', 'Steel', 'Red', 'Green', 'Blue',
            'Gold', 'Silver', 'White', 'Black', 'Thorn',
            'Bone', 'Mind', 'Spirit', 'Rune', 'Crystal',
            'Peace', 'War', 'Life', 'Death', 'Spell'
        ]
    
    def generate_raid_ready_roster(self, num_players=40, target_characters=90):
        """
        Generate a raid-ready roster with proper role distribution
        Optimized for 3x30-person raid groups
        """
        logger.info(f"🎯 Generating raid-ready roster: {num_players} players, {target_characters} characters")
        
        # Clear existing character data but keep static data
        self.db.clear_character_data()
        
        # Get available specs by role
        specs_by_role = self.db.get_available_specs_by_role()
        
        # Target distribution for 3 raid groups (90 characters total)
        # 6 tanks (2 per group), 15 healers (5 per group), 69 DPS
        player_templates = [
            # Tank players (2 players, 3 tank chars each = 6 tanks)
            {"name": "Tank Master Alex", "discord": "TankMaster#0001", "role": "tank", "char_count": 3},
            {"name": "Shield Wall Sarah", "discord": "ShieldWall#0002", "role": "tank", "char_count": 3},
            
            # Healer players (5 players, 3 healer chars each = 15 healers)
            {"name": "Holy Light Emma", "discord": "HolyLight#0003", "role": "healer", "char_count": 3},
            {"name": "Natures Grace Mike", "discord": "NaturesGrace#0004", "role": "healer", "char_count": 3},
            {"name": "Divine Spirit Lisa", "discord": "DivineSpirit#0005", "role": "healer", "char_count": 3},
            {"name": "Restoration Tom", "discord": "Restoration#0006", "role": "healer", "char_count": 3},
            {"name": "Sacred Flame Rachel", "discord": "SacredFlame#0007", "role": "healer", "char_count": 3},
        ]
        
        # Generate DPS player templates (remaining 33 players)
        dps_base_names = [
            "Fire Storm", "Shadow Strike", "Frost Bolt", "Lightning Strike", "Arcane Power",
            "Chaos Bolt", "Hunters Mark", "Stealth Blade", "Storm Strike", "Wild Hunt",
            "Death Coil", "Demon Blade", "Dragon Fire", "Phoenix Rise", "Thunder Clap",
            "Ice Shard", "Void Walker", "Star Fall", "Blood Moon", "Solar Beam",
            "Wind Slash", "Earth Quake", "Time Warp", "Spirit Bond", "Flame Lance",
            "Dark Ritual", "Light Beam", "Storm Guard", "Frost Guard", "Fire Guard",
            "Shadow Guard", "Nature Guard", "Arcane Guard"
        ]
        
        # Add DPS players
        for i, base_name in enumerate(dps_base_names):
            player_templates.append({
                "name": f"{base_name} {chr(65 + (i % 26))}",  # Add letter suffix
                "discord": f"{base_name.replace(' ', '')}#{8 + i:04d}",
                "role": "dps",
                "char_count": random.randint(2, 3)  # 2-3 characters each
            })
        
        return self._generate_from_templates(player_templates, specs_by_role)
    
    def generate_small_test_roster(self, num_players=15, target_characters=30):
        """Generate a smaller roster for testing - 1 raid group worth"""
        logger.info(f"🧪 Generating small test roster: {num_players} players, {target_characters} characters")
        
        self.db.clear_character_data()
        specs_by_role = self.db.get_available_specs_by_role()
        
        player_templates = [
            # Tank players
            {"name": "Test Tank Alpha", "discord": "TestTank#0001", "role": "tank", "char_count": 2},
            
            # Healer players
            {"name": "Test Healer Beta", "discord": "TestHealer#0002", "role": "healer", "char_count": 3},
            {"name": "Test Healer Gamma", "discord": "TestHealer#0003", "role": "healer", "char_count": 2},
            
            # DPS players
            {"name": "Test DPS Delta", "discord": "TestDPS#0004", "role": "dps", "char_count": 2},
            {"name": "Test DPS Echo", "discord": "TestDPS#0005", "role": "dps", "char_count": 2},
            {"name": "Test DPS Foxtrot", "discord": "TestDPS#0006", "role": "dps", "char_count": 2},
            {"name": "Test DPS Golf", "discord": "TestDPS#0007", "role": "dps", "char_count": 2},
            {"name": "Test DPS Hotel", "discord": "TestDPS#0008", "role": "dps", "char_count": 2},
            {"name": "Test DPS India", "discord": "TestDPS#0009", "role": "dps", "char_count": 2},
            {"name": "Test DPS Juliet", "discord": "TestDPS#0010", "role": "dps", "char_count": 2},
            {"name": "Test DPS Kilo", "discord": "TestDPS#0011", "role": "dps", "char_count": 2},
            {"name": "Test DPS Lima", "discord": "TestDPS#0012", "role": "dps", "char_count": 2},
            {"name": "Test DPS Mike", "discord": "TestDPS#0013", "role": "dps", "char_count": 2},
            {"name": "Test DPS November", "discord": "TestDPS#0014", "role": "dps", "char_count": 2},
            {"name": "Test DPS Oscar", "discord": "TestDPS#0015", "role": "dps", "char_count": 1},
        ]
        
        return self._generate_from_templates(player_templates, specs_by_role)
    
    def generate_imbalanced_roster(self, num_players=25, target_characters=50):
        """Generate an intentionally imbalanced roster to test edge cases"""
        logger.info(f"⚠️ Generating imbalanced roster: {num_players} players, {target_characters} characters")
        
        self.db.clear_character_data()
        specs_by_role = self.db.get_available_specs_by_role()
        
        player_templates = [
            # Too few tanks
            {"name": "Lonely Tank", "discord": "LonelyTank#0001", "role": "tank", "char_count": 2},
            
            # Lots of healers
            {"name": "Healer Army Alpha", "discord": "HealerArmy#0001", "role": "healer", "char_count": 4},
            {"name": "Healer Army Beta", "discord": "HealerArmy#0002", "role": "healer", "char_count": 4},
            {"name": "Healer Army Gamma", "discord": "HealerArmy#0003", "role": "healer", "char_count": 4},
            {"name": "Healer Army Delta", "discord": "HealerArmy#0004", "role": "healer", "char_count": 4},
            {"name": "Healer Army Echo", "discord": "HealerArmy#0005", "role": "healer", "char_count": 4},
        ]
        
        # Add many DPS players with varying character counts
        for i in range(20):
            player_templates.append({
                "name": f"DPS Swarm {i+1}",
                "discord": f"DPSSwarm#{i+1:04d}",
                "role": "dps",
                "char_count": random.randint(1, 3)
            })
        
        return self._generate_from_templates(player_templates, specs_by_role)
    
    def _generate_from_templates(self, player_templates: List[Dict], specs_by_role: Dict) -> Dict:
        """Generate players and characters from templates"""
        used_names = set()
        total_characters_created = 0
        
        for i, template in enumerate(player_templates):
            # Create player following exact schema
            player = {
                "displayName": template["name"],
                "discordTag": template["discord"],
                "discordId": f"{2000000000000000000 + i}",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            player_result = self.db.players.insert_one(player)
            player_id = player_result.inserted_id
            
            # Determine character specs based on player role
            player_role = template["role"]
            char_count = template["char_count"]
            
            if player_role == "tank":
                char_specs = random.sample(specs_by_role['tank'], min(char_count, len(specs_by_role['tank'])))
                if len(char_specs) < char_count:
                    char_specs.extend(random.choices(specs_by_role['tank'], k=char_count - len(char_specs)))
                role_groups = ["main"] + ["alt"] * (char_count - 1)
                
            elif player_role == "healer":
                char_specs = random.sample(specs_by_role['healer'], min(char_count, len(specs_by_role['healer'])))
                if len(char_specs) < char_count:
                    char_specs.extend(random.choices(specs_by_role['healer'], k=char_count - len(char_specs)))
                role_groups = ["main"] + ["alt"] * (char_count - 1)
                
            else:  # DPS
                # Mix of melee and ranged DPS
                all_dps_specs = specs_by_role['mdps'] + specs_by_role['rdps']
                char_specs = random.choices(all_dps_specs, k=char_count)
                
                # Mix of priorities for DPS
                if char_count == 1:
                    role_groups = ["main"]
                elif char_count == 2:
                    role_groups = ["main", "alt"]
                elif char_count == 3:
                    role_groups = ["main", "alt", "helper"]
                else:
                    role_groups = ["main", "alt"] + ["helper"] * (char_count - 2)
            
            logger.info(f"👤 Creating {template['name']} ({player_role}) - {char_count} characters")
            
            # Create characters following exact schema
            for j in range(char_count):
                # Get unique character name (max 12 chars per schema)
                char_name = self._get_unique_character_name(used_names, template["name"], j)
                used_names.add(char_name)
                
                # Select class and spec
                class_id, spec_id = char_specs[j]
                group = role_groups[j] if j < len(role_groups) else "helper"
                
                # Character follows exact schema
                character = {
                    "name": char_name,
                    "player_id": str(player_id),  # Convert ObjectId to string
                    "group": group,  # Using "group" not "role_group" per schema
                    "class_id": class_id,
                    "spec": spec_id  # Using "spec" not "spec_id" per schema
                }
                
                self.db.characters.insert_one(character)
                total_characters_created += 1
                
                # Log character creation
                logger.info(f"   ✅ {char_name} ({class_id} - {spec_id}) [{group}]")
        
        # Calculate final statistics
        stats = self._calculate_final_stats(total_characters_created)
        return stats
    
    def _get_unique_character_name(self, used_names: set, player_name: str, char_index: int) -> str:
        """Generate a unique character name (max 12 characters per schema)"""
        # Try random names first
        attempts = 0
        while attempts < 50:
            char_name = random.choice(self.character_names)
            if char_name not in used_names and len(char_name) <= 12:
                return char_name
            attempts += 1
        
        # Fallback to player-based names
        base_name = player_name.split()[0][:8]  # Ensure space for number
        return f"{base_name}{char_index + 1}"
    
    def _calculate_final_stats(self, total_characters: int) -> Dict:
        """Calculate and log final statistics"""
        # Count characters by role using the correct field names
        tank_pipeline = [
            {"$lookup": {"from": "specs", "localField": "spec", "foreignField": "spec_id", "as": "spec_info"}},
            {"$unwind": "$spec_info"},
            {"$match": {"spec_info.role_raid": "tank"}},
            {"$count": "tanks"}
        ]
        tank_count = list(self.db.characters.aggregate(tank_pipeline))
        tank_total = tank_count[0]["tanks"] if tank_count else 0
        
        healer_pipeline = [
            {"$lookup": {"from": "specs", "localField": "spec", "foreignField": "spec_id", "as": "spec_info"}},
            {"$unwind": "$spec_info"},
            {"$match": {"spec_info.role_raid": "healer"}},
            {"$count": "healers"}
        ]
        healer_count = list(self.db.characters.aggregate(healer_pipeline))
        healer_total = healer_count[0]["healers"] if healer_count else 0
        
        dps_total = total_characters - tank_total - healer_total
        player_total = self.db.players.count_documents({})
        
        stats = {
            "players": player_total,
            "characters": total_characters,
            "tanks": tank_total,
            "healers": healer_total,
            "dps": dps_total
        }
        
        logger.info(f"\n📊 Generation Summary:")
        logger.info(f"   Total Players: {player_total}")
        logger.info(f"   Total Characters: {total_characters}")
        logger.info(f"   Tank Characters: {tank_total}")
        logger.info(f"   Healer Characters: {healer_total}")
        logger.info(f"   DPS Characters: {dps_total}")
        
        return stats

# Convenience functions for different data scenarios
def generate_raid_roster(db):
    """Generate the standard raid-ready roster"""
    generator = DataGenerator(db)
    return generator.generate_raid_ready_roster()

def generate_test_roster(db):
    """Generate a small test roster"""
    generator = DataGenerator(db)
    return generator.generate_small_test_roster()

def generate_stress_test_roster(db):
    """Generate an imbalanced roster for edge case testing"""
    generator = DataGenerator(db)
    return generator.generate_imbalanced_roster()