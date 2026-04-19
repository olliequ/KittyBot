import asyncio
import random
from typing import TypedDict

import aiohttp
from bs4 import BeautifulSoup
import lightbulb

plugin = lightbulb.Plugin("IsTheStraitClosed")

STATUS_API_URL = "https://isthestraitclosed.com/api/status"


class StatusDetails(TypedDict):
    label: str
    sublabel: str


STATUS_MAP: dict[str, StatusDetails] = {
    "CLOSED": {
        "label": "YES",
        "sublabel": "The Strait of Hormuz is effectively closed",
    },
    "DISPUTED": {
        "label": "EFFECTIVELY, YES",
        "sublabel": "Iran has announced closure — most shipping is avoiding the strait",
    },
    "THREATENED": {
        "label": "NOT YET",
        "sublabel": "Tensions are elevated but the strait remains open to most traffic",
    },
    "OPEN": {
        "label": "NO",
        "sublabel": "The Strait of Hormuz is open for transit",
    },
}

DEFAULT_STATUS: StatusDetails = {
    "label": "UNKNOWN",
    "sublabel": "Kitti couldn't confidently determine the strait status right meow.",
}

LOADING_MESSAGES = [
    "Kitti is sniffing for the oil... 🐾",
    "Kitti is chasing tankers on the radar... ⛴️",
    "Kitti is checking maritime meow-nitoring feeds... 📡",
]


def _clean_summary(summary: str) -> str:
    return BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)


def _format_response(status: str, summary: str) -> str:
    status_details = STATUS_MAP.get(status, DEFAULT_STATUS)
    return f"{status_details['label']}\n{status_details['sublabel']}\n{summary}"


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command(
    "isthestraitclosed", description="Checks whether the Strait of Hormuz is closed."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(random.choice(LOADING_MESSAGES))
    bot = plugin.bot
    session = getattr(bot.d, "aio_session", None)
    if not isinstance(session, aiohttp.ClientSession) or session.closed:
        await ctx.edit_last_response(
            "Kitti can't reach the maritime scanners right meow. Try again in a bit."
        )
        return

    try:
        async with session.get(
            STATUS_API_URL, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status != 200:
                await ctx.edit_last_response(
                    f"Kitti couldn't fetch the strait status (HTTP {response.status})."
                )
                return
            payload = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        await ctx.edit_last_response(
            "Kitti couldn't reach the strait status service right meow."
        )
        return

    status = str(payload.get("status", "")).upper()
    raw_summary = payload.get("summary")
    summary = (
        _clean_summary(raw_summary)
        if isinstance(raw_summary, str) and raw_summary.strip()
        else "No summary available."
    )

    await ctx.edit_last_response(_format_response(status, summary))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
