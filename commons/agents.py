from pydantic import BaseModel, Field
from pydantic_ai.models.gemini import GeminiModelSettings, ModelSettings
from pydantic_ai.messages import BinaryContent
from pydantic_ai import Agent, RunContext
import db
from typing import Any, Final
import os
import logging as log

class KittyState(BaseModel):
    query: str = Field(description="The query to answer")
    user: str = Field(description="The user who asked the query")

class MemeState(BaseModel):
    user: str = Field(description="The user who posted the meme")

class MemeAnswer(BaseModel):
    rate: int = Field(description="The rating of the meme")  

class KittyAnswer(BaseModel):
    answer: str = Field(description="The answer to the query")

generation_config = {
    "temperature": 1,
    "top_p": 1,
    "top_k": 1,
    "max_tokens": 2000,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
]

DEFAULT_PROMPT = "You are the Savage Kitti Bot on Computer Science @ UniMelb Discord. Respond Appropriately. Kitti has a God Complex and doesn't hold back. You are gen z and reply succinct. User identity is {user}"

MEME_RATE_PROMPT: Final[str] = os.environ.get("MEME_RATING_PROMPT",
    "Rate this meme out of 10, with 10 being the funniest. Rate is solely on how funny a bunch of computer science nerds would find it. ONLY Return an integer."
)


class KittyAgent():
    def __init__(self, model_settings: ModelSettings, model: str, prompt: str = DEFAULT_PROMPT):
        self.model_settings = model_settings
        self.model = model
        self.prompt = prompt 
        self.setup_agent()    

    def setup_agent(self):
        self.agent = Agent(self.model, model_settings=self.model_settings, result_type=KittyAnswer, deps_type=KittyState)
        @self.agent.system_prompt
        def system_prompt(state: RunContext[KittyState]):
            return self.prompt.format_map(state.deps.model_dump())

    async def run(self, query: str, user: str = "ANON", prompt: str = None):
        if prompt:
            self.prompt = prompt
        state = KittyState(query=query, user=user)
        try:
            response = await self.agent.run(query, deps=state)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")            
        return response.data.answer


class KittyMemeRater():
    def __init__(self, model_settings: ModelSettings, model: str, prompt: str):
        self.model_settings = model_settings
        self.model = model
        self.prompt = prompt 
        self.setup_agent()

    def setup_agent(self):
        self.agent = Agent(self.model, model_settings=self.model_settings, deps_type=MemeState, result_type=MemeAnswer)
        @self.agent.system_prompt
        def system_prompt(state: RunContext[MemeState]):
            return self.prompt.format_map(state.deps.model_dump())

    async def run(self, image: BinaryContent, user: str = "ANON", prompt: str = None):
        if prompt:
            self.prompt = prompt
        state = MemeState(user=user)
        image = BinaryContent(data=image.content, media_type=image.headers['Content-Type'])
        try:
            response = await self.agent.run([image], deps=state)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        return response.data.rate



gemini_model_settings = GeminiModelSettings(
                                            **generation_config,  # general model settings can also be specified
                                            gemini_safety_settings=safety_settings,
                                           )

kitty_gemini_agent = KittyAgent(gemini_model_settings, 'gemini-2.0-flash-lite')

kitty_meme_agent = KittyMemeRater(gemini_model_settings, 'gemini-2.0-flash-lite', MEME_RATE_PROMPT)