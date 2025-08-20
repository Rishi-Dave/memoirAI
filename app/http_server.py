from flask import Flask, request, jsonify
import asyncio
import json
import logging
from tools.image_captioning import ImageCaptioningTool
from tools.story_generation import StoryGenerationTool
from tools.story_analysis import StoryAnalysisTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize tools
image_captioner = ImageCaptioningTool()
story_generator = StoryGenerationTool()
story_analyzer = StoryAnalysisTool()

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
        'version': '1.0.0'
    })

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting MemoirAI HTTP Server...")
    app.run(host='0.0.0.0', port=8000, debug=False)