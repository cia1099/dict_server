import asyncio
from io import BytesIO
import pyglet
from httpx import AsyncClient, HTTPStatusError

SPEECH_REGION = "your azure region"
SPEECH_KEY = "speech key"


async def speech_azure(text: str):
    content = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Female' name='en-US-AvaMultilingualNeural'>
            {text}
        </voice>
    </speak>
    """
    async with AsyncClient(
        base_url=f"https://{SPEECH_REGION}.tts.speech.microsoft.com"
    ) as client:
        try:
            res = await client.post(
                "/cognitiveservices/v1",
                content=content,
                headers={
                    "Ocp-Apim-Subscription-Key": SPEECH_KEY,
                    "User-Agent": "stagefright/1.2 (Linux;Android 9.0)",
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                },
            )
            res.raise_for_status()
            with BytesIO() as f:
                f.write(res.content)
                f.seek(0)
                player = pyglet.media.load("_.mp3", file=f).play()
                while player.playing:
                    pyglet.app.platform_event_loop.dispatch_posted_events()
                    pyglet.clock.tick()
        except HTTPStatusError as err:
            raise Exception(
                f"API request failed with status code {err.response.status_code}"
            ) from err
    print("terminal azure")


if __name__ == "__main__":
    asyncio.run(speech_azure("Hello, Azure, fuck you!"))
    # asyncio.run(send_request("Hello Azure, fuck you!"))
