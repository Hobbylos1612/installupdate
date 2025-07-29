import discord
import subprocess
import os

TOKEN = "krNI_N-vtkVBVDigHITIflQld4_NsxAa"  # Replace with your actual Discord bot token
AUTHORIZED_USER_IDS = {1125833421739003976}  # Replace with your Discord user IDs

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def update_repo():
    result = subprocess.run(
        ["git", "pull"], cwd=REPO_DIR, capture_output=True, text=True, shell=True
    )
    return result.stdout + result.stderr

def run_script():
    result = subprocess.run(
        ["python", "main.py"], cwd=REPO_DIR, capture_output=True, text=True, shell=True
    )
    return result.stdout + result.stderr

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.author.id not in AUTHORIZED_USER_IDS:
        return
    if message.content.lower().startswith("!update"):
        await message.channel.send("Updating repo and running script...")
        pull_output = update_repo()
        await message.channel.send(f"Git pull output:\n```\n{pull_output}\n```")
        run_output = run_script()
        await message.channel.send(f"Script output:\n```\n{run_output}\n```")

if __name__ == "__main__":
    client.run(TOKEN)
