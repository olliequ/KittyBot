from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import StrEnum
import json
import logging
import typing
import asyncio
import hikari
import commons.db as db


class _ActionName(StrEnum):
    DELETE_MESSAGE = "delete_message"


@dataclass
class _Arguments:
    channel_id: str
    message_id: str


_discord_bot: hikari.RESTAware | None = None


async def start(bot: hikari.RESTAware):
    global _discord_bot
    _discord_bot = bot
    actions = (
        db.cursor()
        .execute(
            "select rowid, time, action, arguments from scheduled_actions order by time asc"
        )
        .fetchall()
    )
    for rowid, time, action_name, arguments in actions:
        until_next_action = datetime.fromtimestamp(time, timezone.utc) - datetime.now(
            timezone.utc
        )
        if until_next_action.total_seconds() > 0:
            logging.info(
                f"Loaded scheduled action {action_name} to occur in {until_next_action}"
            )
            await asyncio.sleep(until_next_action.total_seconds())
        else:
            logging.info(
                f"Loaded scheduled action {action_name} was scheduled to occur {-until_next_action} ago"
            )
        try:
            await _do_action(rowid, action_name, _Arguments(**json.loads(arguments)))
        except Exception as e:
            logging.exception("An exception occurred", exc_info=e)


async def delay_delete(
    channel: hikari.Snowflake, message: hikari.Snowflake, seconds: int
):
    arguments = _Arguments(channel_id=str(channel), message_id=str(message))
    await _delay_action(_ActionName.DELETE_MESSAGE, arguments, seconds)


async def _delay_action(action: _ActionName, arguments: _Arguments, seconds: int):
    at = int((datetime.now(timezone.utc) + timedelta(seconds=seconds)).timestamp())
    c = db.cursor()
    c.execute(
        "insert into scheduled_actions values (?, ?, ?)",
        (at, action, json.dumps(asdict(arguments))),
    )
    rowid = typing.cast(int, c.lastrowid)
    db.commit()
    await asyncio.sleep(seconds)
    await _do_action(rowid, action, arguments)


async def _do_action(rowid: int, action: _ActionName | str, arguments: _Arguments):
    db.cursor().execute("delete from scheduled_actions where rowid = ?", (rowid,))
    db.commit()
    if _discord_bot is None:
        raise ValueError("Bot instance not set")
    if action == _ActionName.DELETE_MESSAGE:
        await _discord_bot.rest.delete_message(
            int(arguments.channel_id), int(arguments.message_id)
        )
    else:
        logging.warning(f"Unknown action type {action}")
