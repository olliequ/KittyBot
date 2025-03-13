from typing import List

DISCORD_MESSAGE_LIMIT = 2000

def split_message(content: str) -> List[str]:
    """
    Split a message into multiple parts if it exceeds Discord's character limit.
    
    Args:
        content (str): The message content to split
        
    Returns:
        List[str]: List of message parts that are within Discord's character limit
    """
    if len(content) <= DISCORD_MESSAGE_LIMIT:
        return [content]
    
    messages = []
    current_message = ""
    
    # Split by newlines first to try to keep logical breaks
    lines = content.split('\n')
    
    for line in lines:
        # If adding this line would exceed the limit
        if len(current_message) + len(line) + 1 > DISCORD_MESSAGE_LIMIT:
            # If the line itself is longer than the limit
            if len(line) > DISCORD_MESSAGE_LIMIT:
                # If we have a current message, add it to messages
                if current_message:
                    messages.append(current_message.strip())
                    current_message = ""
                
                # Split the long line into chunks
                while line:
                    # Find a good breaking point (space) near the limit
                    split_point = DISCORD_MESSAGE_LIMIT
                    if len(line) > DISCORD_MESSAGE_LIMIT:
                        # Try to split at a space
                        space_index = line[:DISCORD_MESSAGE_LIMIT].rfind(' ')
                        if space_index != -1:
                            split_point = space_index + 1
                    
                    messages.append(line[:split_point].strip())
                    line = line[split_point:].strip()
            else:
                # Add current message and start a new one
                messages.append(current_message.strip())
                current_message = line + '\n'
        else:
            current_message += line + '\n'
    
    # Add any remaining content
    if current_message:
        messages.append(current_message.strip())
    
    return messages

async def send_long_message(ctx, content: str) -> None:
    """
    Send a message that might exceed Discord's character limit by splitting it into multiple messages.
    
    Args:
        ctx: The command context
        content (str): The message content to send
    """
    message_parts = split_message(content)
    
    for part in message_parts:
        await ctx.respond(part) 