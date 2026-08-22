# =============================================================================
#  FLEX FUCKER USERBOT Gemini Fallback Test Command
#  Author:         FLEX FUCKER USERBOT Dev ()
# =============================================================================

from telethon import events
from utils.utils import CipherElite
from plugins.bot import add_handler
from utils.decorators import rishabh

VERSION = "1.0.0"
CATEGORY = "testing"


def init(client_instance):
    commands = [
        ".geminitest - Replies with a success message for Gemini fallback testing"
    ]
    description = "🚀 Test the Gemini fallback mechanism"
    add_handler("geminitest", commands, description)


async def register_commands():
    @CipherElite.on(events.NewMessage(outgoing=True, pattern=r"^\.geminitest$"))
    @rishabh()
    async def geminitest_cmd(event):
        await event.reply("Gemini fallback test successful")
