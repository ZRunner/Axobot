import glob
import os
import sys
from typing import Literal, Optional, Union

import discord
import psutil
from discord.ext import commands

from docs import conf
from libs.bot_classes import Axobot, MyContext
from libs.checks import checks
from libs.formatutils import FormatUtils


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
        await self.refresh_code_lines_count()


    async def refresh_code_lines_count(self):
        """Count lines of Python code in the current folder

        Comments and empty lines are ignored."""
        count = 0
        path = os.getcwd() + '/**/*.py'
        for filename in glob.iglob(path, recursive=True):
            if '/env/' in filename or not filename.endswith('.py'):
                continue
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file.read().split("\n"):
                    cleaned_line = line.strip()
                    if len(cleaned_line) > 2 and not cleaned_line.startswith('#') or cleaned_line.startswith('"'):
                        count += 1
        self.codelines = count

    async def get_ignored_guilds(self) -> list[int]:
        "Get the list of ignored guild IDs"
        if self.bot.database_online:
            if 'banned_guilds' not in self.bot.get_cog('Utilities').config.keys():
                await self.bot.get_cog('Utilities').get_bot_infos()
            return [
                int(x)
                for x in self.bot.get_cog('Utilities').config['banned_guilds'].split(";")
                if len(x) > 0
            ] + self.bot.get_cog('Reloads').ignored_guilds
        return []

    async def get_guilds_count(self, ignored_guilds:list=None) -> int:
        "Get the number of guilds where the bot is"
        if ignored_guilds is None:
            if self.bot.database_online:
                ignored_guilds = await self.get_ignored_guilds()
            else:
                return len(self.bot.guilds)
        return len([x for x in self.bot.guilds if x.id not in ignored_guilds])

    @commands.hybrid_command(name="stats")
    @commands.check(checks.database_connected)
    @commands.cooldown(3, 60, commands.BucketType.guild)
    async def stats_main(self, ctx: MyContext, category: Literal["general", "commands"]="general"):
        """Display some statistics about the bot

        ..Doc infos.html#statistics"""
        if category == "general":
            await self.stats_general(ctx)
        elif category == "commands":
            await self.stats_commands(ctx)

    async def stats_general(self, ctx: MyContext):
        "General statistics about the bot"
        await ctx.defer()
        python_version = sys.version_info
        f_python_version = str(python_version.major)+"."+str(python_version.minor)
        latency = round(self.bot.latency*1000, 2)
        # RAM/CPU
        ram_usage = round(self.process.memory_info()[0]/2.**30,3)
        if cog := self.bot.get_cog("BotStats"):
            cpu: float = await cog.get_list_usage(cog.bot_cpu_records)
        else:
            cpu = 0.0
        # Guilds count
        ignored_guilds = await self.get_ignored_guilds()
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
        cmds_24h = await self.bot.get_cog("BotStats").get_sum_stats("wsevent.CMD_USE", 60*24)
        # RSS messages within 24h
        rss_msg_24h = await self.bot.get_cog("BotStats").get_sum_stats("rss.messages", 60*24)
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
            ('rss_msg_24h', await n_format(rss_msg_24h)),
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

    async def stats_commands(self, ctx: MyContext):
        """List the most used commands

        ..Doc infos.html#statistics"""
        forbidden = ['eval', 'admin', 'test', 'bug', 'idea', 'send_msg']
        forbidden_where = ', '.join(f"'cmd.{elem}'" for elem in forbidden)
        forbidden_where += ', ' + ', '.join(f"'app_cmd.{elem}'" for elem in forbidden)
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
            return [row for row in query_result if not any(row["cmd"].startswith(x) for x in forbidden)]

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


    @commands.hybrid_command(name="documentation", aliases=['doc', 'docs'])
    async def display_doc(self, ctx: MyContext):
        """Get the documentation url"""
        text = self.bot.emojis_manager.customs['readthedocs'] + await self.bot._(ctx.channel,"info.docs") + \
            " https://axobot.rtfd.io"
        if self.bot.entity_id == 1:
            text += '/en/develop'
        await ctx.send(text)


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

    @commands.hybrid_command(name="about", aliases=["botinfos", "botinfo"])
    @commands.cooldown(7, 30, commands.BucketType.user)
    async def about_cmd(self, ctx: MyContext):
        """Information about the bot

..Doc infos.html#about"""
        urls = ""
        bot_invite = discord.utils.oauth_url(self.bot.user.id)
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

    @commands.hybrid_command(name="random-tip")
    @commands.cooldown(10, 30)
    async def tip(self, ctx: MyContext):
        """Send a random tip or trivia about the bot

        ..Doc fun.html#tip"""
        await ctx.send(await self.bot.tips_manager.generate_random_tip(ctx.channel))


async def setup(bot: Axobot):
    await bot.add_cog(BotInfo(bot))
