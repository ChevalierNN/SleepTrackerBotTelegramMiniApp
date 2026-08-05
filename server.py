import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from aiohttp import web
from config import SERVER_HOST, SERVER_PORT
from database import get_week_records, get_all_records, save_record

logger = logging.getLogger(__name__)
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), "webapp")

# CORS helper 

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


async def cors_preflight(request: web.Request) -> web.Response:
    return web.Response(headers=CORS)


# GET /api/stats ─

async def api_stats(request: web.Request) -> web.Response:
    uid_str = request.rel_url.query.get("user_id", "")
    if not uid_str:
        return web.json_response({"error": "user_id required"}, status=400, headers=CORS)
    try:
        user_id = int(uid_str)
    except ValueError:
        return web.json_response({"error": "user_id must be integer"}, status=400, headers=CORS)

    try:
        week   = await get_week_records(user_id)
        recent = await get_all_records(user_id)
        return web.json_response(
            {"week": week, "recent": recent[:30]},
            headers=CORS,
        )
    except Exception:
        logger.exception("Error in GET /api/stats uid=%s", uid_str)
        return web.json_response({"error": "internal server error"}, status=500, headers=CORS)


# POST /api/sleep 

async def api_save_sleep(request: web.Request) -> web.Response:
    """
    Save a sleep record sent directly from the Mini App UI.
    Expected JSON body:
      { "user_id": int, "sleep_time": "HH:MM",
        "wake_time": "HH:MM", "duration_h": float, "quality": str }
    """
    try:
        body = await request.json()
    except (json.JSONDecodeError, Exception):
        return web.json_response({"error": "invalid JSON"}, status=400, headers=CORS)

    try:
        user_id    = int(body["user_id"])
        sleep_time = str(body["sleep_time"])
        wake_time  = str(body["wake_time"])
        duration_h = float(body["duration_h"])
        quality    = str(body["quality"])
    except (KeyError, ValueError, TypeError) as e:
        return web.json_response({"error": f"missing/invalid field: {e}"}, status=400, headers=CORS)

    try:
        await save_record(
            user_id=user_id,
            sleep_time=sleep_time,
            wake_time=wake_time,
            duration_h=round(duration_h, 2),
            quality=quality,
        )
        return web.json_response({"ok": True}, headers=CORS)
    except Exception:
        logger.exception("Error saving sleep for uid=%s", user_id)
        return web.json_response({"error": "db error"}, status=500, headers=CORS)


# Static / SPA 

async def serve_index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(os.path.join(WEBAPP_DIR, "index.html"))


# App factory 

def create_app() -> web.Application:
    app = web.Application()

    # CORS preflight for all API routes
    app.router.add_route("OPTIONS", "/api/{tail:.*}", cors_preflight)

    # API
    app.router.add_get( "/api/stats",  api_stats)
    app.router.add_post("/api/sleep",  api_save_sleep)

    # Static files
    app.router.add_static("/css", os.path.join(WEBAPP_DIR, "css"))
    app.router.add_static("/js",  os.path.join(WEBAPP_DIR, "js"))

    # SPA catch-all
    app.router.add_get("/",          serve_index)
    app.router.add_get("/{tail:.*}", serve_index)

    return app


# Async runner 

async def run_server() -> None:
    """Start aiohttp and block until cancelled."""
    app    = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, SERVER_HOST, SERVER_PORT)
    await site.start()
    logger.info("Mini App server → http://%s:%d", SERVER_HOST, SERVER_PORT)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


# Standalone 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(run_server())
