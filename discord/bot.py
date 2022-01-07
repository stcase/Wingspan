from dataclasses import dataclass
from typing import Dict, Optional

from nextcord.ext import commands, tasks

from wingspan_api.wapi import GameInfo


@dataclass
class Message:
    player: str
    hours_remaining: float


class Bot(commands.Bot):
    def __init__(self, wapi, channel_id: int, game_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wapi = wapi
        self.channel_id = channel_id
        self.sent_messages: Dict[str, Optional[Message]] = dict.fromkeys(game_ids)
        self.subscriptions: Dict[str, set[str]] = {}

        # start the task to run in the background
        self.check_turns.start()

        self.load_commands()

    @tasks.loop(minutes=5)
    async def check_turns(self):
        channel = self.get_channel(self.channel_id)  # channel ID goes here

        for game_id in self.sent_messages:
            game_info = self.wapi.get_game_info(game_id)
            await self.decide_send_message(channel.send, game_info)

    async def decide_send_message(self, send_func, game_info: GameInfo, always_send: bool = False) -> None:
        game_id = game_info.game_id
        player = game_info.current_turn.username
        hours_remaining = game_info.hours_remaining
        sent_message = self.sent_messages.get(game_info.game_id, None)
        notifications = ", ".join([f"<@{subscriber}>" for subscriber in self.subscriptions[player]]) if player in self.subscriptions else ""
        if notifications:
            notifications = f"({notifications})"

        if hours_remaining <= 24 and (always_send or sent_message is None or 24 < sent_message.hours_remaining):
            await send_func(f":rotating_light: {player} {notifications} only has {hours_remaining:.2f} hours remaining in match {game_id} :rotating_light:")
        elif sent_message is None or always_send or sent_message.player != player:
            await send_func(f"It's {player}'s {notifications} turn with {hours_remaining:.2f} hours remaining in match {game_id}")
        else:
            return
        self.sent_messages[game_id] = Message(player=player, hours_remaining=hours_remaining)

    @check_turns.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    def load_commands(self):
        @self.command()
        async def turn(ctx):
            """ Who's turn is it? """
            for game_id in self.sent_messages:
                game_info = self.wapi.get_game_info(game_id)
                await self.decide_send_message(ctx.reply, game_info, always_send=True)

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

        @self.command()
        async def subscribe(ctx, username: str):
            """ Provide a wingspan username you would like to receive notifications for """
            subscriptions = self.subscriptions.get(username, set())
            subscriptions.add(ctx.author.id)
            self.subscriptions[username] = subscriptions
            await ctx.reply(f"Now notifying {ctx.author.name} for {username}")

        @self.command()
        async def unsubscribe(ctx, username: str):
            """ Unsubscribe from notifications for the wingspan username """
            subscriptions = self.subscriptions.get(username, set())
            if not ctx.author.id in subscriptions:
                await ctx.reply(f"{ctx.author.name} is not subscribed to {username}")
            else:
                subscriptions.remove(ctx.author.id)
                await ctx.reply(f"Unsubscribed {ctx.author.name} from {username}")
