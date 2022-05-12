import asyncio
import copy
import datetime
import importlib
import locale
import os
import re
import sys
import time
import typing
from platform import system as system_name  # Returns the system/OS name
from subprocess import call as system_call  # Execute a shell command

import aiohttp
import discord
import psutil
import requests
from discord.ext import commands
from discord.ext.commands.converter import run_converters
from docs import conf
from libs import bitly_api
from libs.classes import MyContext, Zbot
from libs.formatutils import FormatUtils
from utils import count_code_lines

from fcts import args, checks, reloads

default_color = discord.Color(0x50e3c2)

importlib.reload(conf)
# importlib.reload(reloads)
importlib.reload(args)
importlib.reload(checks)
importlib.reload(bitly_api)


async def in_support_server(ctx):
    return ctx.guild is not None and ctx.guild.id == 625316773771608074

class Info(commands.Cog):
    """Here you will find various useful commands to get information about ZBot."""

    def __init__(self, bot: Zbot):
        self.bot = bot
        self.file = "info"
        self.bot_version = conf.release + ('a' if bot.beta else '')
        self.emoji_table = 'emojis_beta' if self.bot.beta else 'emojis'
        self.BitlyClient = bitly_api.Bitly(api_key=self.bot.others['bitly'])

    @commands.Cog.listener()
    async def on_ready(self):
        self.codelines = await count_code_lines()
        self.emoji_table = 'emojis_beta' if self.bot.beta else 'emojis'


    @commands.command(name='admins')
    async def admin_list(self, ctx: MyContext):
        """Get the list of ZBot administrators
        
        ..Doc miscellaneous.html#admins"""
        l  = list()
        for u in reloads.admins_id:
            if u==552273019020771358:
                continue
            l.append(str(self.bot.get_user(u)))
        await ctx.send(await self.bot._(ctx.channel,"info.admins-list", admins=", ".join(l)))

    async def get_guilds_count(self, ignored_guilds:list=None) -> int:
        """Get the number of guilds where Zbot is"""
        if ignored_guilds is None:
            if self.bot.database_online:
                if 'banned_guilds' not in self.bot.get_cog('Utilities').config.keys():
                    await self.bot.get_cog('Utilities').get_bot_infos()
                ignored_guilds = [int(x) for x in self.bot.get_cog('Utilities').config['banned_guilds'].split(";") if len(x) > 0] + self.bot.get_cog('Reloads').ignored_guilds
            else:
                return len(self.bot.guilds)
        return len([x for x in self.bot.guilds if x.id not in ignored_guilds])

    @commands.command(name="stats", enabled=True)
    @commands.cooldown(2,60,commands.BucketType.guild)
    async def stats(self, ctx: MyContext):
        """Display some statistics about the bot
        
        ..Doc infos.html#statistics"""
        v = sys.version_info
        version = str(v.major)+"."+str(v.minor)+"."+str(v.micro)
        pid = os.getpid()
        py = psutil.Process(pid)
        latency = round(self.bot.latency*1000, 2)
        async with ctx.channel.typing():
            # RAM/CPU
            ram_cpu = [round(py.memory_info()[0]/2.**30,3), py.cpu_percent(interval=1)]
            # Guilds count
            ignored_guilds = list()
            if self.bot.database_online:
                ignored_guilds = [int(x) for x in self.bot.get_cog('Utilities').config['banned_guilds'].split(";") if len(x) > 0]
            ignored_guilds += self.bot.get_cog('Reloads').ignored_guilds
            len_servers = await self.get_guilds_count(ignored_guilds)
            # Languages
            langs_list: list = await self.bot.get_cog('Servers').get_languages(ignored_guilds)
            langs_list.sort(reverse=True, key=lambda x: x[1])
            lang_total = sum([x[1] for x in langs_list])
            langs_list = ' | '.join(["{}: {}%".format(x[0],round(x[1]/lang_total*100)) for x in langs_list if x[1] > 0])
            del lang_total
            # Users/bots
            try:
                users,bots = self.get_users_nber(ignored_guilds)
            except Exception as e:
                users = bots = 'unknown'
            # Total XP
            if self.bot.database_online:
                total_xp = await self.bot.get_cog('Xp').bdd_total_xp()
            else:
                total_xp = ""
            # Commands within 24h
            cmds_24h = await self.bot.get_cog("BotStats").get_stats("wsevent.CMD_USE", 60*24)
            # number formatter
            lang = await self.bot._(ctx.guild.id,"_used_locale")
            async def n_format(nbr):
                return await FormatUtils.format_nbr(nbr, lang)
            # Generating message
            d = ""
            for key, var in [
                ('bot_version', self.bot_version),
                ('servers_count', await n_format(len_servers)),
                ('users_count', (await n_format(users), await n_format(bots))),
                ('codes_lines', await n_format(self.codelines)),
                ('languages', langs_list),
                ('python_version', version),
                ('lib_version', discord.__version__),
                ('ram_usage', await n_format(ram_cpu[0])),
                ('cpu_usage', await n_format(ram_cpu[1])),
                ('api_ping', await n_format(latency)),
                ('cmds_24h', await n_format(cmds_24h)),
                ('total_xp', await n_format(total_xp)+" ")]:
                str_args = {f'v{i}': var[i] for i in range(len(var))} if isinstance(var, (tuple, list)) else {'v': var}
                d += await self.bot._(ctx.channel, "info.stats."+key, **str_args) + "\n"
        if ctx.can_send_embed: # if we can use embed
            title = await self.bot._(ctx.channel,"info.stats.title")
            color = ctx.bot.get_cog('Help').help_color
            embed = discord.Embed(title=title, color=color, timestamp=ctx.message.created_at, description=d)
            embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format("png"))
            embed.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)
        else:
            await ctx.send(d)

    def get_users_nber(self, ignored_guilds: list):
        members = [x.members for x in self.bot.guilds if x.id not in ignored_guilds]
        members = list(set([x for x in members for x in x])) # filter users
        return len(members),len([x for x in members if x.bot])

    @commands.command(name="botinvite", aliases=["botinv"])
    async def botinvite(self, ctx:MyContext):
        """Get a link to invite me

        ..Doc infos.html#bot-invite"""
        raw_oauth = "<" + discord.utils.oauth_url(self.bot.user.id) + ">"
        try:
            r = requests.get("https://zrunner.me/invitezbot", timeout=3)
        except requests.exceptions.Timeout:
            url = raw_oauth
        else:
            if r.status_code < 400:
                url = "https://zrunner.me/invitezbot"
            else:
                url = raw_oauth
        await ctx.send(await self.bot._(ctx.channel, "info.botinvite", url=url))

    @commands.command(name="pig", hidden=True)
    async def pig(self, ctx: MyContext):
        """Get bot latency
        You can also use this command to ping any other server"""
        msg = await ctx.send("Pig...")
        delta = (msg.created_at - ctx.message.created_at).total_seconds()
        await msg.edit(content=f":pig:  Groink!\nBot ping: {delta*1000:.0f}ms\nDiscord ping: {self.bot.latency*1000:.0f}ms")

    @commands.command(name="ping",aliases=['rep'])
    @commands.cooldown(5, 45, commands.BucketType.guild)
    async def rep(self, ctx: MyContext, ip=None):
        """Get bot latency
        You can also use this command to ping any other server

        ..Example ping

        ..Example ping google.fr

        ..Doc infos.html#ping"""
        if ip is None:
            m = await ctx.send("Ping...")
            t = (m.created_at - ctx.message.created_at).total_seconds()
            try:
                p = round(self.bot.latency*1000)
            except OverflowError:
                p = "∞"
            await m.edit(content=":ping_pong:  Pong !\nBot ping: {}ms\nDiscord ping: {}ms".format(round(t*1000),p))
        else:
            asyncio.run_coroutine_threadsafe(self.ping_address(ctx,ip),asyncio.get_event_loop())

    async def ping_address(self, ctx: MyContext, ip: str):
        packages = 40
        wait = 0.3
        try:
            try:
                m = await ctx.send("Ping...",file=await self.bot.get_cog('Utilities').find_img('discord-loading.gif'))
            except:
                m = None
            t1 = time.time()
            param = '-n' if system_name().lower()=='windows' else '-c'
            command = ['ping', param, str(packages), '-i', str(wait), ip, '-q']
            result = system_call(command) == 0
        except Exception as e:
            await ctx.send("`Error:` {}".format(e))
            return
        if result:
            t = (time.time() - t1 - wait*(packages-1))/(packages)*1000
            await ctx.send(await self.bot._(ctx.channel, "info.ping.found", tps=round(t,2), url=ip))
        else:
            await ctx.send(await self.bot._(ctx.channel, "info.ping.notfound"))
        if m is not None:
            await m.delete()

    @commands.command(name="docs", aliases=['doc','documentation'])
    async def display_doc(self, ctx: MyContext):
        """Get the documentation url"""
        text = self.bot.get_cog('Emojis').customs['readthedocs'] + await self.bot._(ctx.channel,"info.docs") + \
            " https://zbot.rtfd.io"
        if self.bot.beta:
            text += '/en/develop'
        await ctx.send(text)

    async def display_critical(self, ctx: MyContext):
        return ctx.author.guild_permissions.manage_guild or await self.bot.get_cog('Admin').check_if_god(ctx)

    @commands.group(name='info')
    @commands.guild_only()
    @commands.check(checks.bot_can_embed)
    async def info_main(self, ctx: MyContext):
        """Find informations about someone/something
Available types: member, role, user, emoji, channel, server, invite, category

..Example info role The VIP

..Example info 436835675304755200

..Example info :owo:

..Example info server

..Doc infos.html#info"""
        if not ctx.invoked_subcommand and ctx.subcommand_passed:
            # try to convert ourselves because we are obviously a smart bot
            arg = ctx.message.content.replace(ctx.prefix+ctx.invoked_with, "").lstrip()
            # force the conversion order
            order = ('member', 'role', 'emoji', 'text-channel', 'voice-channel', 'category', 'user', 'invite', 'id')
            commands_list: list[commands.Command] = sorted(
                ctx.command.commands, key=lambda x: order.index(x.name) if x.name in order else 100)

            for cmd in commands_list:
                # if no conversion needed, that's probably not what we are looking for
                if not cmd.clean_params:
                    continue
                # get the needed parameter
                param_name = list(cmd.clean_params.keys())[0]
                param = cmd.clean_params[param_name]
                # convert it
                try:
                    converted_value = await run_converters(ctx, param.annotation, arg, param)
                except commands.BadArgument:
                    # conversion failed, that's not the right subcommand
                    continue
                else:
                    if converted_value is not None:
                        # all is right, execute and return
                        await cmd(ctx, converted_value)
                        return
            # we failed
            await ctx.send(await self.bot._(ctx.guild.id, "info.not-found", N=arg[:1900]))
        elif not ctx.subcommand_passed:
            # no given parameter
            await self.member_infos(ctx, ctx.author)

    @info_main.command(name="member")
    async def member_infos(self, ctx: MyContext, member: discord.Member):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        critical_info = await self.display_critical(ctx)
        since = await self.bot._(ctx.guild.id,"misc.since")
        embed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=member.display_avatar.with_static_format("png"))
        embed.set_author(name=str(member), icon_url=str(member.display_avatar.with_format("png")))
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=str(ctx.author.display_avatar.with_format("png")))
        # Name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=member.name,inline=True)
        # Nickname
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-0"), value=member.nick if member.nick else str(await self.bot._(ctx.channel,"misc.none")).capitalize(),inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(member.id))
        # Roles
        list_role = list()
        for role in member.roles:
            if str(role)!='@everyone':
                list_role.append(role.mention)
        # Created at
        now = ctx.bot.utcnow()
        delta = abs(member.created_at - now)
        created_date = f"<t:{member.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        if member.created_at.day == now.day and member.created_at.month == now.month and member.created_at.year != now.year:
            created_date = "🎂 " + created_date
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # Joined at
        if member.joined_at is not None:
            delta = abs(member.joined_at - now)
            join_date = f"<t:{member.joined_at.timestamp():.0f}>"
            since_date = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
            embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-2"), value = "{} ({} {})".format(join_date, since, since_date), inline=False)
        if member.guild.member_count < 1e4:
            # Join position
            if sum([1 for x in ctx.guild.members if not x.joined_at]) > 0 and ctx.guild.large:
                await ctx.guild.chunk()
            position = str(sorted(ctx.guild.members, key=lambda m: m.joined_at).index(member) + 1) + "/" + str(len(ctx.guild.members))
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-3"), value=position, inline=True)
        # Status
        status_value = (await self.bot._(ctx.guild.id,f"misc.{member.status}")).capitalize()
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-4"), value=status_value, inline=True)
        # Activity
        if member.activity is not None and (member.activity.type == discord.ActivityType.custom and
                member.activity.emoji is None and member.activity.name is None):
            # that's just a bug from discord apparently
            member.activity = None
        if member.activity is None:
            m_activity = str(await self.bot._(ctx.guild.id, "misc.activity.nothing")).capitalize()
        elif member.activity.type == discord.ActivityType.playing:
            m_activity = str(await self.bot._(ctx.guild.id, "misc.activity.play")).capitalize() + " " + member.activity.name
        elif member.activity.type == discord.ActivityType.streaming:
            m_activity = str(await self.bot._(ctx.guild.id, "misc.activity.stream")).capitalize() + f" ({member.activity.name})"
        elif member.activity.type == discord.ActivityType.listening:
            m_activity = str(await self.bot._(ctx.guild.id, "misc.activity.listen")).capitalize() + " " + member.activity.name
        elif member.activity.type == discord.ActivityType.watching:
            m_activity = str(await self.bot._(ctx.guild.id, "misc.activity.watch")).capitalize() +" " + member.activity.name
        elif member.activity.type == discord.ActivityType.custom:
            emoji = str(member.activity.emoji if member.activity.emoji else '')
            m_activity = emoji + " " + (member.activity.name if member.activity.name else '')
            m_activity = m_activity.strip()
        else:
            m_activity="Error"
        if member.activity is None or member.activity.type != 4:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-5"), value = m_activity,inline=True)
        else:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-8"), value = member.activity.state, inline=True)
        # Bot
        if member.bot:
            botb = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            botb = await self.bot._(ctx.guild.id,"misc.no")
        embed.add_field(name="Bot", value=botb.capitalize())
        # Administrator
        if ctx.channel.permissions_for(member).administrator:
            admin = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            admin = await self.bot._(ctx.guild.id,"misc.no")
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-6"), value = admin.capitalize(),inline=True)
        # Infractions count
        if critical_info and not member.bot and self.bot.database_online:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-7"), value = await self.bot.get_cog('Cases').get_nber(member.id,ctx.guild.id),inline=True)
        # Guilds count
        if member.bot:
            session = aiohttp.ClientSession(loop=self.bot.loop)
            guilds_count = await self.bot.get_cog('Partners').get_bot_guilds(member.id,session)
            if guilds_count is not None:
                embed.add_field(name=str(await self.bot._(ctx.guild.id,'misc.servers')).capitalize(),value=guilds_count)
            await session.close()
        # Roles
        _roles = await self.bot._(ctx.guild.id, 'info.info.member-9') + f' [{len(list_role)}]'
        if len(list_role) > 0:
            list_role = list_role[:40]
            embed.add_field(name=_roles, value = ", ".join(list_role), inline=False)
        else:
            embed.add_field(name=_roles, value=(await self.bot._(ctx.guild.id,"misc.none")).capitalize(), inline=False)
        # member verification gate
        if member.pending:
            _waiting = await self.bot._(ctx.guild.id, 'info.info.member-10')
            embed.add_field(name=_waiting, value='\u200b', inline=False)
        await ctx.send(embed=embed)

    @info_main.command(name="role")
    async def role_infos(self, ctx: MyContext, role: discord.Role):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        embed = discord.Embed(colour=role.color, timestamp=ctx.message.created_at)
        embed.set_author(name=str(role), icon_url=ctx.guild.icon)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar)
        since = await self.bot._(ctx.guild.id,"misc.since")
        # Name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=role.mention,inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(role.id),inline=True)
        # Color
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-1"), value=str(role.color),inline=True)
        # Mentionnable
        if role.mentionable:
            mentio = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            mentio = await self.bot._(ctx.guild.id,"misc.no")
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-2"), value=mentio.capitalize(), inline=True)
        # Members nbr
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-3"), value=len(role.members), inline=True)
        # Hoisted
        if role.hoist:
            hoist = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            hoist = await self.bot._(ctx.guild.id,"misc.no")
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-4"), value=hoist.capitalize(), inline=True)
        # Created at
        delta = abs(role.created_at - ctx.bot.utcnow())
        created_date = f"<t:{role.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # Hierarchy position
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-5"), value=str(len(ctx.guild.roles) - role.position), inline=True)
        # Unique member
        if len(role.members)==1:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-6"), value=role.members[0].mention, inline=True)
        await ctx.send(embed=embed)

    @info_main.command(name="user")
    async def user_infos(self, ctx: MyContext, user: discord.User):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        since = await self.bot._(ctx.guild.id,"misc.since")
        if user.bot:
            botb = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            botb = await self.bot._(ctx.guild.id,"misc.no")
        if user in ctx.guild.members:
            on_server = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            on_server = await self.bot._(ctx.guild.id,"misc.no")
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=user.display_avatar.with_static_format("png"))
        embed.set_author(name=str(user), icon_url=user.display_avatar.with_format("png"))
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar.with_format("png"))

        # name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=user.name,inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(user.id))
        # created at
        now = ctx.bot.utcnow()
        delta = abs(user.created_at - now)
        created_date = f"<t:{user.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        if user.created_at.day == now.day and user.created_at.month == now.month and user.created_at.year != now.year:
            created_date = "🎂 " + created_date
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # is bot
        embed.add_field(name="Bot", value=botb.capitalize())
        # is in server
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.user-0"), value=on_server.capitalize())
        if user.bot:
            session = aiohttp.ClientSession(loop=self.bot.loop)
            guilds_count = await self.bot.get_cog('Partners').get_bot_guilds(user.id,session)
            if guilds_count is not None:
                embed.add_field(name=str(await self.bot._(ctx.guild.id,'misc.servers')).capitalize(),value=guilds_count)
            await session.close()
        await ctx.send(embed=embed)

    @info_main.command(name="emoji")
    async def emoji_infos(self, ctx: MyContext, emoji: discord.Emoji):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        since = await self.bot._(ctx.guild.id,"misc.since")
        if emoji.animated:
            animate = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            animate = await self.bot._(ctx.guild.id,"misc.no")
        if emoji.managed:
            manage = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            manage = await self.bot._(ctx.guild.id,"misc.no")
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=emoji.url)
        embed.set_author(name="Emoji '{}'".format(emoji.name), icon_url=emoji.url)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar.with_format("png"))
        # name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=emoji.name,inline=True)
        # id
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(emoji.id))
        # animated
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-0"), value=animate.capitalize())
        # guild name
        if emoji.guild != ctx.guild:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-3"), value=emoji.guild.name)
        # string
        string = "<a:{}:{}>".format(emoji.name,emoji.id) if emoji.animated else "<:{}:{}>".format(emoji.name,emoji.id)
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-2"), value=f"`{string}`")
        # managed
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-1"), value=manage.capitalize())
        # created at
        delta = abs(emoji.created_at - ctx.bot.utcnow())
        created_date = f"<t:{emoji.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # allowed roles
        if len(emoji.roles) > 0:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-4"), value=" ".join([x.mention for x in emoji.roles]))
        # uses
        infos_uses = await self.get_emojis_info(emoji.id)
        if len(infos_uses) > 0:
            infos_uses = infos_uses[0]
            date = f"<t:{infos_uses['added_at'].timestamp():.0f}:D>"
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.emoji-5"), value=await self.bot._(ctx.guild.id,"info.info.emoji-5v",nbr=infos_uses['count'],date=date))
        await ctx.send(embed=embed)

    @info_main.command(name="text-channel")
    async def textChannel_infos(self, ctx: MyContext, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.author).view_channel:
            await ctx.send(await self.bot._(ctx.guild.id, "info.cant-see-channel"))
            return
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        icon_url = channel.guild.icon.with_format('png') if channel.guild.icon else None
        embed.set_author(name="{} '{}'".format(await self.bot._(ctx.guild.id,"info.info.textchan-5"),channel.name), icon_url=icon_url)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar.with_format("png"))
        since = await self.bot._(ctx.guild.id,"misc.since")
        # Name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=channel.name,inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(channel.id))
        # Category
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-0"), value=str(channel.category))
        # NSFW
        if channel.nsfw:
            nsfw = await self.bot._(ctx.guild.id,"misc.yes")
        else:
            nsfw = await self.bot._(ctx.guild.id,"misc.no")
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-2"), value=nsfw.capitalize())
        # Webhooks count
        try:
            web = len(await channel.webhooks())
        except Exception as e:
            await self.bot.get_cog('Errors').on_error(e,ctx)
            web = await self.bot._(ctx.guild.id,"info.info.textchan-4")
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-3"), value=str(web))
        # Members nber
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-3"), value = str(len(channel.members))+"/"+str(ctx.guild.member_count), inline=True)
        # Created at
        delta = abs(channel.created_at - ctx.bot.utcnow())
        created_date = f"<t:{channel.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # Topic
        if channel.permissions_for(ctx.author).read_messages:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-1"), value = channel.topic if channel.topic not in ['',None] else str(await self.bot._(ctx.guild.id,"misc.none")).capitalize(), inline=False)
        await ctx.send(embed=embed)

    @info_main.command(name="voice-channel")
    async def voiceChannel_info(self, ctx: MyContext, channel: discord.VoiceChannel):
        if not channel.permissions_for(ctx.author).view_channel:
            await ctx.send(await self.bot._(ctx.guild.id, "info.cant-see-channel"))
            return
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        since = await self.bot._(ctx.guild.id,"misc.since")
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        icon_url = channel.guild.icon.with_static_format('png') if channel.guild.icon else None
        embed.set_author(name="{} '{}'".format(await self.bot._(ctx.guild.id,"info.info.voicechan-0"),channel.name), icon_url=icon_url)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar)
        # Name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=channel.name,inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(channel.id))
        # Category
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-0"), value=str(channel.category))
        # Created at
        delta = abs(channel.created_at - ctx.bot.utcnow())
        created_date = f"<t:{channel.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # Bitrate
        embed.add_field(name="Bitrate",value=str(channel.bitrate/1000)+" kbps")
        # Members count
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-3"), value="{}/{}".format(len(channel.members),channel.user_limit if channel.user_limit > 0 else "∞"))
        # Region
        if channel.rtc_region is not None:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-2"), value=str(channel.rtc_region).capitalize())
        await ctx.send(embed=embed)

    @info_main.command(name="guild", aliases=["server"])
    @commands.guild_only()
    async def guild_info(self, ctx: MyContext):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        critical_info = await self.display_critical(ctx)
        guild = ctx.guild
        if guild_id := ctx.message.content.split(ctx.invoked_with, 1)[1]:
            if await self.bot.get_cog('Admin').check_if_admin(ctx):
                guild = await commands.GuildConverter().convert(ctx, guild_id.lstrip())
        since = await self.bot._(ctx.guild.id,"misc.since")
        _, bots, online = await self.bot.get_cog("Utilities").get_members_repartition(guild.members)

        desc = await self.bot.get_config(guild.id,'description')
        if (desc is None or len(desc) == 0) and guild.description is not None:
            desc = guild.description
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at, description=desc)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar)
        # Guild icon
        icon_url = guild.icon.with_static_format("png") if guild.icon else None
        embed.set_author(name="{} '{}'".format(await self.bot._(ctx.guild.id,"info.info.guild-0"),guild.name), icon_url=icon_url)
        embed.set_thumbnail(url=icon_url)
        # Guild banner
        if guild.banner is not None:
            embed.set_image(url=guild.banner)
        # Name
        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=guild.name,inline=True)
        # ID
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(guild.id))
        # Owner
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-1"), value=str(guild.owner))
        # Created at
        delta = abs(guild.created_at - ctx.bot.utcnow())
        created_date = f"<t:{guild.created_at.timestamp():.0f}>"
        created_since = await FormatUtils.time_delta(delta.total_seconds(), lang=lang, year=True, hour=delta.total_seconds() < 86400)
        embed.add_field(name=await self.bot._(ctx.guild.id, "info.info.member-1"), value = "{} ({} {})".format(created_date, since, created_since), inline=False)
        # Member count
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-3"), value=await self.bot._(ctx.guild.id,"info.info.guild-7", c=guild.member_count, b=bots, o=online))
        # Channel count
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-6"), value=await self.bot._(ctx.guild.id,"info.info.guild-3", txt=len(guild.text_channels), voc=len(guild.voice_channels), cat=len(guild.categories)))
        # Invite count
        if guild.me.guild_permissions.manage_guild:
            len_invites = str(len(await guild.invites()))
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-12"), value=len_invites)
        # Emojis count
        c = [0, 0]
        for x in guild.emojis:
            c[1 if x.animated else 0] += 1
        emojis_txt = await self.bot._(ctx.guild.id, "info.info.guild-16", l=guild.emoji_limit, s=c[0], a=c[1])
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-5"), value=emojis_txt)
        # AFK timeout
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-10"), value = str(int(guild.afk_timeout/60))+" minutes")
        # Splash url
        try:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-15"), value=str(await guild.vanity_invite()))
        except Exception as e:
            if isinstance(e,(discord.errors.Forbidden, discord.errors.HTTPException)):
                pass
            else:
                await self.bot.get_cog('Errors').on_error(e,ctx)
        # Premium subscriptions count
        if isinstance(guild.premium_subscription_count,int) and guild.premium_subscription_count > 0:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-13"), value=await self.bot._(ctx.guild.id,"info.info.guild-13v",b=guild.premium_subscription_count,p=guild.premium_tier))
        # Roles list
        try:
            if ctx.guild==guild:
                roles = [x.mention for x in guild.roles if len(x.members) > 1][1:]
            else:
                roles = [x.name for x in guild.roles if len(x.members) > 1][1:]
        except Exception as e:
            await self.bot.get_cog('Errors').on_error(e,ctx)
            roles = guild.roles
        roles.reverse()
        if len(roles) == 0:
            temp = (await self.bot._(ctx.guild.id,"misc.none")).capitalize()
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-11.2", c=len(guild.roles)-1), value=temp)
        elif len(roles) > 20:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-11.1", c=len(guild.roles)-1), value=", ".join(roles[:20]))
        else:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-11.2", c=len(guild.roles)-1), value=", ".join(roles))
        # Limitations
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-14"), value=await self.bot._(ctx.guild.id,"info.info.guild-14v",
            bit=round(guild.bitrate_limit/1000),
            fil=round(guild.filesize_limit/1.049e+6),
            emo=guild.emoji_limit,
            mem=guild.max_presences))
        # Features
        if len(guild.features) > 0:
            tr = lambda x: self.bot._(ctx.guild.id,"info.info.guild-features."+x)
            features: list[str] = [await tr(x) for x in guild.features]
            features = [f.split('.')[-1] if '.' in f else f for f in features]
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-9"), value=" - ".join(features))
        if critical_info:
            # A2F activation
            if guild.mfa_level:
                a2f = await self.bot._(ctx.guild.id,"misc.yes")
            else:
                a2f = await self.bot._(ctx.guild.id,"misc.no")
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-8"), value=a2f.capitalize())
            # Verification level
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-9"), value=str(await self.bot._(ctx.guild.id,f"misc.{guild.verification_level}")).capitalize())
        await ctx.send(embed=embed)

    @info_main.command(name="invite")
    async def invite_info(self, ctx: MyContext, invite: discord.Invite):
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        since = await self.bot._(ctx.guild.id,"misc.since")
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        icon_url = invite.guild.icon.with_static_format('png') if invite.guild.icon else None
        embed.set_author(name="{} '{}'".format(await self.bot._(ctx.guild.id,"info.info.inv-4"),invite.code), icon_url=icon_url)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar.replace(static_format="png", size=256))
        # Try to get the complete invite
        if invite.guild in self.bot.guilds:
            try:
                temp = [x for x in await invite.guild.invites() if x.id == invite.id]
                if len(temp) > 0:
                    invite = temp[0]
            except discord.errors.Forbidden:
                pass
            except Exception as e:
                await self.bot.get_cog('Errors').on_error(e,ctx)
        # Invite URL
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-0"), value=invite.url,inline=True)
        # Inviter
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-1"), value=str(invite.inviter) if invite.inviter is not None else await self.bot._(ctx.guild,'misc.unknown'))
        # Invite uses
        if invite.max_uses is not None and invite.uses is not None:
            if invite.max_uses == 0:
                uses = "{}/∞".format(invite.uses)
            else:
                uses = "{}/{}".format(invite.uses,invite.max_uses)
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-2"), value=uses)
        # Duration
        if invite.max_age is not None:
            max_age = str(invite.max_age) if invite.max_age != 0 else "∞"
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-3"), value=max_age)
        if isinstance(invite.channel,(discord.PartialInviteChannel,discord.abc.GuildChannel)):
            # Guild name
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-0"), value=str(invite.guild.name))
            # Channel name
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.textchan-5"), value="#"+str(invite.channel.name))
            # Guild icon
            if invite.guild.icon:
                embed.set_thumbnail(url=icon_url)
            # Guild ID
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-6"), value=str(invite.guild.id))
            # Members count
            if invite.approximate_member_count:
                embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-7"), value=str(invite.approximate_member_count))
        # Guild banner
        if invite.guild.banner is not None:
            embed.set_image(url=invite.guild.banner)
        # Guild description
        if invite.guild.description is not None and len(invite.guild.description) > 0:
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-8"), value=invite.guild.description)
        # Guild features
        if len(invite.guild.features) > 0:
            tr = lambda x: self.bot._(ctx.guild.id,"info.info.guild-features."+x)
            features: list[str] = [await tr(x) for x in invite.guild.features]
            features = [f.split('.')[-1] if '.' in f else f for f in features]
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.inv-9"), value=" - ".join(features))
        # Creation date
        if invite.created_at is not None:
            created_at = f"<t:{invite.created_at.timestamp():.0f}>"
            delta = await FormatUtils.time_delta(invite.created_at,ctx.bot.utcnow(),lang=lang,year=True,hour=False)
            embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-1"), value = "{} ({} {})".format(created_at,since,delta), inline=False)
        await ctx.send(embed=embed)

    @info_main.command(name="category")
    async def category_info(self, ctx: MyContext, category: discord.CategoryChannel):
        if not category.permissions_for(ctx.author).view_channel:
            await ctx.send(await self.bot._(ctx.guild.id, "info.cant-see-channel"))
            return
        lang = await self.bot._(ctx.guild.id,"_used_locale")
        since = await self.bot._(ctx.guild.id,"misc.since")
        tchan = 0
        vchan = 0
        for channel in category.channels:
            if isinstance(channel, discord.TextChannel):
                tchan += 1
            elif isinstance(channel, discord.VoiceChannel):
                vchan +=1
        embed = discord.Embed(colour=default_color, timestamp=ctx.message.created_at)
        icon_url = category.guild.icon.with_static_format('png') if category.guild.icon else None
        embed.set_author(name="{} '{}'".format(await self.bot._(ctx.guild.id,"info.info.categ-0"),category.name), icon_url=icon_url)
        embed.set_footer(text='Requested by {}'.format(ctx.author.name), icon_url=ctx.author.display_avatar)

        embed.add_field(name=str(await self.bot._(ctx.guild.id,"misc.name")).capitalize(), value=category.name,inline=True)
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.role-0"), value=str(category.id))
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.categ-1"), value="{}/{}".format(category.position+1,len(ctx.guild.categories)))
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.guild-6"), value=await self.bot._(ctx.guild.id,"info.info.categ-2", txt=tchan, voc=vchan))
        created_at = f"<t:{category.created_at.timestamp():.0f}>"
        delta = await FormatUtils.time_delta(category.created_at,ctx.bot.utcnow(),lang=lang,year=True,hour=False)
        embed.add_field(name=await self.bot._(ctx.guild.id,"info.info.member-1"), value = "{} ({} {})".format(created_at,since,delta), inline=False)
        await ctx.send(embed=embed)

    @info_main.command(name="id", aliases=["snowflake"])
    async def snowflake_infos(self, ctx: MyContext, snowflake: args.snowflake):
        date = f"<t:{snowflake.date.timestamp():.0f}>"
        embed = discord.Embed(color=default_color, timestamp=ctx.message.created_at)
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-0"), value=date)
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-2"), value=round(snowflake.date.timestamp()))
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-1"), value=snowflake.binary, inline=False)
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-3"), value=snowflake.worker_id)
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-4"), value=snowflake.process_id)
        embed.add_field(name=await self.bot._(ctx.channel,"info.info.snowflake-5"), value=snowflake.increment)
        embed.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)


    @commands.group(name="find")
    @commands.check(reloads.is_support_staff)
    @commands.check(in_support_server)
    async def find_main(self, ctx: MyContext):
        """Same as info, but in a lighter version"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Cette commande permet de retrouver un serveur ou un salon parmi tout les serveurs sur lequel est le"
            " bot. Vous pouvez aussi rechercher les informations d'un utilisateur Discord, peu importe si il partage un serveur"
            " avec moi !\nLa syntaxe est `!find <user|channel|guild> <ID>`")

    @find_main.command(name="user")
    async def find_user(self, ctx: MyContext, *, user:discord.User):
        use_embed = ctx.can_send_embed
        # Servers list
        servers_in = list()
        owned, membered = 0, 0
        for s in user.mutual_guilds:
            if s.owner==user:
                servers_in.append(":crown: "+s.name)
                owned += 1
            else:
                servers_in.append("- "+s.name)
                membered += 1
        if len(servers_in) == 0:
            servers_in = ["No server"]
        elif len("\n".join(servers_in)) > 1020:
            servers_in = [f"{owned} serveurs possédés, membre sur {membered} autres serveurs"]
        # XP card
        xp_card = await self.bot.get_cog('Utilities').get_xp_style(user)
        # Flags
        userflags: list = await self.bot.get_cog('Users').get_userflags(user)
        if await self.bot.get_cog("Admin").check_if_admin(user):
            userflags.append('admin')
        if len(userflags) == 0:
            userflags = ["None"]
        # Votes
        votes = await ctx.bot.get_cog("Utilities").check_votes(user.id)
        if use_embed:
            votes = " - ".join([f"[{x[0]}]({x[1]})" for x in votes])
        else:
            votes = " - ".join([x[0] for x in votes])
        if len(votes) == 0:
            votes = "Nowhere"
        # Languages
        disp_lang = list()
        for lang in await self.bot.get_cog('Utilities').get_languages(user):
            disp_lang.append('{} ({}%)'.format(lang[0],round(lang[1]*100)))
        if len(disp_lang) == 0:
            disp_lang = ["Unknown"]
        # User name
        user_name = str(user)+' <:BOT:544149528761204736>' if user.bot else str(user)
        # XP sus
        xp_sus = "Unknown"
        if Xp := self.bot.get_cog("Xp"):
            if Xp.sus is not None:
                xp_sus = str(user.id in Xp.sus)
        # ----
        if use_embed:
            if ctx.guild is None:
                color = None
            else:
                color = None if ctx.guild.me.color.value == 0 else ctx.guild.me.color

            embed = discord.Embed(title=user_name, color=color)
            embed.set_thumbnail(url=user.display_avatar.replace(static_format="png", size=1024))
            embed.add_field(name="ID", value=user.id)
            embed.add_field(name="Flags", value="-".join(userflags), inline=False)
            embed.add_field(name="Servers", value="\n".join(servers_in))
            embed.add_field(name="Language", value="\n".join(disp_lang))
            embed.add_field(name="XP card", value=xp_card)
            embed.add_field(name="Upvoted the bot?", value=votes)
            embed.add_field(name="XP sus?", value=xp_sus)
            embed.set_footer(text=f'Requested by {ctx.author.name}', icon_url=ctx.author.display_avatar)

            await ctx.send(embed=embed)
        else:
            txt = """Name: {}
