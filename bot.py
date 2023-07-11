# Import the libraries
import discord
from discord.ext import commands
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle
import asyncio, json

preprompt = (f"PLACEHOLDER\n")

# Create an intents object
intents = discord.Intents.default()
# Enable the members intent (requires verification)
intents.members = True
intents.message_content = True

# Load the config file and get the token
with open('./secrets/config.json') as f:
  data = json.load(f)
  token = data["TOKEN"]

# Create a bot instance with intents and a fixed prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Declare a global variable for the chatbot
chatbot = None

# Define a constant for the character limit
CHAR_LIMIT = 2000

# Write an event handler that runs when the bot is ready
@bot.event
async def on_ready():
    global chatbot # Use the global variable
    # Create an edgegpt chatbot instance with your cookie
    # cookies may not be required
    #chatbot = await Chatbot(cookie="_U=your_cookie_here")
    cookies = json.loads(open("./secrets/bing_cookies_*.json", encoding="utf-8").read())  # might omit cookies option
    chatbot = await Chatbot.create(cookies=cookies) # Use await here
    print("Chatbot is ready")

# Write a command that sends a message to edgegpt chatbot and receives a response
@bot.command()
async def chat(ctx, *, message):
    # The parameters for edgegpt chatbot
    params = {
        # Use one of the ConversationStyle values here
        "conversation_style": ConversationStyle.creative,
        "simplify_response": True
    }
    # Concatenate the prompt and the user's input
    prompt = (f"{preprompt}"
              f"{message}")

    # Add the prompt to the params dictionary
    params["prompt"] = prompt
    
    # Create a typing context manager with async with
    async with ctx.typing():
        # Send the request and get the response
        # Use the asterisk operator to unpack the params dictionary
        response = await chatbot.ask(**params) # Use await here
    
    # Try to get the text from the response
    try:
        text = response["text"]
        # Create a new thread from the user's message with name "Chat"
        thread = await ctx.message.create_thread(name="Chat")
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
        await ctx.send("Sorry, something went wrong with the chatbot. Please try again later.")

# Run your bot with your token from config file
bot.run(token)
