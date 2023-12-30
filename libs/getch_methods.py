import discord


async def getch_channel_or_thread(guild: discord.Guild, channel_id: int):
    "Get a channel from its id, or None if not found"
    if channel := guild.get_channel_or_thread(channel_id):
        return channel
    try:
        return await guild.fetch_channel(channel_id)
    except discord.NotFound:
        return None
