from __future__ import annotations

import asyncio
import datetime
import time
from typing import TYPE_CHECKING, Any, Optional, Union, Literal

import async_timeout
import discord
import feedparser
from aiohttp import ClientSession, client_exceptions
from feedparser.util import FeedParserDict

FeedType = Literal['tw', 'yt', 'twitch', 'reddit', 'mc', 'deviant', 'web']

if TYPE_CHECKING:
    from libs.emojis_manager import EmojisManager
    from libs.classes import Zbot

async def feed_parse(bot: Zbot, url: str, timeout: int, session: ClientSession = None) -> Optional[feedparser.FeedParserDict]:
    """Asynchronous parsing using cool methods"""
    # if session is provided, we have to not close it
    _session = session or ClientSession()
    try:
        async with async_timeout.timeout(timeout) as timeout_manager:
            async with _session.get(url) as response:
                html = await response.text()
                headers = response.raw_headers
    except (UnicodeDecodeError, client_exceptions.ClientError):
        if session is None:
            await _session.close()
        return FeedParserDict(entries=[])
    except asyncio.exceptions.TimeoutError:
        if session is None:
            await _session.close()
        return None
    except Exception as err:
        if session is None:
            await _session.close()
        raise err
    if session is None:
        await _session.close()
    if timeout_manager.expired:
        # request was cancelled by timeout
        bot.log.info("[RSS] feed_parse got a timeout")
        return None
    headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in headers}
    return feedparser.parse(html, response_headers=headers)

class RssMessage:
    "Represents a message ready to be sent"

    def __init__(self,
                 bot: Zbot,
                 feed: "FeedObject",
                 url: str,
                 title: str,
                 date: Union[datetime.datetime, time.struct_time,
                             str] = datetime.datetime.now(),
                 author: Optional[str] = None,
                 channel: Optional[str] = None,
                 retweeted_from: Optional[str] = None,
                 image: Optional[str] = None
                 ):
        self.bot = bot
        self.feed = feed
        self.url = url
        self.title = title if len(title) < 300 else title[:299]+'…'
        self.image = image
        if isinstance(date, datetime.datetime):
            self.date = date
        elif isinstance(date, time.struct_time):
            self.date = datetime.datetime(*date[:6]).replace(tzinfo=datetime.timezone.utc)
        elif isinstance(date, str):
            self.date = date
        else:
            self.date = None
        self.author = author if author is None or len(author) < 100 else author[:99]+'…'
        self.logo = feed.get_emoji(bot.emojis_manager)
        if isinstance(self.logo, discord.Emoji):
            self.logo = str(self.logo)
        self.channel = channel
        self.rt_from = retweeted_from
        if self.author is None:
            self.author = channel
        # lazy loading
        self.mentions: list[str] = []
        self.embed_data: dict[str, Any] = {}

    def fill_embed_data(self):
        "Fill any interesting value to send in an embed"
        self.embed_data = {
            'color': discord.Colour(0).default(),
            'footer': '',
            'title': None
        }
        if title := self.feed.embed_title:
            self.embed_data['title'] = title[:256]
        if footer := self.feed.embed_footer:
            self.embed_data['footer'] = footer[:2048]
        if color := self.feed.embed_color:
            self.embed_data['color'] = color

    async def fill_mention(self, guild: discord.Guild):
        "Fill the mentions attribute with required roles mentions"
        if len(self.feed.role_ids) == 0:
            self.mentions = ""
        else:
            roles = []
            for item in self.feed.role_ids:
                if len(item) == 0:
                    continue
                role = discord.utils.get(guild.roles, id=int(item))
                if role is not None:
                    roles.append(role.mention)
                else:
                    roles.append(item)
            self.mentions = roles
        return self

    async def create_msg(self, msg_format: str=None):
        "Create a message ready to be sent, either in string or in embed"
        if msg_format is None:
            msg_format = self.feed.structure
        if isinstance(self.date, datetime.datetime):
            date = f"<t:{self.date.timestamp():.0f}>"
        else:
            date = self.date
        msg_format = msg_format.replace('\\n','\n')
        if self.rt_from is not None:
            self.author = f"{self.author} (retweeted from @{self.rt_from})"
        _channel = discord.utils.escape_markdown(self.channel) if self.channel else "?"
        _author = discord.utils.escape_markdown(self.author) if self.author else "?"
        text = msg_format.format_map(self.bot.SafeDict(channel=_channel, title=self.title, date=date, url=self.url,
                                                    link=self.url, mentions=", ".join(self.mentions), logo=self.logo,
                                                    author=_author))
        if not self.feed.use_embed:
            return text
        emb = discord.Embed(description=text, color=self.embed_data['color'])
        emb.set_footer(text=self.embed_data['footer'])
        if self.embed_data['title'] is None:
            if self.feed.type != 'tw':
                emb.title = self.title
            else:
                emb.title = self.author
        else:
            emb.title = self.embed_data['title']
        emb.add_field(name='URL', value=self.url)
        if self.image is not None:
            emb.set_thumbnail(url=self.image)
        return emb

