from flask import Flask, request, jsonify
import asyncio
import json
import logging
from tools.image_captioning import ImageCaptioningTool
from tools.story_generation import StoryGenerationTool
from tools.story_analysis import StoryAnalysisTool
from tools.database_service import DatabaseService
import bcrypt
import secrets

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
            logger.error("Missing user_id in request")
            return jsonify({'error': 'user_id is required'}), 400
        
        if 'images' not in data or not data['images']:
            logger.error("Missing images in request")
            return jsonify({'error': 'At least one image is required'}), 400
        
        user_id = data['user_id']
        images = data['images']  # Array of {image_data, image_format}
        user_context = data.get('user_context', '')
        tone = data.get('tone', 'heartwarming')
        
        logger.info(f"Creating memoir for user {user_id} with {len(images)} images")
        
        # Step 1: Caption all images
        logger.info(f"Captioning {len(images)} images...")
        captions = []
        image_metadata = []
        
        for i, img in enumerate(images):
            try:
                logger.info(f"Processing image {i+1}/{len(images)}")
                
                # Validate image data
                if 'image_data' not in img or not img['image_data']:
                    logger.error(f"Image {i+1} missing image_data")
                    return jsonify({'error': f'Image {i+1} missing image_data'}), 400
                
                # Caption the image
                caption = run_async(
                    image_captioner.caption_image(
                        img['image_data'],
                        img.get('image_format', 'jpeg')
                    )
                )
                
                # Check if captioning was successful
                if not caption or caption.startswith('Error:'):
                    logger.error(f"Failed to caption image {i+1}: {caption}")
                    return jsonify({'error': f'Failed to caption image {i+1}: {caption}'}), 500
                
                captions.append(caption)
                logger.info(f"Successfully captioned image {i+1}")
                
                # Store image metadata
                image_metadata.append({
                    'image_id': f'img_{i+1}',
                    'caption': caption,
                    'upload_order': i + 1,
                    'image_url': f'placeholder://image_{i+1}.jpg'  # Replace with S3 URL
                })
                
            except Exception as img_error:
                logger.error(f"Error processing image {i+1}: {str(img_error)}")
                return jsonify({'error': f'Error processing image {i+1}: {str(img_error)}'}), 500
        
        # Validate we have captions
        if not captions:
            logger.error("No captions were generated")
            return jsonify({'error': 'Failed to generate any image captions'}), 500
        
        logger.info(f"Generated {len(captions)} captions successfully")
        
        # Step 2: Generate story from captions
        logger.info("Generating story from captions...")
        try:
            story_content = run_async(
                story_generator.generate_story(captions, user_context, tone)
            )
            
            # Check if story generation was successful
            if not story_content or story_content.startswith('Error:'):
                logger.error(f"Failed to generate story: {story_content}")
                return jsonify({'error': f'Failed to generate story: {story_content}'}), 500
            
            logger.info("Story generated successfully")
            
        except Exception as story_error:
            logger.error(f"Error generating story: {str(story_error)}")
            return jsonify({'error': f'Error generating story: {str(story_error)}'}), 500
        
        # Step 3: Analyze sentiment
        logger.info("Analyzing story sentiment...")
        try:
            sentiment_analysis = run_async(
                story_analyzer.analyze_story_sentiment(story_content)
            )
            
            # Check for errors in sentiment analysis
            if isinstance(sentiment_analysis, dict) and 'error' in sentiment_analysis:
                logger.warning(f"Sentiment analysis failed: {sentiment_analysis['error']}")
                # Use default sentiment if analysis fails
                sentiment_analysis = {
                    'primary_mood': 'neutral',
                    'emotional_intensity': 5,
                    'overall_sentiment': 'neutral'
                }
            
            logger.info("Sentiment analysis completed")
            
        except Exception as sentiment_error:
            logger.error(f"Error in sentiment analysis: {str(sentiment_error)}")
            # Use default sentiment
            sentiment_analysis = {
                'primary_mood': 'neutral',
                'emotional_intensity': 5,
                'overall_sentiment': 'neutral'
            }
        
        # Step 4: Generate title
        logger.info("Generating story title...")
        try:
            title = run_async(
                story_analyzer.generate_story_title(story_content, sentiment_analysis)
            )
            
            # Check if title generation was successful
            if not title or (isinstance(title, dict) and 'error' in title):
                logger.warning(f"Title generation failed, using default")
                title = f"My {tone.capitalize()} Memory"
            
            logger.info("Title generated successfully")
            
        except Exception as title_error:
            logger.error(f"Error generating title: {str(title_error)}")
            title = f"My {tone.capitalize()} Memory"
        
        # Step 5: Save to database
        logger.info("Saving entry to database...")
        try:
            entry_id = db_service.save_journal_entry(
                user_id=user_id,
                title=title,
                story_content=story_content,
                user_context=user_context,
                tone=tone,
                images=image_metadata,
                sentiment_analysis=sentiment_analysis
            )
            
            logger.info(f"Entry saved successfully with ID: {entry_id}")
            
        except Exception as db_error:
            logger.error(f"Error saving to database: {str(db_error)}")
            return jsonify({'error': f'Error saving to database: {str(db_error)}'}), 500
        
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
                'created_at': entry_id.split('_')[1] if '_' in entry_id else 'unknown'
            }
        }
        
        logger.info(f"Memoir entry created successfully: {entry_id}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Unexpected error creating memoir entry: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

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
    """Get specific journal entry with better error handling"""
    try:
        logger.info(f"Getting entry {entry_id} for user {user_id}")
        
        entry = db_service.get_entry_by_id(user_id, entry_id)
        if not entry:
            logger.warning(f"Entry {entry_id} not found for user {user_id}")
            return jsonify({'error': 'Entry not found'}), 404
        
        logger.info(f"Successfully retrieved entry {entry_id}")
        return jsonify(entry)
        
    except Exception as e:
        logger.error(f"Error getting entry {entry_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


    """Get entries by mood"""
    try:
        entries = db_service.get_entries_by_mood(user_id, mood)
        return jsonify({'entries': entries, 'mood': mood, 'count': len(entries)})
        
    except Exception as e:
        logger.error(f"Error getting entries by mood: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/favorites', methods=['GET'])
def get_favorite_entries(user_id):
    """Get user's favorite journal entries only"""
    try:
        limit = int(request.args.get('limit', 20))
        newest_first = request.args.get('newest_first', 'true').lower() == 'true'
        
        logger.info(f"Getting favorite entries for user {user_id}, limit: {limit}")
        
        favorite_entries = db_service.get_favorite_entries(user_id, limit, newest_first)
        
        logger.info(f"Retrieved {len(favorite_entries)} favorite entries")
        
        return jsonify({
            'entries': favorite_entries, 
            'count': len(favorite_entries),
            'user_id': user_id,
            'filter': 'favorites'
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        logger.error(f"Error getting favorite entries: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/mood/<mood>', methods=['GET'])
def get_entries_by_mood(user_id, mood):
    """Get entries filtered by specific mood"""
    try:
        limit = int(request.args.get('limit', 20))
        
        # Validate mood parameter
        valid_moods = ['joyful', 'nostalgic', 'adventurous', 'peaceful', 'melancholic', 'excited', 'grateful', 'reflective', 'neutral']
        if mood not in valid_moods:
            return jsonify({
                'error': 'Invalid mood', 
                'valid_moods': valid_moods
            }), 400
        
        logger.info(f"Getting entries with mood '{mood}' for user {user_id}")
        
        mood_entries = db_service.get_entries_by_mood(user_id, mood, limit)
        
        logger.info(f"Retrieved {len(mood_entries)} entries with mood '{mood}'")
        
        return jsonify({
            'entries': mood_entries,
            'count': len(mood_entries), 
            'user_id': user_id,
            'mood': mood,
            'filter': f'mood:{mood}'
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        logger.error(f"Error getting entries by mood: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/users/<user_id>/entries/<entry_id>/favorite', methods=['PATCH'])
def toggle_favorite(user_id, entry_id):
    """Toggle entry favorite status with validation"""
    try:
        data = request.json
        if not data or 'is_favorite' not in data:
            return jsonify({'error': 'is_favorite is required'}), 400
        
        is_favorite = data.get('is_favorite')
        if not isinstance(is_favorite, bool):
            return jsonify({'error': 'is_favorite must be true or false'}), 400
        
        logger.info(f"Toggling favorite for entry {entry_id} to {is_favorite}")
        
        # Attempt to update favorite status
        was_updated = db_service.update_entry_favorite(user_id, entry_id, is_favorite)
        
        if was_updated:
            logger.info(f"Successfully updated favorite status for entry {entry_id}")
            return jsonify({
                'success': True, 
                'is_favorite': is_favorite,
                'entry_id': entry_id,
                'user_id': user_id,
                'message': f'Entry {"added to" if is_favorite else "removed from"} favorites'
            })
        else:
            logger.warning(f"Entry {entry_id} not found for favorite update")
            return jsonify({'error': 'Entry not found'}), 404
        
    except Exception as e:
        logger.error(f"Error toggling favorite for entry {entry_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/entries/<entry_id>', methods=['DELETE'])
def delete_entry(user_id, entry_id):
    """Delete journal entry with proper validation"""
    try:
        logger.info(f"Deleting entry {entry_id} for user {user_id}")
        
        # Attempt to delete the entry
        was_deleted = db_service.delete_entry(user_id, entry_id)
        
        if was_deleted:
            logger.info(f"Successfully deleted entry {entry_id}")
            return jsonify({
                'success': True, 
                'message': 'Entry deleted successfully',
                'entry_id': entry_id,
                'user_id': user_id
            })
        else:
            logger.warning(f"Entry {entry_id} not found for deletion")
            return jsonify({'error': 'Entry not found'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/register', methods=['POST'])
def register_user():
    """Register a new user with email and password"""
    try:
        data = request.json
        logger.info("Processing user registration")
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Basic validation
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        try:
            user_id = db_service.create_user_with_password(
                email=email,
                password=password,
                preferences=data.get('preferences', {})
            )
            
            logger.info(f"User registered successfully: {user_id}")
            return jsonify({
                'success': True,
                'user_id': user_id,
                'email': email,
                'message': 'Account created successfully'
            })
            
        except ValueError as e:
            logger.warning(f"Registration failed: {str(e)}")
            return jsonify({'error': str(e)}), 409
        
    except Exception as e:
        logger.error(f"Error in user registration: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['POST'])
def login_user():
    """Authenticate user with email and password"""
    try:
        data = request.json
        logger.info("Processing user login")
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        user = db_service.authenticate_user(email, password)
        
        if user:
            logger.info(f"User authenticated successfully: {user['user_id']}")
            
            # Remove password hash from response
            user_response = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return jsonify({
                'success': True,
                'user': user_response,
                'message': 'Login successful'
            })
        else:
            logger.warning(f"Authentication failed for email: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        logger.error(f"Error in user login: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/auth/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        data = request.json
        
        if not data or 'user_id' not in data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'user_id, current_password, and new_password are required'}), 400
        
        user_id = data['user_id']
        current_password = data['current_password']
        new_password = data['new_password']
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        # Get user and verify current password
        user = db_service.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        stored_hash = user.get('password_hash', '')
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        success = db_service.update_user_password(user_id, new_password)
        
        if success:
            return jsonify({'success': True, 'message': 'Password updated successfully'})
        else:
            return jsonify({'error': 'Failed to update password'}), 500
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Password change failed'}), 500
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