ID: {}
Perks: {}
Language: {}
XP card: {}
Voted? {}
Servers:
{}""".format(user_name,
                user.id,
                " - ".join(userflags),
                " - ".join(disp_lang),
                xp_card,
                votes,
                "\n".join(servers_in)
                )
            await ctx.send(txt)

    @find_main.command(name="guild", aliases=['server'])
    async def find_guild(self, ctx: MyContext, *, guild: str):
        if guild.isnumeric():
            guild: discord.Guild = ctx.bot.get_guild(int(guild))
        else:
            for x in self.bot.guilds:
                if x.name == guild:
                    guild = x
                    break
        if isinstance(guild, str) or guild is None:
            await ctx.send("Serveur introuvable")
            return
        # Bots
        bots = len([x for x in guild.members if x.bot])
        # Lang
        lang = await ctx.bot.get_config(guild.id,'language')
        if lang is None:
            lang = 'default'
        else:
            lang = ctx.bot.get_cog('Languages').languages[lang]
        # Roles rewards
        rr_len = await self.bot.get_config(guild.id,'rr_max_number')
        rr_len = self.bot.get_cog("Servers").default_opt['rr_max_number'] if rr_len is None else rr_len
        rr_len = '{}/{}'.format(len(await self.bot.get_cog('Xp').rr_list_role(guild.id)),rr_len)
        # Prefix
        pref = await self.bot.prefix_manager.get_prefix(guild)
        if "`" not in pref:
            pref = "`" + pref + "`"
        # Rss
        rss_len = await self.bot.get_config(guild.id,'rss_max_number')
        rss_len = self.bot.get_cog("Servers").default_opt['rss_max_number'] if rss_len is None else rss_len
        rss_numb = "{}/{}".format(len(await self.bot.get_cog('Rss').get_guild_flows(guild.id)), rss_len)
        # Join date
        joined_at = f"<t:{guild.me.joined_at.timestamp():.0f}>"
        # ----
        if ctx.can_send_embed:
            if ctx.guild is None:
                color = None
            else:
                color = None if ctx.guild.me.color.value == 0 else ctx.guild.me.color
            emb = discord.Embed(title=guild.name, color=color)
            if guild.icon:
                emb.set_thumbnail(url=guild.icon.with_static_format("png"))
            emb.add_field(name="ID", value=guild.id)
            emb.add_field(name="Owner", value=f"{guild.owner} ({guild.owner_id})", inline=False)
            emb.add_field(name="Joined at", value=joined_at, inline=False)
            emb.add_field(name="Members", value=f"{guild.member_count} (including {bots} bots)")
            emb.add_field(name="Language", value=lang)
            emb.add_field(name="Prefix", value=pref)
            emb.add_field(name="RSS feeds count", value=rss_numb)
            emb.add_field(name="Roles rewards count", value=rr_len)
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            txt = "Name: {name}\nID: {id}\nOwner: {owner} ({ownerid})\nJoined at: {join}\nMembers: {members} (including {bots} bots)\nLanguage: {lang}\nPrefix: `{prefix}`\nRSS feeds count: {rss}\nRoles rewards count: {rr}".format(name = guild.name,
                id = guild.id,
                owner = guild.owner,
                ownerid = guild.owner_id,
                join = joined_at,
                members = guild.member_count,
                bots = bots,
                lang = lang,
                prefix = pref,
                rss = rss_numb,
                rr = rr_len)
            await ctx.send(txt)

    @find_main.command(name='channel')
    async def find_channel(self, ctx: MyContext, ID:int):
        c = self.bot.get_channel(ID)
        if c is None:
            await ctx.send("Unknonwn channel")
            return
        if ctx.can_send_embed:
            if ctx.guild is None:
                color = None
            else:
                color = None if ctx.guild.me.color.value == 0 else ctx.guild.me.color
            emb = discord.Embed(title="#"+c.name, color=color)
            emb.add_field(name="ID", value=c.id)
            emb.add_field(name="Server", value=f"{c.guild.name} ({c.guild.id})", inline=False)
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            await ctx.send("Nom : {}\nID : {}\nServeur : {} ({})".format(c.name,c.id,c.guild.name,c.guild.id))

    @find_main.command(name='role')
    async def find_role(self, ctx: MyContext, ID:int):
        every_roles = list()
        for serv in ctx.bot.guilds:
            every_roles += serv.roles
        role: discord.Role = discord.utils.find(lambda role: role.id==ID, every_roles)
        if role is None:
            await ctx.send("Rôle introuvable")
            return
        if ctx.can_send_embed:
            if ctx.guild is None:
                color = None
            else:
                color = None if ctx.guild.me.color.value == 0 else ctx.guild.me.color
            emb = discord.Embed(title="@"+role.name, color=color)
            emb.add_field(name="ID", value=role.id)
            emb.add_field(name="Server", value=f"{role.guild.name} ({role.guild.id})", inline=False)
            emb.add_field(name="Members", value=len(role.members))
            emb.add_field(name="Colour", value=str(role.colour))
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            await ctx.send("Name: {}\nID: {}\nServer: {} ({})\nMembers: {}\nColor: {}".format(role.name,role.id,role.guild.name,role.guild.id,len(role.members),role.colour))

    @find_main.command(name='rss')
    async def find_rss(self, ctx: MyContext, ID:int):
        flow = await self.bot.get_cog('Rss').get_flow(ID)
        if len(flow) == 0:
            await ctx.send("Invalid ID")
            return
        else:
            flow = flow[0]
        temp = self.bot.get_guild(flow['guild'])
        if temp is None:
            g = "Unknown ({})".format(flow['guild'])
        else:
            g = "`{}`\n{}".format(temp.name,temp.id)
            temp = self.bot.get_channel(flow['channel'])
        if temp is not None:
            c = "`{}`\n{}".format(temp.name,temp.id)
        else:
            c = "Unknown ({})".format(flow['channel'])
        d = f"<t:{flow['date'].timestamp():.0f}>"
        if d is None or len(d) == 0:
            d = "never"
        if ctx.can_send_embed:
            if ctx.guild is None:
                color = None
            else:
                color = None if ctx.guild.me.color.value == 0 else ctx.guild.me.color
            emb = discord.Embed(title=f"RSS N°{ID}", color=color)
            emb.add_field(name="Server", value=g)
            emb.add_field(name="Channel", value=c)
            emb.add_field(name="URL", value=flow['link'], inline=False)
            emb.add_field(name="Type", value=flow['type'])
            emb.add_field(name="Last post", value=d)
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            await ctx.send("ID: {}\nGuild: {}\nChannel: {}\nLink: <{}>\nType: {}\nLast post: {}".format(flow['ID'],g.replace("\n"," "),c.replace("\n"," "),flow['link'],flow['type'],d))

    @commands.command(name="membercount",aliases=['member_count'])
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def membercount(self, ctx: MyContext):
        """Get some digits on the number of server members

        ..Doc infos.html#membercount"""
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return
        total, bots, c_co, unverified = await self.bot.get_cog("Utilities").get_members_repartition(ctx.guild.members)
        h = total - bots
        h_p = "< 1" if 0 < h / total < 0.01 else ("> 99" if 1 > h/total > 0.99 else round(h*100/total))
        b_p = "< 1" if 0 < bots / total < 0.01 else ("> 99" if 1 > bots/total > 0.99 else round(bots*100/total))
        c_p = "< 1" if 0 < c_co / total < 0.01 else ("> 99" if 1 > c_co/total > 0.99 else round(c_co*100/total))
        pen_p = "< 1" if 0 < unverified / total < 0.01 else ("> 99" if 1 > unverified/total > 0.99 else round(unverified*100/total))
        l = [(await self.bot._(ctx.guild.id, "info.membercount-0"), total),
             (await self.bot._(ctx.guild.id, "info.membercount-2"), "{} ({}%)".format(h, h_p)),
             (await self.bot._(ctx.guild.id, "info.membercount-1"), "{} ({}%)".format(bots, b_p)),
             (await self.bot._(ctx.guild.id, "info.membercount-3"), "{} ({}%)".format(c_co, c_p))]
        if "MEMBER_VERIFICATION_GATE_ENABLED" in ctx.guild.features:
            l.append((await self.bot._(ctx.guild.id, "info.membercount-4"), "{} ({}%)".format(unverified, pen_p)))
        if ctx.can_send_embed:
            embed = discord.Embed(colour=ctx.guild.me.color)
            for i in l:
                embed.add_field(name=i[0], value=i[1], inline=True)
            await ctx.send(embed=embed)
        else:
            text = str()
            for i in l:
                text += f"- {i[0]} : {i[1]}\n"
            await ctx.send(text)

    @commands.group(name="prefix")
    async def get_prefix(self, ctx: MyContext):
        """Show the usable prefix(s) for this server

        ..Doc infos.html#prefix"""
        if ctx.invoked_subcommand is not None:
            return
        txt = await self.bot._(ctx.channel,"info.prefix")
        prefix = "\n".join((await ctx.bot.get_prefix(ctx.message))[1:])
        if ctx.guild is None or ctx.channel.permissions_for(ctx.guild.me):
            emb = discord.Embed(title=txt, description=prefix, timestamp=ctx.message.created_at,
                color=ctx.bot.get_cog('Help').help_color)
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            await ctx.send(txt+"\n"+prefix)

    @get_prefix.command(name="change")
    @commands.guild_only()
    async def prefix_change(self, ctx: MyContext, *, new_prefix: str):
        """Change the used prefix

        ..Example prefix change "Hey Zbot, "

        ..Doc infos.html#prefix"""
        msg: discord.Message = copy.copy(ctx.message)
        if new_prefix.startswith('"') and new_prefix.endswith('"'):
            new_prefix = new_prefix[1:-1]
        msg.content =  f'{ctx.prefix}config change prefix "{new_prefix}"'
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)

    @commands.command(name="discordlinks",aliases=['discord','discordurls'])
    async def discord_status(self, ctx: MyContext):
        """Get some useful links about Discord"""
        l = await self.bot._(ctx.channel,'info.discordlinks')
        links = ["https://dis.gd/status","https://dis.gd/tos","https://dis.gd/report","https://dis.gd/feedback","https://support.discord.com/hc/en-us/articles/115002192352","https://discord.com/developers/docs/legal","https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-","https://support.discord.com/hc/en-us/articles/360040724612", " https://twitter.com/discordapp/status/1060411427616444417", "https://support.discord.com/hc/en-us/articles/360035675191"]
        if ctx.can_send_embed:
            txt = "\n".join(['['+l[i]+']('+links[i]+')' for i in range(len(l))])
            em = discord.Embed(description=txt)
            em.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=em)
        else:
            txt = "\n".join([f'• {l[i]}: <{links[i]}>' for i in range(len(l))])
            await ctx.send(txt)


    async def emoji_analysis(self, msg: discord.Message):
        """Lists the emojis used in a message"""
        try:
            if not self.bot.database_online:
                return
            ctx = await self.bot.get_context(msg)
            if ctx.command is not None:
                return
            liste = list(set(re.findall(r'<a?:[\w-]+:(\d{18})>',msg.content)))
            if len(liste) == 0:
                return
            current_timestamp = datetime.datetime.fromtimestamp(round(time.time()))
            query = "INSERT INTO `{}` (`ID`,`count`,`last_update`) VALUES (%(i)s, 1, %(l)s) ON DUPLICATE KEY UPDATE count = `count` + 1, last_update = %(l)s;".format(self.emoji_table)
            for data in [{ 'i': x, 'l': current_timestamp } for x in liste]:
                async with self.bot.db_query(query, data):
                    pass
        except Exception as e:
            await self.bot.get_cog('Errors').on_error(e,None)

    async def get_emojis_info(self, ID: typing.Union[int,list]):
        """Get info about an emoji"""
        if not self.bot.database_online:
            return list()
        if isinstance(ID, int):
            query = "SELECT * from `{}` WHERE `ID`={}".format(self.emoji_table,ID)
        else:
            query = "SELECT * from `{}` WHERE {}".format(self.emoji_table,"OR".join([f'`ID`={x}' for x in ID]))
        liste = list()
        async with self.bot.db_query(query) as query_results:
            for x in query_results:
                x['emoji'] = self.bot.get_emoji(x['ID'])
                liste.append(x)
        return liste


    @commands.group(name="bitly")
    async def bitly_main(self, ctx: MyContext):
        """Bit.ly website, but in Discord
        Create shortened url and unpack them by using Bitly services

        ..Doc miscellaneous.html#bitly-urls"""
        if ctx.subcommand_passed is None:
            await self.bot.get_cog('Help').help_command(ctx,['bitly'])
        elif ctx.invoked_subcommand is None and ctx.subcommand_passed is not None:
            try:
                url = await args.URL.convert(ctx,ctx.subcommand_passed)
            except:
                return
            if url.domain in ['bit.ly','bitly.com','bitly.is']:
                msg = copy.copy(ctx.message)
                msg.content = ctx.prefix + 'bitly find '+url.url
                new_ctx = await self.bot.get_context(msg)
                await self.bot.invoke(new_ctx)
            else:
                msg = copy.copy(ctx.message)
                msg.content = ctx.prefix + 'bitly create '+url.url
                new_ctx = await self.bot.get_context(msg)
                await self.bot.invoke(new_ctx)

    @bitly_main.command(name="create", aliases=["shorten"])
    async def bitly_create(self, ctx: MyContext, url: args.URL):
        """Create a shortened url

        ..Example bitly create https://fr-minecraft.net

        ..Doc miscellaneous.html#bitly-urls"""
        if url.domain == 'bit.ly':
            return await ctx.send(await self.bot._(ctx.channel,'info.bitly_already_shortened'))
        await ctx.send(await self.bot._(ctx.channel,'info.bitly_short', url=self.BitlyClient.shorten_url(url.url)))

    @bitly_main.command(name="find", aliases=['expand'])
    async def bitly_find(self, ctx: MyContext, url: args.URL):
        """Find the long url from a bitly link

        ..Example bitly find https://bit.ly/2JEHsUf

        ..Doc miscellaneous.html#bitly-urls"""
        if url.domain != 'bit.ly':
            return await ctx.send(await self.bot._(ctx.channel,'info.bitly_nobit'))
        await ctx.send(await self.bot._(ctx.channel,'info.bitly_long', url=self.BitlyClient.expand_url(url.url)))

    @commands.command(name='changelog',aliases=['changelogs'])
    @commands.check(checks.database_connected)
    async def changelog(self, ctx: MyContext, version: str=None):
        """Get the changelogs of the bot

        ..Example changelog

        ..Example changelog 3.7.0

        ..Doc miscellaneous.html#changelogs"""
        if version=='list':
            if not ctx.bot.beta:
                query = "SELECT `version`, `release_date` FROM `changelogs` WHERE beta=False ORDER BY release_date"
            else:
                query = f"SELECT `version`, `release_date` FROM `changelogs` ORDER BY release_date"
            async with self.bot.db_query(query) as query_results:
                results = query_results
            desc = "\n".join(reversed(["**v{}:** <t:{:.0f}>".format(x['version'],x['release_date'].timestamp()) for x in results]))
            time = None
            title = await self.bot._(ctx.channel,'info.changelogs.index')
        else:
            if version is None:
                if not ctx.bot.beta:
                    query = "SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` FROM `changelogs` WHERE beta=False ORDER BY release_date DESC LIMIT 1"
                else:
                    query = f"SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` FROM `changelogs` ORDER BY release_date DESC LIMIT 1"
            else:
                query = f"SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` FROM `changelogs` WHERE `version`='{version}'"
                if not ctx.bot.beta:
                    query += " AND `beta`=0"
            async with self.bot.db_query(query) as query_results:
                results = query_results
            if len(results) > 0:
                used_lang = await self.bot._(ctx.channel,'_used_locale')
                if used_lang not in results[0].keys():
                    used_lang = "en"
                desc = results[0][used_lang]
                time = results[0]['utc_release']
                title = (await self.bot._(ctx.channel,'misc.version')).capitalize() + ' ' + results[0]['version']
        if len(results) == 0:
            await ctx.send(await self.bot._(ctx.channel,'info.changelog.notfound'))
        elif ctx.can_send_embed:
            emb = discord.Embed(title=title, description=desc, timestamp=time, color=ctx.bot.get_cog('Servers').embed_color)
            await ctx.send(embed=emb)
        else:
            await ctx.send(desc)

    @commands.command(name="usernames", aliases=["username","usrnm"])
    @commands.check(checks.database_connected)
    async def username(self, ctx: MyContext, *, user: discord.User=None):
        """Get the names history of an user
        Default user is you

        ..Doc infos.html#usernames-history"""
        if user is None:
            user = ctx.author
        cond = f"user='{user.id}'"
        if not self.bot.beta:
            cond += " AND beta=0"
        query = f"SELECT `old`, `new`, `guild`, CONVERT_TZ(`date`, @@session.time_zone, '+00:00') AS `utc_date` FROM `usernames_logs` WHERE {cond} ORDER BY date DESC"
        async with self.bot.db_query(query) as results:
            # List creation
            this_guild = list()
            global_list = [x for x in results if x['guild'] in (None,0)]
            if ctx.guild is not None:
                this_guild = [x for x in results if x['guild']==ctx.guild.id]
        # title
        t = await self.bot._(ctx.channel,'info.usernames.title',u=user.name)
        # Embed creation
        if ctx.can_send_embed:
            MAX = 28
            date = ""
            desc = None
            fields = list()
            if len(global_list) > 0:
            # Usernames part
                temp = [x['new'] for x in global_list if x['new']!='']
                if len(temp) > 0:
                    if len(temp) > MAX:
                        temp = temp[:MAX] + [await self.bot._(ctx.channel, 'info.usernames.more', nbr=len(temp)-MAX)]
                    fields.append({'name':await self.bot._(ctx.channel,'info.usernames.global'), 'value':"\n".join(temp)})
                    date += "General: <t:{}>".format(round(global_list[0]['utc_date'].timestamp()))
            if len(this_guild) > 0:
            # Nicknames part
                temp = [x['new'] for x in this_guild if x['new']!='']
                if len(temp) > 0:
                    if len(temp) > MAX:
                        temp = temp[:MAX] + [await self.bot._(ctx.channel, 'info.usernames.more', nbr=len(temp)-MAX)]
                    fields.append({'name':await self.bot._(ctx.channel,'info.usernames.local'), 'value':"\n".join(temp)})
                    date += "\nServer: <t:{}>".format(round(this_guild[0]['utc_date'].timestamp()))
            if len(date) > 0:
                fields.append({'name':await self.bot._(ctx.channel,'info.usernames.last-date'), 'value':date})
            else:
                desc = await self.bot._(ctx.channel,'info.usernames.empty')
            if ctx.guild is not None and ctx.guild.get_member(user.id) is not None and ctx.guild.get_member(user.id).color!=discord.Color(0):
                c = ctx.guild.get_member(user.id).color
            else:
                c = 1350390
            allowing_logs = await self.bot.get_cog("Utilities").get_db_userinfo(["allow_usernames_logs"],["userID="+str(user.id)])
            if allowing_logs is None or allowing_logs["allow_usernames_logs"]:
                footer = await self.bot._(ctx.channel,'info.usernames.disallow')
            else:
                footer = await self.bot._(ctx.channel,'info.usernames.allow')
            emb = discord.Embed(title=t, description=desc, color=c)
            emb.set_footer(text=footer)
            for field in fields:
                emb.add_field(**field)
            await ctx.send(embed=emb)
        # Raw text creation
        else:
            MAX = 25
            text = ""
            if len(global_list) > 0:
                temp = [x['new'] for x in global_list if x['new']!='']
                if len(temp) > MAX:
                    temp = temp[:MAX] + [await self.bot._(ctx.channel, 'info.usernames.more', nbr=len(temp)-MAX)]
                text += "**" + await self.bot._(ctx.channel,'info.usernames.global') + "**\n" + "\n".join(temp)
            if len(this_guild) > 0:
                if len(text) > 0:
                    text += "\n\n"
                temp = [x['new'] for x in this_guild if x['new']!='']
                if len(temp) > MAX:
                    temp = temp[:MAX] + [await self.bot._(ctx.channel, 'info.usernames.more', nbr=len(temp)-MAX)]
                text += "**" + await self.bot._(ctx.channel,'info.usernames.local') + "**\n" + "\n".join(temp)
            if len(text) == 0:
                # no change known
                text = await self.bot._(ctx.channel, 'info.usernames.empty')
            await ctx.send(text)


async def setup(bot):
    locale.setlocale(locale.LC_ALL, '')
    await bot.add_cog(Info(bot))
    