class FeedSelectView(discord.ui.View):
    "Used to ask to select an rss feed"
    def __init__(self, feeds: list[dict[str, Any]], max_values: int, placeholder: str):
        super().__init__()
        options = self.build_options(feeds)
        self.select = discord.ui.Select(placeholder=placeholder, min_values=1, max_values=max_values, options=options)
        self.select.callback = self.callback
        self.add_item(self.select)
        self.feeds: list[int] = None

    def build_options(self, feeds: list[dict[str, Any]]) -> list[discord.SelectOption]:
        "Build the options list for Discord"
        res = []
        for feed in feeds:
            if len(feed['name']) > 90:
                feed['name'] = feed['name'][:89] + '…'
            label = f"{feed['tr_type']} - {feed['name']}"
            desc = f"{feed['tr_channel']} - Last post: {feed['tr_lastpost']}"
            res.append(discord.SelectOption(value=feed['id'], label=label, description=desc, emoji=feed['emoji']))
        return res

    async def callback(self, interaction: discord.Interaction):
        "Called when the dropdown menu has been validated by the user"
        self.feeds = self.select.values
        await interaction.response.defer()
        self.select.disabled = True
        await interaction.edit_original_message(view=self)
        self.stop()

class FeedObject:
    "A feed record from the database"
    def __init__(self, from_dict: dict):
        self.feed_id: int = from_dict['ID']
        self.added_at: datetime.datetime = from_dict['added_at']
        self.structure: str = from_dict['structure']
        self.guild_id: int = from_dict['guild']
        self.channel_id: int = from_dict['channel']
        self.type: FeedType = from_dict['type']
        self.link: str = from_dict['link']
        self.date: datetime.datetime = from_dict['date']
        self.role_ids: list[str] = [role for role in from_dict['roles'].split(';') if role.isnumeric()]
        self.use_embed: bool = from_dict['use_embed']
        self.embed_footer: str = from_dict['embed_footer']
        self.embed_title: str = from_dict['embed_title']
        self.embed_color: int = from_dict['embed_color']
        self.last_update: Optional[datetime.datetime] = from_dict['last_update']
        self.recent_errors: int = from_dict['recent_errors']

    @classmethod
    def unrecorded(cls, from_type: str, guild_id: Optional[int]=None, channel_id: Optional[int]=None):
        return cls({
            "ID": None,
            "added_at": None,
            "structure": None,
            "guild": guild_id,
            "channel": channel_id,
            "type": from_type,
            "link": None,
            "date": None,
            "roles": "",
            "use_embed": False,
            "embed_footer": "",
            "embed_title": "",
            "embed_color": "",
            "last_update": None,
            "recent_errors": 0
        })

    def get_emoji(self, cog: "EmojisManager") -> Union[discord.Emoji, str]:
        "Get the representative emoji of a feed type"
        if self.type == 'tw':
            return cog.get_emoji('twitter')
        elif self.type == 'yt':
            return cog.get_emoji('youtube')
        elif self.type == 'twitch':
            return cog.get_emoji('twitch')
        elif self.type == 'reddit':
            return cog.get_emoji('reddit')
        elif self.type == 'mc':
            return cog.get_emoji('minecraft')
        elif self.type == 'deviant':
            return cog.get_emoji('deviant')
        else:
            return "📰"
