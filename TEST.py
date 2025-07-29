import discord
from discord.ext import commands
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.invites = True  # Enable invite tracking
intents.members = True  # Enable member tracking
intents.guilds = True   # Enable guild tracking

bot = commands.Bot(command_prefix='!', intents=intents)

# Store invites for each guild
guild_invites = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    
    # Store all existing invites for each guild
    for guild in bot.guilds:
        try:
            # Fetch and store all guild invites
            guild_invites[guild.id] = await guild.invites()
            print(f"Cached invites for {guild.name}")
        except discord.Forbidden:
            print(f"No permission to fetch invites for {guild.name}")
        except Exception as e:
            print(f"Error caching invites for {guild.name}: {e}")

@bot.event
async def on_invite_create(invite):
    """Log when a new invite is created"""
    guild = invite.guild
    inviter = invite.inviter
    
    # Format expiration time if it exists
    expires = f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Never"
    
    # Create embed for logging
    embed = discord.Embed(
        title="Invite Created",
        description=f"A new invite has been created for {guild.name}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name="Invite Code", value=invite.code, inline=True)
    embed.add_field(name="Created By", value=f"{inviter.name} ({inviter.id})", inline=True)
    embed.add_field(name="Channel", value=f"#{invite.channel.name}", inline=True)
    embed.add_field(name="Max Uses", value=invite.max_uses if invite.max_uses else "Unlimited", inline=True)
    embed.add_field(name="Expires", value=expires, inline=True)
    
    # Update our invite cache
    if guild.id in guild_invites:
        guild_invites[guild.id] = await guild.invites()
    
    # Send log to a designated channel
    log_channel = discord.utils.get(guild.text_channels, name="invite-logs")
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"No invite-logs channel found in {guild.name}")

@bot.event
async def on_invite_delete(invite):
    """Log when an invite is deleted"""
    guild = invite.guild
    
    embed = discord.Embed(
        title="Invite Deleted",
        description=f"An invite has been deleted from {guild.name}",
        color=discord.Color.red(),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name="Invite Code", value=invite.code, inline=True)
    embed.add_field(name="Channel", value=f"#{invite.channel.name}", inline=True)
    
    # Update our invite cache
    if guild.id in guild_invites:
        guild_invites[guild.id] = await guild.invites()
    
    # Send log to a designated channel
    log_channel = discord.utils.get(guild.text_channels, name="invite-logs")
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"No invite-logs channel found in {guild.name}")

@bot.event
async def on_member_join(member):
    """Track which invite was used when a member joins"""
    guild = member.guild
    
    # If we don't have the invites cached, we can't determine which one was used
    if guild.id not in guild_invites:
        try:
            guild_invites[guild.id] = await guild.invites()
            print(f"Cached invites for {guild.name} after member join")
            return  # We don't have the before state to compare
        except Exception as e:
            print(f"Error caching invites for {guild.name}: {e}")
            return
    
    # Get the invites before the user joined
    invites_before = guild_invites[guild.id]
    
    # Get the invites after the user joined
    try:
        invites_after = await guild.invites()
        guild_invites[guild.id] = invites_after  # Update our cache
    except Exception as e:
        print(f"Error fetching invites after member join: {e}")
        return
    
    # Find the invite that was used
    used_invite = None
    inviter = None
    
    for invite_after in invites_after:
        # Find the matching invite from our before list
        for invite_before in invites_before:
            if invite_before.code == invite_after.code:
                # If the use count has gone up, this is the one
                if invite_after.uses > invite_before.uses:
                    used_invite = invite_after
                    inviter = used_invite.inviter
                    break
        
        if used_invite:
            break
    
    # Create an embed for logging
    embed = discord.Embed(
        title="Member Joined",
        description=f"{member.name} ({member.id}) has joined {guild.name}",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    
    if used_invite:
        embed.add_field(name="Invite Used", value=used_invite.code, inline=True)
        embed.add_field(name="Invite Creator", value=f"{inviter.name} ({inviter.id})" if inviter else "Unknown", inline=True)
        embed.add_field(name="Invite Channel", value=f"#{used_invite.channel.name}", inline=True)
        embed.add_field(name="Total Uses", value=used_invite.uses, inline=True)
    else:
        embed.add_field(name="Invite Used", value="Could not determine", inline=True)
    
    # Send log to a designated channel
    log_channel = discord.utils.get(guild.text_channels, name="invite-logs")
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"No invite-logs channel found in {guild.name}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def invites(ctx, member: discord.Member = None):
    """Show all invites created by a user or all invites for the server"""
    if member:
        # Get all invites created by the specified member
        invites = [invite for invite in await ctx.guild.invites() if invite.inviter.id == member.id]
        title = f"Invites created by {member.name}"
    else:
        # Get all invites for the server
        invites = await ctx.guild.invites()
        title = f"All invites for {ctx.guild.name}"
    
    if not invites:
        await ctx.send("No invites found.")
        return
    
    # Create an embed to display the invites
    embed = discord.Embed(
        title=title,
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    
    for invite in invites:
        expires = f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Never"
        value = (
            f"Creator: {invite.inviter.name}\n"
            f"Channel: #{invite.channel.name}\n"
            f"Uses: {invite.uses}/{invite.max_uses if invite.max_uses else '∞'}\n"
            f"Expires: {expires}"
        )
        embed.add_field(name=f"Invite: {invite.code}", value=value, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_invite_logs(ctx):
    """Create an invite-logs channel if it doesn't exist"""
    # Check if the channel already exists
    if discord.utils.get(ctx.guild.text_channels, name="invite-logs"):
        await ctx.send("The invite-logs channel already exists!")
        return
    
    # Create the channel with appropriate permissions
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        # Add permissions for moderators/admins as needed
    }
    
    try:
        channel = await ctx.guild.create_text_channel(
            'invite-logs', 
            overwrites=overwrites,
            reason="Created for invite logging"
        )
        await ctx.send(f"Created {channel.mention} for invite logging!")
    except Exception as e:
        await ctx.send(f"Failed to create channel: {e}")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))