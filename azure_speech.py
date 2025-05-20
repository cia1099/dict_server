import asyncio
from io import BytesIO
import pyglet
from aiohttp import ClientSession, ClientResponseError
from config import config

SPEECH_REGION = config.SPEECH_REGION
SPEECH_KEY = config.SPEECH_KEY


async def speech_azure(text: str):
    lang = "en-US"
    name = "iu-Latn-CA-TaqqiqNeural"
    content = f"""
    <speak version='1.0' xml:lang='{lang}'>
        <voice xml:lang='{lang}' xml:gender='Female' name='{name}'>
            {text}
        </voice>
    </speak>
    """
    async with ClientSession(
        base_url=f"https://{SPEECH_REGION}.tts.speech.microsoft.com"
    ) as client:

        try:
            res = await client.post(
                "/cognitiveservices/v1",
                data=content,
                headers={
                    "Ocp-Apim-Subscription-Key": SPEECH_KEY or "",
                    "User-Agent": "stagefright/1.2 (Linux;Android 9.0)",
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                },
            )
            res.raise_for_status()
            with BytesIO() as f:
                async for bytes in res.content.iter_chunked(1024):
                    f.write(bytes)
                f.seek(0)
                player = pyglet.media.load("_.mp3", file=f).play()
                while player.playing:
                    pyglet.app.platform_event_loop.dispatch_posted_events()
                    pyglet.clock.tick()
        except ClientResponseError as err:
            raise Exception(f"{err.message} ({err.status})") from err
    # print("terminal azure")


if __name__ == "__main__":
    asyncio.run(speech_azure("Sometime you can see snail in mountain\nBottle of water"))
    # asyncio.run(send_request("Hello Azure, fuck you!"))
