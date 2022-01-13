import json
import logging
from dataclasses import dataclass, asdict
from json import JSONDecodeError
from typing import Dict, Optional

from nextcord.ext import commands, tasks

from wingspan_api.wapi import GameInfo, Wapi

STATE_FILE = "state_data.json"

logger = logging.getLogger(__name__)


@dataclass
class Message:
    player: Optional[str]
    hours_remaining: float


class Bot(commands.Bot):
    def __init__(self, wapi: Wapi, channel_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wapi = wapi
        self.channel_id = channel_id
        self.sent_messages: Dict[str, Optional[Message]] = {}
        self.subscriptions: Dict[str, set[str]] = {}
        self.load_data()

        # start the task to run in the background
        self.check_turns.start()

        self.load_commands()

    def save_data(self):
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

    def load_data(self):
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

    @tasks.loop(minutes=5)
    async def check_turns(self):
        channel = self.get_channel(self.channel_id)  # channel ID goes here

        for game_id in self.sent_messages:
            game_info = self.wapi.get_game_info(game_id)
            await self.decide_send_message(channel.send, game_id, game_info)

    async def decide_send_message(self, send_func, game_id: str, game_info: GameInfo, always_send: bool = False) -> None:
        normal_play = not (not game_info.valid or game_info.is_completed or game_info.waiting_to_start)
        player = game_info.current_turn.username if normal_play else None
        hours_remaining = game_info.hours_remaining if normal_play else 0
        sent_message = self.sent_messages.get(game_id, None)
        notifications = (
            ", ".join([f"<@{subscriber}>" for subscriber in self.subscriptions[player]])
            if player in self.subscriptions
            else ""
        )
        if notifications:
            notifications = f" ({notifications})"
        if not normal_play and (always_send or sent_message is None or sent_message.player != player):
            if not game_info.valid:
                await send_func(f"Error getting data {game_id}: {game_info.data}")
            elif game_info.is_completed:
                await send_func(f"Game {game_id} is Complete!")
            elif game_info.waiting_to_start:
                await send_func(f"Game {game_id} is waiting to start")
            else:
                await send_func(f"Unknown error {game_id}: {game_info.data}")
        elif hours_remaining <= 24 and (
            always_send or sent_message is None or 24 < sent_message.hours_remaining or sent_message.player != player
        ):
            await send_func(
                f":rotating_light: {player} {notifications} only has {hours_remaining:.2f} hours remaining in match {game_id} :rotating_light:"
            )
        elif sent_message is None or always_send or sent_message.player != player:
            await send_func(
                f"It's {player}'s{notifications} turn with {hours_remaining:.2f} hours remaining in match {game_id}"
            )
        else:
            return
        self.sent_messages[game_id] = Message(player=player, hours_remaining=hours_remaining)
        self.save_data()

    @check_turns.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    def load_commands(self):
        @self.command()
        async def turn(ctx):
            """ Who's turn is it? """
            for game_id in self.sent_messages:
                game_info = self.wapi.get_game_info(game_id)
                await self.decide_send_message(ctx.reply, game_id, game_info, always_send=True)

        @self.command()
        async def add(ctx, game_id: str):
            """ Add the game_id to be monitored """
            if game_id in self.sent_messages:
                await ctx.reply(f"Already monitoring game_id: {game_id}")
            else:
                game_info = self.wapi.get_game_info(game_id)
                print(game_info.data)
                if not game_info.is_valid:
                    await ctx.reply(f"Invalid game_id: {game_id}")
                else:
                    self.sent_messages[game_id] = None
                    await ctx.reply(f"Now monitoring game_id: {game_id}")
                    self.save_data()

        @self.command()
        async def remove(ctx, game_id: str):
            """ Remove the game_id from being monitored """
            if game_id not in self.sent_messages:
                await ctx.reply(f"Not monitoring game_id: {game_id}")
            else:
                del self.sent_messages[game_id]
                await ctx.reply(f"No longer monitoring game_id: {game_id}")
                self.save_data()

        @self.command()
        async def subscribe(ctx, username: str):
            """ Provide a wingspan username you would like to receive notifications for """
            subscriptions = self.subscriptions.get(username, set())
            subscriptions.add(ctx.author.id)
            self.subscriptions[username] = subscriptions
            await ctx.reply(f"Now notifying {ctx.author.name} for {username}")
            self.save_data()

        @self.command()
        async def unsubscribe(ctx, username: str):
            """ Unsubscribe from notifications for the wingspan username """
            subscriptions = self.subscriptions.get(username, set())
            if ctx.author.id not in subscriptions:
                await ctx.reply(f"{ctx.author.name} is not subscribed to {username}")
            else:
                subscriptions.remove(ctx.author.id)
                await ctx.reply(f"Unsubscribed {ctx.author.name} from {username}")
                self.save_data()
