if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

import asyncio
from io import BytesIO
import json, base64
import math
from pathlib import Path
from datetime import datetime
from typing import BinaryIO
from aiofiles import open as aopen
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Body,
    Depends,
    Request,
    Response,
    HTTPException,
)
from aiohttp import ClientSession, FormData, AsyncIterablePayload

from pydub import AudioSegment

from config import config
from models.chat import ChatIn
from models.role import Role
from services.character import Character
from services.utils import read_ram_chunk, async_wrapper
from services.auth import member_auth

router = APIRouter()


@router.post("/chat/speech")
async def speech_recognize(speech: UploadFile = File(...), _=Depends(member_auth)):
    res = await azure_speech(speech)
    text = res.get("DisplayText", "")
    recognize = res["RecognitionStatus"] == "Success" and len(text) > 0
    return {
        "status": 200,
        "content": json.dumps(
            {
                "text": text,
                "recognize": recognize,
            }
        ),
    }


@router.post("/pronunciation")
async def pronunciation_word(
    word: str, req: Request, speech: UploadFile = File(...)  # , _=Depends(member_auth)
):
    pron_assessment = {
        "ReferenceText": word,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive",
        # "EnableMiscue": True,
        # "EnableProsodyAssessment": True,
    }
    pron_base64 = base64.b64encode(bytes(json.dumps(pron_assessment), "utf-8"))
    res = await azure_speech(
        speech, header={"Pronunciation-Assessment": str(pron_base64, "utf-8")}
    )
    return {"status": 200, "content": json.dumps(res)}


# async def azure_speech(req: Request, speech: bytes = Body(...)):
async def azure_speech(speech: UploadFile, header: dict = {}):
    audio_type = speech.content_type  # req.headers.get("Content-Type")
    if audio_type == "audio/mp3":
        speech = convert2wav(speech.file, format="mp3")
    elif audio_type != "audio/wav":
        return {"status": 400, "content": f"Unsupported speech file type:{audio_type}"}
    header.update(
        {
            "Ocp-Apim-Subscription-Key": config.SPEECH_KEY,
            "Content-Type": "audio/wav",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "Expect": "100-continue",
        }
    )
    # explicit set {"Transfer-Encoding": "chunked"} into aiohttp
    payload = AsyncIterablePayload(
        async_wrapper(read_ram_chunk(speech.file, chunk_size=1024)),
        content_type=header.get("Content-Type"),
    )
    async with ClientSession(
        f"https://{config.SPEECH_REGION}.stt.speech.microsoft.com"
    ) as session:
        res = await session.post(
            "/speech/recognition/conversation/cognitiveservices/v1?language=en-US&format=simple",
            data=payload,
            headers=header,
        )
    res.raise_for_status()
    jobj: dict = await res.json()
    res.close()
    # print(jobj)
    return jobj


@router.post("/chat/{vocabulary}")
async def azure_chat(
    chat: ChatIn, vocabulary: str, character: Character = Depends(member_auth)
):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    prompt = (
        chat.text
        if chat.is_help
        else f'Do I make a correct example sentence for {vocabulary}? I said "{chat.text}". Please just answer yes or no. If the answer is no, give the reasons.'
    )
    body = {
        "messages": [
            {
                "role": "system",
                "content": "You are an English tutor. Please keep patience to teach students understand and know English grammar",
            },
            {
                "role": "system",
                "content": f'You need to guide students to know how to use the vocabulary "{vocabulary}". You can\'t give any example to student, you should guide them to do it themselves',
            },
            {
                "role": "assistant",
                "content": f'Hello student. We are going to learn the word "{vocabulary}". I will watch you make a sentence or paragraph using this word.',
            },
            {"role": "user", "content": prompt},
        ]
    }
    character.raise_withdraw()

    async with ClientSession(host) as session:
        async with session.post(endpoint, json=body, headers=headers) as res:
            res.raise_for_status()
            jobj: dict = await res.json()
        # print(jobj)
    talk = jobj["choices"][0]["message"]["content"]
    created = jobj["created"]
    total_tokens = jobj["usage"]["total_tokens"]
    # print("OpenAI said:\x1b[32m%s\x1b[0m" % talk)
    micro_now = datetime.now().microsecond
    created = created * 1000 + micro_now // 1000
    # cost token
    cost_tokens = total_tokens * 2e-3
    _ = character - cost_tokens
    ans = {
        "quiz": "Yes" in talk,
        "answer": talk,
        "created": created,
        "user_id": config.CHAT_BOT_UUID,
    }
    # print(json.dumps(ans))
    # return {"status": 200, "content": json.dumps(ans)}
    return ans


def convert2wav(file: BinaryIO, format: str):
    convert: AudioSegment = AudioSegment.from_file(file, format=format)
    fp = BytesIO()
    convert.export(fp, format="wav")
    fp.seek(0)
    # with open("convert.wav", "wb") as f:
    #     f.write(fp.read())
    # fp.close()
    return UploadFile(fp)


async def test_upload(file_name: str):
    p = Path(file_name)
    form = FormData()
    form.add_field(
        "speech",
        open(file_name, "rb"),  # 打开文件以二进制形式读取
        filename=p.name,  # 指定文件名
        content_type=f"audio/{p.suffix[1:]}",  # 指定文件类型
    )
    async with ClientSession("http://127.0.0.1:8000") as session:
        async with session.post(
            "/chat/speech",
            # headers={"Content-Type": "multipart/form-data"},
            # data=await f.read(),
            data=form,
        ) as res:
            res.raise_for_status()
            jobj = await res.json()
        print(jobj)


if __name__ == "__main__":
    vocabulary = "apple"
    # prompt = "I like apple company because their products are great and legendary."
    # prompt = "I eat apple juice this morning."
    # prompt = "To eat an apple every day, you can leave doctor away"
    # prompt = "apple juice"  # correct
    # prompt = "I like the flavor of apples."  # correct
    # prompt = "Can you explain the definition of this word?"
    # prompt = "Can you give me some examples of sentences with the word apple?"
    # prompt = "I am like a peace of apple"
    prompt = "She always poop apples everyday."
    asyncio.run(azure_chat(ChatIn(text=prompt), vocabulary))

    help = "Can you give me tips to help me to do a sentence?"
    # asyncio.run(azure_chat(ChatIn(text=help, is_help=True), vocabulary))
    # asyncio.run(test_upload("audio_test/whatstheweatherlike.wav"))
    # asyncio.run(test_upload("audio_test/fuck_mom.wav"))
    # with open("audio_test/fuck_mom.m4a", "rb") as f:
    #     convert2wav(f, "m4a")
