import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
import json
from tools.image_captioning import ImageCaptioningTool
from tools.story_generation import StoryGenerationTool
from tools.story_analysis import StoryAnalysisTool

class MemoirAIServer:
    def __init__(self):
        self.server = Server("memoirai-storyteller")
        self.image_captioner = ImageCaptioningTool()
        self.story_generator = StoryGenerationTool()
        self.story_analysis = StoryAnalysisTool()

        self._register_handlers()


    def _register_handlers(self):
        """Register MCP handlers"""

        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool


    async def list_tools(self):
        """Define available tools for the LLM"""
        return [
            Tool(
                name = "caption_image",
                description = "Analyze an image and provide a detailed caption",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_data": {"type": "string", "description": "Base64 encoded image"},
                        "image_format": {"type": "string", "description": "Image format(jpg, png, etc.)"}
                    },
                    "required": ["image_data"]
                }
            ),
            Tool (
                name = "generate_story",
                description = "Create a cohesive story from image captions and context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "captions": {"type": "array", "items": {"type": "string"}},
                        "user_context": {"type": "string"},
                        "tone": {"type": "string", "enum": ["whimsical", "nostalgic", "adventurous", "heartwarming"]}
                    },
                    "required": ["captions"]
                }
            ),

            Tool(
                name="analyze_story_sentiment",
                description="Analyze the emotional tone, themes, and mood of a journal entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "story_content": {"type": "string", "description": "The journal entry text to analyze"}
                    },
                    "required": ["story_content"]
                }
            ),
            Tool(
                name="generate_story_title",
                description="Create compelling, personalized titles for journal entries",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "story_content": {"type": "string", "description": "The journal entry content"},
                        "sentiment_data": {"type": "object", "description": "Optional sentiment analysis data for context"}
                    },
                    "required": ["story_content"]
                }
            )
        ]
    
    async def call_tool(self, name:str, arguments: dict):
        """Route tools calls to appropriate handlers"""

        if name == "caption_image":
            result = await self.image_captioner.caption_image(
                arguments["image_data"],
                arguments.get("image_format", "jpeg")
            )
            return TextContent(type="text", text=result)
        
        elif name == "generate_story":
            result = await self.story_generator.generate_story(
                arguments["captions"],
                arguments.get("user_context", ""),
                arguments.get("tone", "heartwarming")
            )
            return TextContent(type="text", text=result)
        
        elif name == "analyze_story_sentiment":
            result = await self.story_analysis.analyze_story_sentiment(
                arguments["story_content"],
            )
            return TextContent(type="text", text=json.dumps(result, indent=2))
        
        elif name == "generate_story_title":
            result = await self.story_analysis.generate_story_title(
                arguments["story_content"],
                arguments.get("sentiment_data", {}),
            )
            return TextContent(type="text", text=result)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
    def run(self):
        asyncio.run(self.server.run())

if __name__ == "__main__":
    server = MemoirAIServer()
    server.run()