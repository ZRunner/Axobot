import copy
import datetime
import time
from typing import Optional

import discord
from asyncache import cached
from cachetools import TTLCache
from discord import app_commands
from discord.ext import commands

from libs.arguments import args
from libs.bot_classes import Axobot, MyContext
from libs.checks import checks
from libs.formatutils import FormatUtils
from libs.paginator import PaginatedSelectView
from libs.views import ConfirmView


class Timers(commands.Cog):
    "Reminders system"

    def __init__(self, bot: Axobot):
        self.bot = bot
        self.file = "timers"

    async def db_get_reminder(self, reminder_id: int, user: Optional[int] = None) -> Optional[dict]:
        "Get a specific reminder for a user"
        if user is not None:
            query = "SELECT * FROM `timed` WHERE user=%s AND action='timer' AND ID=%s AND `beta`=%s"
            q_args = (user, reminder_id, self.bot.beta)
        else:
            query = "SELECT * FROM `timed` WHERE action='timer' AND ID=%s AND `beta`=%s"
            q_args = (reminder_id, self.bot.beta)
        async with self.bot.db_query(query, q_args, fetchone=True) as query_result:
            return query_result

    async def db_get_user_reminders(self, user: int) -> list[dict]:
        "Get every active user reminder"
        query = "SELECT * FROM `timed` WHERE user=%s AND action='timer' AND `beta`=%s"
        async with self.bot.db_query(query, (user, self.bot.beta)) as query_results:
            return query_results

    async def db_get_user_reminders_count(self, user: int) -> int:
        "Get the number of active user reminder"
        query = "SELECT COUNT(*) as count FROM `timed` WHERE user=%s AND action='timer' AND `beta`=%s"
        async with self.bot.db_query(query, (user, self.bot.beta), fetchone=True) as query_results:
            return query_results["count"]

    async def db_delete_reminder(self, reminder_id: int, user: int):
        "Delete a reminder for a user"
        query = "DELETE FROM `timed` WHERE user=%s AND action='timer' AND ID=%s AND `beta`=%s"
        async with self.bot.db_query(query, (user, reminder_id, self.bot.beta), returnrowcount=True) as query_result:
            return query_result > 0

    async def db_delete_reminders(self, reminder_ids: list[int], user: int) -> bool:
        "Delete multiple reminders for a user"
        list_placeholder = ",".join(["%s"] * len(reminder_ids))
        query = f"DELETE FROM `timed` WHERE user=%s AND action='timer' AND ID IN ({list_placeholder})"
        async with self.bot.db_query(query, (user, *reminder_ids), returnrowcount=True) as query_result:
            return query_result > 0

    async def db_delete_all_user_reminders(self, user: int):
        "Delete every reminder for a user"
        query = "DELETE FROM `timed` WHERE user=%s AND action='timer' AND `beta`=%s"
        async with self.bot.db_query(query, (user, self.bot.beta)) as _:
            pass

    async def db_register_reminder_snooze(self, original_duration: int, new_duration: int):
        "Register a snooze"
        query = "INSERT INTO `reminder_snoozes_logs` (`original_duration`, `snooze_duration`, `beta`) VALUES (%s, %s, %s)"
        async with self.bot.db_query(query, (original_duration, new_duration, self.bot.beta)):
            pass

    @cached(TTLCache(1_000, ttl=60))
    async def format_duration_left(self, end_date: datetime.datetime, lang: str) -> str:
        "Format the duration left for a reminder"
        now = self.bot.utcnow() if end_date.tzinfo else datetime.datetime.utcnow()
        if now > end_date:
            return "-" + await FormatUtils.time_delta(
                end_date, now,
                lang=lang, year=True, seconds=False, form="short"
            )
        return await FormatUtils.time_delta(
            now, end_date,
            lang=lang, year=True, seconds=False, form="short"
        )

    @cached(TTLCache(1_000, ttl=30))
    async def _get_reminders_for_choice(self, user_id: int):
        "Returns a list of reminders for a given user"
        return await self.db_get_user_reminders(user_id)

    @cached(TTLCache(1_000, ttl=60))
    async def _format_reminder_choice(self, current: str, lang: str, reminder_id: int, begin_date: datetime.datetime,
                                      duration: str, reminder_message: str
                                      ) -> Optional[tuple[bool, float, app_commands.Choice[str]]]:
        "Format a reminder for a discord Choice"
        end_date: datetime.datetime = begin_date + datetime.timedelta(seconds=duration)
        f_duration = await self.format_duration_left(end_date, lang)
        label: str = f_duration + " - " + reminder_message
        if current not in label:
            return None
        if len(label) > 40:
            label = label[:37] + "..."
        choice = app_commands.Choice(value=str(reminder_id), name=label)
        priority = not reminder_message.lower().startswith(current)
        return (priority, -end_date.timestamp(), choice)


    @cached(TTLCache(1_000, ttl=30))
    async def get_reminders_choice(self, user_id: int, lang: str, current: str) -> list[app_commands.Choice[str]]:
        "Returns a list of reminders Choice for a given user, matching the current input"
        reminders = await self._get_reminders_for_choice(user_id)
        if len(reminders) == 0:
            return []
        choices: list[tuple[bool, int, app_commands.Choice[str]]] = []
        for reminder in reminders:
            if formated_reminder := await self._format_reminder_choice(
                current, lang, reminder["ID"], reminder["begin"], reminder["duration"], reminder["message"]
                ):
                choices.append(formated_reminder)
        return [choice for _, _, choice in sorted(choices, key=lambda x: x[0:2])]


    @commands.hybrid_command(name="remindme", aliases=['rmd'])
    @app_commands.describe(duration="The duration to wait, eg. '2d 4h'", message="The message to remind you of")
    @commands.cooldown(5, 30, commands.BucketType.channel)
    @commands.cooldown(5, 60, commands.BucketType.user)
    @commands.check(checks.database_connected)
    async def remindme(self, ctx: MyContext, duration: commands.Greedy[args.Duration], *, message: str):
        """Create a new reminder
        This is actually an alias of `reminder create`

        ..Example rmd 3h 5min It's pizza time!

        ..Example remindme 3months Christmas is coming!

        ..Doc miscellaneous.html#create-a-new-reminder"""
        await self.remind_create(ctx, duration, message=message)


    @commands.hybrid_group(name="reminders", aliases=["reminds", "reminder"])
    async def remind_main(self, ctx: MyContext):
        """Manage your pending reminders

        ..Doc miscellaneous.html#reminders"""
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)


    @remind_main.command(name="create", aliases=["add"])
    @app_commands.describe(duration="The duration to wait, eg. '2d 4h'", message="The message to remind you of")
    @commands.cooldown(5, 30, commands.BucketType.channel)
    @commands.cooldown(5, 60, commands.BucketType.user)
    @commands.check(checks.database_connected)
    async def remind_create(self, ctx: MyContext, duration: commands.Greedy[args.Duration], *, message: str):
        """Create a new reminder

        Please use the following format:
        `XXm` : XX minutes
        `XXh` : XX hours
        `XXd` : XX days
        `XXw` : XX weeks
        `XXm` : XX months

        ..Example reminders create 49d Think about doing my homework

        ..Example reminders create 3h 5min It's pizza time!

        ..Doc miscellaneous.html#create-a-new-reminder
        """
        duration = sum(duration)
        if duration < 1:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.too-short"))
            return
        if duration > 60*60*24*365*5:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.too-long"))
            return
        await ctx.defer()
        lang = await self.bot._(ctx.channel,'_used_locale')
        f_duration = await FormatUtils.time_delta(duration, lang=lang, year=True, form='developed')
        try:
            data = {'msg_url': ctx.message.jump_url}
            await ctx.bot.task_handler.add_task(
                "timer",
                duration,
                ctx.author.id,
                ctx.guild.id if ctx.guild else None,
                ctx.channel.id,
                message,
                data
            )
        except Exception as err:
            self.bot.dispatch("command_error", ctx, err)
        else:
            timestamp = f"<t:{time.time() + duration:.0f}>"
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.saved", duration=f_duration, timestamp=timestamp))


    @remind_main.command(name="list")
    @commands.cooldown(5, 60, commands.BucketType.user)
    @commands.check(checks.database_connected)
    async def remind_list(self, ctx: MyContext):
        """List your pending reminders

        ..Doc miscellaneous.html#list-your-reminders
        """
        reminders = await self.db_get_user_reminders(ctx.author.id)
        if len(reminders) == 0:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.empty"))
            return
        txt = await self.bot._(ctx.channel, "timers.rmd.item")
        lang = await self.bot._(ctx.channel, '_used_locale')
        reminders_formated_list: list[int, str] = []
        for item in reminders:
            ctx2 = copy.copy(ctx)
            ctx2.message.content = item["message"]
            item["message"] = await commands.clean_content(fix_channel_mentions=True).convert(ctx2, item["message"])
            msg = item['message'] if len(item['message'])<=50 else item['message'][:47]+"..."
            msg = discord.utils.escape_markdown(msg).replace("\n", " ")
            chan = '<#'+str(item['channel'])+'>'
            end: datetime.datetime = item["begin"] + datetime.timedelta(seconds=item['duration'])
            duration = await self.format_duration_left(end, lang)
            item = txt.format(id=item['ID'], duration=duration, channel=chan, msg=msg)
            reminders_formated_list.append((-end.timestamp(), item))
        reminders_formated_list.sort()
        labels = [item[1] for item in reminders_formated_list]
        if ctx.can_send_embed:
            emb = discord.Embed(title=await self.bot._(ctx.channel, "timers.rmd.title"),color=16108042)
            if len("\n".join(labels)) > 2000:
                step = 5
                for i in range(0, max(25, len(labels)), step):
                    emb.add_field(name=self.bot.zws, value="\n".join(labels[i:i+step]), inline=False)
            else:
                emb.description = "\n".join(labels)
            await ctx.send(embed=emb)
        else:
            text = "**"+await self.bot._(ctx.channel, "timers.rmd.title")+"**\n\n".join(labels)
            await ctx.send(text)

    async def transform_reminders_options(self, reminders: list[dict]):
        "Transform reminders data into discord SelectOption"
        res = []
        for reminder in reminders:
            if len(reminder['message']) > 90:
                reminder['message'] = reminder['message'][:89] + '…'
            label = reminder['message']
            desc = f"{reminder['tr_channel']} - {reminder['tr_duration']}"
            res.append(discord.SelectOption(value=str(reminder['id']), label=label, description=desc))
        return res

    async def ask_reminder_ids(self, input_id: Optional[int], ctx: MyContext, title: str) -> Optional[list[int]]:
        "Ask the user to select reminder IDs"
        selection = []
        if input_id is not None:
            input_reminder = await self.db_get_reminder(input_id, ctx.author.id)
            if not input_reminder:
                input_id = None
            else:
                selection.append(input_reminder["ID"])
        if input_id is None:
            reminders = await self.db_get_user_reminders(ctx.author.id)
            if len(reminders) == 0:
                await ctx.send(await self.bot._(ctx.channel, "timers.rmd.empty"))
                return
            reminders_data: list[dict] = []
            lang = await self.bot._(ctx.channel, '_used_locale')
            for reminder in reminders:
                rmd_data = {
                    "id": reminder["ID"],
                    "message": reminder["message"]
                }
                # channel name
                if channel := self.bot.get_channel(reminder["channel"]):
                    rmd_data["tr_channel"] = "DM" if isinstance(channel, discord.abc.PrivateChannel) else ("#" + channel.name)
                else:
                    rmd_data["tr_channel"] = reminder["channel"]
                # duration
                end: datetime.datetime = reminder["begin"] + datetime.timedelta(seconds=reminder['duration'])
                now = ctx.bot.utcnow() if end.tzinfo else datetime.datetime.utcnow()
                if now > end:
                    duration = "-" + await FormatUtils.time_delta(
                        end, now,
                        lang=lang, year=True, form="short"
                    )
                else:
                    duration = await FormatUtils.time_delta(
                        now, end,
                        lang=lang, year=True, form="short"
                    )
                rmd_data["tr_duration"] = duration
                # append to the list
                reminders_data.append(rmd_data)
            form_placeholder = await self.bot._(ctx.channel, 'timers.rmd.select-placeholder')
            view = PaginatedSelectView(self.bot,
                message=title,
                options=await self.transform_reminders_options(reminders_data),
                user=ctx.author,
                placeholder=form_placeholder,
                max_values=len(reminders_data)
            )
            msg = await view.send_init(ctx)
            await view.wait()
            if view.values is None:
                # timeout
                await view.disable(msg)
                return
            try:
                if isinstance(view.values, str):
                    selection = [int(view.values)]
                else:
                    selection = list(map(int, view.values))
            except ValueError:
                selection = []
                self.bot.dispatch("error", ValueError(f"Invalid reminder IDs: {view.values}"), ctx)
        if len(selection) == 0:
            cmd = await self.bot.get_command_mention("about")
            await ctx.send(await self.bot._(ctx.guild, "errors.unknown2", about=cmd))
            return
        return selection

    @remind_main.command(name="delete", aliases=["remove", "del"])
    @commands.cooldown(5, 30, commands.BucketType.user)
    @commands.check(checks.database_connected)
    async def remind_del(self, ctx: MyContext, reminder_id: Optional[int] = None):
        """Delete a reminder
        ID can be found with the `reminder list` command.

        ..Example reminders delete

        ..Example reminders delete 253

        ..Doc miscellaneous.html#delete-a-reminder
        """
        ids = await self.ask_reminder_ids(reminder_id, ctx, await ctx.bot._(ctx.channel, "timers.rmd.delete.title"))
        if ids is None:
            return
        if await self.db_delete_reminders(ids, ctx.author.id):
            for rmd_id in ids:
                await self.bot.task_handler.remove_task(rmd_id)
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.delete.success", count=len(ids)))
        else:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.delete.error"))
            try:
                raise ValueError(f"Failed to delete reminders: {ids}")
            except ValueError as err:
                self.bot.dispatch("error", err, ctx)

    @remind_del.autocomplete("reminder_id")
    async def remind_del_autocomplete(self, interaction: discord.Interaction, current: str):
        "Autocomplete for the reminder ID"
        try:
            return await self.get_reminders_choice(interaction.user.id, "en", current.lower())
        except Exception as err:
            self.bot.dispatch("interaction_error", interaction, err)

    @remind_main.command(name="clear")
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.check(checks.database_connected)
    async def remind_clear(self, ctx: MyContext):
        """Remove every pending reminder

        ..Doc miscellaneous.html#clear-every-reminders"""
        count = await self.db_get_user_reminders_count(ctx.author.id)
        if count == 0:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.empty"))
            return

        confirm_view = ConfirmView(self.bot, ctx.channel,
            validation=lambda inter: inter.user==ctx.author,
            timeout=20)
        await confirm_view.init()
        confirm_msg = await ctx.send(await self.bot._(ctx.channel, "timers.rmd.confirm", count=count), view=confirm_view)

        await confirm_view.wait()
        await confirm_view.disable(confirm_msg)
        if confirm_view.value is None:
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.cancelled"))
            return
        if confirm_view.value:
            await self.db_delete_all_user_reminders(ctx.author.id)
            await ctx.send(await self.bot._(ctx.channel, "timers.rmd.cleared"))


    @commands.Cog.listener()
    async def on_reminder_snooze(self, initial_duration: int, snooze_duration: int):
        "Called when a reminder is snoozed"
        await self.db_register_reminder_snooze(initial_duration, snooze_duration)


async def setup(bot):
    await bot.add_cog(Timers(bot))
