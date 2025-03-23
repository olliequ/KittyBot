from typing import TypeVar, Sequence, Callable, Coroutine
import logging
import asyncio
import hikari
import lightbulb

from behaviours import notalurker, jimmy_nerfer, messageparty
from behaviours import userinfo
from behaviours import meme_repost_blocker, meme_rater, rant_patrol, paidnotpayed
from behaviours import snark, deletes, duplicate_message_policing

_Evt = TypeVar("_Evt", bound=hikari.Event)
_Chain = Sequence[Sequence[Callable[[_Evt], Coroutine[None, None, None]]]]

_message_create_chain: _Chain[hikari.GuildMessageCreateEvent] = [
    # Message filtering & deletion
    [
        notalurker.main,
        jimmy_nerfer.delete_duplicate,
        duplicate_message_policing.delete_duplicate,
    ],
    # Stats collection & triggers
    [userinfo.analyse_message],
    [messageparty.main],
    # Only rate meme if not a repost
    [meme_repost_blocker.main],
    [meme_rater.msg_create],
    # Generic responses
    [rant_patrol.main],
    [paidnotpayed.main],
    [snark.main],
]

_message_update_chain: _Chain[hikari.GuildMessageUpdateEvent] = [
    [meme_rater.msg_update]
]

_message_delete_chain: _Chain[hikari.GuildMessageDeleteEvent] = [
    [
        deletes.delete_increment,
        duplicate_message_policing.delete_hash,
    ]
]

_reaction_add_chain: _Chain[hikari.GuildReactionAddEvent] = [
    [
        meme_rater.respond_to_question_mark,
        meme_rater.delete_meme,
    ],
    [
        userinfo.analyse_reaction,
    ],
]

_reaction_remove_chain: _Chain[hikari.GuildReactionDeleteEvent] = [
    [userinfo.remove_reaction]
]


class EndProcessing(Exception):
    pass


def register(bot: lightbulb.BotApp):
    duplicate_message_policing.load()
    meme_repost_blocker.load()
    bot.listen(hikari.GuildMessageCreateEvent)(_on_message_create)
    bot.listen(hikari.GuildMessageUpdateEvent)(_on_message_update)
    bot.listen(hikari.GuildMessageDeleteEvent)(_on_message_delete)
    bot.listen(hikari.GuildReactionAddEvent)(_on_reaction_add)
    bot.listen(hikari.GuildReactionDeleteEvent)(_on_reaction_remove)


async def _run_chain(event: _Evt, chain: _Chain[_Evt]):
    for group in chain:
        coros = map(lambda f: f(event), group)
        res = await asyncio.gather(*coros, return_exceptions=True)
        end_processing = False
        for r in res:
            if r is None:
                continue
            elif isinstance(r, EndProcessing):
                end_processing = True
            else:
                logging.exception(f"An exception occurred", exc_info=r)
        if end_processing:
            return


async def _on_message_create(event: hikari.GuildMessageCreateEvent):
    await _run_chain(event, _message_create_chain)


async def _on_message_update(event: hikari.GuildMessageUpdateEvent):
    await _run_chain(event, _message_update_chain)


async def _on_message_delete(event: hikari.GuildMessageDeleteEvent):
    await _run_chain(event, _message_delete_chain)


async def _on_reaction_add(event: hikari.GuildReactionAddEvent):
    await _run_chain(event, _reaction_add_chain)


async def _on_reaction_remove(event: hikari.GuildReactionDeleteEvent):
    await _run_chain(event, _reaction_remove_chain)
