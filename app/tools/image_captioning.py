import asyncio
from openai import AzureOpenAI
from config.settings import settings

class ImageCaptioningTool:
    def __init__(self):
        self.client = AzureOpenAI(
            api_version="2025-01-01-preview",
            azure_endpoint="https://memoir-ai-resource.cognitiveservices.azure.com/",
            api_key=settings.OPENAI_API_KEY
        )

    async def caption_image(self, image_data: str, image_format: str):
        try:
            messages = [
                {
                    "role":"user",
                    "content": [
                        {
                            "type":"text",
                            "text": """Describe this image in blunt detail for journaling purposes. Focus on the emotions, setting, people, action, and memorable moments captured. 
                                    Do not add your own description, just analyze the image itself.
                                    IMPORTANT: Each caption should only be 1-2 concise sentences.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{image_data}"
                            }
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                messages = messages,
                model="gpt-4o",
                max_tokens = 300
            )

            

            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"