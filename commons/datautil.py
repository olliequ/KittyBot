"""
Wrapper functions for getting various discord data. For fullest
correctness these should make a rest query when the entity is not
found in the hikari cache, but in reality the cache is fully
populated for guilds & members unless something goes wrong or
there are > 75k members. So we ignore that possibility.
"""

import hikari
import typing as t

class NoEntityError(Exception):
    pass

class _GuildProvider(t.Protocol):
    def get_guild(self) -> t.Optional[hikari.Guild]: ...

def get_member(ctx: _GuildProvider, user_id: hikari.Snowflakeish) -> hikari.Member:
    guild = ctx.get_guild()
    if guild is None:
        raise NoEntityError("Cannot get context guild")
    member = guild.get_member(user_id)
    if member is None:
        raise NoEntityError(f"Unknown member {user_id}")
    return member