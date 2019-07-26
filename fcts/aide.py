import discord, re, inspect
from discord.ext import commands

class HelpCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = "aide"
        bot.remove_command("help")
        self._mentions_transforms = {
    '@everyone': '@\u200beveryone',
    '@here': '@\u200bhere'}
        self._mention_pattern = re.compile('|'.join(self._mentions_transforms.keys()))
        self.help_color = 8311585
        try:
            self.translate = bot.cogs["LangCog"].tr
        except:
            pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.translate = self.bot.cogs["LangCog"].tr

    @commands.command(name="welcome",aliases=['bvn','bienvenue','leave'])
    @commands.cooldown(10,30,commands.BucketType.channel)
    async def bvn_help(self,ctx):
        """Help on setting up welcome / leave messages"""
        await ctx.send(await self.bot.cogs['LangCog'].tr(ctx.guild,'bvn','aide'))


    @commands.command(name="about",aliases=["botinfos","botinfo"])
    @commands.cooldown(7,30,commands.BucketType.user)
    async def infos(self,ctx):
        """Information about the bot"""
        msg = await self.bot.cogs['LangCog'].tr(ctx.guild,'infos','text-0')
        await ctx.send(msg.format(ctx.guild.me.mention if ctx.guild!=None else ctx.bot.user.mention))

    

    @commands.command(name="help")
    @commands.cooldown(1,5,commands.BucketType.user)
    async def help_cmd(self,ctx,*commands : str):
        """Shows this message
        Enable "Embed Links" permission for better rendering"""
        try:
            commands = [x.replace('@everyone','@​everyone').replace('@here','@​here') for x in commands]
            if len(commands) == 0:
                await self.help_command(ctx)
            else:
                await self.help_command(ctx,commands)
        except discord.errors.Forbidden:
            pass
        except Exception as e:
            await self.bot.cogs["ErrorsCog"].on_error(e,ctx)
            if len(commands) == 0:
                await self._default_help_command(ctx)
            else:
                await self._default_help_command(ctx,commands)


    async def help_command(self,ctx, commands=()):
        """Main command for the creation of the help message
If the bot can't send the new command format, it will try to send the old one."""
        async with ctx.channel.typing():
            destination = None
            if ctx.guild!=None:
                if await self.bot.cogs["ServerCog"].find_staff(ctx.guild,'help_in_dm') == 1:
                    destination = ctx.message.author.dm_channel
                    await self.bot.cogs["UtilitiesCog"].suppr(ctx.message)
                else:
                    destination = ctx.message.channel
            if destination == None:
                await ctx.message.author.create_dm()
                destination = ctx.message.author.dm_channel
        
            def repl(obj):
                return self._mentions_transforms.get(obj.group(0), '')

            if len(commands) == 0:  #aucune commande
                pages = await self.all_commands(ctx)
            elif len(commands) == 1:    #Nom de cog/commande unique ?
                name = self._mention_pattern.sub(repl, commands[0])
                command = None
                if name in self.bot.cogs:
                    cog = self.bot.cogs[name]
                    pages = await self.cog_commands(ctx,cog)
                else:
                    command = self.bot.all_commands.get(name)
                    if command is None:
                        await destination.send(str(await self.translate(ctx.channel,"aide","cmd-not-found")).format(name))
                        return
                    pages = await self.cmd_help(ctx,command)
            else:  #nom de sous-commande ?
                name = self._mention_pattern.sub(repl, commands[0])
                command = self.bot.all_commands.get(name)
                if command is None:
                    await destination.send(str(await self.translate(ctx.channel,"aide","cmd-not-found")).format(name))
                    return
                for key in commands[1:]:
                    try:
                        key = self._mention_pattern.sub(repl, key)
                        command = command.all_commands.get(key)
                        if command is None:
                            await destination.send(str(await self.translate(ctx.channel,"aide","subcmd-not-found")).format(key))
                            return
                    except AttributeError:
                        await destination.send(str(await self.translate(ctx.channel,"aide","no-subcmd")).format(command))
                        return
                pages = await self.cmd_help(ctx,command)

            me = destination.me if type(destination)==discord.DMChannel else destination.guild.me
            ft = await self.translate(ctx.channel,"aide","footer")
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix)==list:
                prefix = prefix[0]
        if destination.permissions_for(me).embed_links:
            for page in pages:
                embed = self.bot.cogs["EmbedCog"].Embed(desc=page,footer_text=ft.format(prefix)).update_timestamp().discord_embed()
                if ctx.guild != None:
                    embed.colour = ctx.guild.me.color if ctx.guild.me.color != discord.Colour(self.help_color).default() else discord.Colour(self.help_color)
                await destination.send(embed=embed)
        else:
            for page in pages:
                await destination.send(page)

    async def display_cmd(self,cmd):
        #return "**{}**\n\t\t*{}*".format(cmd.name,cmd.short_doc.strip()) if len(cmd.short_doc)>0 else "**{}**".format(cmd.name)
        return "• **{}**\t\t*{}*".format(cmd.name,cmd.short_doc.strip()) if len(cmd.short_doc)>0 else "• **{}**".format(cmd.name)

    def sort_by_name(self,cmd):
            return cmd.name

    async def all_commands(self,ctx:commands.Context):
        """Create pages for every bot command"""
        def category(cmd):
            cog = cmd.cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'
        
        cmds = sorted([c for c in self.bot.commands],key=self.sort_by_name)
        modhelp = ""
        otherhelp = ""
        for cmd in cmds:
            try:
                if cmd.hidden==True or cmd.enabled==False:
                    continue
                if (await cmd.can_run(ctx))==False:
                    continue
            except Exception as e:
                if not "discord.ext.commands.errors" in str(type(e)):
                    raise e
                else:
                    continue
            temp = await self.display_cmd(cmd)
            if cmd.cog_name in ['AdminCog','ServerCog','ModeratorCog','CasesCog','ReloadsCog','TimedCog']:
                modhelp += "\n"+temp
            else:
                otherhelp += "\n"+temp
        tr = await self.translate(ctx.channel,"aide","mods")
        if len(modhelp+otherhelp)<1900:
            return ["__• **{}**__\n{}".format(tr[0],modhelp) + "\n\n__• **{}**__\n{}".format(tr[1],otherhelp)]
        else:
            return ["__• **{}**__\n{}".format(tr[0],modhelp) , "\n\n__• **{}**__\n{}".format(tr[1],otherhelp)]

    async def cog_commands(self,ctx:commands.Context,cog:commands.Cog):
        """Create pages for every command of a cog"""
        description = inspect.getdoc(cog)
        page = ""
        form = "**{}**\n\n {} \n{}"
        pages = list()
        cog_name = cog.__class__.__name__
        if description == None:
            description = await self.translate(ctx.channel,"aide","no-desc-cog")
        for cmd in sorted([c for c in self.bot.commands],key=self.sort_by_name):
            try:
                if (await cmd.can_run(ctx))==False or cmd.hidden==True or cmd.enabled==False or cmd.cog_name != cog_name:
                    continue
            except Exception as e:
                if not "discord.ext.commands.errors" in str(type(e)):
                    raise e
                else:
                    continue
            text = await self.display_cmd(cmd)
            if len(page+text)>1900:
                pages.append(form.format(cog_name,description,page))
                page = text
            else:
                page += "\n"+text
        pages.append(form.format(cog_name,description,page))
        return pages
    
    async def cmd_help(self,ctx:commands.Context,cmd:commands.core.Command):
        """Create pages for a command explanation"""
        desc = cmd.description.strip() if cmd.description!=None else str(await self.translate(ctx.channel,"aide","no-desc-cmd"))
        if desc=='' and cmd.help!=None:
            desc = cmd.help.strip()
        # Prefix
        prefix = await self.bot.get_prefix(ctx.message)
        if type(prefix)==list:
            prefix = prefix[0]
        # Syntax
        syntax = cmd.qualified_name + "** " + cmd.signature
        # Subcommands
        if type(cmd)==commands.core.Group:
            syntax += " ..."
            subcmds = "__{}__".format(str(await self.translate(ctx.channel,"keywords","subcmds")).capitalize())
            sublist = list()
            for x in sorted(cmd.all_commands.values(),key=self.sort_by_name):
                try:
                    if x.hidden==False and x.enabled==True and x.name not in sublist and await x.can_run(ctx):
                        subcmds += "\n- {} {}".format(x.name,"*({})*".format(x.short_doc) if len(x.short_doc)>0 else "")
                        sublist.append(x.name)
                except Exception as e:
                    if not "discord.ext.commands.errors" in str(type(e)):
                        raise e
                    else:
                        continue
            if len(sublist)==0:
                subcmds = ""
        else:
            subcmds = ""
        # Aliases
        aliases = " - ".join(cmd.aliases)
        if len(aliases)>0:
            aliases = await self.translate(ctx.channel,"aide","aliases") + " " + aliases
        # Is enabled
        enabled = ""
        if not cmd.enabled:
            enabled = await self.translate(ctx.channel,"aide","not-enabled")
        # Checks
        checks = list()
        if len(cmd.checks)>0:
            maybe_coro = discord.utils.maybe_coroutine
            check_msgs = await self.translate(ctx.channel,'aide','check-desc')
            for c in cmd.checks:
                try:
                    if 'guild_only.<locals>.predicate' in str(c):
                        check_name = 'guild_only'
                    elif 'is_owner.<locals>.predicate' in str(c):
                        check_name = 'is_owner'
                    elif 'bot_has_permissions.<locals>.predicate' in str(c):
                        check_name = 'bot_has_permissions'
                    else:
                        check_name = c.__name__
                    if check_name in check_msgs.keys():
                        try:
                            pass_check = await maybe_coro(c,ctx)
                        except:
                            pass_check = False
                        if pass_check:
                            checks.append(":small_orange_diamond: "+check_msgs[check_name][0])
                        else:
                            pass
                            checks.append('❌ '+check_msgs[check_name][1])
                    else:
                        print(check_name,str(c))
                except Exception as e:
                    await self.bot.cogs["ErrorsCog"].on_error(e,ctx)
        checks = '\n'.join(checks)

        answer = f"**{prefix}{syntax}\n\n{desc}\n"
        if len(subcmds)>0:
            answer += "\n"+subcmds+"\n"
        if len(aliases)>0:
            answer += "\n"+aliases
        if len(enabled)>0:
            answer += enabled
        if len(checks)>0:
            answer += "\n"+checks
        return [answer]



    async def _default_help_command(self,ctx:commands.Context,command=None):
        truc = commands.DefaultHelpCommand()
        truc.context = ctx
        truc._command_impl = self.help_cmd
        # General help
        if command is None:
            mapping = truc.get_bot_mapping()
            return await truc.send_bot_help(mapping)
        # Check if it's a cog
        cog = self.bot.get_cog(" ".join(command))
        if cog is not None:
            return await truc.send_cog_help(cog)
        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        maybe_coro = discord.utils.maybe_coroutine
        keys = command
        cmd = self.bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(truc.command_not_found, truc.remove_mentions(keys[0]))
            return await truc.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(truc.subcommand_not_found, cmd, truc.remove_mentions(key))
                return await truc.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(truc.subcommand_not_found, cmd, truc.remove_mentions(key))
                    return await truc.send_error_message(string)
                cmd = found

        if isinstance(cmd, commands.Group):
            return await truc.send_group_help(cmd)
        else:
            return await truc.send_command_help(cmd)


def setup(bot):
    bot.add_cog(HelpCog(bot))
