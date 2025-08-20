from flask import Flask, request, jsonify
import asyncio
import json
import logging
from tools.image_captioning import ImageCaptioningTool
from tools.story_generation import StoryGenerationTool
from tools.story_analysis import StoryAnalysisTool
from tools.database_service import DatabaseService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize tools
image_captioner = ImageCaptioningTool()
story_generator = StoryGenerationTool()
story_analyzer = StoryAnalysisTool()
db_service = DatabaseService()

def run_async(coro):
    """Helper to run async functions in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'memoir-ai-server',
        'version': '1.0.0',
        'database': 'connected'
    })

# ==================================================================================
# INDIVIDUAL AI TOOLS (existing endpoints)
# ==================================================================================

@app.route('/tools/caption_image', methods=['POST'])
def caption_image_endpoint():
    """Caption an image"""
    try:
        data = request.json
        logger.info("Processing image caption request")
        
        if not data or 'image_data' not in data:
            return jsonify({'error': 'image_data is required'}), 400
        
        result = run_async(
            image_captioner.caption_image(
                data['image_data'], 
                data.get('image_format', 'jpeg')
            )
        )
        
        logger.info("Image caption generated successfully")
        return jsonify({'result': result})
        
    except Exception as e:
        logger.error(f"Error in caption_image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tools/generate_story', methods=['POST'])
def generate_story_endpoint():
    """Generate a story from captions"""
    try:
        data = request.json
        logger.info("Processing story generation request")
        
        if not data or 'captions' not in data:
            return jsonify({'error': 'captions array is required'}), 400
        
        result = run_async(
            story_generator.generate_story(
                data['captions'],
                data.get('user_context', ''),
                data.get('tone', 'heartwarming')
            )
        )
        
        logger.info("Story generated successfully")
        return jsonify({'result': result})
        
    except Exception as e:
        logger.error(f"Error in generate_story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tools/analyze_story_sentiment', methods=['POST'])
def analyze_sentiment_endpoint():
    """Analyze story sentiment"""
    try:
        data = request.json
        logger.info("Processing sentiment analysis request")
        
        if not data or 'story_content' not in data:
            return jsonify({'error': 'story_content is required'}), 400
        
        result = run_async(
            story_analyzer.analyze_story_sentiment(
                data['story_content']
            )
        )
        
        logger.info("Sentiment analysis completed successfully")
        return jsonify({'result': result})
        
    except Exception as e:
        logger.error(f"Error in analyze_sentiment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tools/generate_story_title', methods=['POST'])
def generate_title_endpoint():
    """Generate story titles"""
    try:
        data = request.json
        logger.info("Processing title generation request")
        
        if not data or 'story_content' not in data:
            return jsonify({'error': 'story_content is required'}), 400
        
        result = run_async(
            story_analyzer.generate_story_title(
                data['story_content'],
                data.get('sentiment_data', {})
            )
        )
        
        logger.info("Title generation completed successfully")
        return jsonify({'result': result})
        
    except Exception as e:
        logger.error(f"Error in generate_title: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================================================================================
# COMPLETE WORKFLOW ENDPOINTS (NEW - combines AI + Database)
# ==================================================================================

@app.route('/memoir/create_entry', methods=['POST'])
def create_memoir_entry():
    """
    Complete workflow: Images → Captions → Story → Analysis → Save to DB
    This is the main endpoint your iOS app will use
    """
    try:
        data = request.json
        logger.info("Processing complete memoir entry creation")
        
        # Validate required fields
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400
        
        if 'images' not in data or not data['images']:
            return jsonify({'error': 'At least one image is required'}), 400
        
        user_id = data['user_id']
        images = data['images']  # Array of {image_data, image_format}
        user_context = data.get('user_context', '')
        tone = data.get('tone', 'heartwarming')
        
        # Step 1: Caption all images
        logger.info(f"Captioning {len(images)} images...")
        captions = []
        image_metadata = []
        
        for i, img in enumerate(images):
            caption = run_async(
                image_captioner.caption_image(
                    img['image_data'],
                    img.get('image_format', 'jpeg')
                )
            )
            captions.append(caption)
            
            # Store image metadata (in real app, you'd upload to S3)
            image_metadata.append({
                'image_id': f'img_{i+1}',
                'caption': caption,
                'upload_order': i + 1,
                'image_url': f'placeholder://image_{i+1}.jpg'  # Replace with S3 URL
            })
        
        # Step 2: Generate story from captions
        logger.info("Generating story from captions...")
        story_content = run_async(
            story_generator.generate_story(captions, user_context, tone)
        )
        
        # Step 3: Analyze sentiment
        logger.info("Analyzing story sentiment...")
        sentiment_analysis = run_async(
            story_analyzer.analyze_story_sentiment(story_content)
        )
        
        # Step 4: Generate title
        logger.info("Generating story title...")
        title = run_async(
            story_analyzer.generate_story_title(story_content, sentiment_analysis)
        )
        
        # Step 5: Save to database
        logger.info("Saving entry to database...")
        entry_id = db_service.save_journal_entry(
            user_id=user_id,
            title=title,
            story_content=story_content,
            user_context=user_context,
            tone=tone,
            images=image_metadata,
            sentiment_analysis=sentiment_analysis
        )
        
        # Prepare response
        response = {
            'success': True,
            'entry_id': entry_id,
            'title': title,
            'story_content': story_content,
            'sentiment_analysis': sentiment_analysis,
            'images': image_metadata,
            'metadata': {
                'word_count': len(story_content.split()),
                'tone': tone,
                'created_at': entry_id.split('#')[1]  # Extract timestamp from entry_id
            }
        }
        
        logger.info(f"Memoir entry created successfully: {entry_id}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error creating memoir entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================================================================================
# USER MANAGEMENT ENDPOINTS
# ==================================================================================

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.json
        
        if not data or 'email' not in data:
            return jsonify({'error': 'email is required'}), 400
        
        # Check if user already exists
        existing_user = db_service.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        user_id = db_service.create_user(
            email=data['email'],
            preferences=data.get('preferences', {})
        )
        
        return jsonify({'user_id': user_id, 'email': data['email']})
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = db_service.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user)
        
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics and insights"""
    try:
        stats = db_service.get_user_stats(user_id)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================================================================================
