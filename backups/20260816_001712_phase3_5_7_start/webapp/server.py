"""Lightweight aiohttp server for the Telegram Mini App."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from aiohttp import web

import config
from .auth import (
    MiniAppAuthError,
    issue_ticket,
    validate_init_data,
    verify_ticket,
)

logger = logging.getLogger(__name__)
_STATIC_DIR = Path(__file__).with_name("static")


class MiniAppServer:
    """Owns the Mini App HTTP server and keeps all account state server-side."""

    _MAX_REQUEST_BYTES = 64 * 1024

    def __init__(self, manager):
        self.manager = manager
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    @property
    def is_running(self) -> bool:
        return self._runner is not None and self._site is not None

    async def start(self) -> bool:
        if self.is_running:
            return True
        if not config.SESSION_SECRET:
            logger.error(
                "Mini App disabled: SESSION_SECRET is not available in the bot workflow."
            )
            return False

        app = web.Application(client_max_size=self._MAX_REQUEST_BYTES)
        app.router.add_get(config.MINI_APP_PATH, self._index)
        base_path = config.MINI_APP_PATH.rstrip("/")
        app.router.add_get(base_path, self._redirect_to_index)
        app.router.add_post(f"{base_path}/api/auth", self._authenticate)
        app.router.add_get(f"{base_path}/api/status", self._status)
        app.router.add_static(f"{base_path}/static/", _STATIC_DIR, show_index=False)

        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        try:
            site = web.TCPSite(runner, "0.0.0.0", config.WEBAPP_PORT)
            await site.start()
        except Exception:
            await runner.cleanup()
            raise

        self._runner = runner
        self._site = site
        logger.info(
            "Telegram Mini App listening on 0.0.0.0:%s at %s",
            config.WEBAPP_PORT,
            config.MINI_APP_PATH,
        )
        if not config.mini_app_url():
            logger.warning(
                "MINI_APP_URL is not configured and no Replit domain was detected; "
                "the /start Web App button will be omitted."
            )
        return True

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
        self._runner = None
        self._site = None

    async def _index(self, _request: web.Request) -> web.StreamResponse:
        return web.FileResponse(_STATIC_DIR / "index.html")

    async def _redirect_to_index(self, _request: web.Request) -> web.StreamResponse:
        raise web.HTTPFound(config.MINI_APP_PATH)

    async def _authenticate(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            if not isinstance(body, dict):
                raise MiniAppAuthError("Authentication payload is malformed.")
            init_data = str(body.get("initData") or "")
            user = validate_init_data(init_data, config.BOT_TOKEN)
            if not self.manager.is_hosted(user.user_id):
                return web.json_response(
                    {
                        "ok": False,
                        "code": "not_hosted",
                        "message": "No active hosted Telegram account is connected.",
                    },
                    status=403,
                )
            ticket = issue_ticket(user, config.SESSION_SECRET)
            return web.json_response({"ok": True, "ticket": ticket})
        except (MiniAppAuthError, json.JSONDecodeError, ValueError, TypeError):
            return web.json_response(
                {"ok": False, "code": "unauthorized", "message": "Telegram authentication failed."},
                status=401,
            )

    async def _status(self, request: web.Request) -> web.Response:
        try:
            user_id = verify_ticket(
                self._bearer_token(request),
                config.SESSION_SECRET,
            )
        except MiniAppAuthError:
            return web.json_response(
                {"ok": False, "code": "unauthorized", "message": "Authorization expired."},
                status=401,
            )

        # A ticket is deliberately stateless, so re-check the live hosted-user
        # mapping on every request. This immediately revokes access after
        # /unhost or a session disconnect instead of trusting an old ticket.
        if not self.manager.is_hosted(user_id):
            return web.json_response(
                {
                    "ok": False,
                    "code": "not_hosted",
                    "message": "No active hosted Telegram account is connected.",
                },
                status=403,
            )

        hosted = self.manager.get_client(user_id)
        is_hosted = hosted is not None and hosted.is_running()
        payload = {
            "ok": True,
            "telegram_user_id": user_id,
            "hosted": is_hosted,
            "session_active": is_hosted,
            "voice_chat": {
                "connected": False,
                "chat_id": None,
                "title": None,
                "playing": False,
                "queued": 0,
                "volume": 100,
                "muted": False,
            },
        }
        if not is_hosted:
            return web.json_response(payload)

        voice = getattr(hosted.client, "_voice_chat_manager", None)
        state = getattr(voice, "state", None)
        if state is not None:
            payload["voice_chat"] = {
                "connected": True,
                "chat_id": state.chat_id,
                "title": state.chat_title or "Voice Chat",
                "playing": state.current is not None,
                "queued": len(state.queue),
                "volume": state.volume,
                "muted": state.muted,
            }
        return web.json_response(payload)

    @staticmethod
    def _bearer_token(request: web.Request) -> str:
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        return token.strip() if scheme.lower() == "bearer" else ""