import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, asdict
from json import JSONDecodeError
from typing import Any

import nextcord
from nextcord.ext import commands, tasks  # type: ignore[attr-defined]
from nextcord.ext.commands import Context

from wingspan_api.wapi import GameInfo, Wapi

STATE_FILE = "state_data.json"

logger = logging.getLogger(__name__)


@dataclass
class Message:
    player: str | None
    hours_remaining: float | None


class Bot(commands.Bot):  # type: ignore[misc]
    def __init__(self, wapi: Wapi, channel_id: int, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.wapi = wapi
        self.channel_id = channel_id
        self.sent_messages: dict[str, Message | None] = {}
        self.subscriptions: dict[str, set[str]] = {}
        self.load_data()

        # start the task to run in the background
        self.check_turns.start()

        self.load_commands()

    def save_data(self) -> None:
        with open(STATE_FILE, "w") as f:
            json.dump(
                {
                    "messages": {
                        game_id: (asdict(message) if message is not None else None)
                        for game_id, message in self.sent_messages.items()
                    },
                    "subscriptions": {player: list(ids) for player, ids in self.subscriptions.items()},
                },
                f,
                indent=2,
            )

    def load_data(self) -> None:
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            self.subscriptions = {player: set(ids) for player, ids in data["subscriptions"].items()}
            self.sent_messages = {
                game_id: (Message(**message) if message is not None else None)
                for game_id, message in data["messages"].items()
            }
        except (JSONDecodeError, FileNotFoundError) as e:
            logger.info(f"Failed to load state file: {e}")

    @tasks.loop(minutes=5)  # type: ignore[misc]
    async def check_turns(self) -> None:
        channel = self.get_channel(self.channel_id)  # channel ID goes here

        for game_id in self.sent_messages:
            game_info = self.wapi.get_game_info(game_id)
            if self.should_send_message(game_id, game_info):
                await self.send_message(channel.send, game_id, game_info)

    def should_send_message(self, game_id: str, game_info: GameInfo) -> bool:
        sent_message = self.sent_messages.get(game_id, None)
        player = game_info.current_turn.username
        hours_remaining = game_info.hours_remaining
        return (sent_message is None  # no messages sent
                or sent_message.player != player  # player's turn changed
                or (hours_remaining is not None and sent_message.hours_remaining is not None
                    and hours_remaining < 24 < sent_message.hours_remaining))  # out of time warning

    async def send_message(self,
                           send_func: Callable[[str], Awaitable[nextcord.message.Message]],
                           game_id: str,
                           game_info: GameInfo) -> None:
        hours_remaining = game_info.hours_remaining
        player = game_info.current_turn.username
        tagged_users = (
            ", ".join([f"<@{subscriber}>" for subscriber in self.subscriptions[player]])
            if player in self.subscriptions
            else ""
        )

        if game_info.is_completed:
            await send_func(f"Game {game_id} is Complete!")
        elif game_info.waiting_to_start:
            await send_func(f"Game {game_id} is waiting to start")
        elif hours_remaining is not None and hours_remaining <= 24:
            await send_func(
                f":rotating_light: {player}{tagged_users} only has {hours_remaining:.2f} hours remaining"
                f"in match {game_id} :rotating_light:"
            )
        elif hours_remaining is not None:
            await send_func(
                f"It's {player}'s{tagged_users} turn with {hours_remaining:.2f} hours remaining in match {game_id}"
            )
        else:
            await send_func(f"Unknown error {game_id}: {game_info.data}")

        self.sent_messages[game_id] = Message(player=player, hours_remaining=hours_remaining)
        self.save_data()

    @check_turns.before_loop  # type: ignore[misc]
    async def before_my_task(self) -> None:
        await self.wait_until_ready()  # wait until the bot logs in

    def load_commands(self) -> None:
        @self.command()  # type: ignore[misc]
        async def turn(ctx: Context) -> None:
            """ Who's turn is it? """
            for game_id in self.sent_messages:
                game_info = self.wapi.get_game_info(game_id)
                await self.send_message(ctx.reply, game_id, game_info)

        @self.command()  # type: ignore[misc]
        async def add(ctx: Context, game_id: str) -> None:
            """ Add the game_id to be monitored """
            if game_id in self.sent_messages:
                await ctx.reply(f"Already monitoring game_id: {game_id}")
            else:
                game_info = self.wapi.get_game_info(game_id)
                print(game_info.data)
                if not game_info.valid:
                    await ctx.reply(f"Invalid game_id: {game_id}")
                else:
                    self.sent_messages[game_id] = None
                    await ctx.reply(f"Now monitoring game_id: {game_id}")
                    self.save_data()

        @self.command()  # type: ignore[misc]
        async def remove(ctx: Context, game_id: str) -> None:
            """ Remove the game_id from being monitored """
            if game_id not in self.sent_messages:
                await ctx.reply(f"Not monitoring game_id: {game_id}")
            else:
                del self.sent_messages[game_id]
                await ctx.reply(f"No longer monitoring game_id: {game_id}")
                self.save_data()

        @self.command()  # type: ignore[misc]
        async def subscribe(ctx: Context, username: str) -> None:
            """ Provide a wingspan username you would like to receive notifications for """
            subscriptions = self.subscriptions.get(username, set())
            subscriptions.add(ctx.author.id)
            self.subscriptions[username] = subscriptions
            await ctx.reply(f"Now notifying {ctx.author.name} for {username}")
            self.save_data()

        @self.command()  # type: ignore[misc]
        async def unsubscribe(ctx: Context, username: str) -> None:
            """ Unsubscribe from notifications for the wingspan username """
            subscriptions = self.subscriptions.get(username, set())
            if ctx.author.id not in subscriptions:
                await ctx.reply(f"{ctx.author.name} is not subscribed to {username}")
            else:
                subscriptions.remove(ctx.author.id)
                await ctx.reply(f"Unsubscribed {ctx.author.name} from {username}")
                self.save_data()
