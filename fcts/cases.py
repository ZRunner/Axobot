import discord, importlib, typing
from discord.ext import commands
from utils import Zbot, MyContext

from fcts import args, reloads
importlib.reload(args)


async def can_edit_case(ctx: MyContext):
    if await ctx.bot.get_cog('Admin').check_if_admin(ctx.author):
        return True
    if ctx.bot.database_online:
        return await ctx.bot.get_cog("Servers").staff_finder(ctx.author,"warn")
    return False

class Cases(commands.Cog):
    """This part of the bot allows you to manage all your members' cases, to delete or edit them"""

    def __init__(self, bot: Zbot):
        self.bot = bot
        self.file = "cases"
        if bot.user is not None:
            self.table = 'cases_beta' if bot.beta else 'cases'

    @commands.Cog.listener()
    async def on_ready(self):
        self.table = 'cases_beta' if self.bot.beta else 'cases'

    class Case:
        def __init__(self,bot:Zbot,guildID:int,memberID:int,Type,ModID:int,Reason,date,duration=None,caseID=None):
            self.bot = bot
            self.guild = guildID
            self.id = caseID
            self.user = memberID
            self.type = Type
            self.mod = ModID
            self.reason = Reason
            self.duration = duration
            if date is None:
                self.date = "Unknown"
            else:
                self.date = date

        async def display(self, display_guild: bool=False) -> str:
            u = self.bot.get_user(self.user)
            if u is None:
                u = self.user
            else:
                u = u.mention
            g: discord.Guild = self.bot.get_guild(self.guild)
            if g is None:
                g = self.guild
            else:
                g = g.name
            text = await self.bot._(self.guild, "cases.title-search", ID=self.id)
            # add guild name if needed
            if display_guild:
                text += await self.bot._(self.guild, "cases.display.guild", data=g)
            # add fields
            for key, value in (
                ("type", self.type),
                ("user", u),
                ("moderator", self.mod),
                ("date", self.date or self.bot._(self.guild, "misc.unknown")),
                ("reason", self.reason)):
                text += await self.bot._(self.guild, "cases.display."+key, data=value)
            # add duration if exists
            if self.duration is not None and self.duration > 0:
                cog = await self.bot.get_cog('TimeUtils')
                if cog is not None:
                    lang = await self.bot._(self.guild, "_used_locale")
                    text += await self.bot._(self.guild, "cases.display.duration", data=cog.time_delta(self.duration,lang=lang,form='temp'))
            return text

    async def get_case(self, columns=None, criters=None, relation="AND") -> typing.Optional[list[Case]]:
        """return every cases"""
        if not self.bot.database_online:
            return None
        if columns is None:
            columns = []
        if criters is None:
            criters = ["1"]
        if not isinstance(columns, list) or not isinstance(criters, list):
            raise ValueError
        if len(columns) == 0:
            cl = "*"
        else:
            cl = "`"+"`,`".join(columns)+"`"
        relation = " "+relation+" "
        query = ("SELECT {} FROM `{}` WHERE {}".format(cl,self.table,relation.join(criters)))
        liste = list()
        async with self.bot.db_query(query) as query_results:
            if len(columns) == 0:
                for elem in query_results:
                    case = self.Case(bot=self.bot, guildID=elem['guild'], caseID=elem['ID'], memberID=elem['user'],
                                     Type=elem['type'], ModID=elem['mod'], date=elem['created_at'], Reason=elem['reason'],
                                     duration=elem['duration'])
                    liste.append(case)
            else:
                for elem in query_results:
                    liste.append(elem)
        return liste

    async def get_nber(self, user_id:int, guild_id:int):
        """Get the number of users infractions"""
        try:
            query = ("SELECT COUNT(*) as count FROM `{}` WHERE `user`={} AND `guild`={} AND `type`!='unban'".format(self.table, user_id, guild_id))
            async with self.bot.db_query(query, fetchone=True) as query_results:
                if len(query_results) == 1:
                    return query_results['count']
            return 0
        except Exception as err:
            await self.bot.get_cog('Errors').on_error(err,None)

    async def delete_case(self, case_id: int):
        """delete a case from the db"""
        if not self.bot.database_online:
            return None
        if not isinstance(case_id, int):
            raise ValueError
        query = ("DELETE FROM `{}` WHERE `ID`='{}'".format(self.table, case_id))
        async with self.bot.db_query(query):
            pass
        return True

    async def add_case(self, case):
        """add a new case to the db"""
        if not self.bot.database_online:
            return None
        if not isinstance(case, self.Case):
            raise ValueError
        query = "INSERT INTO `{}` (`guild`, `user`, `type`, `mod`, `reason`,`duration`) VALUES (%(g)s, %(u)s, %(t)s, %(m)s, %(r)s, %(d)s)".format(self.table)
        query_args = { 'g': case.guild, 'u': case.user, 't': case.type, 'm': case.mod, 'r': case.reason, 'd': case.duration }
        async with self.bot.db_query(query, query_args) as last_row_id:
            case.id = last_row_id
        return True

    async def update_reason(self, case):
        """update infos of a case"""
        if not self.bot.database_online:
            return False
        if not isinstance(case, self.Case):
            raise ValueError
        query = ("UPDATE `{}` SET `reason` = %s WHERE `ID` = %s".format(self.table))
        async with self.bot.db_query(query, (case.reason, case.id)):
            pass
        return True


    @commands.group(name="cases",aliases=['case', 'infractions'])
    @commands.guild_only()
    @commands.cooldown(5, 15, commands.BucketType.user)
    @commands.check(can_edit_case)
    async def case_main(self, ctx: MyContext):
        """Do anything with any user cases
        
        ..Doc moderator.html#handling-cases"""
        if ctx.subcommand_passed is None:
            await self.bot.get_cog('Help').help_command(ctx, ['cases'])

    @case_main.command(name="list")
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def see_case(self, ctx: MyContext, *, user:args.user):
        """Get every case of a user
        This user can have left the server

        ..Example cases list someone#7515
        
        ..Doc moderator.html#view-list"""
        if not self.bot.database_online:
            return await ctx.send(await self.bot._(ctx.guild.id,'cases.no_database'))
        await self.see_case_main(ctx,ctx.guild.id,user.id)

    @case_main.command(name="glist")
    @commands.guild_only()
    @commands.check(reloads.is_support_staff)
    async def see_case_2(self, ctx: MyContext, guild: typing.Optional[args.Guild], *, user:args.user):
        """Get every case of a user on a specific guild or on every guilds
        This user can have left the server
        
        ..Example cases glist "ZBot Staff" someone
        
        ..Example cases glist someone"""
        if not self.bot.database_online:
            return await ctx.send(await self.bot._(ctx.guild.id,'cases.no_database'))
        await self.see_case_main(ctx, guild.id if guild else None, user.id)
        
    async def see_case_main(self, ctx: MyContext, guild:discord.Guild, user:discord.User):
        if guild is not None:
            criters = ["`user`='{}'".format(user),"guild='{}'".format(guild)]
            syntax: str = await self.bot._(ctx.guild,'cases.list-0')  
        else:
            syntax: str = await self.bot._(ctx.guild,'cases.list-1')
            criters = ["`user`='{}'".format(user)]
        try:
            MAX_CASES = 60
            cases = await self.get_case(criters=criters)
            total_nbr = len(cases)
            cases = cases[-MAX_CASES:]
            cases.reverse()
            u = self.bot.get_user(user)
            if len(cases) == 0:
                await ctx.send(await self.bot._(ctx.guild.id, "cases.no-case"))
                return
            if ctx.can_send_embed:
                last_case = e = total_nbr if len(cases) > 0 else 0
                embed = discord.Embed(title="title", colour=self.bot.get_cog('Servers').embed_color, timestamp=ctx.message.created_at)
                if u is None:
                    embed.set_author(name=str(user))
                else:
                    embed.set_author(name="Cases from "+str(u), icon_url=str(u.display_avatar.with_format("png")))
                embed.set_footer(text="Requested by {}".format(ctx.author), icon_url=str(ctx.author.display_avatar.with_format("png")))
                if len(cases) > 0:
                    l = await self.bot._(ctx.guild.id,'_used_locale')
                    for x in cases:
                        e -= 1
                        g: discord.Guild = self.bot.get_guild(x.guild)
                        if g is None:
                            g = x.guild
                        else:
                            g = g.name
                        m: discord.Member = self.bot.get_user(x.mod)
                        if m is None:
                            m = x.mod
                        else:
                            m = m.mention
                        text = syntax.format(G=g,T=x.type,M=m,R=x.reason,D=await self.bot.get_cog('TimeUtils').date(x.date,lang=l,year=True,digital=True))
                        if x.duration is not None and x.duration > 0:
                            text += "\n" + await self.bot._(ctx.guild.id,'cases.display.duration', data=await self.bot.get_cog('TimeUtils').time_delta(x.duration,lang=l,year=False,form='temp'))
                        embed.add_field(name=await self.bot._(ctx.guild.id, "cases.title-search", ID=x.id), value=text, inline=False)
                        if len(embed.fields) == 20:
                            embed.title = await self.bot._(ctx.guild.id,"cases.cases-0", nbr=total_nbr, start=e+1, end=last_case)
                            await ctx.send(embed=embed)
                            embed.clear_fields()
                            last_case = e
                if len(embed.fields) > 0:
                    embed.title = await self.bot._(ctx.guild.id,"cases.cases-0", nbr=total_nbr, start=e+1, end=last_case)
                    await ctx.send(embed=embed)
            else:
                if len(cases) > 0:
                    text = await self.bot._(ctx.guild.id,"cases.cases-0", nbr=total_nbr, start=1, end=total_nbr) + "\n"
                    for e, x in enumerate(cases):
                        text += "```{}\n```".format((await x.display(True)).replace('*',''))
                        if len(text) > 1800:
                            await ctx.send(text)
                            text = ""
                    if len(text) > 0:
                        await ctx.send(text)
        except Exception as e:
            await self.bot.get_cog("Errors").on_error(e,None)
    

    @case_main.command(name="reason",aliases=['edit'])
    @commands.guild_only()
    async def reason(self, ctx: MyContext, case:int, *, reason):
        """Edit the reason of a case
        
        ..Example cases reason 95 Was too dumb
        
        ..Doc moderator.html#edit-reason"""
        if not self.bot.database_online:
            return await ctx.send(await self.bot._(ctx.guild.id,'cases.no_database'))
        try:
            c = ["ID="+str(case)]
            if not await self.bot.get_cog('Admin').check_if_admin(ctx.author):
                c.append("guild="+str(ctx.guild.id))
            cases = await self.get_case(criters=c)
        except Exception as e:
            await self.bot.get_cog("Errors").on_error(e,None)
            return
        if len(cases)!=1:
            await ctx.send(await self.bot._(ctx.guild.id,"cases.not-found"))
            return
        case = cases[0]
        old_reason = case.reason
        case.reason = reason
        await self.update_reason(case)
        await ctx.send(await self.bot._(ctx.guild.id,"cases.reason-edited", ID=case.id))
        log = await self.bot._(ctx.guild.id,"logs.case-reason",old=old_reason,new=case.reason,id=case.id)
        await self.bot.get_cog("Events").send_logs_per_server(ctx.guild,"case-edit",log,ctx.author)
    
    @case_main.command(name="search")
    @commands.guild_only()
    async def search_case(self, ctx: MyContext, case:int):
        """Search for a specific case in your guild
        
        ..Example cases search 69
        
        ..Doc moderator.html#search-for-a-case"""
        if not self.bot.database_online:
            return await ctx.send(await self.bot._(ctx.guild.id,'cases.no_database'))
        try:
            isSupport = await reloads.is_support_staff(ctx)
            c = ["ID="+str(case)]
            if not isSupport:
                c.append("guild="+str(ctx.guild.id))
            cases = await self.get_case(criters=c)
        except Exception as err:
            await self.bot.get_cog("Errors").on_error(err,ctx)
            return
        if len(cases)!=1:
            await ctx.send(await self.bot._(ctx.guild.id,"cases.not-found"))
            return
        if not ctx.can_send_embed:
            await ctx.send(await self.bot._(ctx.guild.id,"minecraft.cant-embed"))
            return
        try:
            case = cases[0]
            user = await self.bot.fetch_user(case.user)
            mod = await self.bot.fetch_user(case.mod)
            u = "{} ({})".format(user,user.id)
            title = await self.bot._(ctx.guild.id,"cases.title-search", ID=case.id)
            l = await self.bot._(ctx.guild.id, '_used_locale')
            # main structure
            if not isSupport:
                guild = ctx.guild.name
                _msg = await self.bot._(ctx.guild.id,'cases.search-0')
            else: # if support: add guild
                guild = "{0.name} ({0.id})".format(self.bot.get_guild(case.guild))
                _msg = await self.bot._(ctx.guild.id,'cases.search-1')
            # add duration
            if case.duration is not None and case.duration > 0:
                _msg += await self.bot._(ctx.guild.id,'cases.display.duration', data=await self.bot.get_cog('TimeUtils').time_delta(case.duration,lang=l,year=False,form='temp'))
            # format date
            _date = await self.bot.get_cog('TimeUtils').date(case.date,lang=l,year=True,digital=True)
            # finish message
            _msg = _msg.format(G=guild,U=u,T=case.type,M=str(mod),R=case.reason,D=_date)

            emb = discord.Embed(title=title, description=_msg, color=self.bot.get_cog('Servers').embed_color, timestamp=ctx.message.created_at)
            emb.set_author(name=user, icon_url=user.display_avatar)
            await ctx.send(embed=emb)
        except Exception as err:
            await self.bot.get_cog("Errors").on_error(err,ctx)


    @case_main.command(name="remove", aliases=["clear", "delete"])
    @commands.guild_only()
    async def remove(self, ctx: MyContext, case:int):
        """Delete a case forever
        Warning: "Forever", it's very long. And no backups are done
        
        ..Example cases remove 42
        
        ..Doc moderator.html#remove-case"""
        if not self.bot.database_online:
            return await ctx.send(await self.bot._(ctx.guild.id,'cases.no_database'))
        try:
            c = ["ID="+str(case)]
            if not await self.bot.get_cog('Admin').check_if_admin(ctx.author):
                c.append("guild="+str(ctx.guild.id))
            cases = await self.get_case(columns=['ID','user'],criters=c)
        except Exception as err:
            await self.bot.get_cog("Errors").on_error(err,None)
            return
        if len(cases) != 1:
            await ctx.send(await self.bot._(ctx.guild.id,"cases.not-found"))
            return
        case = cases[0]
        await self.delete_case(case['ID'])
        await ctx.send(await self.bot._(ctx.guild.id,"cases.deleted", ID=case['ID']))
        user = ctx.bot.get_user(case['user'])
        if user is None:
            user = case['user']
        log = await self.bot._(ctx.guild.id,"logs.case-del",id=case['ID'],user=str(user))
        await self.bot.get_cog("Events").send_logs_per_server(ctx.guild,"case-edit",log,ctx.author)


def setup(bot):
    bot.add_cog(Cases(bot))
