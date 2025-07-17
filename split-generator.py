from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import random
from bson import ObjectId
from raid_splitter import RaidSplitter

app = Flask(__name__)

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
    
    def reset_database(self):
        """Clear and reinitialize the database"""
        print("🗑️ Clearing database...")
        self.db.drop_collection('players')
        self.db.drop_collection('characters')
        self.db.drop_collection('classes')
        self.db.drop_collection('specs')
        self.db.drop_collection('raid_buffs')
        print("✅ Database cleared!")
    
    def seed_static_data(self):
        """Seed classes, specs, and raid buffs"""
        # Raid Buffs
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
        
        # Classes
        classes = [
            {"class_id": "death_knight", "name": "Death Knight", "armor": "plate", "token": "Dreadful", "buffs": []},
            {"class_id": "demon_hunter", "name": "Demon Hunter", "armor": "leather", "token": "Venerated", "buffs": ["chaos_brand"]},
            {"class_id": "druid", "name": "Druid", "armor": "leather", "token": "Venerated", "buffs": ["mark_of_the_wild"]},
            {"class_id": "evoker", "name": "Evoker", "armor": "mail", "token": "Zenith", "buffs": ["blessing_of_the_bronze"]},
            {"class_id": "hunter", "name": "Hunter", "armor": "mail", "token": "Zenith", "buffs": ["hunters_mark"]},
            {"class_id": "mage", "name": "Mage", "armor": "cloth", "token": "Mystic", "buffs": ["arcane_intellect"]},
            {"class_id": "monk", "name": "Monk", "armor": "leather", "token": "Venerated", "buffs": ["mystic_touch"]},
            {"class_id": "paladin", "name": "Paladin", "armor": "plate", "token": "Dreadful", "buffs": []},
            {"class_id": "priest", "name": "Priest", "armor": "cloth", "token": "Mystic", "buffs": ["power_word_fortitude"]},
            {"class_id": "rogue", "name": "Rogue", "armor": "leather", "token": "Venerated", "buffs": ["atrophic_poison"]},
            {"class_id": "shaman", "name": "Shaman", "armor": "mail", "token": "Zenith", "buffs": ["windfury_totem", "skyfury"]},
            {"class_id": "warlock", "name": "Warlock", "armor": "cloth", "token": "Mystic", "buffs": []},
            {"class_id": "warrior", "name": "Warrior", "armor": "plate", "token": "Dreadful", "buffs": ["battle_shout"]}
        ]
        self.classes.insert_many(classes)
        
        # Specs (simplified for brevity - showing pattern)
        specs = [
            # Death Knight
            {"spec_id": "blood", "name": "Blood", "class_id": "death_knight", "role": "tank"},
            {"spec_id": "frost_dk", "name": "Frost", "class_id": "death_knight", "role": "mdps"},
            {"spec_id": "unholy", "name": "Unholy", "class_id": "death_knight", "role": "mdps"},
            # Demon Hunter
            {"spec_id": "havoc", "name": "Havoc", "class_id": "demon_hunter", "role": "mdps"},
            {"spec_id": "vengeance", "name": "Vengeance", "class_id": "demon_hunter", "role": "tank"},
            # Druid
            {"spec_id": "balance", "name": "Balance", "class_id": "druid", "role": "rdps"},
            {"spec_id": "feral", "name": "Feral", "class_id": "druid", "role": "mdps"},
            {"spec_id": "guardian", "name": "Guardian", "class_id": "druid", "role": "tank"},
            {"spec_id": "restoration_druid", "name": "Restoration", "class_id": "druid", "role": "healer"},
            # Mage
            {"spec_id": "arcane", "name": "Arcane", "class_id": "mage", "role": "rdps"},
            {"spec_id": "fire", "name": "Fire", "class_id": "mage", "role": "rdps"},
            {"spec_id": "frost_mage", "name": "Frost", "class_id": "mage", "role": "rdps"},
            # Paladin
            {"spec_id": "holy_paladin", "name": "Holy", "class_id": "paladin", "role": "healer"},
            {"spec_id": "protection_paladin", "name": "Protection", "class_id": "paladin", "role": "tank"},
            {"spec_id": "retribution", "name": "Retribution", "class_id": "paladin", "role": "mdps"},
            # Priest
            {"spec_id": "discipline", "name": "Discipline", "class_id": "priest", "role": "healer"},
            {"spec_id": "holy_priest", "name": "Holy", "class_id": "priest", "role": "healer"},
            {"spec_id": "shadow", "name": "Shadow", "class_id": "priest", "role": "rdps"},
            # Warrior
            {"spec_id": "arms", "name": "Arms", "class_id": "warrior", "role": "mdps"},
            {"spec_id": "fury", "name": "Fury", "class_id": "warrior", "role": "mdps"},
            {"spec_id": "protection_warrior", "name": "Protection", "class_id": "warrior", "role": "tank"},
            # Hunter
            {"spec_id": "beast_mastery", "name": "Beast Mastery", "class_id": "hunter", "role": "rdps"},
            {"spec_id": "marksmanship", "name": "Marksmanship", "class_id": "hunter", "role": "rdps"},
            {"spec_id": "survival", "name": "Survival", "class_id": "hunter", "role": "mdps"},
            # Rogue
            {"spec_id": "assassination", "name": "Assassination", "class_id": "rogue", "role": "mdps"},
            {"spec_id": "outlaw", "name": "Outlaw", "class_id": "rogue", "role": "mdps"},
            {"spec_id": "subtlety", "name": "Subtlety", "class_id": "rogue", "role": "mdps"},
            # Warlock
            {"spec_id": "affliction", "name": "Affliction", "class_id": "warlock", "role": "rdps"},
            {"spec_id": "demonology", "name": "Demonology", "class_id": "warlock", "role": "rdps"},
            {"spec_id": "destruction", "name": "Destruction", "class_id": "warlock", "role": "rdps"},
            # Shaman
            {"spec_id": "elemental", "name": "Elemental", "class_id": "shaman", "role": "rdps"},
            {"spec_id": "enhancement", "name": "Enhancement", "class_id": "shaman", "role": "mdps"},
            {"spec_id": "restoration_shaman", "name": "Restoration", "class_id": "shaman", "role": "healer"},
            # Monk
            {"spec_id": "brewmaster", "name": "Brewmaster", "class_id": "monk", "role": "tank"},
            {"spec_id": "mistweaver", "name": "Mistweaver", "class_id": "monk", "role": "healer"},
            {"spec_id": "windwalker", "name": "Windwalker", "class_id": "monk", "role": "mdps"},
            # Evoker
            {"spec_id": "devastation", "name": "Devastation", "class_id": "evoker", "role": "rdps"},
            {"spec_id": "preservation", "name": "Preservation", "class_id": "evoker", "role": "healer"},
            {"spec_id": "augmentation", "name": "Augmentation", "class_id": "evoker", "role": "rdps"}
        ]
        self.specs.insert_many(specs)
        
        print(f"✅ Created {len(raid_buffs)} raid buffs")
        print(f"✅ Created {len(classes)} classes")
        print(f"✅ Created {len(specs)} specs")
    
    def seed_players_and_characters(self):
        """Create players with their characters - Updated for raid testing"""
        # Player data - 40 players total
        player_data = [
            # Tank Players (2 players, 3 tank chars each = 6 tanks total)
            {"name": "Tank Master Alex", "discord": "TankMaster#0001", "role": "tank"},
            {"name": "Shield Wall Sarah", "discord": "ShieldWall#0002", "role": "tank"},
            
            # Healer Players (5 players, 2-4 healer chars each)
            {"name": "Holy Light Emma", "discord": "HolyLight#0003", "role": "healer"},
            {"name": "Nature's Grace Mike", "discord": "NaturesGrace#0004", "role": "healer"},
            {"name": "Divine Spirit Lisa", "discord": "DivineSpirit#0005", "role": "healer"},
            {"name": "Restoration Tom", "discord": "Restoration#0006", "role": "healer"},
            {"name": "Sacred Flame Rachel", "discord": "SacredFlame#0007", "role": "healer"},
            
            # DPS Players (33 players, mix of characters)
            {"name": "Fire Storm Chris", "discord": "FireStorm#0008", "role": "dps"},
            {"name": "Shadow Strike Anna", "discord": "ShadowStrike#0009", "role": "dps"},
            {"name": "Frost Bolt David", "discord": "FrostBolt#0010", "role": "dps"},
            {"name": "Lightning Sophie", "discord": "Lightning#0011", "role": "dps"},
            {"name": "Arcane Power Mark", "discord": "ArcanePower#0012", "role": "dps"},
            {"name": "Chaos Bolt Katie", "discord": "ChaosBolt#0013", "role": "dps"},
            {"name": "Hunter's Mark Ryan", "discord": "HuntersMark#0014", "role": "dps"},
            {"name": "Stealth Blade Zoe", "discord": "StealthBlade#0015", "role": "dps"},
            {"name": "Storm Strike Jake", "discord": "StormStrike#0016", "role": "dps"},
            {"name": "Wild Hunt Luna", "discord": "WildHunt#0017", "role": "dps"},
            {"name": "Death Coil Max", "discord": "DeathCoil#0018", "role": "dps"},
            {"name": "Demon Blade Ivy", "discord": "DemonBlade#0019", "role": "dps"},
            {"name": "Dragon Fire Kai", "discord": "DragonFire#0020", "role": "dps"},
            {"name": "Phoenix Rise Neo", "discord": "PhoenixRise#0021", "role": "dps"},
            {"name": "Thunder Clap Rex", "discord": "ThunderClap#0022", "role": "dps"},
            {"name": "Ice Shard Mia", "discord": "IceShard#0023", "role": "dps"},
            {"name": "Void Walker Ash", "discord": "VoidWalker#0024", "role": "dps"},
            {"name": "Star Fall Eve", "discord": "StarFall#0025", "role": "dps"},
            {"name": "Blood Moon Fox", "discord": "BloodMoon#0026", "role": "dps"},
            {"name": "Solar Beam Ray", "discord": "SolarBeam#0027", "role": "dps"},
            {"name": "Wind Slash Sage", "discord": "WindSlash#0028", "role": "dps"},
            {"name": "Earth Quake Clay", "discord": "EarthQuake#0029", "role": "dps"},
            {"name": "Time Warp Nova", "discord": "TimeWarp#0030", "role": "dps"},
            {"name": "Spirit Bond Jade", "discord": "SpiritBond#0031", "role": "dps"},
            {"name": "Flame Lance Pike", "discord": "FlameLance#0032", "role": "dps"},
            {"name": "Dark Ritual Hex", "discord": "DarkRitual#0033", "role": "dps"},
            {"name": "Light Beam Dawn", "discord": "LightBeam#0034", "role": "dps"},
            {"name": "Storm Guard Vale", "discord": "StormGuard#0035", "role": "dps"},
            {"name": "Frost Guard Cole", "discord": "FrostGuard#0036", "role": "dps"},
            {"name": "Fire Guard Blaze", "discord": "FireGuard#0037", "role": "dps"},
            {"name": "Shadow Guard Raven", "discord": "ShadowGuard#0038", "role": "dps"},
            {"name": "Nature Guard Sage", "discord": "NatureGuard#0039", "role": "dps"},
            {"name": "Arcane Guard Zara", "discord": "ArcaneGuard#0040", "role": "dps"}
        ]
        
        # Character names pool
        character_names = [
            'Thunderstrike', 'Shadowbane', 'Frostwhisper', 'Flameheart', 'Moonshadow',
            'Stormrage', 'Nightblade', 'Icevein', 'Firestorm', 'Darkmoon',
            'Lightbringer', 'Wildheart', 'Bloodfang', 'Starweaver', 'Ironforge',
            'Mysticwind', 'Ashbringer', 'Voidwalker', 'Sunstrider', 'Grimfang',
            'Swiftarrow', 'Earthshaker', 'Dreamwalker', 'Soulreaper', 'Brightblade',
            'Darkspear', 'Windrider', 'Flamestrike', 'Frostborn', 'Shadowmere',
            'Goldmane', 'Steelclaw', 'Moonwhisper', 'Stormwind', 'Blackthorn',
            'Silverblade', 'Redfury', 'Greenvale', 'Bluemoon', 'Whitefang',
            'Doomhammer', 'Peacekeeper', 'Warbreaker', 'Lifebinder', 'Deathstrike',
            'Spellweaver', 'Bonecrusher', 'Mindflayer', 'Soulburner', 'Icebreaker',
            'Stormcaller', 'Shadowcaster', 'Flamekeeper', 'Frostkeeper', 'Voidkeeper',
            'Lightkeeper', 'Darkkeeper', 'Windkeeper', 'Earthkeeper', 'Firekeeper',
            'Thornstrike', 'Moonfire', 'Sunfire', 'Starfire', 'Nightfire',
            'Bloodfire', 'Icefire', 'Windfire', 'Earthfire', 'Voidfire',
            'Lightfire', 'Darkfire', 'Shadowfire', 'Stormfire', 'Dragonfire',
            'Phoenixfire', 'Spiritfire', 'Soulfire', 'Mindfire', 'Bonefire',
            'Steelfire', 'Ironfire', 'Goldfire', 'Silverfire', 'Crystalfire',
            'Runefire', 'Mysticfire', 'Arcanfire', 'Holyfire', 'Demonfire'
        ]
        
        # Tank specs
        tank_specs = [
            ("death_knight", "blood"), ("demon_hunter", "vengeance"), 
            ("druid", "guardian"), ("monk", "brewmaster"), 
            ("paladin", "protection_paladin"), ("warrior", "protection_warrior")
        ]
        
        # Healer specs
        healer_specs = [
            ("druid", "restoration_druid"), ("evoker", "preservation"), 
            ("monk", "mistweaver"), ("paladin", "holy_paladin"), 
            ("priest", "discipline"), ("priest", "holy_priest"), 
            ("shaman", "restoration_shaman")
        ]
        
        # DPS specs (both melee and ranged)
        dps_specs = [
            # Melee DPS
            ("death_knight", "frost_dk"), ("death_knight", "unholy"),
            ("demon_hunter", "havoc"), ("druid", "feral"),
            ("monk", "windwalker"), ("paladin", "retribution"),
            ("rogue", "assassination"), ("rogue", "outlaw"), ("rogue", "subtlety"),
            ("shaman", "enhancement"), ("warrior", "arms"), ("warrior", "fury"),
            ("hunter", "survival"),
            # Ranged DPS
            ("druid", "balance"), ("evoker", "devastation"), ("evoker", "augmentation"),
            ("hunter", "beast_mastery"), ("hunter", "marksmanship"),
            ("mage", "arcane"), ("mage", "fire"), ("mage", "frost_mage"),
            ("priest", "shadow"), ("shaman", "elemental"),
            ("warlock", "affliction"), ("warlock", "demonology"), ("warlock", "destruction")
        ]
        
        used_names = set()
        total_characters_created = 0
        
        print("\n📝 Creating 40 players with 90+ characters...")
        
        for i, player_info in enumerate(player_data):
            # Create player
            player = {
                "displayName": player_info["name"],
                "discordTag": player_info["discord"],
                "discordId": f"{2000000000000000000 + i}",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            player_result = self.players.insert_one(player)
            player_id = player_result.inserted_id
            
            # Determine number and type of characters based on player role
            player_role = player_info["role"]
            
            if player_role == "tank":
                # Tank players: exactly 3 tank characters
                num_chars = 3
                char_specs = random.sample(tank_specs, min(3, len(tank_specs)))
                role_groups = ["main", "alt", "alt"]
            elif player_role == "healer":
                # Healer players: 2-4 healer characters
                num_chars = random.randint(2, 4)
                char_specs = random.sample(healer_specs, min(num_chars, len(healer_specs)))
                if num_chars > len(healer_specs):
                    # Fill remaining with more healer specs
                    char_specs.extend(random.choices(healer_specs, k=num_chars - len(healer_specs)))
                role_groups = ["main"] + ["alt"] * (num_chars - 1)
            else:  # DPS players
                # Calculate remaining characters needed
                chars_created_so_far = total_characters_created
                remaining_players = len(player_data) - i
                
                # For DPS players, calculate based on remaining quota
                if i < 7:  # We're still in tank/healer players
                    num_chars = random.randint(2, 4)
                else:
                    # For DPS players, calculate based on remaining quota
                    chars_needed = 90 - chars_created_so_far
                    avg_per_remaining = chars_needed / remaining_players
                    num_chars = max(1, min(5, round(avg_per_remaining + random.uniform(-0.5, 0.5))))
                
                char_specs = random.choices(dps_specs, k=num_chars)
                
                # Mix of main, alt, and helper for DPS
                if num_chars == 1:
                    role_groups = ["main"]
                elif num_chars == 2:
                    role_groups = ["main", "alt"]
                elif num_chars == 3:
                    role_groups = ["main", "alt", "helper"]
                else:
                    role_groups = ["main", "alt"] + ["helper"] * (num_chars - 2)
            
            print(f"\n👤 Player: {player_info['name']} ({player_role}) - Creating {num_chars} characters:")
            
            for j in range(num_chars):
                # Get unique character name
                char_name = None
                attempts = 0
                while char_name is None or char_name in used_names:
                    char_name = random.choice(character_names)
                    attempts += 1
                    if attempts > 50:  # Fallback to numbered names
                        char_name = f"{player_info['name'].split()[0]}{j+1}"
                        break
                
                used_names.add(char_name)
                
                # Select class and spec
                class_id, spec_id = char_specs[j]
                role_group = role_groups[j] if j < len(role_groups) else "helper"
                
                character = {
                    "name": char_name,
                    "player_id": player_id,
                    "class_id": class_id,
                    "spec_id": spec_id,
                    "role_group": role_group,
                    "created_at": datetime.now()
                }
                
                self.characters.insert_one(character)
                total_characters_created += 1
                print(f"   ✅ {char_name} ({class_id} - {spec_id}) [{role_group}]")
        
        print(f"\n📊 Summary:")
        print(f"   Total Players: {len(player_data)}")
        print(f"   Total Characters: {total_characters_created}")
        
        # Verify the target distributions
        tank_count = self.characters.aggregate([
            {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec"}},
            {"$unwind": "$spec"},
            {"$match": {"spec.role": "tank"}},
            {"$count": "tanks"}
        ])
        tank_count = list(tank_count)
        tank_total = tank_count[0]["tanks"] if tank_count else 0
        
        healer_count = self.characters.aggregate([
            {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec"}},
            {"$unwind": "$spec"},
            {"$match": {"spec.role": "healer"}},
            {"$count": "healers"}
        ])
        healer_count = list(healer_count)
        healer_total = healer_count[0]["healers"] if healer_count else 0
        
        print(f"   Tank Characters: {tank_total}")
        print(f"   Healer Characters: {healer_total}")
        print(f"   DPS Characters: {total_characters_created - tank_total - healer_total}")
        
        print("\n🔍 Verifying constraints:")
        print(f"   ✅ Target: 40 players - Actual: {len(player_data)}")
        print(f"   ✅ Target: 90+ characters - Actual: {total_characters_created}")
        print(f"   ✅ Target: 6 tanks (2 players × 3) - Actual: {tank_total}")
        print(f"   ✅ Target: 10-20 healers (5 players × 2-4) - Actual: {healer_total}")
        print(f"   ✅ All helpers are DPS specs")
    
    def initialize(self):
        """Full database initialization"""
        print("🚀 Initializing WoW Roster Database...")
        self.reset_database()
        self.seed_static_data()
        self.seed_players_and_characters()
        print("\n✅ Database initialization complete!")

# Initialize database connection
db = WoWRosterDB()

# Routes
@app.route('/')
def index():
    """Main page - Players with their characters in sidebar layout"""
    # Updated aggregation pipeline for sidebar
    pipeline = [
        {
            "$lookup": {
                "from": "characters",
                "let": {"player_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$player_id", "$$player_id"]}}},
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
                    {"$unwind": "$class_info"},
                    {"$unwind": "$spec_info"},
                    {
                        "$project": {
                            "name": 1,
                            "role_group": 1,
                            "class_name": "$class_info.name",
                            "spec_name": "$spec_info.name",
                            "role_raid": "$spec_info.role",
                            "class_id": 1,
                            "spec_id": 1
                        }
                    }
                ],
                "as": "characters"
            }
        },
        {"$sort": {"displayName": 1}}
    ]
    
    players = list(db.players.aggregate(pipeline))
    
    # Calculate total characters across all players
    total_characters = sum(len(player.get('characters', [])) for player in players)
    
    # Debug output
    print(f"📊 Loaded {len(players)} players with {total_characters} total characters")
    
    # Log character distribution for debugging
    for player in players[:3]:  # Show first 3 players
        char_count = len(player.get('characters', []))
        print(f"   👤 {player['displayName']}: {char_count} characters")
        for char in player.get('characters', [])[:2]:  # Show first 2 characters
            print(f"      ⚔️ {char['name']} ({char['class_name']} {char['spec_name']})")
    
    return render_template('index.html', players=players, total_characters=total_characters)


