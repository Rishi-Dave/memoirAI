import asyncio
from openai import AzureOpenAI
from config.settings import settings
import json

class StoryAnalysisTool:
    def __init__(self):
        self.client = AzureOpenAI(
            api_version="2025-01-01-preview",
            azure_endpoint="https://memoir-ai-resource.cognitiveservices.azure.com/",
            api_key=settings.OPENAI_API_KEY
        )

    async def analyze_story_sentiment(self, story_content: str):
        """
        Analyze the emotional tone and themes of a journal entry
        Returns structured data about mood, themes and emotional intensity
        """
        try:
            prompt = f"""Analyze this journey entry and provide a detailed sentiment analysis in JSON format:

            Story: {story_content}

            moods to choose from: (joyful, nostalgic, adventurous, peaceful, melancholic, excited, grateful, reflective)
            *Only add moods from this list*

            Return a JSON object with:
            - primary_mood: main emotional tone 
            - secondary_moods: array of 1-2 additional emotions present
            - emotional_intensity: scale 1-10 (1=very mild, 10=very intense)
            - themes: array of key themes (family, travel, achievement, nature, friendship, etc.)
            - overall_sentiment: positive, negative, or neutral

            IMPORTANT: Return ONLY the JSON object, no markdown formatting, no code blocks, no additional text.
            """

            messages = [
                {
                    "role":"user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                messages = messages,
                model="gpt-4o",
                max_tokens = 300,
                temperature=0.3
            )
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse sentiment analysis",
                "primary_mood": "neutral",
                "emotional_intensity": 5,
                "overall_sentiment": "neutral",
                "mood_color": "#808080"
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
        
    async def generate_story_title(self, story_content: str, sentiment_data: dict = None):
        """
        Create a compelling, personalized title for journal entries
        Uses story content and optional sentiment data for context
        """
        try:
            mood_context = ""
            if sentiment_data and "primary_mood" in sentiment_data:
                mood_context = f"The story has a {sentiment_data['primary_mood']} mood. "

            prompt = f"""Create an engaging title for this journal entry. {mood_context}

            Story: {story_content}

            Generate titles that are:
            - Personal and meaningful
            - Capture the essence of the day/moment
            - 3-8 words long
            - Emotionally resonant
            - Not generic or cliché

            Return as a string.

            Examples of good journal titles:
            - "Morning Coffee and Life-Changing Conversations"
            - "The Day Everything Clicked Into Place"
            - "Sunset Reflections and New Beginnings"
            - "Unexpected Adventures in My Own Backyard"

            Respond only with valid string."""

            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=messages,
                max_tokens=200,
                temperature=0.6  # Slightly higher temperature for creativity
            )

            title = response.choices[0].message.content
            return title

        except Exception as e:
            return {"error": f"Title generation failed: {str(e)}"}
