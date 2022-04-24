import logging
import sys
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

import nextcord
from nextcord.ext import commands, tasks  # type: ignore[attr-defined]
from nextcord.ext.commands import Context

from configs import ADMIN_CHANNEL
from discord.data.data_controller import DataController
from discord.data.models import MessageType
from wingspan_api.wapi import Match

logger = logging.getLogger(__name__)


class Bot(commands.Bot):  # type: ignore[misc]
    def __init__(self, data_controller: DataController, *args: Any, **kwargs: Any):
        self.dc = data_controller
        super().__init__(*args, **kwargs)

        self.check_turns.start()  # start the task to run in the background
        self.add_cog(BotCommands(self, data_controller))
        self.in_error_state = False

    @tasks.loop(minutes=5)  # type: ignore[misc]
    async def check_turns(self) -> None:
        try:
            for channel_id, match in self.dc.get_matches():
                channel = self.get_channel(channel_id)
                if self.dc.should_send_message(channel_id, match):
                    await self.send_message(channel.send, channel_id, match)
        except BaseException:
            admin_channel = self.get_channel(ADMIN_CHANNEL).send if not self.in_error_state else None
            self.in_error_state = True
            await _handle_error(admin_channel, "checking turns")
        else:
            self.in_error_state = False

    async def send_message(self,
                           send_func: Callable[[str], Awaitable[nextcord.message.Message]],
                           channel: int,
                           match: Match | str) -> None:
        message_type = self.dc.get_message_type(match)
        hours_remaining = None if isinstance(match, str) else match.hours_remaining
        player = None if isinstance(match, str) else match.current_player_name
        subscriptions = self.dc.get_subscriptions(channel)
        tagged_users = (
            ", ".join([f"<@{subscriber}>" for subscriber in subscriptions[player]])
            if player in subscriptions
            else ""
        )
        if message_type == MessageType.ERROR:
            await send_func(f"Exception while checking {match} - check the logs")
        if message_type == MessageType.GAME_COMPLETE:
            await send_func(f"Game {match} is Complete!")
        if message_type == MessageType.WAITING:
            await send_func(f"Game {match} is waiting to start")
        if message_type == MessageType.READY:
            await send_func(f"Game {match} is ready to start")
        if message_type == MessageType.NEW_TURN:
            await send_func(
                f"It's {player}'s{tagged_users} turn with {hours_remaining:.2f}"
                f" hours remaining in match {match}"
            )
        if message_type == MessageType.REMINDER:
            await send_func(
                f":rotating_light: {player}{tagged_users} only has {hours_remaining:.2f} hours remaining"
                f"in match {match} :rotating_light:"
            )
        self.dc.db.add_message(match, channel, player, message_type)  # TODO: move to dc

    @check_turns.before_loop  # type: ignore[misc]
    async def before_my_task(self) -> None:
        await self.wait_until_ready()  # wait until the bot logs in


class BotCommands(commands.Cog):  # type: ignore[misc]
    def __init__(self, bot: Bot, data_controller: DataController):
        self.bot = bot
        self.dc = data_controller

    @commands.command()  # type: ignore[misc]
    async def turn(self, ctx: Context) -> None:
        """ Who's turn is it? """
        try:
            channel = ctx.channel.id
            for _, match in self.dc.get_matches(channel):
                if isinstance(match, str):
                    await ctx.reply(f"Exception while checking {match} - check the logs")
                    continue
                await self.bot.send_message(ctx.reply, channel, match)
        except BaseException:
            await _handle_error(ctx.reply, "checking turns")

    @commands.command()  # type: ignore[misc]
    async def add(self, ctx: Context, game_id: str) -> None:
        """ Add the game_id to be monitored """
        await self.command_template(
            ctx,
            lambda: self.dc.add(ctx.channel.id, game_id),
            f"Now monitoring {game_id}",
            f"Already monitoring {game_id}",
            f"adding match {game_id}, maybe an invalid ID?"
        )

    @commands.command()  # type: ignore[misc]
    async def remove(self, ctx: Context, game_id: str) -> None:
        """ Remove the game_id from being monitored """
        await self.command_template(
            ctx,
            lambda: self.dc.remove(ctx.channel.id, game_id),
            f"No longer monitoring {game_id}",
            f"Not monitoring {game_id}",
            f"removing match {game_id}"
        )

    @commands.command()  # type: ignore[misc]
    async def subscribe(self, ctx: Context, wingspan_name: str) -> None:
        """ Provide a wingspan username you would like to receive notifications for """
        await self.command_template(
            ctx,
            lambda: self.dc.subscribe(ctx.channel.id, ctx.author.id, wingspan_name),
            f"Now notifying {ctx.author.name} for {wingspan_name}",
            f"Already subscribed to {wingspan_name}",
            f"subscribing to {wingspan_name}"
        )

    @commands.command()  # type: ignore[misc]
    async def unsubscribe(self, ctx: Context, wingspan_name: str) -> None:
        """ Unsubscribe from notifications for the wingspan username """
        await self.command_template(
            ctx,
            lambda: self.dc.unsubscribe(ctx.channel.id, ctx.author.id, wingspan_name),
            f"No longer notifying for {wingspan_name}",
            f"Not subscribed to {wingspan_name}",
            f"unsubscribing from {wingspan_name}"
        )

    async def command_template(
            self, ctx: Context,
            func: Callable[[], bool],
            success_msg: str,
            failure_msg: str,
            error_msg: str) -> None:
        try:
            success = func()
            await ctx.reply(success_msg if success else failure_msg)
        except BaseException:
            await _handle_error(ctx.reply, error_msg)


async def _handle_error(send_func: Callable[[str], Awaitable[nextcord.message.Message]] | None, data: str) -> None:
    logger.error(f"Exception while {data}")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    if send_func is not None:
        await send_func(f"Exception while {data} - check the logs")
