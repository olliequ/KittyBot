import lightbulb

plugin = lightbulb.Plugin("Userlist")

@plugin.command
@lightbulb.command('listusers', 'List users')
@lightbulb.implements(lightbulb.PrefixCommand)
async def main(ctx: lightbulb.Context) -> None:
    guild = ctx.get_guild()
    await ctx.app.request_guild_members(guild, include_presences=False, query='', limit=0)
    print({guild.get_member(i).username + '#' + guild.get_member(i).discriminator: i for i in guild.get_members()})
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)