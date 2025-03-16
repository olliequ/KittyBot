from pydantic import BaseModel, Field
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.gemini import GeminiModel, GeminiModelSettings, GeminiSafetySettings
from pydantic_ai.messages import BinaryContent, ModelMessage
from pydantic_ai import Agent, RunContext
from typing import Final
import os
import logging as log
from collections import deque

import requests

class KittyState(BaseModel):
    query: str = Field(description="The query to answer")
    user: str = Field(description="The user who asked the query")


class MemeState(BaseModel):
    user: str = Field(description="The user who posted the meme")


class MemeAnswer(BaseModel):
    rate: int = Field(description="The rating of the meme")
    explanation: str = Field(description="The explanation of the rating")


class MemeDescription(BaseModel):
    description: str = Field(description="The textual description of the meme")


class KittyAnswer(BaseModel):
    answer: str = Field(description="The answer to the query")


generation_config: ModelSettings = {
    "temperature": 1,
    "max_tokens": 2000,
}

safety_settings: list[GeminiSafetySettings] = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

DEFAULT_PROMPT = "You are the Savage Kitti Bot on Computer Science @ UniMelb Discord. Respond Appropriately. Kitti has a God Complex and doesn't hold back. You are gen z and reply succinct. User identity is {user}"


EYE_RATE_PROMPT: Final[str] = os.environ.get(
    "EYE_RATING_PROMPT",
    "Describe this image, please do not leave any detail out, just describe it do not give any opinions on it unless is not a meme, then explain why. Ensure that the image is a meme and not debug or simple coding screenshots, that is code or debug output without any context. If you found this just said this is not a meme",
)

REASONER_MEME_PROMPT: Final[str] = os.environ.get(
    "REASONER_MEME_PROMPT",
    """
    Rate the following meme on a scale from 1 to 10, where 10 is the funniest.
    The rating should be based solely on how humorous a group of computer science enthusiasts—particularly those familiar with algorithms, programming languages, system design, debugging struggles, and internet culture—would find it.
    Prioritize technical wit, inside jokes, and references to common CS experiences (e.g., recursion jokes, stack overflows, regex pain).
    Do NOT factor in general audience appeal.
    If the description said is not a meme, factors the explanation in your rate and give a 0. 
    ONLY return an integer.
    """,
)


class KittyAgent:
    def __init__(
        self, model_settings: ModelSettings, model: Model, prompt: str = DEFAULT_PROMPT
    ):
        self.model_settings = model_settings
        self.model = model
        self.prompt = prompt
        self.messages: deque[ModelMessage] = deque(maxlen=10)
        self.setup_agent()

    def setup_agent(self):
        self.agent = Agent(
            self.model,
            model_settings=self.model_settings,
            result_type=KittyAnswer,
            deps_type=KittyState,
        )

        @self.agent.system_prompt
        def system_prompt(state: RunContext[KittyState]): # pyright: ignore [reportUnusedFunction]
            return self.prompt.format_map(state.deps.model_dump())

    async def run(self, query: str, user: str = "ANON", prompt: str | None = None):
        if prompt:
            self.prompt = prompt
        state = KittyState(query=query, user=user)
        try:
            response = await self.agent.run(
                query, deps=state, message_history=list(self.messages)
            )
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        for messages in response.new_messages():
            self.messages.append(messages)
        return response.data.answer


class ReasonerMemeRater:
    def __init__(
        self,
        eye_model_settings: ModelSettings,
        eye_model: Model,
        reasoner_model: Model,
        eye_prompt: str,
        reasoner_prompt: str,
    ):
        self.eye_model_settings = eye_model_settings
        self.eye_model = eye_model
        self.reasoner_model = reasoner_model
        self.eye_prompt = eye_prompt
        self.reasoner_prompt = reasoner_prompt
        self.setup_agent()

    def setup_agent(self):
        self.eyes = Agent(
            self.eye_model,
            model_settings=self.eye_model_settings,
            deps_type=MemeState,
            result_type=MemeDescription,
        )
        self.reasoner = Agent(
            self.reasoner_model, deps_type=MemeDescription, result_type=MemeAnswer
        )

        @self.eyes.system_prompt
        def system_prompt_eye(state: RunContext[MemeState]): # pyright: ignore [reportUnusedFunction]
            return self.eye_prompt.format_map(state.deps.model_dump())

        @self.reasoner.system_prompt
        def system_prompt_reasoner(state: RunContext[MemeDescription]): # pyright: ignore [reportUnusedFunction]
            return self.reasoner_prompt.format_map(state.deps.model_dump())

    async def run(
        self, web_image: requests.Response, user: str | None, prompt: str | None = None
    ) -> MemeAnswer:
        if prompt:
            self.prompt = prompt
        state = MemeState(user=user if user else "ANON")
        image = BinaryContent(
            data=web_image.content, media_type=web_image.headers["Content-Type"]
        )
        try:
            eyes_response = await self.eyes.run([image], deps=state)
            log.info(f"Eyes response: {eyes_response.data.description}")
            response = await self.reasoner.run(
                eyes_response.data.description, deps=eyes_response.data
            )
            log.info(response.data)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        return response.data


_chat_agent: KittyAgent
_meme_rater_agent: ReasonerMemeRater

def load():
    global _chat_agent, _meme_rater_agent
    gemini_model_settings = GeminiModelSettings(
        **generation_config,  # general model settings can also be specified
        gemini_safety_settings=safety_settings,
    )
    _chat_agent = KittyAgent(gemini_model_settings, GeminiModel("gemini-2.0-flash-lite"))
    _meme_rater_agent = ReasonerMemeRater(
        gemini_model_settings,
        GeminiModel("gemini-2.0-flash-lite"),
        GeminiModel("gemini-2.0-flash-lite"),
        EYE_RATE_PROMPT,
        REASONER_MEME_PROMPT,
    )


def chat_agent() -> KittyAgent:
    return _chat_agent

def meme_rater_agent() -> ReasonerMemeRater:
    return _meme_rater_agent