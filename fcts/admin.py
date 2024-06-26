import asyncio
import copy
import datetime
import importlib
import io
import os
import sys
import textwrap
import time
import traceback
from collections import defaultdict
from contextlib import redirect_stdout
from typing import TYPE_CHECKING, Literal, Optional, Union

import discord
from asyncache import cached
from cachetools import TTLCache
from discord.ext import commands
from git import GitCommandError, Repo

from docs import conf
from libs.antiscam import update_unicode_map
from libs.antiscam.training_bayes import train_model
from libs.bot_classes import (PRIVATE_GUILD_ID, SUPPORT_GUILD_ID, Axobot,
                              MyContext)
from libs.checks import checks
from libs.enums import RankCardsFlag, UserFlag
from libs.formatutils import FormatUtils
from libs.rss.rss_general import feed_parse
from libs.views import ConfirmView

if TYPE_CHECKING:
    from fcts.antiscam import AntiScam


AvailableGitBranches = Literal["main", "develop"]


def cleanup_code(content: str):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    # remove `foo`
    return content.strip('` \n')

class Admin(commands.Cog):
    "All commands related to the internal administration of the bot, only accessible by whitelisted users"

    def __init__(self, bot: Axobot):
        self.bot = bot
        self.file = "admin"
        self.emergency_time = 15.0
        self.update: dict[Literal["fr", "en"], Optional[str]]
        if self.bot.beta:
            self.update = {"fr": "Foo", "en": "Bar"}
        else:
            self.update = {"fr": None, "en": None}
        try:
            self.utilities = self.bot.get_cog("Utilities")
        except KeyError:
            pass
        self._last_result = None
        self._upvote_emojis = ()
        self.god_mode = []

    @property
    def upvote_emojis(self):
        "Emojis used for the idea channel"
        if not self._upvote_emojis:
            self._upvote_emojis = (
                self.bot.get_emoji(938416027274993674),
                self.bot.get_emoji(938416007549186049)
            )
        return self._upvote_emojis

    @commands.Cog.listener()
    async def on_ready(self):
        self.utilities = self.bot.get_cog("Utilities")

    async def check_if_admin(self, ctx: MyContext):
        return await checks.is_bot_admin(ctx)

    async def check_if_god(self, ctx: Union[discord.User, discord.Guild, MyContext]):
        "Check if a user is in God mode for a given context"
        if isinstance(ctx, discord.User):
            return await checks.is_bot_admin(ctx)
        elif isinstance(ctx.guild, discord.Guild) and ctx.guild is not None:
            return await checks.is_bot_admin(ctx) and ctx.guild.id in self.god_mode
        else:
            return await checks.is_bot_admin(ctx)

    async def add_success_reaction(self, msg: discord.Message):
        "Add a check reaction to a message"
        if self.bot.zombie_mode:
            return
        try:
            emoji = self.bot.get_emoji(625426328275124296)
            if emoji:
                await msg.add_reaction(emoji)
            else:
                await msg.add_reaction('\u2705')
        except discord.Forbidden:
            await msg.channel.send(":ok:")
        except discord.DiscordException:
            pass

    @commands.hybrid_group(name="admin", hidden=True)
    @discord.app_commands.guilds(PRIVATE_GUILD_ID)
    @discord.app_commands.default_permissions(administrator=True)
    @commands.check(checks.is_bot_admin)
    async def admin_group(self, ctx: MyContext):
        """Commandes réservées aux administrateurs du bot"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("admin")

    @admin_group.command(name="send-msg")
    @commands.check(checks.is_bot_admin)
    async def send_msg(self, ctx: MyContext, user: discord.User, message: str):
        "Send a DM to any user the bot can reach"
        await ctx.defer()
        await user.send(message)
        await ctx.send(content="Done!")

    @admin_group.command(name="sync")
    @commands.check(checks.is_bot_admin)
    async def sync_app_commands(self, ctx: MyContext, scope: Literal["global", "staff-server", "public-server"]):
        "Sync app commands for either global or staff server scope"
        await ctx.defer()
        if scope == "global":
            if self.bot.beta:
                self.bot.tree.copy_global_to(guild=PRIVATE_GUILD_ID)
                cmds = await self.bot.tree.sync(guild=PRIVATE_GUILD_ID)
                txt = f"{len(cmds)} (global + local) app commands synced in staff server"
            else:
                cmds = await self.bot.tree.sync()
                txt = f"{len(cmds)} global app commands synced"
        elif scope == "staff-server":
            cmds = await self.bot.tree.sync(guild=PRIVATE_GUILD_ID)
            txt = f"{len(cmds)} app commands synced in staff server"
        elif scope == "public-server":
            cmds = await self.bot.tree.sync(guild=SUPPORT_GUILD_ID)
            txt = f"{len(cmds)} app commands synced in the support server"
        else:
            await ctx.send("Unknown scope")
            return
        self.bot.app_commands_list = None
        self.bot.log.info(txt)
        emb = discord.Embed(description=txt, color=discord.Color.blue())
        await self.bot.send_embed(emb)
        await ctx.send(txt + '!')

    @admin_group.command(name="god")
    @commands.check(checks.is_bot_admin)
    @commands.guild_only()
    async def enable_god_mode(self, ctx: MyContext, enable:bool=True):
        """Get full powaaaaaa

        Donne les pleins-pouvoirs aux admins du bot sur ce serveur (accès à toutes les commandes de modération)"""
        if enable:
            if ctx.guild.id not in self.god_mode:
                self.god_mode.append(ctx.guild.id)
                await ctx.send("<:nitro:548569774435598346> Mode superadmin activé sur ce serveur",delete_after=3)
            else:
                await ctx.send("Mode superadmin déjà activé sur ce serveur",delete_after=3)
        else:
            if ctx.guild.id in self.god_mode:
                self.god_mode.remove(ctx.guild.id)
                await ctx.send("Mode superadmin désactivé sur ce serveur",delete_after=3)
            else:
                await ctx.send("Ce mode n'est pas actif ici",delete_after=3)
        await ctx.message.delete(delay=0)

    @admin_group.command(name="faq")
    @commands.check(checks.is_bot_admin)
    async def send_faq(self, ctx: MyContext):
        "Update the FAQ channels from the private preparation channels"
        msg = await ctx.send("Suppression des salons...")
        guild = self.bot.get_guild(SUPPORT_GUILD_ID.id)
        destination_fr = guild.get_channel(508028818154323980)
        destination_en = guild.get_channel(541599345972346881)
        chan_fr = guild.get_channel(541228784456695818)
        chan_en = guild.get_channel(541599226623426590)
        role_fr = guild.get_role(541224634087899146)
        role_en = guild.get_role(537597687801839617)
        await destination_fr.set_permissions(role_fr, read_messages=False)
        await destination_en.set_permissions(role_en, read_messages=False)
        await destination_fr.purge()
        await destination_en.purge()
        await msg.edit(content="Envoi des messages...")
        async for message in chan_fr.history(limit=200, oldest_first=True):
            await destination_fr.send(message.content)
        async for message in chan_en.history(limit=200, oldest_first=True):
            await destination_en.send(message.content)
        await destination_fr.set_permissions(role_fr, read_messages=True)
        await destination_en.set_permissions(role_en, read_messages=True)
        await msg.edit(content="Terminé !")
        await self.add_success_reaction(ctx.message)


    @admin_group.command(name="update")
    @commands.check(checks.is_bot_admin)
    async def update_config(self, ctx: MyContext, send: bool=False):
        """Préparer/lancer un message de mise à jour
        Ajouter "send" en argument déclenche la procédure pour l'envoyer à tous les serveurs"""
        if send:
            await self.send_updates(ctx)
            return
        def check(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel
        msg = None
        for language in self.update:
            await ctx.send(f"Message en {language} ?")
            try:
                msg = await ctx.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send("Trop tard !")
            if msg.content.lower() in ["none", "annuler", "stop", "oups"]:
                return await ctx.send("Annulé !")
            self.update[language] = msg.content
        if msg:
            await self.add_success_reaction(msg)

    async def send_updates(self, ctx:MyContext):
        """Lance un message de mise à jour"""
        if self.bot.zombie_mode:
            return
        if None in self.update.values():
            return await ctx.send("Les textes ne sont pas complets !")
        text = "Vos messages contiennent"
        confirm_view = ConfirmView(
            self.bot, ctx.channel,
            validation=lambda inter: inter.user == ctx.author,
            ephemeral=False)
        await confirm_view.init()
        if max([len(x) for x in self.update.values()]) > 1900//len(self.update.keys()):
            for i, lang in enumerate(self.update.keys()):
                text += f"\n{lang}:```\n{self.update.get(lang)}\n```"
                await ctx.send(text, view=confirm_view if i == len(self.update)-1 else None)
                text = ''
        else:
            text += "\n"+"\n".join([f"{lang}:\n```\n{value}\n```" for lang, value in self.update.items()])
            await ctx.send(text, view=confirm_view)

        await confirm_view.wait()
        if confirm_view.value is None:
            await ctx.send("Trop long !")
            return
        if not confirm_view.value:
            return
        count = 0
        for guild in ctx.bot.guilds:
            channel: Optional[discord.TextChannel] = await ctx.bot.get_config(guild.id, "bot_news")
            if channel is None:
                # no channel configured
                continue
            lang: Optional[str] = await ctx.bot.get_config(guild.id, "language")
            if lang not in self.update:
                lang = "fr" if lang == "fr2" else "en"
            mentions_roles: list[discord.Role] = await self.bot.get_config(guild.id, "update_mentions") or []
            mentions = " ".join(x.mention for x in mentions_roles if x is not None)
            allowed_mentions = discord.AllowedMentions(everyone=False, roles=True)
            try:
                await channel.send(self.update[lang]+"\n\n"+mentions, allowed_mentions=allowed_mentions)
            except Exception as err:
                self.bot.dispatch("error", err, ctx)
            else:
                count += 1
            if guild.id == SUPPORT_GUILD_ID.id:
                fr_chan = guild.get_channel(494870602146906113)
                if fr_chan != channel:
                    # special treatment for the French channel in the bot support server
                    await fr_chan.send(self.update["fr"] + "\n\n<@&1092557246921179257>", allowed_mentions=allowed_mentions)
                    count += 1

        await ctx.send(f"Message envoyé dans {count} salons !")
        # add changelog in the database
        query = "INSERT INTO `changelogs` (`version`, `release_date`, `fr`, `en`, `beta`) VALUES (%(v)s, %(r)s, %(fr)s, %(en)s, %(b)s) ON DUPLICATE KEY UPDATE `fr` = %(fr)s, `en` = %(en)s;"
        args = {
            "v": conf.release, "r": ctx.message.created_at, "b": self.bot.beta,
            "fr": self.update["fr"], "en": self.update["en"]
        }
        async with self.bot.db_query(query, args):
            pass
        for language in self.update:
            self.update[language] = None


    @admin_group.group(name="cog")
    @commands.check(checks.is_bot_admin)
    async def cogs_group(self, ctx: MyContext):
        """Voir la liste de tout les cogs"""
        text = ""
        for cog_name, cog in self.bot.cogs.items():
            text += f"- {cog.file} ({cog_name}) \n"
        await ctx.send(text)

    @cogs_group.command(name="load")
    @commands.check(checks.is_bot_admin)
    async def add_cog(self, ctx: MyContext, name: str):
        """Ajouter un cog au bot"""
        try:
            await self.bot.load_extension('fcts.'+name)
            await ctx.send(f"Module '{name}' ajouté !")
            self.bot.log.info("Extension %s loaded", name)
        except Exception as err:
            await ctx.send(str(err))

    @cogs_group.command("unload")
    @commands.check(checks.is_bot_admin)
    async def rm_cog(self, ctx: MyContext, name: str):
        """Enlever un cog au bot"""
        try:
            await self.bot.unload_extension('fcts.'+name)
            await ctx.send(f"Module '{name}' désactivé !")
            self.bot.log.info("Extension %s unloaded", name)
        except Exception as err:
            await ctx.send(str(err))

    @cogs_group.command(name="reload")
    @commands.check(checks.is_bot_admin)
    async def reload_cog(self, ctx: MyContext, *, cog: str):
        """Recharge un module"""
        cogs = cog.split(" ")
        if len(cogs)==1 and cogs[0]=='all':
            cogs = sorted([x.file for x in self.bot.cogs.values()])
        reloaded_cogs = []
        for cog in cogs:
            if not cog.startswith("fcts."):
                fcog = "fcts."+cog
            else:
                fcog = cog
            try:
                await self.bot.reload_extension(fcog)
            except ModuleNotFoundError:
                await ctx.send(f"Cog {cog} can't be found")
            except commands.errors.ExtensionNotLoaded :
                try:
                    flib = importlib.import_module(cog)
                    importlib.reload(flib)
                except ModuleNotFoundError:
                    await ctx.send(f"Cog {cog} was never loaded")
                else:
                    self.bot.log.info("Lib %s reloaded", cog)
                    await ctx.send(f"Lib {cog} reloaded")
            except Exception as err:
                self.bot.dispatch("error", err, ctx)
                await ctx.send(f'**`ERROR:`** {type(err).__name__} - {err}')
            else:
                self.bot.log.info("Extension %s reloaded", cog)
                reloaded_cogs.append(cog)
            if cog == 'utilities':
                await self.bot.get_cog('Utilities').on_ready()
        if len(reloaded_cogs) > 0:
            await ctx.send(f"These cogs has successfully reloaded: {', '.join(reloaded_cogs)}")
            if info_cog := self.bot.get_cog("BotInfo"):
                await info_cog.refresh_code_lines_count()

    @reload_cog.autocomplete("cog")
    async def reload_cog_autocom(self, _: discord.Interaction, current: str):
        "Autocompletion for the cog name"
        if " " in current:
            fixed, current = current.rsplit(" ", maxsplit=1)
        else:
            fixed = None
        data: list[tuple[str, str]] = [
            (cog.qualified_name, cog.file if hasattr(cog, "file") else cog.qualified_name)
            for cog in self.bot.cogs.values()
        ]
        filtered = [
            cog for cog in data
            if current.lower() in cog[0].lower() or current.lower() in cog[1].lower()
        ]
        if len(filtered) == 0:
            filtered = [(current, current)]
        if fixed:
            filtered = [
                (fixed + " " + cog[0], fixed + " " + cog[1])
                for cog in filtered
            ]
        filtered.sort()
        return [
            discord.app_commands.Choice(name=cog[0], value=cog[1])
            for cog in filtered
        ][:25]

    @admin_group.command(name="shutdown")
    @commands.check(checks.is_bot_admin)
    async def shutdown(self, ctx: MyContext):
        """Eteint le bot"""
        msg = await ctx.send("Nettoyage de l'espace de travail...")
        await self.cleanup_workspace()
        await msg.edit(content="Bot en voie d'extinction")
        await self.bot.change_presence(status=discord.Status("offline"))
        self.bot.log.info("Closing Discord connection")
        await self.bot.close()

    async def cleanup_workspace(self):
        "Delete python cache files and close database connexions"
        for folder_name, _, filenames in os.walk('.'):
            if folder_name.startswith("./env"):
                continue
            for filename in filenames:
                if filename.endswith(".pyc"):
                    os.unlink(folder_name+'/'+filename)
            if folder_name.endswith("__pycache__"):
                os.rmdir(folder_name)
        if self.bot.database_online:
            self.bot.close_database_cnx()

    @admin_group.command(name="reboot")
    @commands.check(checks.is_bot_admin)
    async def restart_bot(self, ctx: MyContext):
        """Relance le bot"""
        await ctx.send(content="Redémarrage en cours...")
        await self.cleanup_workspace()
        self.bot.log.info("Redémarrage du bot")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @admin_group.command(name="pull")
    @commands.check(checks.is_bot_admin)
    async def git_pull(self, ctx: MyContext, branch: Optional[AvailableGitBranches]=None, install_requirements: bool=False):
        """Pull du code depuis le dépôt git"""
        msg = await ctx.send("Pull en cours...")
        repo = Repo(os.getcwd())
        assert not repo.bare
        if branch:
            try:
                repo.git.checkout(branch)
            except GitCommandError as err:
                self.bot.dispatch("command_error", ctx, err)
            else:
                msg = await msg.edit(content=msg.content+f"\nBranche {branch} correctement sélectionnée")
        origin = repo.remotes.origin
        origin.pull()
        msg = await msg.edit(content=msg.content + f"\nPull effectué avec succès sur la branche {repo.active_branch.name}")
        if install_requirements:
            await msg.edit(content=msg.content+"\nInstallation des dépendances...")
            os.system("pip install -qr requirements.txt")
            msg = await msg.edit(content=msg.content+"\nDépendances installées")

    @admin_group.command(name="membercounter")
    @commands.check(checks.is_bot_admin)
    async def membercounter(self, ctx: MyContext):
        """Recharge tout ces salons qui contiennent le nombre de membres, pour tout les serveurs"""
        if self.bot.database_online:
            i = 0
            for guild in self.bot.guilds:
                if await self.bot.get_cog("ServerConfig").update_memberchannel(guild):
                    i += 1
            await ctx.send(f"{i} salons mis à jours !")
        else:
            await ctx.send("Impossible de faire ceci, la base de donnée est inaccessible")

    @admin_group.command(name="config")
    @commands.check(checks.is_bot_admin)
    async def admin_sconfig_see(self, ctx: MyContext, guild: discord.Guild, option: Optional[str]=None):
        """Affiche les options d'un serveur"""
        if not ctx.bot.database_online:
            await ctx.send("Impossible d'afficher cette commande, la base de donnée est hors ligne :confused:")
            return
        if option is None:
            await self.bot.get_cog("ServerConfig").send_all_config(guild, ctx)
        else:
            await self.bot.get_cog("ServerConfig").send_specific_config(guild, ctx, option)

    @admin_group.group(name="database", aliases=["db"])
    @commands.check(checks.is_bot_admin)
    async def admin_db(self, _ctx: MyContext):
        "Commandes liées à la base de données"

    @admin_db.command(name="reload")
    @commands.check(checks.is_bot_admin)
    async def db_reload(self, ctx: MyContext):
        "Reconnecte le bot à la base de donnée"
        await ctx.defer()
        self.bot.cnx_axobot.close()
        self.bot.connect_database_axobot()
        self.bot.cnx_xp.close()
        self.bot.connect_database_xp()
        if self.bot.cnx_axobot is not None and self.bot.cnx_xp is not None:
            if ctx.interaction:
                await ctx.reply("Done!")
            else:
                await self.add_success_reaction(ctx.message)
            if xp := self.bot.get_cog("Xp"):
                await xp.reload_sus()
            if serverconfig := self.bot.get_cog("ServerConfig"):
                await serverconfig.clear_cache()

    @admin_db.command(name="biggest-tables")
    @commands.check(checks.is_bot_admin)
    async def db_biggest(self, ctx: MyContext, database: Optional[str] = None):
        "Affiche les tables les plus lourdes de la base de données"
        query = "SELECT table_name AS \"Table\", ROUND(((data_length + index_length) / 1024 / 1024), 2) AS \"Size (MB)\" FROM information_schema.TABLES"
        if database:
            query += f" WHERE table_schema = \"{database}\""
        query += " ORDER BY (data_length + index_length) DESC LIMIT 15"
        async with self.bot.db_query(query, astuple=True) as query_results:
            if len(query_results) == 0:
                await ctx.send("Invalid or empty database")
                return
            length = max(len(result[0]) for result in query_results)
            txt = "\n".join(f"{result[0]:>{length}}: {result[1]} MB" for result in query_results if result[1] is not None)
        await ctx.send("```yaml\n" + txt + "\n```")

    @cached(TTLCache(1, 3600))
    async def get_databases_names(self) -> list[str]:
        "Get every database names visible for the bot"
        query = "SHOW DATABASES"
        async with self.bot.db_query(query, astuple=True) as query_results:
            print(query_results)
            return [row[0] for row in query_results]

    @db_biggest.autocomplete("database")
    async def db_biggest_autocompl(self, _: discord.Interaction, current: str):
        "Autocompletion for the database name"
        databases = await self.get_databases_names()
        return [
            discord.app_commands.Choice(name=db, value=db)
            for db in databases if current.lower() in db.lower()
        ][:25]


    @admin_group.command(name="emergency", with_app_command=False)
    @commands.check(checks.is_bot_admin)
    async def emergency_cmd(self, ctx: MyContext):
        """Déclenche la procédure d'urgence
        A N'UTILISER QU'EN CAS DE BESOIN ABSOLU !
        Le bot quittera tout les serveurs après avoir envoyé un MP à chaque propriétaire"""
        await ctx.send(await self.emergency())

    async def emergency(self, level=100):
        "Trigger the emergency procedure: leave every servers and send a DM to every owner"
        if self.bot.zombie_mode:
            return
        timeout = round(self.emergency_time - level/100, 1)
        for user_id in checks.admins_id:
            try:
                user = self.bot.get_user(user_id)
                if user.dm_channel is None:
                    await user.create_dm()
                emoji = self.bot.emojis_manager.customs["red_warning"]
                msg = await user.dm_channel.send(
                    f"{emoji} La procédure d'urgence vient d'être activée. Si vous souhaitez l'annuler, veuillez \
                        cliquer sur la réaction ci-dessous dans les {timeout} secondes qui suivent l'envoi de ce message."
                )
                await msg.add_reaction('🛑')
            except Exception as err:
                self.bot.dispatch("error", err, "Emergency command")

        def check(_, user: discord.User):
            return user.id in checks.admins_id
        try:
            await self.bot.wait_for("reaction_add", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            owners = set()
            guilds_count = 0
            for guild in self.bot.guilds:
                if guild.id == 500648624204808193:
                    continue
                try:
                    if guild.owner not in owners:
                        await guild.owner.send(await self.bot._(guild,"admin.emergency"))
                        owners.add(guild.owner)
                    await guild.leave()
                    guilds_count +=1
                except discord.HTTPException:
                    continue
            chan: discord.TextChannel = await self.bot.get_channel(500674177548812306)
            emoji = self.bot.emojis_manager.customs["red_alert"]
            await chan.send(
                f"{emoji} Prodédure d'urgence déclenchée : {guilds_count} serveurs quittés - {len(owners)} propriétaires prévenus"
            )
            return f"{emoji}  {len(owners)} propriétaires de serveurs ont été prévenu ({guilds_count} serveurs)"
        for user_id in checks.admins_id:
            try:
                user = self.bot.get_user(user_id)
                await user.send("La procédure a été annulée !")
            except Exception as err:
                self.bot.dispatch("error", err, None)
        return "Qui a appuyé sur le bouton rouge ? :thinking:"

    @admin_group.command(name="ignore")
    @commands.check(checks.is_bot_admin)
    async def add_ignoring(self, ctx: MyContext, target_id: str):
        """Ajoute un serveur ou un utilisateur dans la liste des utilisateurs/serveurs ignorés"""
        int_target_id = int(target_id)
        utils = ctx.bot.get_cog("Utilities")
        if utils is None:
            await ctx.send("Unable to find Utilities cog")
            return
        config = await ctx.bot.get_cog("Utilities").get_bot_infos()
        if config is None:
            await ctx.send("The config dictionnary has not been initialized")
            return
        if not (target := self.bot.get_guild(int_target_id)):
            target = self.bot.get_user(int_target_id)
        if target is None:
            await ctx.send("Unable to find any guild or user with this ID")
            return
        if isinstance(target, discord.Guild):
            servs: list[str] = config["banned_guilds"].split(';')
            if str(target) in servs:
                servs.remove(str(target))
                await utils.edit_bot_infos(self.bot.user.id,[("banned_guilds",';'.join(servs))])
                await ctx.send(f"Le serveur {target.name} n'est plus blacklisté")
            else:
                servs.append(str(target.id))
                await utils.edit_bot_infos(self.bot.user.id,[("banned_guilds",';'.join(servs))])
                await ctx.send(f"Le serveur {target.name} a bien été blacklist")
        else:
            usrs: list[str] = config["banned_users"].split(';')
            if str(target.id) in usrs:
                usrs.remove(str(target.id))
                await utils.edit_bot_infos(self.bot.user.id,[("banned_users",';'.join(usrs))])
                await ctx.send(f"L'utilisateur {target} n'est plus blacklisté")
            else:
                usrs.append(str(target.id))
                await utils.edit_bot_infos(self.bot.user.id,[("banned_users",';'.join(usrs))])
                await ctx.send(f"L'utilisateur {target} a bien été blacklist")
        ctx.bot.get_cog("Utilities").config = None


    @admin_group.command(name="module")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.describe(enable="Should we enable or disable this module")
    async def enable_module(self, ctx: MyContext, module: Literal["xp", "rss", "stats", "files-count"], enable: bool):
        """Active ou désactive un module (xp/rss/alerts)
Cette option affecte tous les serveurs"""
        if module == "xp":
            self.bot.xp_enabled = enable
            if enable:
                await ctx.send("L'xp est mainenant activée")
            else:
                await ctx.send("L'xp est mainenant désactivée")
        elif module == "rss":
            self.bot.rss_enabled = enable
            if enable:
                await ctx.send("Les flux RSS sont mainenant activée")
            else:
                await ctx.send("Les flux RSS sont mainenant désactivée")
        elif module == "alerts":
            self.bot.stats_enabled = enable
            if enable:
                await ctx.send("Le système de log de statistiques est mainenant activé")
            else:
                await ctx.send("Le système de log de statistiques est mainenant désactivé")
        elif module == "files-count":
            self.bot.files_count_enabled = enable
            if enable:
                await ctx.send("Le comptage de fichiers ouverts est mainenant activé")
            else:
                await ctx.send("Le comptage de fichiers ouverts est mainenant désactivé")
        else:
            await ctx.send("Module introuvable")

    @admin_group.group(name="flag", aliases=["flags"])
    @commands.check(checks.is_bot_admin)
    async def admin_flag(self, ctx: MyContext):
        "Ajoute ou retire un attribut à un utilisateur"
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @admin_flag.command(name="list")
    @commands.check(checks.is_bot_admin)
    async def admin_flag_list(self, ctx: MyContext, user: discord.User):
        "Liste les flags d'un utilisateur"
        await ctx.defer()
        userflags: list[str] = sorted(await self.bot.get_cog("Users").get_userflags(user))
        if userflags:
            await ctx.send(f"Liste des flags de {user} : {', '.join(userflags)}")
        else:
            await ctx.send(f"{user} n'a aucun flag pour le moment")

    @admin_flag.command(name="add")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.choices(flag=[
        discord.app_commands.Choice(name=flag, value=flag)
        for flag in UserFlag.FLAGS.values()
    ])
    async def admin_flag_add(self, ctx: MyContext, user: discord.User, flag: str):
        """Ajoute un flag à un utilisateur

        Flags valides : support, contributor, premium, partner, translator, cookie"""
        await ctx.defer()
        userflags: list[str] = await self.bot.get_cog("Users").get_userflags(user)
        if flag in userflags:
            await ctx.send(f"L'utilisateur {user} a déjà ce flag !")
            return
        userflags.append(flag)
        await self.bot.get_cog("Users").db_edit_user_flags(user.id, UserFlag().flags_to_int(userflags))
        await ctx.send(f"L'utilisateur {user} a maintenant les flags {', '.join(userflags)}")

    @admin_flag.command(name="remove")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.choices(flag=[
        discord.app_commands.Choice(name=flag, value=flag)
        for flag in UserFlag.FLAGS.values()
    ])
    async def admin_flag_remove(self, ctx: MyContext, user: discord.User, flag: str):
        """Retire un flag à un utilisateur

        Flags valides : support, contributor, premium, partner, translator, cookie"""
        await ctx.defer()
        userflags: list[str] = await self.bot.get_cog("Users").get_userflags(user)
        if flag not in userflags:
            await ctx.send(f"L'utilisateur {user} n'a déjà pas ce flag")
            return
        userflags.remove(flag)
        await self.bot.get_cog("Users").db_edit_user_flags(user.id, UserFlag().flags_to_int(userflags))
        if userflags:
            await ctx.send(f"L'utilisateur {user} a maintenant les flags {', '.join(userflags)}")
        else:
            await ctx.send(f"L'utilisateur {user} n'a plus aucun flag")

    @admin_group.group(name="rankcard")
    @commands.check(checks.is_bot_admin)
    async def admin_rankcard(self, ctx: MyContext):
        "Ajoute ou retire une carte d'xp à un utilisateur"
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @admin_rankcard.command(name="list")
    @commands.check(checks.is_bot_admin)
    async def admin_card_list(self, ctx: MyContext, user: discord.User):
        "Liste les cartes d'xp d'un utilisateur"
        await ctx.defer()
        rankcards: list[str] = sorted(await self.bot.get_cog("Users").get_rankcards(user))
        if rankcards:
            await ctx.send(f"Liste des cartes d'xp de {user} : {', '.join(rankcards)}")
        else:
            await ctx.send(f"{user} n'a aucune carte d'xp spéciale pour le moment")

    @admin_rankcard.command(name="add")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.choices(rankcard=[
        discord.app_commands.Choice(name=rankcard, value=rankcard)
        for rankcard in RankCardsFlag.FLAGS.values()
    ])
    async def admin_card_add(self, ctx: MyContext, user: discord.User, rankcard: str):
        """Autorise une carte d'xp à un utilisateur"""
        await ctx.defer()
        rankcards: list[str] = await self.bot.get_cog("Users").get_rankcards(user)
        if rankcard in rankcards:
            await ctx.send(f"L'utilisateur {user} a déjà cette carte d'xp !")
            return
        rankcards.append(rankcard)
        await self.bot.get_cog("Users").set_rankcard(user, rankcard, add=True)
        await ctx.send(f"L'utilisateur {user} a maintenant les cartes d'xp {', '.join(rankcards)}")

    @admin_rankcard.command(name="remove")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.choices(rankcard=[
        discord.app_commands.Choice(name=rankcard, value=rankcard)
        for rankcard in RankCardsFlag.FLAGS.values()
    ])
    async def admin_card_remove(self, ctx: MyContext, user: discord.User, rankcard: str):
        """Retire une carte d'xp à un utilisateur"""
        await ctx.defer()
        rankcards: list[str] = await self.bot.get_cog("Users").get_rankcards(user)
        if rankcard not in rankcards:
            await ctx.send(f"L'utilisateur {user} n'a déjà pas cette carte d'xp")
            return
        rankcards.remove(rankcard)
        await self.bot.get_cog("Users").set_rankcard(user, rankcard, add=False)
        if rankcards:
            await ctx.send(f"L'utilisateur {user} a maintenant les cartes d'xp {', '.join(rankcards)}")
        else:
            await ctx.send(f"L'utilisateur {user} n'a plus aucune catre d'xp spéciale")


    @admin_group.group(name="server")
    @commands.check(checks.is_bot_admin)
    async def main_botserv(self, ctx: MyContext):
        """Quelques commandes liées au serveur officiel"""
        if ctx.invoked_subcommand is None or ctx.invoked_subcommand==self.main_botserv: # pylint: disable=comparison-with-callable
            text = "Liste des commandes disponibles :"
            for cmd in ctx.command.commands:
                cmd: commands.Command
                text += f"\n- {cmd.name} *({cmd.help})*"
            await ctx.send(text)

    @main_botserv.command(name="owner_reload")
    @commands.check(checks.is_bot_admin)
    async def owner_reload(self, ctx: MyContext):
        """Ajoute le rôle Owner à tout les membres possédant un serveur avec le bot
        Il est nécessaire d'avoir au moins 10 membres pour que le rôle soit ajouté"""
        server = self.bot.get_guild(SUPPORT_GUILD_ID.id)
        if server is None:
            await ctx.send("Serveur de support introuvable")
            return
        role = server.get_role(486905171738361876)
        if role is None:
            await ctx.send("Rôle Owners introuvable")
            return
        await ctx.defer()
        owner_list: list[int] = []
        for guild in self.bot.guilds:
            if len(guild.members)>9:
                if guild.owner_id is None:
                    await ctx.send(f"Oops, askip le propriétaire de {guild.id} n'existe pas ._.")
                    continue
                owner_list.append(guild.owner_id)
        text: list[str] = []
        for member in server.members:
            if member.id in owner_list and role not in member.roles:
                text.append("Rôle ajouté à " + (member.global_name or member.name))
                await member.add_roles(role,reason="This user support me")
            elif (member.id not in owner_list) and role in member.roles:
                text.append("Rôle supprimé à " + (member.global_name or member.name))
                await member.remove_roles(role,reason="This user doesn't support me anymore")
        if text:
            await ctx.send("\n".join(text))
        else:
            await ctx.send("Aucun changement n'a été effectué")

    async def _get_ideas_list(self, channel: discord.TextChannel):
        "Get ideas from the ideas channel"
        now = self.bot.utcnow()
        liste: list[tuple[int, datetime.timedelta, str, int, int]] = []
        async for msg in channel.history(limit=500):
            if len(msg.reactions) > 0:
                upvotes = 0
                downvotes = 0
                for reaction in msg.reactions:
                    users = [x async for x in reaction.users() if not x.bot]
                    if reaction.emoji in ('👍', self.upvote_emojis[0]):
                        upvotes = len(users)
                    if reaction.emoji in ('👎', self.upvote_emojis[1]):
                        downvotes = len(users)
                duration = now-msg.created_at
                if len(msg.embeds) > 0:
                    liste.append((upvotes-downvotes,duration,msg.embeds[0].fields[0].value,upvotes,downvotes))
                else:
                    liste.append((upvotes-downvotes,duration,msg.content,upvotes,downvotes))
        liste.sort(reverse=True)
        return liste

    @main_botserv.command(name="best_ideas")
    @commands.check(checks.is_bot_admin)
    async def best_ideas(self, ctx: MyContext, number: int=10):
        """Donne la liste des 10 meilleures idées"""
        bot_msg = await ctx.send("Chargement des idées...")
        server = self.bot.get_guild(SUPPORT_GUILD_ID.id if not self.bot.beta else PRIVATE_GUILD_ID.id)
        if server is None:
            return await ctx.send("Serveur introuvable")
        channel = server.get_channel(488769306524385301 if not self.bot.beta else 929864644678549534)
        if channel is None:
            return await ctx.send("Salon introuvable")
        ideas_list = await self._get_ideas_list(channel)
        count = len(ideas_list)
        ideas_list = ideas_list[:number]
        title = f"Liste des {len(ideas_list)} meilleures idées (sur {count}) :"
        text = ""
        if ctx.guild is not None:
            color = ctx.guild.me.color
        else:
            color = discord.Colour(8311585)
        for (_, _, content, upvotes, downvotes) in ideas_list:
            text += f"\n**[{upvotes} - {downvotes}]**  {content}"
        try:
            if ctx.can_send_embed:
                emb = discord.Embed(title=title, description=text, color=color, timestamp=self.bot.utcnow())
                return await bot_msg.edit(content=None,embed=emb)
            await bot_msg.edit(content=title+text)
        except discord.HTTPException:
            await ctx.send("Le message est trop long pour être envoyé !")

    @admin_group.command(name="activity")
    @commands.check(checks.is_bot_admin)
    @discord.app_commands.rename(activity_type="type")
    async def change_activity(self, ctx: MyContext, activity_type: Literal["play", "watch", "listen", "stream"], *, text: str):
        """Change l'activité du bot (play, watch, listen, stream)"""
        if activity_type == "play":
            new_activity = discord.Game(name=text)
        elif activity_type == "watch":
            new_activity = discord.Activity(type=discord.ActivityType.watching, name=text, timestamps={"start":time.time()})
        elif activity_type == "listen":
            new_activity = discord.Activity(type=discord.ActivityType.listening, name=text, timestamps={"start":time.time()})
        elif activity_type == "stream":
            new_activity = discord.Activity(type=discord.ActivityType.streaming, name=text, timestamps={"start":time.time()})
        else:
            await ctx.send("Sélectionnez *play*, *watch*, *listen* ou *stream* suivi du nom")
            return
        await self.bot.change_presence(activity=new_activity)
        if not ctx.interaction:
            await ctx.message.delete()

    @admin_group.command(name="test-rss-url")
    @commands.check(checks.is_bot_admin)
    async def test_rss_url(self, ctx: MyContext, url: str, *, arguments=None):
        """Teste une url rss"""
        await ctx.defer()
        url = url.replace('<','').replace('>','')
        feed = await feed_parse(url, 8)
        if feed is None:
            await ctx.send("Got a timeout")
            return
        txt = f"feeds.keys()\n```py\n{feed.keys()}\n```"
        if "bozo_exception" in feed:
            txt += f"\nException ({feed['bozo']}): {feed['bozo_exception']}"
            return await ctx.send(txt)
        if len(str(feed.feed)) < 1400-len(txt):
            txt += f"feeds.feed\n```py\n{feed.feed}\n```"
        else:
            txt += f"feeds.feed.keys()\n```py\n{feed.feed.keys()}\n```"
        if len(feed.entries) > 0:
            if len(str(feed.entries[0])) < 1950-len(txt):
                txt += f"feeds.entries[0]\n```py\n{feed.entries[0]}\n```"
            else:
                txt += f"feeds.entries[0].keys()\n```py\n{feed.entries[0].keys()}\n```"
        if arguments is not None and "feeds" in arguments and "ctx" not in arguments:
            txt += f"\n{arguments}\n```py\n{eval(arguments)}\n```" # pylint: disable=eval-used
        try:
            await ctx.send(txt)
        except discord.DiscordException as err:
            print("[rss_test] Error:",err)
            await ctx.send("`Error`: "+str(err))
            print(txt)
        if arguments is None:
            ok_ = "<:greencheck:513105826555363348>"
            notok_ = "<:redcheck:513105827817717762>"
            nothing_ = "<:_nothing:446782476375949323>"
            txt = ["**__Analyse :__**", '']
            if feed.status >= 400:
                txt.append(f"{notok_} Status code: {feed.status}")
            if not url.startswith("https://"):
                txt.append(f"{notok_} Not https")
            youtube_rss = self.bot.get_cog("Rss").youtube_rss
            if "link" not in feed.feed:
                txt.append(notok_+" No 'link' var")
            elif yt_account := await youtube_rss.get_channel_by_any_url(feed.feed["link"]):
                txt.append("<:youtube:447459436982960143>  " + yt_account)
            elif "link" in feed.feed.keys():
                txt.append(f":newspaper:  <{feed.feed['link']}>")
            else:
                txt.append(":newspaper:  No 'link' var")
            txt.append(f"Entrées : {len(feed.entries)}")
            if len(feed.entries) > 0:
                entry = feed.entries[0]
                if "title" in entry:
                    txt.append(nothing_+ok_+" title: ")
                    if len(entry["title"].split('\n')) > 1:
                        txt[-1] += entry["title"].split('\n')[0]+"..."
                    else:
                        txt[-1] += entry["title"]
                else:
                    txt.append(nothing_+notok_+' title')
                if "published_parsed" in entry:
                    txt.append(nothing_+ok_+" published_parsed")
                elif "published" in entry:
                    txt.append(nothing_+ok_+" published")
                elif "updated_parsed" in entry:
                    txt.append(nothing_+ok_+" updated_parsed")
                else:
                    txt.append(nothing_+notok_+' date')
                if "author" in entry:
                    txt.append(nothing_+ok_+" author: "+entry["author"])
                else:
                    txt.append(nothing_+notok_+' author')
                if "content" in entry:
                    txt.append(nothing_+ok_+" content")
                elif "summary" in entry:
                    txt.append(nothing_+ok_+" summary (as main content)")
                else:
                    txt.append(nothing_+notok_+' content')
                if "content" in entry and "summary" in entry:
                    txt.append(nothing_+ok_+" summary")
                else:
                    txt.append(nothing_+notok_+' summary (as description)')
            await ctx.send("\n".join(txt))

    @admin_group.group(name="antiscam")
    @commands.check(checks.is_bot_admin)
    async def main_antiscam(self, ctx: MyContext):
        "Gère le modèle d'anti-scam"
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @main_antiscam.command(name="fetch-unicode")
    @commands.check(checks.is_bot_admin)
    async def antiscam_fetch_unicode(self, ctx: MyContext):
        "Récupérer la table unicode des caractères confusables"
        if not self.bot.beta:
            await ctx.send("Not usable in production!", ephemeral=True)
            return
        await ctx.defer()
        await update_unicode_map()
        await ctx.send("Done!")

    @main_antiscam.command(name="update-table")
    @commands.check(checks.is_bot_admin)
    async def antiscam_update_table(self, ctx: MyContext):
        "Met à jour la table des messages enregistrés"
        if (antiscam := self.bot.get_cog("AntiScam")) is None:
            await ctx.send("AntiScam cog not found!")
            return
        antiscam: "AntiScam"
        await ctx.defer()
        msg = await ctx.send("Hold on, I'm on it...")
        counter = await antiscam.db_update_messages(antiscam.table)
        await msg.edit(content=f"{counter} messages updated!")

    @main_antiscam.command(name="train")
    @commands.check(checks.is_bot_admin)
    async def antiscam_train_model(self, ctx: MyContext):
        "Ré-entraine le modèle d'anti-scam (ACTION DESTUCTRICE)"
        if not self.bot.beta:
            await ctx.send("Not usable in production!", ephemeral=True)
            return
        if (antiscam := self.bot.get_cog("AntiScam")) is None:
            await ctx.send("AntiScam cog not found!")
            return
        antiscam: "AntiScam"
        await ctx.defer()
        msg = await ctx.send("Hold on, this may take a while...")
        start = time.time()
        data = await antiscam.get_messages_list()
        model = await train_model(data)
        acc = model.get_external_accuracy(data)
        elapsed_time = await FormatUtils.time_delta(time.time() - start, lang="en")
        txt = f"New model has been generated in {elapsed_time}!\nAccuracy of {acc:.3f}"
        current_acc = antiscam.agent.model.get_external_accuracy(data)
        if acc > current_acc:
            antiscam.agent.save_model(model)
            txt += f"\n✅ This model is better than the current one ({current_acc:.3f}), replacing it!"
        else:
            txt += f"\n❌ This model is not better than the current one ({current_acc:.3f})"
        await msg.edit(content=txt)
        self.bot.log.info(txt)

    @main_antiscam.command(name="list-words")
    @commands.check(checks.is_bot_admin)
    async def antiscam_list_words(self, ctx: MyContext,
                                  words_category: Literal["spam-words", "safe-words", "all"]="all",
                                  words_count: commands.Range[int, 1, 100]=15
                                  ):
        "Liste les mots les plus importants dans la détection de scam"
        if (antiscam := self.bot.get_cog("AntiScam")) is None:
            await ctx.send("AntiScam cog not found!")
            return
        antiscam: "AntiScam"
        await ctx.defer()
        attr_counts: dict[str, int] = defaultdict(int)
        for tree in antiscam.agent.model.trees:
            for word, count in tree.attr_counts["spam"].items():
                attr_counts[word] += count
            for word, count in tree.attr_counts["ham"].items():
                attr_counts[word] -= count
        sorted_words = sorted(attr_counts.items(), key=lambda x: x[1], reverse=True)
        result: list[str] = []
        if words_category in {"spam-words", "all"}:
            result.extend(f"{word} ({score})" for word, score in sorted_words[:words_count])
        if words_category == "all":
            result.append("...")
        if words_category in {"safe-words", "all"}:
            result.extend(f"{word} ({score})" for word, score in sorted_words[-words_count:])
        await ctx.send("\n".join(result))


    @commands.command(name="eval", hidden=True)
    @commands.check(checks.is_bot_admin)
    async def _eval(self, ctx: MyContext, *, body: str):
        """Evaluates a code
        Credits: Rapptz (https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py)"""
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result
        }
        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()
        try:
            to_compile = f"async def func():\n{textwrap.indent(body, '  ')}"
        except Exception as err:
            self.bot.dispatch("error", err, ctx)
            return
        try:
            exec(to_compile, env) # pylint: disable=exec-used
        except Exception as err:
            return await ctx.send(f"```py\n{err.__class__.__name__}: {err}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as err:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()[:1990]}\n```")
        else:
            value = stdout.getvalue()
            await self.add_success_reaction(ctx.message)

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")

    @admin_group.command(name="execute")
    @commands.check(checks.is_bot_admin)
    async def sudo(self, ctx: MyContext, who: Union[discord.Member, discord.User], *, command: str):
        """Exécute une commande en tant qu'un autre utilisateur
        Credits: Rapptz (https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py)"""
        await ctx.defer()
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)
        await ctx.send(f"Command executed as {who} with success")

    @admin_group.command(name="rss-loop")
    @commands.check(checks.is_bot_admin)
    async def rss_loop(self, ctx: MyContext, new_state: Literal["start", "stop", "run-once"]):
        """Start or stop the RSS refresh loop"""
        if not ctx.bot.database_online:
            return await ctx.send("Lol, t'as oublié que la base de donnée était hors ligne ?")
        cog = self.bot.get_cog("Rss")
        if cog is None:
            return await ctx.send("Le module RSS n'est pas chargé !")
        if new_state == "start":
            try:
                cog.rss_loop.start() # pylint: disable=no-member
            except RuntimeError:
                await ctx.send("La boucle est déjà en cours !")
            else:
                await ctx.send("Boucle rss relancée !")
        elif new_state == "stop":
            cog.rss_loop.cancel() # pylint: disable=no-member
            cog.log.info(" RSS loop force-stopped by an admin")
            await ctx.send("Boucle rss arrêtée de force !")
        elif new_state == "run-once":
            if cog.loop_processing:
                await ctx.send("Une boucle rss est déjà en cours !")
            else:
                await ctx.send("Et hop ! Une itération de la boucle en cours !")
                cog.log.info(" RSS loop forced by an admin")
                await cog.refresh_feeds()

    @admin_group.group(name="bug")
    @commands.check(checks.is_bot_admin)
    async def main_bug(self, ctx: MyContext):
        """Gère la liste des bugs"""

    @main_bug.command(name="add")
    async def bug_add(self, ctx: MyContext, french: str, english: str):
        """Ajoute un bug à la liste"""
        channel = ctx.bot.get_channel(929864644678549534) if self.bot.beta else ctx.bot.get_channel(488769283673948175)
        if channel is None:
            return await ctx.send("Salon 488769283673948175 introuvable")
        emb = discord.Embed(title="New bug", timestamp=self.bot.utcnow(), color=13632027)
        emb.add_field(name="Français", value=french, inline=False)
        emb.add_field(name="English", value=english, inline=False)
        await channel.send(embed=emb)
        await self.add_success_reaction(ctx.message)

    @main_bug.command(name="fix")
    async def bug_fix(self, ctx: MyContext, msg_id: str, fixed: bool=True):
        """Marque un bug comme étant fixé"""
        chan = ctx.bot.get_channel(929864644678549534) if self.bot.beta else ctx.bot.get_channel(488769283673948175)
        if chan is None:
            return await ctx.send("Salon introuvable")
        try: # try to fetch message from the bugs channel
            msg = await chan.fetch_message(msg_id)
        except discord.DiscordException as err:
            return await ctx.send(f"`Error:` {err}")
        if len(msg.embeds) != 1:
            return await ctx.send("Nombre d'embeds invalide")
        emb = msg.embeds[0]
        if fixed: # if the bug should be marked as fixed
            emb.color = discord.Color(10146593)
            emb.title = "New bug [fixed soon]"
        else:
            emb.color = discord.Color(13632027)
            emb.title = "New bug"
        await msg.edit(embed=emb)
        await self.add_success_reaction(ctx.message)

    @admin_group.group(name="idea")
    @commands.check(checks.is_bot_admin)
    async def main_idea(self, ctx: MyContext):
        """Ajouter une idée dans le salon des idées, en français et anglais"""

    @main_idea.command(name="add")
    async def idea_add(self, ctx: MyContext, french: str, english: str):
        """Ajoute une idée à la liste"""
        channel = ctx.bot.get_channel(929864644678549534) if self.bot.beta else ctx.bot.get_channel(488769306524385301)
        if channel is None:
            return await ctx.send("Salon introuvable")
        emb = discord.Embed(color=16106019, timestamp=self.bot.utcnow())
        emb.add_field(name="Français", value=french, inline=False)
        emb.add_field(name="English", value=english, inline=False)
        msg = await channel.send(embed=emb)
        for emoji in self.upvote_emojis:
            await msg.add_reaction(emoji)
        await self.add_success_reaction(ctx.message)

    @main_idea.command(name="valid")
    async def idea_valid(self, ctx: MyContext, msg_id: str, implemented: bool=True):
        """Marque une idée comme étant ajoutée à la prochaine MàJ"""
        chan = ctx.bot.get_channel(929864644678549534) if self.bot.beta else ctx.bot.get_channel(488769306524385301)
        if chan is None:
            return await ctx.send("Salon introuvable")
        try: # try to fetch message from ideas channel
            msg = await chan.fetch_message(msg_id)
        except discord.DiscordException as err:
            # something went wrong (invalid message ID, or any other Discord API error)
            return await ctx.send(f"`Error:` {err}")
        if len(msg.embeds) != 1:
            return await ctx.send("Nombre d'embeds invalide")
        emb = msg.embeds[0]
        if implemented: # if the idea should be marked as soon-released
            emb.color = discord.Color(10146593)
        else:
            emb.color = discord.Color(16106019)
        await msg.edit(embed=emb)
        await self.add_success_reaction(ctx.message)

async def setup(bot):
    await bot.add_cog(Admin(bot))
