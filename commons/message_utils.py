from typing import Dict, Any

DISCORD_MESSAGE_LIMIT = 2000

def split_message(content: str) -> list[str]:
    """
    Split a message into multiple parts if it exceeds Discord's character limit.
    
    Args:
        content (str): The message content to split
        
    Returns:
        list[str]: List of message parts that are within Discord's character limit
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

async def send_long_message(ctx, content: str, **kwargs) -> None:
    """
    Send a message that might exceed Discord's character limit by splitting it into multiple messages.
    
    Args:
        ctx: The command context or message object with a respond method
        content (str): The message content to send
        **kwargs: Additional keyword arguments to pass to the respond method
                 (e.g., user_mentions=True, reply=True)
    """
    message_parts = split_message(content)
    
    # Send the first part with all kwargs (including reply=True if provided)
    if message_parts:
        await ctx.respond(message_parts[0], **kwargs)
    
    # Send any remaining parts without the reply flag
    # This prevents all messages from being replies to the original message
    remaining_kwargs = kwargs.copy()
    if 'reply' in remaining_kwargs:
        del remaining_kwargs['reply']
    
    for part in message_parts[1:]:
        await ctx.respond(part, **remaining_kwargs) 