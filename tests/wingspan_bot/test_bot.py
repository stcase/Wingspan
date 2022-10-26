from collections.abc import Generator
from unittest import mock

import pytest

from wingspan_bot.bot import Bot, BotCommands
from wingspan_bot.data.data_controller import DataController


class TestBot:
    @pytest.fixture
    def bot(self, dc_monitor_many: DataController) -> Bot:
        bot = Bot(admin_channel=0, data_controller=dc_monitor_many)
        return bot

    @pytest.fixture
    def get_channel(self) -> Generator[mock.MagicMock, None, None]:
        with mock.patch("wingspan_bot.bot.Bot.get_channel") as channel:
            instance = mock.MagicMock()
            channel.return_value = instance
            instance.send = mock.AsyncMock()
            yield channel

    async def test_channel_not_found(self, bot: Bot, get_channel: mock.MagicMock) -> None:
        await self.channel_not_found_helper(bot, get_channel().send)

    async def test_channel_not_found_no_admin(self, bot: Bot, get_channel: mock.MagicMock) -> None:
        get_channel().send = None
        with mock.patch("wingspan_bot.bot.logger") as logger:
            logger.info = mock.MagicMock()
            await self.channel_not_found_helper(bot, logger.info)

    @staticmethod
    async def channel_not_found_helper(bot: Bot, log_func: mock.AsyncMock) -> None:
        channel_id = 2
        await bot.channel_not_found(channel_id=channel_id)

        calls = [mock.call(f"Channel {channel_id} not found. Removing matches from channel...")]
        for match_id in ["game1", "game4"]:
            calls.append(mock.call(f" Removed match {match_id}"))
        assert log_func.call_args_list == calls
        assert bot.dc.get_monitored_matches(channel_id=channel_id) == []


class TestBotCommands:
    @pytest.fixture
    def bot_commands(self, dc_monitor_many: DataController) -> BotCommands:
        return BotCommands(bot=mock.MagicMock(), data_controller=dc_monitor_many)

    async def test_stats(self, bot_commands: BotCommands) -> None:
        context = mock.AsyncMock()
        context.channel.id = 1
        await bot_commands.stats.callback(bot_commands, context, None)
        context.reply.assert_called_with(
            "Global channel data:\n"
            "3 matches monitored since 2020-01-01 01:01:01\n"
            "```"
            "Fastest average turn time (hours): None\n"
            "Highest score:                     None\n"
            "Most points from birds:            None\n"
            "Most points from bonus cards:      None\n"
            "Most points from goals:            None\n"
            "Most points from eggs:             None\n"
            "Most points from cached food:      None\n"
            "Most points from tucked cards:     None\n"
            "\n"
            "Hours each player commonly plays (in UTC):\n"
            "```")

    async def test_stats_stop_watching(self, bot_commands: BotCommands) -> None:
        context = mock.AsyncMock()
        context.channel.id = 1
        bot_commands.dc.remove(channel=context.channel.id, game_id="game1")

        await bot_commands.stats.callback(bot_commands, context, None)
        context.reply.assert_called_with(
            "Global channel data:\n"
            "3 matches monitored since 2020-01-01 01:01:01\n"
            "```"
            "Fastest average turn time (hours): None\n"
            "Highest score:                     None\n"
            "Most points from birds:            None\n"
            "Most points from bonus cards:      None\n"
            "Most points from goals:            None\n"
            "Most points from eggs:             None\n"
            "Most points from cached food:      None\n"
            "Most points from tucked cards:     None\n"
            "\n"
            "Hours each player commonly plays (in UTC):\n"
            "```")
