from flask import Flask, render_template, jsonify, request
from bson import ObjectId
import os
import random 
import logging

# Import our modular components
from database import WoWRosterDB
from data_generators import generate_raid_roster, generate_test_roster, generate_stress_test_roster
from raid_splitter import RaidSplitter  # Original complex splitter
from simple_splitter import create_simple_raid_groups  # New simple splitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize database connection
db = WoWRosterDB()

# Routes (keeping existing ones unchanged)
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
                            "group": "$role_group",
                            "class_name": "$class_info.class_name",
                            "spec_name": "$spec_info.spec_name",
                            "role_raid": "$spec_info.role_raid",
                            "class_id": 1,
                            "spec": "$spec_id"
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

@app.route('/api/generate-splits', methods=['POST'])
def generate_splits():
    """Generate raid groups using the NEW Simple Splitter with character locks"""
    try:
        data = request.get_json() or {}
        num_groups = data.get('num_groups', 3)
        group_size = data.get('group_size', 30)
        character_locks = data.get('character_locks', [])
        
        logger.info(f"🎯 Generating {num_groups} groups with max {group_size} characters each (Simple Splitter)")
        if character_locks:
            logger.info(f"🔒 Processing {len(character_locks)} character locks")
            for lock in character_locks:
                logger.info(f"   🔒 {lock.get('characterName')} → Group {lock.get('groupId')}")
        
        # FIXED: Import and use the class to support locks
        from simple_splitter import SimpleRaidSplitter
        
        # Use the class with locks
        splitter = SimpleRaidSplitter(db)
        groups = splitter.create_groups(num_groups, group_size, character_locks)
        groups_data = splitter.groups_to_dict(groups)
        
        logger.info(f"✅ Successfully generated {len(groups_data)} groups using Simple Splitter")
        if character_locks:
            logger.info(f"✅ Applied {len(character_locks)} character locks")
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'settings': {
                'num_groups': num_groups,
                'group_size': group_size
            },
            'splitter_type': 'simple',
            'locks_applied': len(character_locks)
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating splits: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-splits-complex', methods=['POST'])
def generate_splits_complex():
    """Generate raid groups using the Original Complex Splitter (for comparison)"""
    try:
        data = request.get_json() or {}
        num_groups = data.get('num_groups', 3)
        healers_per_group = data.get('healers_per_group', 5)
        group_size = data.get('group_size', 30)
        
        logger.info(f"🎯 Generating {num_groups} groups with {healers_per_group} healers each (Complex Splitter)")
        
        splitter = RaidSplitter(db)
        groups = splitter.create_optimal_groups(
            num_groups=num_groups,
            group_size=group_size,
            healers_per_group=healers_per_group
        )
        
        groups_data = splitter.groups_to_dict(groups)
        logger.info(f"✅ Successfully generated {len(groups_data)} groups using Complex Splitter")
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'settings': {
                'num_groups': num_groups,
                'healers_per_group': healers_per_group,
                'group_size': group_size
            },
            'splitter_type': 'complex'
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating splits: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
                "group": "$role_group",
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
            {"$lookup": {"from": "specs", "localField": "spec_id", "foreignField": "spec_id", "as": "spec"}},
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
                            "group": "$role_group",
                            "class_name": "$class_info.class_name",
                            "spec_name": "$spec_info.spec_name",
                            "role_raid": "$spec_info.role_raid",
                            "class_id": 1,
                            "spec": "$spec_id"
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

@app.route('/api/generate-raid-roster', methods=['POST', 'GET'])
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

