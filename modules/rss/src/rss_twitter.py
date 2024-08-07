from __future__ import annotations

import datetime as dt
import html
import re
from typing import TYPE_CHECKING

import discord
import twitter
from asyncache import cached
from cachetools import TTLCache

from .rss_general import FeedObject, RssMessage

if TYPE_CHECKING:
    from core.bot_classes import Axobot


class TwitterRSS:
    "Utilities class for any twitter-related RSS actions"

    def __init__(self, bot: Axobot):
        self.bot = bot
        self.min_time_between_posts = 15 # seconds
        self.api = twitter.Api(**bot.secrets["twitter"], tweet_mode="extended", timeout=15, application_only_auth=True)
        self.url_pattern = r"(?:https://)?(?:www\.)?(?:twitter\.com/)([^?\s/]+)"

    def is_twitter_url(self, string: str):
        "Check if an url is a valid Twitter URL"
        matches = re.match(self.url_pattern, string)
        return bool(matches)

    async def get_userid_from_url(self, url: str) -> int | None:
        "Get a Twitter user ID from a twitter url"
        match = re.search(self.url_pattern, url)
        if match is None:
            return None
        name = match.group(1)
        usr = await self.get_user_from_name(name)
        return usr.id if usr else None

    @cached(TTLCache(maxsize=10_000, ttl=86400))
    async def get_user_from_name(self, name: str):
        "Get a Twitter user object from a twitter username"
        try:
            return self.api.GetUser(screen_name=name)
        except twitter.TwitterError:
            return None

    @cached(TTLCache(maxsize=10_000, ttl=86400))
    async def get_user_from_id(self, user_id: int):
        "Get a Twitter user object from a Twitter user ID"
        try:
            return self.api.GetUser(user_id=user_id)
        except twitter.TwitterError:
            return None

    async def remove_image(self, channel: discord.abc.Messageable, text: str):
        "Remove images links from a tweet if needed"
        if channel.guild is None or channel.permissions_for(channel.guild.me).embed_links:
            find_url = self.bot.get_cog("Utilities").find_url_redirection
            for match in re.finditer(r"https://t.co/([^\s]+)", text):
                final_url = await find_url(match.group(0))
                if "/photo/" in final_url:
                    text = text.replace(match.group(0), '')
        return text

    async def _get_feed_list(self, name: str):
        "Get tweets from a given Twitter user"
        try:
            if isinstance(name, int) or name.isnumeric():
                posts = self.api.GetUserTimeline(user_id=int(name), exclude_replies=True)
                # username = (await self.get_user_from_id(int(name))).screen_name
            else:
                posts = self.api.GetUserTimeline(screen_name=name, exclude_replies=True)
                # username = name
        except twitter.error.TwitterError as err:
            if err.message == "Not authorized." or "Unknown error" in err.message:
                return None
            if err.message[0]["code"] == 34:
                return None
            raise err
        return posts

    async def get_last_post(self, channel: discord.TextChannel, name: str) -> RssMessage | None:
        "Get the last post from a given Twitter user"
        # fetch tweets
        posts = await self._get_feed_list(name)
        if len(posts) == 0:
            return await self.bot._(channel, "rss.nothing")
        # get username
        if isinstance(name, int) or name.isnumeric():
            username = (await self.get_user_from_id(int(name))).screen_name
        else:
            username = name
        lastpost = posts[0]
        # detect if retweet
        is_rt = None
        text = html.unescape(getattr(lastpost, "full_text", lastpost.text))
        if lastpost.retweeted:
            if possible_rt := re.search(r"^RT @([\w-]+):", text):
                is_rt = possible_rt.group(1)
        # remove images links if needed
        text = await self.remove_image(channel, text)
        # format URL
        url = f"https://twitter.com/{username.lower()}/status/{lastpost.id}"
        img = None
        if lastpost.media: # if exists and is not empty
            img = lastpost.media[0].media_url_https
        return RssMessage(
            bot=self.bot,
            feed=FeedObject.unrecorded("tw", channel.guild.id if channel.guild else None, channel.id, url),
            url=url,
            title=text,
            date=dt.datetime.fromtimestamp(lastpost.created_at_in_seconds),
            author=lastpost.user.screen_name,
            retweeted_from=is_rt,
            channel=lastpost.user.name,
            image=img,
            post_text=getattr(lastpost, "full_text", lastpost.text)
        )

    async def get_new_posts(self, channel: discord.TextChannel, name: str, date: dt.datetime) -> list[RssMessage]:
        "Get new posts from a given Twitter user"
        # fetch tweets
        posts = await self._get_feed_list(name)
        if len(posts) == 0:
            return []
        posts_list = []
        for post in posts:
            # don't return more than 10 posts
            if len(posts_list) > 10:
                break
            # don't return posts older than the date
            if (dt.datetime.fromtimestamp(post.created_at_in_seconds) - date).total_seconds() < self.min_time_between_posts:
                break
            # detect if retweet
            is_rt = None
            text: str = html.unescape(getattr(post, "full_text", post.text))
            if post.retweeted:
                if possible_rt := re.search(r"^RT @([\w-]+):", text):
                    is_rt = possible_rt.group(1)
            # remove images links if needed
            text = await self.remove_image(channel, text)
            # format URL
            url = f"https://twitter.com/{name.lower()}/status/{post.id}"
            img = None
            if post.media: # if exists and is not empty
                img = post.media[0].media_url_https
            obj = RssMessage(
                bot=self.bot,
                feed=FeedObject.unrecorded("tw", channel.guild.id if channel.guild else None, channel.id, url),
                url=url,
                title=text,
                date=dt.datetime.fromtimestamp(post.created_at_in_seconds),
                author=post.user.screen_name,
                retweeted_from=is_rt,
                channel=post.user.name,
                image=img,
                post_text=getattr(post, "full_text", post.text)
            )
            posts_list.append(obj)
        posts_list.reverse()
        return posts_list
