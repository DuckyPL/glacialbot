import asyncio
import random
import time

from datetime import datetime
import json

import discord
from discord.ext import commands

import aiohttp
import requests

from utils import cooldowns
from utils.jsonLoader import read_json
from utils.util import (
    CreateNewTicket,
    SudoCreateNewTicket,
    CloseTicket,
    IsATicket,
    ReactionCreateNewTicket,
    SetupNewTicketMessage,
    CheckIfValidReactionMessage,
    ReactionCloseTicket,
)

config = read_json("config")
secret = read_json("secrets")
baseurl = "https://duckypl.pythonanywhere.com/"

command_prefix=['$', '<@814799034950746112> ', '<@814799034950746112>']
intents = discord.Intents.default()
intents.members = True
servername = config["serverName"]
description = f'''A multi-purpose Discord bot for the {servername} server.'''
bot = commands.Bot(command_prefix=command_prefix, description=description)
cid = 810241344295534652

bot.new_ticket_channel_id = 810122282793828364
bot.log_channel_id = 812043079905050624
bot.category_id = 810246662751780915
bot.staff_role_id = 810123961283117086

bot.remove_command('help')

on_cooldown = {}


def cooldown(seconds):
    def predicate(context):
        if (cooldown_end := on_cooldown.get(context.author.id)) is None or cooldown_end < datetime.datetime.now():
            if context.valid and context.invoked_with in (*context.command.aliases, context.command.name):
                on_cooldown[context.author.id] = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            return True
        else:
            raise commands.CommandOnCooldown(commands.BucketType.user, (cooldown_end - datetime.datetime.now()).seconds)
    return commands.check(predicate)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name="@GlacialBot help | $help"))
    

@bot.event
async def on_member_join(member):
    return


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please pass in all arguments.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the permissions to run this command.")

        @bot.event
        async def on_raw_reaction_add(payload):

            if payload.user_id == bot.user.id:
                return


            reaction = str(payload.emoji)
            if reaction not in ["🔒", "✅"]:
                return


            if not payload.channel_id == bot.new_ticket_channel_id and not IsATicket(
                    str(payload.channel_id)
            ):
                return


            if not CheckIfValidReactionMessage(payload.message_id):
                return



            data = read_json("config")
            if payload.message_id == data["ticketSetupMessageId"] and reaction == "✅":
                # We want a new ticket...
                await ReactionCreateNewTicket(bot, payload)


                guild = bot.get_guild(payload.guild_id)
                member = await guild.fetch_member(payload.user_id)

                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction("✅", member)

                return

            elif reaction == "🔒":

                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await message.add_reaction("✅")

            elif reaction == "✅":

                guild = bot.get_guild(payload.guild_id)
                member = await guild.fetch_member(payload.user_id)

                channel = bot.get_channel(payload.channel_id)
                await ReactionCloseTicket(bot, channel, member)

        @bot.event
        async def on_raw_reaction_remove(payload):

            if payload.user_id == bot.user.id:
                return


            reaction = str(payload.emoji)
            if reaction not in ["🔒"]:
                return


            if not payload.channel_id == bot.new_ticket_channel_id and not IsATicket(
                    str(payload.channel_id)
            ):
                return


            if not CheckIfValidReactionMessage(payload.message_id):
                return

            if reaction == "🔒":

                guild = bot.get_guild(payload.guild_id)
                member = await guild.fetch_member(bot.user.id)

                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction("✅", member)


@bot.command()
@commands.has_role("Staff")
async def help(ctx, *args):

    embed = discord.Embed(title="Command List", description="`[]` means optional arg and `<>` means required arg", colour=discord.Colour.red())
    embed.add_field(name="**$help**", value="Brings you to this page.")
    embed.add_field(name="**$prefix**", value="Gets the prefix of the bot.")
    embed.add_field(name="**$avatar [\\@user]**", value="Gets your avatar or someones avatar.")
    embed.add_field(name="**$whois [\\@user]**", value="Shows user information about a specific player.")
    embed.add_field(name="**$new [subject]**", value="Creates a ticket with the specified subject.")
    embed.add_field(name="**$ping**", value="Pings the Discord API and the Bots API to get latency.")
    embed.add_field(name="**$geolocate**", value="Get the GeoLocation information of a specified IP address.")
    embed.add_field(name="**$bruh**", value="Bruh")

    await ctx.send(embed=embed)



