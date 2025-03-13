import lightbulb
from commons.message_utils import send_long_message

plugin = lightbulb.Plugin("test_split")

@plugin.command
@lightbulb.command("test_split", "Test message splitting functionality")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    # Test case 1: Message under limit
    short_message = "This is a short message that should not be split."
    await send_long_message(ctx, short_message)
    
    # Test case 2: Message exactly at limit
    at_limit = "a" * 2000
    await send_long_message(ctx, at_limit)
    
    # Test case 3: Long message with newlines
    long_with_newlines = "Line 1\n" + ("Medium length line that should be kept together\n" * 50)
    await send_long_message(ctx, long_with_newlines)
    
    # Test case 4: Very long line without spaces
    long_no_spaces = "x" * 3000
    await send_long_message(ctx, long_no_spaces)
    
    # Test case 5: Long message with mixed content
    mixed_content = (
        "This is a test of mixed content splitting.\n"
        + ("Some regular lines that should stay together.\n" * 20)
        + ("a" * 1500) + "\n"
        + "Final line with some content"
    )
    await send_long_message(ctx, mixed_content)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin) 