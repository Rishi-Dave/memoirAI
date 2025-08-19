import asyncio
from openai import AzureOpenAI
from config.settings import settings

class StoryGenerationTool():
    def __init__(self):
        self.client = AzureOpenAI(
            api_version="2025-01-01-preview",
            azure_endpoint="https://memoir-ai-resource.cognitiveservices.azure.com/",
            api_key=settings.OPENAI_API_KEY
        )


    async def generate_story(self, captions: list, user_context: str = "", tone: str="heartwarming"):
        try:
            captions_text = "\n".join(captions)
            prompt = f"""Create a {tone} journal entry from these image descriptions:
            {captions_text}
            More context from the user: {user_context}
            Write a short, meaningful entry summarizes how the user's day went
            
            """
            messages = [
                {
                    "role":"user",
                    "content": prompt
                }
            ]
        
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages = messages,
                max_tokens = 300
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

