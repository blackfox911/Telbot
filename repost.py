import os
import re
import sys
import random
import signal
import asyncio
import logging

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError

PROMO_LINK = "https://ke7.com/?urc=11917"
PROMO_CODE = "11917"
URL_RE = re.compile(r"https?://\S+")
AD_KEYWORDS = ("#ad", "#advertisement", "sponsored post")
MAX_SEND_RETRIES = 3
CONNECT_RETRY_DELAY = 5
RESTART_DELAY = 10

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

_api_id = os.getenv("API_ID")
_api_hash = os.getenv("API_HASH")
source_channel = os.getenv("SOURCE_CHANNEL")
destination_channel = os.getenv("DEST_CHANNEL")

for name, val in [("API_ID", _api_id), ("API_HASH", _api_hash), ("SOURCE_CHANNEL", source_channel), ("DEST_CHANNEL", destination_channel)]:
    if not val or not str(val).strip():
        sys.exit(f"Missing env var: {name}. Set it in run_local.bat or as env var.")
api_id = int(_api_id)
api_hash = _api_hash

session_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_name")

client = TelegramClient(
    session_path,
    api_id,
    api_hash,
    connection_retries=999,
    request_retries=5,
    use_ipv6=False,
)
dest_entity = None  # Cached at startup to avoid lookup per message


def is_ad(message):
    try:
        text = (getattr(message, "text", None) or getattr(message, "caption", None) or getattr(message, "message", None) or "").lower()
        return any(kw in text for kw in AD_KEYWORDS)
    except Exception:
        return False


def is_image_only(message):
    """Skip only if it's a photo with no text/caption (image-only post). GIFs and stickers are allowed."""
    try:
        if getattr(message, "gif", None) or getattr(message, "sticker", None):
            return False
        if not getattr(message, "photo", None):
            return False
        text = (getattr(message, "text", None) or getattr(message, "caption", None) or getattr(message, "message", None) or "").strip()
        return not text
    except Exception:
        return False


def is_gif(message):
    """Check if message contains a GIF (animated)."""
    try:
        return bool(getattr(message, "gif", None))
    except Exception:
        return False


def is_sticker(message):
    """Check if message contains a sticker."""
    try:
        # Telethon exposes .sticker for stickers (static/animated/video)
        if getattr(message, "sticker", None):
            return True
        # Fallbacks for animated/video stickers by mime type
        doc = getattr(message, "document", None)
        mime = getattr(getattr(doc, "mime_type", None), "lower", lambda: "")()
        return mime in ("application/x-tgsticker", "video/webm")
    except Exception:
        return False


def build_caption(message):
    text = (getattr(message, "text", None) or getattr(message, "caption", None) or getattr(message, "message", None) or "").strip()
    text = URL_RE.sub(PROMO_LINK, text)
    return (text + "\n\n" if text else "") + f"🔥 Play Now: {PROMO_LINK}\n\nPromo code: {PROMO_CODE}"


def get_random_image():
    if not os.path.isdir(IMAGES_DIR):
        return None
    try:
        files = [
            f for f in os.listdir(IMAGES_DIR)
            if f.lower().endswith(IMAGE_EXTENSIONS)
        ]
        if not files:
            return None
        return os.path.join(IMAGES_DIR, random.choice(files))
    except OSError:
        return None


async def _repost_handler(event):
    try:
        message = event.message
        log.info("Message received (id=%s)", getattr(message, "id", "?"))
        if is_ad(message):
            log.info("Skipped (ad)")
            return
        if is_image_only(message):
            log.info("Skipped (image only)")
            return

        text = build_caption(message)
        dest = dest_entity or destination_channel

        for attempt in range(MAX_SEND_RETRIES):
            try:
                # Stickers cannot have captions on Telegram. Send sticker first, then promo text.
                if is_sticker(message) and message.media:
                    await client.send_file(dest, message.media)
                    await client.send_message(dest, text, link_preview=False)
                elif is_gif(message) and message.media:
                    await client.send_file(dest, message.media, caption=text, link_preview=False)
                elif (image_path := get_random_image()):
                    await client.send_file(dest, image_path, caption=text, link_preview=False)
                else:
                    await client.send_message(dest, text, link_preview=False)
                log.info("Reposted")
                return
            except FloodWaitError as e:
                log.warning("FloodWait %ds, sleeping", e.seconds)
                await asyncio.sleep(e.seconds)
            except RPCError as e:
                log.error("RPC error: %s", e)
                return
    except Exception as e:
        log.exception("Handler error: %s", e)


@client.on(events.NewMessage(chats=source_channel))
async def handler(event):
    await _repost_handler(event)


async def connect_with_retry():
    while True:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                log.info("Logging in... Enter phone and code when prompted")
                await client.start()
            return
        except Exception as e:
            log.warning("Connect failed: %s. Retry in %ds", e, CONNECT_RETRY_DELAY)
            await asyncio.sleep(CONNECT_RETRY_DELAY)


async def main():
    global dest_entity
    await connect_with_retry()
    dest_entity = await client.get_input_entity(destination_channel)
    _ = await client.get_input_entity(source_channel)
    img_count = 0
    if os.path.isdir(IMAGES_DIR):
        try:
            img_count = len([f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMAGE_EXTENSIONS)])
        except OSError:
            pass
    log.info("Bot is running. Watching %s -> %s (%d images in folder)", source_channel, destination_channel, img_count)
    await client.run_until_disconnected()


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def on_sigterm():
        log.info("SIGTERM received, disconnecting...")
        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)

    try:
        loop.add_signal_handler(signal.SIGTERM, on_sigterm)
    except (ValueError, OSError, NotImplementedError):
        pass

    try:
        while True:
            try:
                loop.run_until_complete(main())
            except (ConnectionError, OSError) as e:
                log.warning("Connection lost: %s. Restarting in %ds...", e, RESTART_DELAY)
                loop.run_until_complete(asyncio.sleep(RESTART_DELAY))
            except KeyboardInterrupt:
                log.info("Stopping...")
                break
            except Exception as e:
                log.exception("Fatal: %s. Restarting in %ds...", e, RESTART_DELAY)
                loop.run_until_complete(asyncio.sleep(RESTART_DELAY))
    finally:
        try:
            if client.is_connected():
                loop.run_until_complete(asyncio.wait_for(client.disconnect(), timeout=5))
        except Exception:
            pass
        loop.close()


if __name__ == "__main__":
    run()
