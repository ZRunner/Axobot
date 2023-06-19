
import sys
from typing import Optional, Union

import aiohttp
import discord
import psutil
from discord.ext import commands

from docs import conf
from libs.checks import checks
from libs.bot_classes import Axobot, MyContext
from libs.formatutils import FormatUtils
from utils import count_code_lines


class BotInfo(commands.Cog):
    "Commands to get information about the bot"

    def __init__(self, bot: Axobot):
        self.bot = bot
        self.file = "bot_info"
        self.bot_version = conf.release + ('a' if bot.beta else '')
        self.process = psutil.Process()
        self.process.cpu_percent()
        self.codelines: Optional[int] = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.codelines = await count_code_lines()


    @commands.command(name="admins")
    async def admin_list(self, ctx: MyContext):
        """Get the list of the bot administrators

        ..Doc miscellaneous.html#admins"""
        users_list  = []
        for user_id in checks.admins_id:
            if user_id == 552273019020771358:
                continue
            users_list.append(self.bot.get_user(user_id).name)
        await ctx.send(await self.bot._(ctx.channel,"info.admins-list", admins=", ".join(users_list)))

    async def get_guilds_count(self, ignored_guilds:list=None) -> int:
        "Get the number of guilds where the bot is"
        if ignored_guilds is None:
            if self.bot.database_online:
                if 'banned_guilds' not in self.bot.get_cog('Utilities').config.keys():
                    await self.bot.get_cog('Utilities').get_bot_infos()
                ignored_guilds = [
                    int(x)
                    for x in self.bot.get_cog('Utilities').config['banned_guilds'].split(";")
                    if len(x) > 0
                ] + self.bot.get_cog('Reloads').ignored_guilds
            else:
                return len(self.bot.guilds)
        return len([x for x in self.bot.guilds if x.id not in ignored_guilds])

    @commands.group(name="stats")
    @commands.check(checks.database_connected)
    @commands.cooldown(3, 60, commands.BucketType.guild)
    async def stats_main(self, ctx: MyContext):
        """Display some statistics about the bot

        ..Doc infos.html#statistics"""
        if ctx.subcommand_passed is None:
            await self.stats_general(ctx)

    @stats_main.command(name="general")
    async def stats_general(self, ctx: MyContext):
        "General statistics about the bot"
        python_version = sys.version_info
        f_python_version = str(python_version.major)+"."+str(python_version.minor)
        latency = round(self.bot.latency*1000, 2)
        async with ctx.channel.typing():
            # RAM/CPU
            ram_usage = round(self.process.memory_info()[0]/2.**30,3)
            if cog := self.bot.get_cog("BotStats"):
                cpu: float = await cog.get_list_usage(cog.bot_cpu_records)
            else:
                cpu = 0.0
            # Guilds count
            ignored_guilds = []
            if self.bot.database_online:
                ignored_guilds = [int(x) for x in self.bot.get_cog('Utilities').config['banned_guilds'].split(";") if len(x) > 0]
            ignored_guilds += self.bot.get_cog('Reloads').ignored_guilds
            len_servers = await self.get_guilds_count(ignored_guilds)
            # Languages
            langs_list = list((await self.bot.get_cog('ServerConfig').get_languages(ignored_guilds)).items())
            langs_list.sort(reverse=True, key=lambda x: x[1])
            lang_total = sum(x[1] for x in langs_list)
            langs_list = ' | '.join([f"{x[0]}: {x[1]/lang_total*100:.0f}%" for x in langs_list if x[1] > 0])
            del lang_total
            # Users/bots
            users,bots = self.get_users_nber(ignored_guilds)
            # Total XP
            if self.bot.database_online:
                total_xp = await self.bot.get_cog('Xp').db_get_total_xp()
            else:
                total_xp = ""
            # Commands within 24h
            cmds_24h = await self.bot.get_cog("BotStats").get_stats("wsevent.CMD_USE", 60*24)
            # number formatter
            lang = await self.bot._(ctx.guild.id,"_used_locale")
            async def n_format(nbr: Union[int, float, None]):
                return await FormatUtils.format_nbr(nbr, lang) if nbr is not None else "0"
            # Generating message
            desc = ""
            for key, var in [
                ('bot_version', self.bot_version),
                ('servers_count', await n_format(len_servers)),
                ('users_count', (await n_format(users), await n_format(bots))),
                ('codes_lines', await n_format(self.codelines)),
                ('languages', langs_list),
                ('python_version', f_python_version),
                ('lib_version', discord.__version__),
                ('ram_usage', await n_format(ram_usage)),
                ('cpu_usage', await n_format(cpu)),
                ('api_ping', await n_format(latency)),
                ('cmds_24h', await n_format(cmds_24h)),
                ('total_xp', await n_format(total_xp)+" ")]:
                str_args = {f'v{i}': var[i] for i in range(len(var))} if isinstance(var, (tuple, list)) else {'v': var}
                desc += await self.bot._(ctx.channel, "info.stats."+key, **str_args) + "\n"
        if ctx.can_send_embed: # if we can use embed
            title = await self.bot._(ctx.channel,"info.stats.title")
            color = ctx.bot.get_cog('Help').help_color
            embed = discord.Embed(title=title, color=color, description=desc)
            embed.set_thumbnail(url=self.bot.user.display_avatar.with_static_format("png"))
            await ctx.send(embed=embed)
        else:
            await ctx.send(desc)

    def get_users_nber(self, ignored_guilds: list[int]):
        "Return the amount of members and the amount of bots in every reachable guild, excepted in ignored guilds"
        members = [x.members for x in self.bot.guilds if x.id not in ignored_guilds]
        members = list(set(x for x in members for x in x)) # filter users
        return len(members), len([x for x in members if x.bot])

    @stats_main.command(name="commands", aliases=["cmds"])
    async def stats_commands(self, ctx: MyContext):
        """List the most used commands

        ..Doc infos.html#statistics"""
        forbidden = ['cmd.eval', 'cmd.admin', 'cmd.test', 'cmd.bug', 'cmd.idea', 'cmd.send_msg']
        forbidden_where = ', '.join(f"'{elem}'" for elem in forbidden)
        commands_limit = 15
        lang = await self.bot._(ctx.channel, '_used_locale')
        # SQL query
        async def do_query(minutes: Optional[int] = None):
            if minutes:
                date_where_clause = "date BETWEEN (DATE_SUB(UTC_TIMESTAMP(), INTERVAL %(minutes)s MINUTE)) AND UTC_TIMESTAMP() AND"
            else:
                date_where_clause = ""
            query = f"""
SELECT
    `all`.`variable`,
    SUBSTRING_INDEX(`all`.`variable`, ".", -1) as cmd,
    SUM(`all`.`value`) as usages
FROM
(
    (
        SELECT
    		`variable`,
	    	`value`
    	FROM `statsbot`.`zbot`
    	WHERE
        	`variable` LIKE "cmd.%" AND
            {date_where_clause}
            `variable` NOT IN ({forbidden_where}) AND
        	`entity_id` = %(entity_id)s
	) UNION ALL (
    	SELECT
        	`variable`,
	    	`value`
    	FROM `statsbot`.`zbot-archives`
    	WHERE
        	`variable` LIKE "cmd.%" AND
            {date_where_clause}
            `variable` NOT IN ({forbidden_where}) AND
        	`entity_id` = %(entity_id)s
	)
) AS `all`
GROUP BY cmd
ORDER BY usages DESC LIMIT %(limit)s"""
            query_args = {"entity_id": self.bot.entity_id, "minutes": minutes, "limit": commands_limit}
            async with self.bot.db_query(query, query_args) as query_result:
                pass
            return query_result

        # in the last 24h
        data_24h = await do_query(60*24)
        text_24h = '• ' + "\n• ".join([
            data['cmd'] + ': ' + await FormatUtils.format_nbr(data['usages'], lang)
            for data in data_24h
        ])
        title_24h = await self.bot._(ctx.channel, 'info.stats-cmds.day')
        # since the beginning
        data_total = await do_query()
        text_total = '• ' + "\n• ".join([
            data['cmd'] + ': ' + await FormatUtils.format_nbr(data['usages'], lang)
            for data in data_total
        ])
        title_total = await self.bot._(ctx.channel, 'info.stats-cmds.total')
        # message title and desc
        title = await self.bot._(ctx.channel, "info.stats-cmds.title")
        desc = await self.bot._(ctx.channel, "info.stats-cmds.description", number=commands_limit)
        # send everything
        if ctx.can_send_embed:
            emb = discord.Embed(
                title=title,
                description=desc,
                color=ctx.bot.get_cog('Help').help_color,
            )
            emb.set_thumbnail(url=self.bot.user.display_avatar.with_static_format("png"))
            emb.add_field(name=title_total, value=text_total)
            emb.add_field(name=title_24h, value=text_24h)
            await ctx.send(embed=emb)
        else:
            await ctx.send(f"**{title}**\n{desc}\n\n{title_total}:\n{text_total}\n\n{title_24h}:\n{text_24h}")

    @commands.command(name="botinvite", aliases=["botinv"])
    async def botinvite(self, ctx:MyContext):
        """Get a link to invite me

        ..Doc infos.html#bot-invite"""
        raw_oauth = "<" + discord.utils.oauth_url(self.bot.user.id) + ">"
        url = "https://zrunner.me/" + ("invitezbot" if self.bot.entity_id == 0 else "invite-axobot")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as resp:
                if resp.status >= 400:
                    url = raw_oauth
        cmd = await self.bot.get_command_mention("about")
        await ctx.send(await self.bot._(ctx.channel, "info.botinvite", url=url, about=cmd))

    @commands.command(name="pig", hidden=True)
    async def pig(self, ctx: MyContext):
        """Get bot latency
        You can also use this command to ping any other server"""
        msg = await ctx.send("Pig...")
        bot_delta = (msg.created_at - ctx.message.created_at).total_seconds()
        try:
            api_latency = round(self.bot.latency*1000)
        except OverflowError:
            api_latency = "∞"
        await msg.edit(content=await self.bot._(ctx.channel, "info.ping.pig",
                                                bot=round(bot_delta*1000),
                                                api=api_latency)
                       )

    @commands.hybrid_command(name="ping", aliases=['rep'])
    @commands.cooldown(5, 45, commands.BucketType.guild)
    async def rep(self, ctx: MyContext, ):
        """Get the bot latency

        ..Example ping

        ..Doc infos.html#ping"""
        msg = await ctx.send("Ping...")
        bot_delta = (msg.created_at - ctx.message.created_at).total_seconds()
        try:
            api_latency = round(self.bot.latency*1000)
        except OverflowError:
            api_latency = "∞"
        await msg.edit(content=await self.bot._(ctx.channel, "info.ping.normal",
                                                bot=round(bot_delta*1000),
                                                api=api_latency)
                       )


    @commands.command(name="docs", aliases=['doc','documentation'])
    async def display_doc(self, ctx: MyContext):
        """Get the documentation url"""
        text = self.bot.emojis_manager.customs['readthedocs'] + await self.bot._(ctx.channel,"info.docs") + \
            " https://axobot.rtfd.io"
        if self.bot.entity_id == 0:
            text += '/en/main'
        elif self.bot.entity_id == 1:
            text += '/en/develop'
        await ctx.send(text)

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
                query = "SELECT `version`, `release_date` FROM `changelogs` ORDER BY release_date"
            async with self.bot.db_query(query) as query_results:
                results = query_results
            desc = "\n".join(reversed([
                "**v{}:** <t:{:.0f}>".format(row['version'], row['release_date'].timestamp())
                for row in results
            ]))
            last_release_time = None
            title = await self.bot._(ctx.channel,'info.changelogs.index')
        else:
            if version is None:
                if not ctx.bot.beta:
                    query = "SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` \
                        FROM `changelogs` WHERE beta=False ORDER BY release_date DESC LIMIT 1"
                else:
                    query = "SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` \
                        FROM `changelogs` ORDER BY release_date DESC LIMIT 1"
            else:
                query = f"SELECT *, CONVERT_TZ(`release_date`, @@session.time_zone, '+00:00') AS `utc_release` \
                    FROM `changelogs` WHERE `version`='{version}'"
                if not ctx.bot.beta:
                    query += " AND `beta`=0"
            async with self.bot.db_query(query) as query_results:
                results = query_results
            if len(results) > 0:
                used_lang = await self.bot._(ctx.channel,'_used_locale')
                if used_lang not in results[0].keys():
                    used_lang = "en"
                desc = results[0][used_lang]
                last_release_time = results[0]['utc_release']
                title = (await self.bot._(ctx.channel,'misc.version')).capitalize() + ' ' + results[0]['version']
        if len(results) == 0:
            await ctx.send(await self.bot._(ctx.channel,'info.changelog.notfound'))
        elif ctx.can_send_embed:
            embed_color = ctx.bot.get_cog('ServerConfig').embed_color
            emb = discord.Embed(title=title, description=desc, timestamp=last_release_time, color=embed_color)
            await ctx.send(embed=emb)
        else:
            await ctx.send(desc)

    @commands.command(name="prefix")
    async def get_prefix(self, ctx: MyContext):
        """Show the usable prefix(s) for this server

        ..Doc infos.html#prefix"""
        txt = await self.bot._(ctx.channel,"info.prefix")
        prefix = "\n".join((await ctx.bot.get_prefix(ctx.message))[1:])
        if ctx.can_send_embed:
            emb = discord.Embed(title=txt, description=prefix, timestamp=ctx.message.created_at,
                color=ctx.bot.get_cog('Help').help_color)
            emb.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.send(embed=emb)
        else:
            await ctx.send(txt+"\n"+prefix)

    @commands.command(name="welcome", aliases=['bvn', 'bienvenue', 'leave'])
    @commands.cooldown(10, 30, commands.BucketType.channel)
    async def bvn_help(self, ctx: MyContext):
        """Help on setting up welcome / leave messages

..Doc infos.html#welcome-message"""
        config_cmd = await self.bot.get_command_mention("config set")
        await ctx.send(await self.bot._(ctx.guild, "welcome.help", config_cmd=config_cmd))

    @commands.hybrid_command(name="about", aliases=["botinfos", "botinfo"])
    @commands.cooldown(7, 30, commands.BucketType.user)
    async def about_cmd(self, ctx: MyContext):
        """Information about the bot

..Doc infos.html#about"""
        urls = ""
        bot_invite = "https://zrunner.me/" + ("invitezbot" if self.bot.entity_id == 0 else "invite-axobot")
        links = {
            "server": "https://discord.gg/N55zY88",
            "invite": bot_invite,
            "docs": "https://axobot.rtfd.io/",
            "privacy": "https://zrunner.me/axobot-privacy.pdf",
            "sponsor": "https://github.com/sponsors/ZRunner",
        }
        for key, url in links.items():
            urls += "\n:arrow_forward: " + await self.bot._(ctx.channel, f"info.about.{key}") + " <" + url + ">"
        msg = await self.bot._(ctx.channel, "info.about-main", mention=ctx.bot.user.mention, links=urls)
        if ctx.can_send_embed:
            await ctx.send(embed=discord.Embed(description=msg, color=16298524))
        else:
            await ctx.send(msg)


async def setup(bot: Axobot):
    await bot.add_cog(BotInfo(bot))
