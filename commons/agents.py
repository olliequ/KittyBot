from pydantic import BaseModel, Field
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from google.genai.types import SafetySettingDict, HarmCategory, HarmBlockThreshold
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.messages import BinaryContent
from pydantic_ai import Agent, RunContext
from typing import Final
import os
import logging as log
from commons.memory import memory
import requests


class KittyState(BaseModel):
    query: str = Field(description="The query to answer")
    memory: str = Field(description="The context of the conversation")
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

safety_settings: list[SafetySettingDict] = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH,
    },
]

DEFAULT_PROMPT = "You are the Savage Kitti Bot on Computer Science @ UniMelb Discord. Respond Appropriately. Kitti has a God Complex and doesn't hold back. You are gen z and reply succinct. User identity is {user}. Context of the conversation is {memory}"


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
        self.setup_agent()

    def setup_agent(self):
        self.agent = Agent(
            self.model,
            model_settings=self.model_settings,
            output_type=KittyAnswer,
            deps_type=KittyState,
        )

        @self.agent.system_prompt(dynamic=True)
        def system_prompt(  # pyright: ignore [reportUnusedFunction]
            state: RunContext[KittyState],
        ):
            return self.prompt.format_map(state.deps.model_dump())

    async def run(self, query: str, user: str = "ANON", prompt: str | None = None):
        if prompt:
            self.prompt = prompt
        user_memory = memory.get_user_context(user)
        general_memory = memory.get_global_context()
        context = f"User Context: {user_memory}\nGeneral Context: {general_memory}"
        state = KittyState(query=query, user=user, memory=context)
        try:
            response = await self.agent.run(query, deps=state)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        memory.add_turn(user, query, response.output.answer)
        return response.output.answer


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
            output_type=MemeDescription,
        )
        self.reasoner = Agent(
            self.reasoner_model, deps_type=MemeDescription, output_type=MemeAnswer
        )

        @self.eyes.system_prompt(dynamic=True)
        def system_prompt_eye(  # pyright: ignore [reportUnusedFunction]
            state: RunContext[MemeState],
        ):
            return self.eye_prompt.format_map(state.deps.model_dump())

        @self.reasoner.system_prompt(dynamic=True)
        def system_prompt_reasoner(  # pyright: ignore [reportUnusedFunction]
            state: RunContext[MemeDescription],
        ):
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
            log.info(f"Eyes response: {eyes_response.output.description}")
            response = await self.reasoner.run(
                eyes_response.output.description, deps=eyes_response.output
            )
            log.info(response.output)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        return response.output


_chat_agent: KittyAgent
_meme_rater_agent: ReasonerMemeRater


def load():
    global _chat_agent, _meme_rater_agent
    gemini_model_settings = GoogleModelSettings(
        **generation_config,  # general model settings can also be specified
        google_safety_settings=safety_settings,
    )
    fallback_model = FallbackModel(
        GoogleModel("gemini-3-flash-preview"),
        GoogleModel("gemini-2.5-flash"),
        GoogleModel("gemini-2.5-flash-lite"),
    )
    _chat_agent = KittyAgent(gemini_model_settings, fallback_model)
    _meme_rater_agent = ReasonerMemeRater(
        gemini_model_settings,
        fallback_model,
        fallback_model,
        EYE_RATE_PROMPT,
        REASONER_MEME_PROMPT,
    )


def chat_agent() -> KittyAgent:
    return _chat_agent


def meme_rater_agent() -> ReasonerMemeRater:
    return _meme_rater_agent
