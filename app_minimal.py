from flask import Flask, render_template, jsonify, request
from bson import ObjectId
import os
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
    """Generate raid groups using the NEW Simple Splitter"""
    try:
        data = request.get_json() or {}
        num_groups = data.get('num_groups', 3)
        group_size = data.get('group_size', 30)
        
        logger.info(f"🎯 Generating {num_groups} groups with max {group_size} characters each (Simple Splitter)")
        
        # Use the new simple splitter
        groups_data = create_simple_raid_groups(db, num_groups, group_size)
        
        logger.info(f"✅ Successfully generated {len(groups_data)} groups using Simple Splitter")
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'settings': {
                'num_groups': num_groups,
                'group_size': group_size
            },
            'splitter_type': 'simple'
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating splits: {str(e)}")
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