from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from datetime import datetime
import random
from bson import ObjectId

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
        """Create players with their characters"""
        # Player data
        player_data = [
            {"name": "Alex Thunder", "discord": "AlexThunder#1234"},
            {"name": "Sarah Storm", "discord": "SarahStorm#5678"},
            {"name": "Mike Frost", "discord": "MikeFrost#9012"},
            {"name": "Emma Fire", "discord": "EmmaFire#3456"},
            {"name": "Jake Shadow", "discord": "JakeShadow#7890"},
            {"name": "Lisa Light", "discord": "LisaLight#2345"},
            {"name": "Tom Nature", "discord": "TomNature#6789"},
            {"name": "Rachel Arcane", "discord": "RachelArcane#0123"},
            {"name": "Chris Steel", "discord": "ChrisSteel#4567"},
            {"name": "Anna Void", "discord": "AnnaVoid#8901"},
            {"name": "David Hunt", "discord": "DavidHunt#1357"},
            {"name": "Sophie Heal", "discord": "SophieHeal#2468"},
            {"name": "Mark Tank", "discord": "MarkTank#3579"},
            {"name": "Katie Burn", "discord": "KatieBurn#4680"},
            {"name": "Ryan Blade", "discord": "RyanBlade#5791"}
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
            'Doomhammer', 'Peacekeeper', 'Warbreaker', 'Lifebinder', 'Deathstrike'
        ]
        
        # Common class/spec combinations
        common_combos = [
            ("mage", "fire"), ("warrior", "fury"), ("priest", "holy_priest"),
            ("hunter", "beast_mastery"), ("paladin", "retribution"),
            ("rogue", "assassination"), ("warlock", "affliction"),
            ("druid", "balance"), ("shaman", "elemental"), ("monk", "windwalker"),
            ("death_knight", "unholy"), ("demon_hunter", "havoc"),
            ("evoker", "devastation"), ("priest", "shadow"), ("warrior", "protection_warrior")
        ]
        
        used_names = set()
        
        print("\n📝 Creating players and characters...")
        
        for i, player_info in enumerate(player_data):
            # Create player
            player = {
                "displayName": player_info["name"],
                "discordTag": player_info["discord"],
                "discordId": f"{1000000000000000000 + i}",
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            }
            
            player_result = self.players.insert_one(player)
            player_id = player_result.inserted_id
            
            # Randomly assign 1-3 characters per player
            num_chars = random.randint(1, 3)
            
            print(f"\n👤 Player: {player_info['name']} (ID: {player_id})")
            print(f"   Creating {num_chars} characters:")
            
            for j in range(num_chars):
                # Get unique character name
                char_name = None
                attempts = 0
                while char_name is None or char_name in used_names:
                    char_name = random.choice(character_names)
                    attempts += 1
                    if attempts > 50:  # Fallback to numbered names
                        char_name = f"{player_info['name'].split()[0]}Alt{j+1}"
                        break
                
                used_names.add(char_name)
                
                # Select class and spec
                class_id, spec_id = random.choice(common_combos)
                
                character = {
                    "name": char_name,
                    "player_id": player_id,  # THIS IS THE KEY - proper ObjectId reference
                    "class_id": class_id,
                    "spec_id": spec_id,
                    "role_group": "main" if j == 0 else "alt",
                    "created_at": datetime.now()
                }
                
                self.characters.insert_one(character)
                print(f"   ✅ {char_name} ({class_id} - {spec_id})")
        
        # Verify the relationships
        print("\n🔍 Verifying player-character relationships:")
        for player in self.players.find().limit(5):
            char_count = self.characters.count_documents({"player_id": player["_id"]})
            print(f"   {player['displayName']}: {char_count} characters")
    
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
    """Main page - Players with their characters"""
    # Fixed aggregation pipeline
    pipeline = [
        {
            "$lookup": {
                "from": "characters",
                "let": {"player_id": "$_id"},  # Pass player's _id
                "pipeline": [
                    # THIS IS THE FIX - properly match character's player_id to player's _id
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
                            "role_raid": "$spec_info.role"
                        }
                    }
                ],
                "as": "characters"
            }
        },
        {"$sort": {"displayName": 1}}
    ]
    
    players = list(db.players.aggregate(pipeline))
    
    # Debug: Print first player's character count
    if players:
        print(f"First player ({players[0]['displayName']}) has {len(players[0]['characters'])} characters")
    
    return render_template('index.html', players=players)

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

if __name__ == '__main__':
    import os
    
    # Only initialize database on first run, not on reload
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        db.initialize()
    
    print("\n🌐 Starting Flask server...")
    print("📊 Visit http://localhost:5000 to view your roster!")
    
    app.run(debug=True, port=5000)