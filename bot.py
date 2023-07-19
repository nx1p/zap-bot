# Import the libraries
import discord
from discord.ext import commands
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle
import asyncio, json

# Load the config file and get the token
def get_token(config_file_location: str) -> str:
    """Open json config file and return token."""
    with open(config_file_location) as config_file:
        data = json.load(config_file)
        token = data["TOKEN"]
        return token

global bot 
global b_chat # Declare a global variable for b_chat
global CHAR_LIMIT
global preprompt

preprompt = (f"PLACEHOLDER\n")
CHAR_LIMIT = 2000 # Define a constant for the Discord character limit

# Create an intents object
intents = discord.Intents.default()
# Enable the members intent (requires verification)
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents) # Create a bot instance with intents and no prefix


async def setup_edgegpt():
    """This function is used to setup the edgegpt chatbot.
    - returns: None"""
    # Create an edgegpt chatbot instance with your cookie
    global b_chat
    cookies = json.loads(open("./secrets/bing_cookies_*.json", encoding="utf-8").read())  
    b_chat = await Chatbot.create(cookies=cookies) # Use await here

# Event handler
# - Runs when the Discord bot is ready
@bot.event
async def on_ready():
    await setup_edgegpt()
    print("Chatbot is ready")

def thread_owner_is_me(message):
    """Check if message is from a thread owned by the bot. \n
    This function is used to check if the bot should reply to a message. 
    - message: discord.Message
    - returns True if the message is in a thread owned by the bot
    - returns False otherwise"""
    if hasattr(message, "thread"): 
        if message.thread.owner == bot.user:
            return True
    else:
        return False

def should_i_reply(message):
    """This function contains the logic for deciding if the bot should reply to a message.
    - message: discord.Message
    - returns: bool
        - returns True if the bot should reply to the message
            - if
                - message is not from a bot
                - (bot is mentioned OR message is in a thread owned by the bot)
        - returns False otherwise"""
    if not message.author.bot:     # must not be from a bot
        if thread_owner_is_me(message): # or must be in a thread owned by the bot
            return True
        if bot.user.mentioned_in(message): # must contain a mention of the bot
            return True


# Event handler
# - Runs when a message is received
@bot.event
async def on_message(message):
    # Log received messages
    print(f"Message from {message.author}: {message.content}")
    # Check if the bot is mentioned or if the message is in a thread owned by the bot and the message is not from another bot
    if should_i_reply(message):
        # Check if the message content has a mention
        if bot.user.mentioned_in(message):
            # Get the message content without the mention
            message_content = message.clean_content.replace(bot.user.mention, "").strip()
        else:
            # If there is no mention, use the original message content
            message_content = message.clean_content.strip()
        # The parameters for edgegpt chatbot
        params = {
            # Use one of the ConversationStyle values here
            "conversation_style": ConversationStyle.creative,
            "simplify_response": True
        }
        # Concatenate the prompt and the user's input
        prompt = (f"{preprompt}"
                  f"{message_content}")

        # Add the prompt to the params dictionary
        params["prompt"] = prompt
        
        # Create a typing context manager with async with
        async with message.channel.typing():
            # Send the request and get the response
            # Use the asterisk operator to unpack the params dictionary
            response = await b_chat.ask(**params) # Use await here
        
        # Try to get the text from the response
        try:
            text = response["text"]
            # Check if there is already a thread for this message or create one with name "Chat"
            # Use hasattr() to check if message.thread exists
            thread = message.thread if hasattr(message, "thread") else await message.create_thread(name="Chat")
            # Check if the text is longer than the limit
            while len(text) > CHAR_LIMIT:
                # Find the last newline before the limit
                index = text.rfind("\n", 0, CHAR_LIMIT)
                # If there is no newline, use the limit as index
                if index == -1:
                    index = CHAR_LIMIT
                # Slice the text from 0 to index and store it in chunk
                chunk = text[:index]
                # Send the chunk as a reply in the thread
                await thread.send(chunk)
                # Update the text by slicing it from index to end
                text = text[index:]
            # Send the remaining text as a reply in the same thread
            await thread.send(text)
        except KeyError:
            # The response did not have a text key
            await message.channel.send("Sorry, something went wrong with the chatbot. Please try again later.")

if __name__ == "__main__": # If script run
    bot.run(get_token('./secrets/config.json')) # Run bot with token from config file