@app.route('/api/debug-schema')
def debug_schema():
    """Debug endpoint to check actual database schema"""
    try:
        # Get field names only (no ObjectId values)
        char_fields = []
        spec_fields = []
        class_fields = []
        
        sample_char = db.characters.find_one()
        if sample_char:
            char_fields = [f for f in sample_char.keys() if f != '_id']
            
        sample_spec = db.specs.find_one()
        if sample_spec:
            spec_fields = [f for f in sample_spec.keys() if f != '_id']
            
        sample_class = db.classes.find_one()
        if sample_class:
            class_fields = [f for f in sample_class.keys() if f != '_id']
        
        # Get sample data without ObjectIds
        char_sample = db.characters.find_one({}, {"_id": 0, "player_id": 0})
        spec_sample = db.specs.find_one({}, {"_id": 0})
        class_sample = db.classes.find_one({}, {"_id": 0})
        
        return jsonify({
            "character_fields": char_fields,
            "spec_fields": spec_fields,
            "class_fields": class_fields,
            "sample_character": char_sample,
            "sample_spec": spec_sample,
            "sample_class": class_sample
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/api/roster-stats')
def api_roster_stats():
    """API endpoint for detailed roster statistics"""
    try:
        # Get role group counts
        role_groups_pipeline = [
            {
                "$group": {
                    "_id": "$role_group",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        role_groups_result = list(db.characters.aggregate(role_groups_pipeline))
        role_group_counts = {
            "main": 0,
            "alt": 0,
            "helper": 0
        }
        
        for group in role_groups_result:
            if group['_id'] in role_group_counts:
                role_group_counts[group['_id']] = group['count']
        
        # Get mains statistics - tokens and armor
        mains_pipeline = [
            {
                "$lookup": {
                    "from": "classes",
                    "localField": "class_id",
                    "foreignField": "class_id",
                    "as": "class_info"
                }
            },
            {"$unwind": "$class_info"},
            {"$match": {"role_group": "main"}},  # Filter for mains only
            {
                "$group": {
                    "_id": None,
                    "tokens": {
                        "$push": "$class_info.tier_token"
                    },
                    "armor": {
                        "$push": "$class_info.armor_type"
                    }
                }
            }
        ]
        
        mains_result = list(db.characters.aggregate(mains_pipeline))
        
        # Initialize counts
        token_counts = {"Zenith": 0, "Dreadful": 0, "Mystic": 0, "Venerated": 0}
        armor_counts = {"plate": 0, "mail": 0, "leather": 0, "cloth": 0}
        
        if mains_result and mains_result[0]:
            # Count tokens
            for token in mains_result[0].get('tokens', []):
                if token in token_counts:
                    token_counts[token] += 1
            
            # Count armor
            for armor in mains_result[0].get('armor', []):
                if armor in armor_counts:
                    armor_counts[armor] += 1
        
        # Get raid buffs from ALL characters
        raid_buffs_pipeline = [
            {
                "$lookup": {
                    "from": "classes",
                    "localField": "class_id",
                    "foreignField": "class_id",
                    "as": "class_info"
                }
            },
            {"$unwind": "$class_info"},
            {"$unwind": {"path": "$class_info.raid_buff_ids", "preserveNullAndEmptyArrays": False}},
            {
                "$lookup": {
                    "from": "raid_buffs",
                    "localField": "class_info.raid_buff_ids",
                    "foreignField": "buff_id",
                    "as": "buff_info"
                }
            },
            {"$unwind": "$buff_info"},
            {
                "$group": {
                    "_id": "$buff_info.name",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        raid_buffs_result = list(db.characters.aggregate(raid_buffs_pipeline))
        
        # Format raid buffs
        raid_buffs = {}
        for buff in raid_buffs_result:
            raid_buffs[buff['_id']] = buff['count']
        
        # Get all possible raid buffs and set count to 0 if not present
        all_buffs = list(db.raid_buffs.find({}, {"name": 1, "_id": 0}))
        for buff in all_buffs:
            if buff['name'] not in raid_buffs:
                raid_buffs[buff['name']] = 0
        
        return jsonify({
            "roleGroups": role_group_counts,
            "mains": {
                "tokens": token_counts,
                "armor": armor_counts
            },
            "all": {
                "raidBuffs": raid_buffs
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating roster stats: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500
        
if __name__ == '__main__':
    # Simplified startup - no debug functions that might hang
    try:
        stats = db.get_stats()
        logger.info(f"📊 Current database state: {stats}")
        
        if stats['players'] == 0:
            logger.info("🔧 Database appears empty, initializing...")
            db.initialize_schema()
            generate_raid_roster(db)
        else:
            logger.info(f"✅ Database ready with {stats['players']} players and {stats['characters']} characters")
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
    
    logger.info("🌐 Starting Flask server...")
    logger.info("📊 Visit http://localhost:5000 to view your roster!")
    logger.info("⚔️ NEW: Using Simple Splitter by default")
    logger.info("⚔️ OLD: Complex splitter available at /api/generate-splits-complex")
    
    app.run(debug=True, port=5000, host='127.0.0.1')