@bot.command()
async def staffhelp(ctx):
    embed = discord.Embed(title="Staff Command List", description=f"`[]` means optional arg and `<>` means required arg", color=discord.Colour.red())
    embed.add_field(name="**$help staff**", value="Brings you to this page.")
    embed.add_field(name="**$ban <@User> <Reason>**", value=f"Bans a specified user from {config['serverName']}")
    embed.add_field(name="**$unban <@User>**", value=f"Unbans a member from {config['serverName']}")
    embed.add_field(name="**$mute <@User> <Time> [Reason]**", value=f"Mutes a member in {config['serverName']}")
    embed.add_field(name="**$kick <@User> [Reason]**", value=f"Kicks a specified user from {config['serverName']}")
    embed.add_field(name="**$purge [Amount]**", value="Deletes a certain number of messages from a channel (default 5)")

    await ctx.send(embed=embed)


@bot.command()
async def prefix(ctx):
    '''Shows the prefix of Mega Bot'''
    embed = discord.Embed(title=f"{config['botName']} Prefix(es)", color=discord.Colour.blue())
    embed.add_field(name="_ _", value=f"```{prefix[0]}```")
    embed.add_field(name="_ _", value=f"```{prefix[1]}```")

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def repeat(ctx, times: int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await ctx.send(content)


@bot.command(aliases=["clear", "cl", "pr"], usage="<amount>")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount=5):
    await ctx.channel.purge(limit=amount+1)


@bot.command(usage="[member]", aliases=["av", "a", "pfp", "pic"])
async def avatar(ctx, *args):
    """Grab someones avatar"""
    colour = discord.Colour(0xBDECB6)
    if ctx.message.mentions:
        avatar_url = ctx.message.mentions[0].avatar_url_as(size=2048)
        embed = discord.Embed(title=f'{str(ctx.message.mentions[0])}\'s avatar!',
                              colour=colour,
                              description=f'Click [here]({avatar_url}) to download the avatar!',
                              timestamp=datetime.utcnow())
        embed.set_footer(text=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed)
    else:
        if args:
            if len(args) == 1:
                try:
                    id_user = int(args[0])
                    user = bot.get_user(id_user)
                    if user is None:
                        try:
                            user = await bot.fetch_user(id_user)
                        except discord.errors.NotFound:
                            user = None
                    if user is None:
                        return await ctx.send(f'{ctx.author.mention} invalid id!')
                    avatar_url = user.avatar_url_as(size=2048).__str__()
                    e = discord.Embed(title=f'Avatar of {str(user)}!',
                                      colour=colour,
                                      description=f'Click [here]({avatar_url}) to download the avatar!',
                                      timestamp=datetime.utcnow())
                    e.set_footer(text=f'{ctx.author}', icon_url=ctx.author.avatar_url)
                    e.set_image(url=avatar_url)
                    return await ctx.send(embed=e)
                except ValueError:
                    pass

            user = None
            args = ' '.join(args)
            if ctx.guild:
                for member in ctx.guild.members:
                    if member.nick is not None:
                        if member.nick.lower() == args.lower():
                            user = member
                            break
                    if (args.lower() == member.name.lower()) or (args.lower() == str(member).lower()):
                        user = member
                        break
            if user is None:
                for _user in bot.users:
                    if (args.lower() == _user.name) or (args.lower() == str(_user)):
                        user = _user
                        break
        else:
            user = ctx.author
        if user is None:
            return await ctx.send(f'{ctx.author.mention} I did not find this user.')
        avatar_url = user.avatar_url_as(size=2048)
        e = discord.Embed(title=f'Avatar of {str(user)}!',
                          colour=colour,
                          description=f'Click [here]({avatar_url}) to download the avatar!',
                          timestamp=datetime.utcnow())
        e.set_footer(text=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        e.set_image(url=avatar_url)
        await ctx.send(embed=e)


@bot.command(usage="<member>")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, why=None):
    """Kick a member from the server (staff only)"""
    await member.kick(reason=why)
    await ctx.channel.send(f"**{member} has been kicked from this server by {ctx.author}**")