# JOURNAL ENTRY MANAGEMENT
# ==================================================================================

@app.route('/users/<user_id>/entries', methods=['GET'])
def get_user_entries(user_id):
    """Get user's journal entries"""
    try:
        limit = int(request.args.get('limit', 20))
        newest_first = request.args.get('newest_first', 'true').lower() == 'true'
        
        entries = db_service.get_user_entries(user_id, limit, newest_first)
        return jsonify({'entries': entries, 'count': len(entries)})
        
    except Exception as e:
        logger.error(f"Error getting user entries: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/<entry_id>', methods=['GET'])
def get_entry_by_id(user_id, entry_id):
    """Get specific journal entry"""
    try:
        entry = db_service.get_entry_by_id(user_id, entry_id)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        return jsonify(entry)
        
    except Exception as e:
        logger.error(f"Error getting entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/mood/<mood>', methods=['GET'])
def get_entries_by_mood(user_id, mood):
    """Get entries by mood"""
    try:
        entries = db_service.get_entries_by_mood(user_id, mood)
        return jsonify({'entries': entries, 'mood': mood, 'count': len(entries)})
        
    except Exception as e:
        logger.error(f"Error getting entries by mood: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/<entry_id>/favorite', methods=['PATCH'])
def toggle_favorite(user_id, entry_id):
    """Toggle entry favorite status"""
    try:
        data = request.json
        is_favorite = data.get('is_favorite', False)
        
        db_service.update_entry_favorite(user_id, entry_id, is_favorite)
        return jsonify({'success': True, 'is_favorite': is_favorite})
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/<entry_id>', methods=['DELETE'])
def delete_entry(user_id, entry_id):
    """Delete journal entry"""
    try:
        db_service.delete_entry(user_id, entry_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================================================================================
# ERROR HANDLERS
# ==================================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting MemoirAI HTTP Server with DynamoDB integration...")
    app.run(host='0.0.0.0', port=8000, debug=False)