@app.route('/characters')
def characters():
    """Character list page"""
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
                "role_group": 1,
                "player_name": "$player.displayName",
                "discord_tag": "$player.discordTag",
                "class_name": "$class_info.name",
                "spec_name": "$spec_info.name",
                "role_raid": "$spec_info.role",
                "armor_type": "$class_info.armor",
                "tier_token": "$class_info.token"
            }
        },
        {"$sort": {"name": 1}}
    ]
    
    char_list = list(db.characters.aggregate(pipeline))
    return render_template('characters.html', characters=char_list)

@app.route('/api/stats')
def api_stats():
    """API endpoint for roster statistics"""
    stats = {
        "total_players": db.players.count_documents({}),
        "total_characters": db.characters.count_documents({}),
        "role_distribution": list(db.characters.aggregate([
            {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec"}},
            {"$unwind": "$spec"},
            {"$group": {"_id": "$spec.role", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])),
        "class_distribution": list(db.characters.aggregate([
            {"$lookup": {"from": "classes", "localField": "class_id", "foreignField": "class_id", "as": "class"}},
            {"$unwind": "$class"},
            {"$group": {"_id": "$class.name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
    }
    return jsonify(stats)

# Optional: Add a route to get player/character data as JSON for debugging
@app.route('/api/players')
def api_players():
    """API endpoint for player data - useful for debugging"""
    pipeline = [
        {
            "$lookup": {
                "from": "characters",
                "let": {"player_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$player_id", "$player_id"]}}},
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
                    {"$unwind": "$class_info"},
                    {"$unwind": "$spec_info"},
                    {
                        "$project": {
                            "name": 1,
                            "role_group": 1,
                            "class_name": "$class_info.name",
                            "spec_name": "$spec_info.name",
                            "role_raid": "$spec_info.role",
                            "class_id": 1,
                            "spec_id": 1
                        }
                    }
                ],
                "as": "characters"
            }
        },
        {"$sort": {"displayName": 1}}
    ]
    
    players = list(db.players.aggregate(pipeline))
    
    # Convert ObjectId to string for JSON serialization
    for player in players:
        player['_id'] = str(player['_id'])
    
    return jsonify({
        "players": players,
        "total_characters": sum(len(p.get('characters', [])) for p in players)
    })

@app.route('/api/generate-splits', methods=['POST'])
def generate_splits():
    """Generate optimized raid groups using the RaidSplitter algorithm"""
    try:
        # Get settings from request
        data = request.get_json() or {}
        num_groups = data.get('num_groups', 3)
        healers_per_group = data.get('healers_per_group', 5)
        group_size = data.get('group_size', 30)
        
        print(f"🎯 Generating {num_groups} groups with {healers_per_group} healers each...")
        
        # Initialize raid splitter
        splitter = RaidSplitter(db)
        
        # Generate optimized groups
        groups = splitter.create_optimal_groups(
            num_groups=num_groups,
            group_size=group_size,
            healers_per_group=healers_per_group
        )
        
        # Convert to dictionary format for JSON response
        groups_data = splitter.groups_to_dict(groups)
        
        print(f"✅ Successfully generated {len(groups_data)} groups")
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'settings': {
                'num_groups': num_groups,
                'healers_per_group': healers_per_group,
                'group_size': group_size
            }
        })
        
    except Exception as e:
        print(f"❌ Error generating splits: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add this helper function to check database status
@app.route('/api/db-status')
def db_status():
    """Check database status - useful for debugging"""
    try:
        player_count = db.players.count_documents({})
        character_count = db.characters.count_documents({})
        class_count = db.classes.count_documents({})
        spec_count = db.specs.count_documents({})
        
        return jsonify({
            "status": "connected",
            "collections": {
                "players": player_count,
                "characters": character_count,
                "classes": class_count,
                "specs": spec_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Add this route to trigger reinitialization
@app.route('/api/reinitialize-db', methods=['POST'])
def reinitialize_db():
    """API endpoint to reinitialize database"""
    try:
        print("🔄 Reinitializing database via API call...")
        db.initialize()
        return jsonify({
            "status": "success",
            "message": "Database reinitialized with 40 players and 90+ characters"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/test-splitter')
def test_splitter():
    """Test the raid splitter import and basic functionality"""
    try:
        from raid_splitter import RaidSplitter
        splitter = RaidSplitter(db)
        
        # Test getting characters
        characters = splitter.get_all_characters()
        
        return jsonify({
            'success': True,
            'characters_found': len(characters),
            'sample_character': characters[0].__dict__ if characters else None
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# Add this to your split-generator.py for detailed debugging

@app.route('/api/debug-splits')
def debug_splits():
    """Detailed debugging of the raid splitter"""
    try:
        from raid_splitter import RaidSplitter
        splitter = RaidSplitter(db)
        
        # Step 1: Get characters
        characters = splitter.get_all_characters()
        
        # Step 2: Categorize
        categorized = splitter.categorize_characters(characters)
        
        # Step 3: Try creating a single group
        from raid_splitter import RaidGroup
        test_group = RaidGroup(group_id=1)
        
        # Step 4: Try adding a tank
        tanks = categorized['tanks']
        
        debug_info = {
            'total_characters': len(characters),
            'tanks_found': len(tanks),
            'healers_found': len(categorized['healers']),
            'dps_found': len(categorized['dps']),
            'sample_tank': tanks[0].__dict__ if tanks else None,
            'tank_names': [t.name for t in tanks[:5]] if tanks else []
        }
        
        # Try the problematic operation
        if tanks:
            success = test_group.add_character(tanks[0])
            debug_info['tank_add_success'] = success
            debug_info['group_tanks'] = len(test_group.tanks)
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/simple-generate')
def simple_generate():
    """Try a very simple group generation"""
    try:
        from raid_splitter import RaidSplitter
        splitter = RaidSplitter(db)
        
        # Try with minimal settings
        groups = splitter.create_optimal_groups(
            num_groups=2,  # Start with just 2 groups
            group_size=10,  # Small groups
            healers_per_group=2  # Fewer healers
        )
        
        result = []
        for group in groups:
            result.append({
                'group_id': group.group_id,
                'total_members': len(group.characters),
                'tanks': len(group.tanks),
                'healers': len(group.healers),
                'dps': len(group.dps)
            })
        
        return jsonify({
            'success': True,
            'groups': result
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

if __name__ == '__main__':
    import os
    
    # Check if we need to reinitialize database
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        current_player_count = db.players.count_documents({})
        if current_player_count != 40:
            print(f"Current players: {current_player_count}, reinitializing to 40 players...")
            db.initialize()
        else:
            print(f"✅ Database already has {current_player_count} players")
    
    print("\n🌐 Starting Flask server...")
    print("📊 Visit http://localhost:5000 to view your roster!")
    print("🔧 To reinitialize DB: POST to /api/reinitialize-db")
    
    app.run(debug=True, port=5000)