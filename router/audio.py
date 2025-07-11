from io import BytesIO
from pathlib import Path
from typing import Iterator
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS
from aiohttp import ClientResponseError, ClientSession

from models.role import Role
from models.text2speech import Text2SpeechIn
from services.auth import member_auth
from services.utils import iter_file, read_ram_chunk
from config import config

router = APIRouter()


@router.get("/dictionary/audio/{filename}")
async def dictionary_audio(filename: str):
    p = Path(f"dictionary/audio/{filename}")
    try:
        return StreamingResponse(iter_file(str(p)), media_type=f"audio/{p.suffix[1:]}")
    except FileNotFoundError:
        raise HTTPException(404, detail="open %s has error" % p)


@router.post("/gtts/audio")
async def gtts_audio(tts: Text2SpeechIn):
    langs = tts.lang.split("-")
    accentMap = {"uk": "co.uk", "au": "com.au"}
    accent = accentMap.get(langs[-1].lower(), langs[-1].lower())
    gtts = gTTS(tts.text, lang=langs[0], tld=accent)
    # gtts = gTTS("hello gtts, shit man", lang="en")
    fp = BytesIO()
    gtts.write_to_fp(fp)
    return StreamingResponse(read_ram_chunk(fp), media_type=f"audio/mp3")


@router.post("/azure/audio")
async def azure_audio(tts: Text2SpeechIn, _=Depends(member_auth)):
    content = f"""
    <speak version='1.0' xml:lang='{tts.lang}'>
        <voice xml:lang='{tts.lang}' xml:gender='{tts.gender}' name='{tts.get_voice()}'>
            {tts.text}
        </voice>
    </speak>
    """
    # f"""
    # <speak version='1.0' xml:lang='en-US'>
    #     <voice xml:lang='en-US' xml:gender='Female' name='en-US-AvaMultilingualNeural'>
    #         {'Hello, Azure, fuck you!'}
    #     </voice>
    # </speak>
    # """
    header = {
        "Ocp-Apim-Subscription-Key": config.SPEECH_KEY,
        "User-Agent": "stagefright/1.2 (Linux;Android 9.0)",
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
    }
    async with ClientSession(
        f"https://{config.SPEECH_REGION}.tts.speech.microsoft.com"
    ) as session:
        res = await session.post("/cognitiveservices/v1", data=content, headers=header)
        res.raise_for_status()
        fp = BytesIO()
        async for bytes in res.content.iter_chunked(1024):
            fp.write(bytes)
        res.close()
    return StreamingResponse(read_ram_chunk(fp), media_type=f"audio/mp3")
