# =============================================================================
#  FLEX FUCKER USERBOT Tohid Command
#  Author:         FLEX FUCKER USERBOT Dev ()
# =============================================================================

from telethon import events
from utils.utils import CipherElite
from plugins.bot import add_handler
from utils.decorators import rishabh

VERSION = "1.0.0"
CATEGORY = "fun"


def init(client_instance):
    commands = [".tohid - Show Sareef Fucker username"]
    description = "📢 Show the Sareef Fucker Telegram username"
    add_handler("tohid", commands, description)

async def register_commands():
    @CipherElite.on(events.NewMessage(pattern=r"^\.tohid$"))
    @rishabh()
    async def tohid_cmd(event):
        await event.reply(
            "📢 **Sareef Fucker Telegram Username:** `@SAREEF_FUCKER`"
        )