@bot.command(usage="<member> <reason>")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member from the server (staff only)"""
    if reason is None:
        await ctx.send(f"Woah {ctx.author.mention}, Make sure you provide a reason!")
    else:
        messageok = f"You have been banned from {ctx.guild.name} for {reason}"
        await member.send(messageok)
        await member.ban(reason=reason)


# The below code unbans player.
@bot.command(usage="<member>")
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    """Unban a member from the server (staff only)"""
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.name}')
            return


@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, mute_time: int, *, reason=None):
    """Mute a member in the server (staff only)"""
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    await member.add_roles(role)
    await ctx.send(f'**Muted** {member.mention}\n**Reason: **{reason}\n**Duration:** {mute_time}')

    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name=f"You've been **Muted** in {ctx.guild.name}.",
                    value=f"**Action By: **{ctx.author.mention}\n**Reason: **{reason}\n**Duration:** {mute_time}")
    await member.send(embed=embed)

    await asyncio.sleep(mute_time)
    await member.remove_roles(role)
    await ctx.send(f"**Unmuted {member.mention}**")


@bot.command(aliases=["userinfo", "ui", "who", "user", "info"], usage="[mention]")
async def whois(ctx, member: discord.Member = None):
    """See the information of a member in this guild"""
    if not member:  # if member is no mentioned
        member = ctx.message.author  # set member as the author
    roles = [role for role in member.roles[1:]]
    embed = discord.Embed(colour=discord.Colour.purple(), timestamp=ctx.message.created_at,
                          title=f"User Info - {member}")
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}")

    embed.add_field(name="ID:", value=member.id)
    embed.add_field(name="Display Name:", value=member.display_name)

    embed.add_field(name="Created Account On:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    embed.add_field(name="Joined Server On:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))

    embed.add_field(name="Roles:", value="".join([role.mention for role in roles]))
    embed.add_field(name="Highest Role:", value=member.top_role.mention)
    print(member.top_role.mention)
    await ctx.send(embed=embed)


@bot.command(usage="[subject]", aliases=["ticket", "t", "n"])
async def new(ctx, *, subject=None):
    """Creates a new ticket"""
    await CreateNewTicket(bot, ctx, subject)


@bot.command(usage="<message>")
@commands.has_permissions(administrator=True)
async def announce(ctx, *args):
    try:
        amessageraw = " ".join(args[:])
        amessage = amessageraw.replace("\\n", "\n")
        await ctx.send(f"{amessage}")
        time.sleep(3)
        await ctx.message.delete()
    except:
        await ctx.send("Invalid message")


@bot.command()
async def close(ctx, *, reason=None):
    """Closes a ticket"""
    try:
        await CloseTicket(bot, ctx, reason)
    except Exception as e:
        await ctx.send(e)


@bot.command()
@commands.has_role(bot.staff_role_id)
async def adduser(ctx, user: discord.Member):
    """
    add users to a ticket - only staff role can add users.
    """
    channel = ctx.channel
    if not IsATicket(channel.id):
        await ctx.send("This is not a ticket! Users can only be added to a ticket channel")
        return

    await channel.set_permissions(user, read_messages=True, send_messages=True)
    await ctx.message.delete()


@bot.command()
@commands.has_role(bot.staff_role_id)
async def removeuser(ctx, user: discord.Member):
    """
    removes users from a ticket - only staff role can remove users.
    """
    channel = ctx.channel
    if not IsATicket(channel.id):
        await ctx.send("This is not a ticket! Users can only be removed from a ticket channel")
        return

    await channel.set_permissions(user, read_messages=False, send_messages=False)
    await ctx.message.delete()


@bot.command()
@commands.is_owner()
async def sudonew(ctx, user: discord.Member):
    await ctx.message.delete()
    await SudoCreateNewTicket(bot, ctx.guild, user, ctx.message)


@bot.command()
@commands.is_owner()
async def setup():
    await SetupNewTicketMessage(bot)


@bot.command()
@commands.is_owner()
async def echo(ctx, channel: discord.TextChannel, *, content):
    await ctx.message.delete()
    embed = discord.Embed(
        description=content, color=0x808080, timestamp=ctx.message.created_at
    )
    embed.set_author(name=ctx.guild.me.display_name, icon_url=ctx.guild.me.avatar_url)
    await channel.send(embed=embed)


@bot.command(aliases=["p", "latency"])
async def ping(ctx):
    """Check the latency of the bot and api"""
    apiping = baseurl + "api/ping"
    url = apiping
    payload = {}
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)
    ping1 = response.text
    ping2 = float(ping1)
    ping3 = round(ping2, 5)
    start = datetime.timestamp(datetime.now())
    msg = await ctx.send(content='Pinging')
    await msg.edit(
        content=f"Pong!\n> Average Bot RTT is {round((datetime.timestamp(datetime.now()) - start) * 1000)}ms.\n> Average API TTFB is {ping3}ms.")
    return


@bot.command(aliases=["geo", "loc", "locate", "geolocate", "glocate", "gloc"], usage="<IPv4/IPv6/AS Number>")
async def geoloc(ctx, *args):
    '''Get reliable IP geolocation information with this command!'''
    geoapi = baseurl + "/api/geo/" + args[0]
    async with aiohttp.ClientSession() as session:
        async with session.get(geoapi) as resp:
            jsonresp = await resp.json()

    try:
        dict_json = json.loads(jsonresp)
        line1 = dict_json['ip']
        line2 = dict_json["hostname"]
        line3 = dict_json["city"]
        line4 = dict_json["region"]
        line5 = dict_json["country"]
        line6 = dict_json["loc"]
        #line7 = dict_json["org"]
        line8 = dict_json["postal"]
        line9 = dict_json["timezone"]

        embed = discord.Embed(colour=discord.Colour.purple(), timestamp=ctx.message.created_at, title="IP Geolocation")
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/789160964750704681/0414e68bb20f1cef85a9561b6f61abfe.webp?size=256")
        embed.set_footer(text=f"Requested by {ctx.author}")
    
        embed.add_field(name="IP: ", value=line1)
        embed.add_field(name="Hostname: ", value=line2)
        embed.add_field(name="City: ", value=line3)
        embed.add_field(name="Region: ", value=line4)
        embed.add_field(name="Country: ", value=line5)
        embed.add_field(name="Coordinates: ", value=line6)
        #embed.add_field(name="Organisation: ", value=line7)
        embed.add_field(name="Postal Code: ", value=line8)
        embed.add_field(name="Timezone: ", value=line9)
    
        await ctx.send(embed=embed)
    except:
        await ctx.send("Invalid IP Address")


@bot.command()
async def verify(ctx):
    try:
        role = discord.utils.get(ctx.guild.roles, name="Verified")
        await discord.Member.add_roles(ctx.author, role)
        await ctx.send(f"Verified user {ctx.author.mention}")
    except Exception as e:
        print(e)
        await ctx.send("You are already verified!")


@bot.command()
async def bruh(ctx):
    await ctx.send("bruh")
    await ctx.message.delete()


@bot.command()
@commands.has_permissions(administrator=True)
@cooldowns.cooldown(10)
async def test(ctx):
    await ctx.send("test")


if __name__ == "__main__":
    bot.run(secret["token"])
