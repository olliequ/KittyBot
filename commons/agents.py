from pydantic import BaseModel, Field
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.gemini import (
    GeminiModel,
    GeminiModelSettings,
    GeminiSafetySettings,
)
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import BinaryContent
from pydantic_ai import Agent, RunContext
from typing import Final
import os
import logging as log
from commons.memory import memory
import requests
import asyncio
import re
import uuid

SIM_THRESHOLD: float = float(os.getenv("KITTY_SIM_THRESHOLD", 0.35))  # Chroma distance
TOP_K: int = int(os.getenv("KITTY_TOP_K", 6))  # fetch extra → filter
MAX_TOKENS: int = int(os.getenv("KITTY_CONTEXT_TOKENS", 1024))  # model context size

# Private Information Identification Regex
PII_RE = re.compile(
    r"(?i)\b(?:\d{3}-\d{2}-\d{4}|[\w\.-]+@\w+\.\w+|"
    r"\+?\d{1,3}(?:\s|-)\d{2,4}(?:\s|-)\d{2,4}(?:\s|-)?\d{2,4})\b"
)


def pii_redact(text: str) -> str:
    """Very small-footprint PII redactor; extend as needed."""
    return PII_RE.sub("[REDACTED]", text)


def rough_token_count(text: str) -> int:
    """Cheap token estimator; ~4 chars per token for English/Gemini."""
    return len(text) // 4 + 1


async def summarise_if_needed(text: str, agent: Agent, budget: int) -> str:
    """Summarise with the same model if the text overflows `budget` tokens."""
    prompt = f"""
    Please read the following text carefully and write a concise summary with key facts in bullet points.
    The following text provides context of conversation between an ai and the user and some general conversation with other users:\n
    {text}
    Summary:
    """
    result = await agent.run(prompt)
    clean_result = re.sub(r"<think>.*?</think>", "", result.data, flags=re.DOTALL)  # type: ignore[attr-defined]
    return clean_result


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
    "temperature": 0.7,
    "max_tokens": 2000,
}

local_config: ModelSettings = {**generation_config, "num_ctx": 4096}

safety_settings: list[GeminiSafetySettings] = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

DEFAULT_PROMPT = "You are the Savage Kitti Bot on Computer Science @ UniMelb Discord. Respond Appropriately. Kitti has a God Complex and doesn't hold back. You are gen z and reply succinct. User identity is {user}. You can recall the following memory: {memory}"


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
            result_type=KittyAnswer,
            deps_type=KittyState,
            retries=2,
        )
        ollama_model = OpenAIModel(
            model_name="qwen3:0.6b",
            provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
        )
        aux_config = ModelSettings(**local_config)
        aux_config["temperature"] = 0.1
        self.aux = Agent(
            ollama_model,
            model_settings=aux_config,
            retries=2,
        )

        @self.agent.system_prompt(dynamic=True)
        def system_prompt(  # pyright: ignore [reportUnusedFunction]
            state: RunContext[KittyState],
        ):
            log.info(self.prompt.format_map(state.deps.model_dump()))
            return self.prompt.format_map(state.deps.model_dump())

    async def run(self, query: str, user: str = "ANON", prompt: str | None = None):
        if prompt:
            self.prompt = prompt

        # -------- parallel Chroma queries --------
        async def q_user():
            return memory.query(
                query_texts=[query],
                n_results=TOP_K,
                include=["documents", "distances"],
                where={"user": user},
            )

        async def q_gen():
            return memory.query(
                query_texts=[query],
                n_results=TOP_K,
                include=["documents", "distances"],
            )

        # -------- filter by similarity threshold --------
        def filter_docs(res):
            if not res["documents"]:
                return []
            docs = res["documents"][0]
            dists = res["distances"][0]
            return [d for d, dist in zip(docs, dists) if dist < SIM_THRESHOLD]

        user_res, gen_res = await asyncio.gather(q_user(), q_gen())
        user_memory = "\n".join(
            [document for document in user_res["documents"][0]]
            if user_res["documents"]
            else []
        )
        general_memory = memory.query(query_texts=[query], n_results=5)
        general_memory = "\n".join(
            [document for document in gen_res["documents"][0]]
            if gen_res["documents"]
            else []
        )
        raw_context = f"User Context: {user_memory}\nGeneral Context: {general_memory}"
        context = await summarise_if_needed(raw_context, self.aux, MAX_TOKENS)
        log.info(f"context: {context}\n\n")
        state = KittyState(query=query, user=user, memory=context)
        try:
            response = await self.agent.run(query, deps=state)
        except Exception as e:
            raise Exception(f"Error running agent: {e}")
        log.info(f"response: {response.data.answer}\n\n")
        messages = (
            f"\nUser {user} query: {query}\nAssistant response: {response.data.answer}"
        )
        memory.add(
            ids=[str(uuid.uuid4())], metadatas=[{"user": user}], documents=[messages]
        )
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
_local_agent: KittyAgent


def load():
    global _chat_agent, _meme_rater_agent, _local_agent, local_config
    gemini_model_settings = GeminiModelSettings(
        **generation_config,  # general model settings can also be specified
        gemini_safety_settings=safety_settings,
    )
    _chat_agent = KittyAgent(gemini_model_settings, GeminiModel("gemini-2.0-flash"))
    _meme_rater_agent = ReasonerMemeRater(
        gemini_model_settings,
        GeminiModel("gemini-2.0-flash-lite"),
        GeminiModel("gemini-2.0-flash-lite"),
        EYE_RATE_PROMPT,
        REASONER_MEME_PROMPT,
    )
    ollama_model = OpenAIModel(
        model_name="qwen3:1.7b",
        provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
    )
    _local_agent = KittyAgent(
        model_settings=local_config,
        model=ollama_model,
    )


def chat_agent() -> KittyAgent:
    return _chat_agent


def local_agent() -> KittyAgent:
    return _local_agent


def meme_rater_agent() -> ReasonerMemeRater:
    return _meme_rater_agent
