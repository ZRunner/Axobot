from __future__ import annotations

import datetime as dt
import re
from typing import TYPE_CHECKING, Optional, Literal

import aiohttp
import discord
from feedparser.util import FeedParserDict

from .convert_post_to_text import get_text_from_entry
from .rss_general import FeedObject, RssMessage, feed_parse

if TYPE_CHECKING:
    from libs.bot_classes import Axobot

class WebRSS:
    "Utilities class for any web-related RSS actions"

    def __init__(self, bot: Axobot):
        self.bot = bot
        self.min_time_between_posts = 120 # seconds
        self.url_pattern = r'^(?:https://)(?:www\.)?(\S+)$'

    def is_web_url(self, string: str):
        "Check if an url is a valid HTTPS web URL"
        matches = re.match(self.url_pattern, string)
        return bool(matches)

    async def _get_feed(self, url: str, session: Optional[aiohttp.ClientSession]=None) -> FeedParserDict:
        "Get a list of feeds from a web URL"
        feed = await feed_parse(self.bot, url, 9, session)
        if feed is None or 'bozo_exception' in feed or not feed.entries:
            return None
        date_field_key = await self._get_feed_date_key(feed.entries[0])
        if date_field_key is not None and len(feed.entries) > 1:
            # Remove entries that are older than the next one
            try:
                while (len(feed.entries) > 1) \
                    and (feed.entries[1][date_field_key] is not None) \
                        and (feed.entries[0][date_field_key] < feed.entries[1][date_field_key]):
                    del feed.entries[0]
            except KeyError:
                pass
        return feed

    async def _get_feed_date_key(self, entry: FeedParserDict) -> Optional[
        Literal['published_parsed', 'published', 'updated_parsed']
    ]:
        "Compute which key to use to get the date from a feed"
        for i in ['published_parsed', 'published', 'updated_parsed']:
            if entry.get(i) is not None:
                return i

    async def get_last_post(self, channel: discord.TextChannel, url: str, session: Optional[aiohttp.ClientSession]=None):
        "Get the last post from a web feed"
        feed = await self._get_feed(url, session)
        if not feed:
            return await self.bot._(channel, "rss.web-invalid")
        entry = feed.entries[0]
        date_field_key = await self._get_feed_date_key(entry)
        if date_field_key is None:
            date = 'Unknown'
        else:
            date = entry[date_field_key]
        if 'link' in entry:
            link = entry['link']
        elif 'link' in feed:
            link = feed['link']
        else:
            link = url
        if 'author' in entry:
            author = entry['author']
        elif 'author' in feed:
            author = feed['author']
        elif 'title' in feed['feed']:
            author = feed['feed']['title']
        else:
            author = '?'
        if 'title' in entry:
            title = entry['title']
        elif 'title' in feed:
            title = feed['title']
        else:
            title = '?'
        post_text = await get_text_from_entry(entry)
        img = None
        img_match = re.search(r'(http(s?):)([/|.\w\s-])*\.(?:jpe?g|gif|png|webp)', str(entry))
        if img_match is not None:
            img = img_match.group(0)
        return RssMessage(
            bot=self.bot,
            feed=FeedObject.unrecorded("web", channel.guild.id if channel.guild else None, channel.id, url),
            url=link,
            title=title,
            date=date,
            author=author,
            channel=feed.feed['title'] if 'title' in feed.feed else '?',
            image=img,
            post_text=post_text
        )

    async def get_new_posts(self, channel: discord.TextChannel, url: str, date: dt.datetime,
                            session: Optional[aiohttp.ClientSession]=None) -> list[RssMessage]:
        "Get new posts from a web feed"
        feed = await self._get_feed(url, session)
        if not feed:
            return []
        posts_list: list[RssMessage] = []
        date_field_key = await self._get_feed_date_key(feed.entries[0])
        if date_field_key is None or date_field_key == "published":
            last_entry = await self.get_last_post(channel, url, session)
            if isinstance(last_entry, RssMessage):
                return [last_entry]
            return []
        for entry in feed.entries:
            if len(posts_list) > 10:
                break
            try:
                entry_date = entry.get(date_field_key)
                # check if the entry is not too close to (or passed) the last post
                if entry_date is None or (
                        dt.datetime(*entry_date[:6]) - date).total_seconds() < self.min_time_between_posts:
                    # we know we can break because entries are sorted by most recent first
                    break
                if 'link' in entry:
                    link = entry['link']
                elif 'link' in feed:
                    link = feed['link']
                else:
                    link = url
                if 'author' in entry:
                    author = entry['author']
                elif 'author' in feed:
                    author = feed['author']
                elif 'title' in feed['feed']:
                    author = feed['feed']['title']
                else:
                    author = '?'
                if 'title' in entry:
                    title = entry['title']
                elif 'title' in feed:
                    title = feed['title']
                else:
                    title = '?'
                post_text = await get_text_from_entry(entry)
                img = None
                img_match = re.search(r'(http(s?):)([/|.\w\s-])*\.(?:jpe?g|gif|png|webp)', str(entry))
                if img_match is not None:
                    img = img_match.group(0)
                obj = RssMessage(
                    bot=self.bot,
                    feed=FeedObject.unrecorded("web", channel.guild.id if channel.guild else None, channel.id, url),
                    url=link,
                    title=title,
                    date=entry_date,
                    author=author,
                    channel=feed.feed['title'] if 'title' in feed.feed else '?',
                    image=img,
                    post_text=post_text
                )
                posts_list.append(obj)
            except Exception as err:
                self.bot.dispatch("error", err)
        posts_list.reverse()
        return posts_list