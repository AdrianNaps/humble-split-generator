from flask import Flask, render_template, jsonify, request
from bson import ObjectId
import os
import logging

# Import our new modular components
from database import WoWRosterDB
from data_generators import generate_raid_roster, generate_test_roster, generate_stress_test_roster
from raid_splitter import RaidSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize database connection
db = WoWRosterDB()

def debug_data_structure():
    """Debug function to see how data is actually stored"""
    print("\n🔍 DEBUGGING DATA STRUCTURE:")
    
    # Check players
    sample_player = db.players.find_one()
    if sample_player:
        print(f"📋 Sample Player: {sample_player}")
        print(f"   Player _id type: {type(sample_player['_id'])}")
        print(f"   Player _id value: {sample_player['_id']}")
    else:
        print("❌ No players found!")
    
    # Check characters  
    sample_character = db.characters.find_one()
    if sample_character:
        print(f"🗡️ Sample Character: {sample_character}")
        print(f"   Character player_id type: {type(sample_character['player_id'])}")
        print(f"   Character player_id value: {sample_character['player_id']}")
    else:
        print("❌ No characters found!")
    
    # Count totals
    player_count = db.players.count_documents({})
    char_count = db.characters.count_documents({})
    print(f"📊 Totals: {player_count} players, {char_count} characters")

# Routes
@app.route('/')
def index():
    """Main page - Players with their characters in sidebar layout"""
    pipeline = [
        {
            "$lookup": {
                "from": "characters",
                "localField": "_id",
                "foreignField": "player_id",
                "as": "characters",
                "pipeline": [
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
                            "localField": "spec_id",  # Changed from "spec" to "spec_id"
                            "foreignField": "spec_id",
                            "as": "spec_info"
                        }
                    },
                    {"$unwind": "$class_info"},
                    {"$unwind": "$spec_info"},
                    {
                        "$project": {
                            "name": 1,
                            "group": "$role_group",  # Map role_group to group for template compatibility
                            "class_name": "$class_info.class_name",
                            "spec_name": "$spec_info.spec_name",
                            "role_raid": "$spec_info.role_raid",
                            "class_id": 1,
                            "spec": "$spec_id"  # Map spec_id to spec for template compatibility
                        }
                    }
                ]
            }
        },
        {"$sort": {"displayName": 1}}
    ]
    
    players = list(db.players.aggregate(pipeline))
    total_characters = sum(len(player.get('characters', [])) for player in players)
    
    logger.info(f"📊 Loaded {len(players)} players with {total_characters} total characters")
    
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
                "localField": "spec_id",  # Changed from "spec" to "spec_id"
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
                "group": "$role_group",  # Map role_group to group
                "player_name": "$player.displayName",
                "discord_tag": "$player.discordTag",
                "class_name": "$class_info.class_name",
                "spec_name": "$spec_info.spec_name",
                "role_raid": "$spec_info.role_raid",
                "armor_type": "$class_info.armor_type",
                "tier_token": "$class_info.tier_token"
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
            {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec"}},  # Changed from "spec"
            {"$unwind": "$spec"},
            {"$group": {"_id": "$spec.role_raid", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])),
        "class_distribution": list(db.characters.aggregate([
            {"$lookup": {"from": "classes", "localField": "class_id", "foreignField": "class_id", "as": "class"}},
            {"$unwind": "$class"},
            {"$group": {"_id": "$class.class_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
    }
    return jsonify(stats)

@app.route('/api/players')
def api_players():
    """API endpoint for player data"""
    pipeline = [
        {
            "$lookup": {
                "from": "characters",
                "localField": "_id",
                "foreignField": "player_id",
                "as": "characters",
                "pipeline": [
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
                            "localField": "spec_id",  # Changed from "spec" to "spec_id"
                            "foreignField": "spec_id",
                            "as": "spec_info"
                        }
                    },
                    {"$unwind": "$class_info"},
                    {"$unwind": "$spec_info"},
                    {
                        "$project": {
                            "name": 1,
                            "group": "$role_group",  # Map role_group to group
                            "class_name": "$class_info.class_name",
                            "spec_name": "$spec_info.spec_name",
                            "role_raid": "$spec_info.role_raid",
                            "class_id": 1,
                            "spec": "$spec_id"  # Map spec_id to spec
                        }
                    }
                ]
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
        data = request.get_json() or {}
        num_groups = data.get('num_groups', 3)
        healers_per_group = data.get('healers_per_group', 5)
        group_size = data.get('group_size', 30)
        
        logger.info(f"🎯 Generating {num_groups} groups with {healers_per_group} healers each...")
        
        splitter = RaidSplitter(db)
        groups = splitter.create_optimal_groups(
            num_groups=num_groups,
            group_size=group_size,
            healers_per_group=healers_per_group
        )
        
        groups_data = splitter.groups_to_dict(groups)
        logger.info(f"✅ Successfully generated {len(groups_data)} groups")
        
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
        logger.error(f"❌ Error generating splits: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/db-status')
def db_status():
    """Check database status"""
    try:
        stats = db.get_stats()
        return jsonify({
            "status": "connected",
            "collections": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Data Generation Endpoints
@app.route('/api/initialize-schema', methods=['POST'])
def initialize_schema():
    """Initialize database schema with static data only"""
    try:
        logger.info("🔧 Initializing database schema...")
        db.initialize_schema()
        return jsonify({
            "status": "success",
            "message": "Database schema initialized with static data"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/generate-raid-roster', methods=['POST'])
def api_generate_raid_roster():
    """Generate the standard raid-ready roster (40 players, 90+ chars)"""
    try:
        logger.info("🎯 Generating raid-ready roster...")
        stats = generate_raid_roster(db)
        return jsonify({
            "status": "success",
            "message": "Raid-ready roster generated",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/generate-test-roster', methods=['POST'])
def api_generate_test_roster():
    """Generate a small test roster (15 players, 30 chars)"""
    try:
        logger.info("🧪 Generating test roster...")
        stats = generate_test_roster(db)
        return jsonify({
            "status": "success",
            "message": "Test roster generated",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/generate-stress-test', methods=['POST'])
def api_generate_stress_test():
    """Generate an imbalanced roster for edge case testing"""
    try:
        logger.info("⚠️ Generating stress test roster...")
        stats = generate_stress_test_roster(db)
        return jsonify({
            "status": "success",
            "message": "Stress test roster generated",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Check database state on startup
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        try:
            stats = db.get_stats()
            logger.info(f"📊 Current database state: {stats}")
            
            # Debug the data structure
            debug_data_structure()
            
            # Auto-initialize if empty
            if stats['players'] == 0:
                logger.info("🔧 Database appears empty, initializing...")
                db.initialize_schema()
                generate_raid_roster(db)
                # Debug again after generation
                print("\n🔄 After generating data:")
                debug_data_structure()
            else:
                logger.info(f"✅ Database ready with {stats['players']} players and {stats['characters']} characters")
                
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
    
    logger.info("\n🌐 Starting Flask server...")
    logger.info("📊 Visit http://localhost:5000 to view your roster!")
    logger.info("\n🔧 Available data generation endpoints:")
    logger.info("   POST /api/initialize-schema - Set up database structure")
    logger.info("   POST /api/generate-raid-roster - Generate raid-ready roster (40 players)")
    logger.info("   POST /api/generate-test-roster - Generate small test roster (15 players)")
    logger.info("   POST /api/generate-stress-test - Generate imbalanced roster for testing")
    
    app.run(debug=True, port=5000)