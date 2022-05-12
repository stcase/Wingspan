from collections.abc import Generator
from unittest import mock

import pytest

from discord.bot import Bot
from discord.data.data_controller import DataController


class TestBot:
    @pytest.fixture
    def bot(self, dc_monitor_many: DataController) -> Bot:
        bot = Bot(dc_monitor_many)
        return bot

    @pytest.fixture
    def get_channel(self) -> Generator[mock.MagicMock, None, None]:
        with mock.patch("discord.bot.Bot.get_channel") as channel:
            instance = mock.MagicMock()
            channel.return_value = instance
            instance.send = mock.AsyncMock()
            yield channel

    async def test_channel_not_found(self, bot: Bot, get_channel: mock.MagicMock) -> None:
        await self.channel_not_found_helper(bot, get_channel().send)

    async def test_channel_not_found_no_admin(self, bot: Bot, get_channel: mock.MagicMock) -> None:
        get_channel().send = None
        with mock.patch("discord.bot.logger") as logger:
            logger.info = mock.MagicMock()
            await self.channel_not_found_helper(bot, logger.info)

    @staticmethod
    async def channel_not_found_helper(bot: Bot, log_func: mock.AsyncMock) -> None:
        channel_id = 2
        await bot.channel_not_found(channel_id=channel_id)

        calls = [mock.call(f"Channel {channel_id} not found. Removing matches from channel...")]
        for match_id in ["game1", "game4"]:
            calls.append(mock.call(f" Removed match {match_id}"))
        log_func.assert_has_calls(calls)
        assert bot.dc.get_monitored_matches(channel_id=channel_id) == []
