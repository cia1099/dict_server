if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

import asyncio
from io import BytesIO
import json
from pathlib import Path
from datetime import datetime
from typing import IO
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
from aiohttp import ClientSession, FormData
from pydub import AudioSegment
from __init__ import config
from models.chat import ChatIn

router = APIRouter()


@router.post("/chat/speech")
# async def azure_speech(req: Request, speech: bytes = Body(...)):
async def azure_speech(speech: UploadFile = File(...)):
    audio_type = speech.content_type  # req.headers.get("Content-Type")
    if audio_type == "audio/mp3":
        speech = convert2wav(speech.file, format="mp3")
    elif audio_type != "audio/wav":
        return {"status": 400, "content": f"Unsupported speech file type:{audio_type}"}
    header = {
        "Ocp-Apim-Subscription-Key": config.SPEECH_KEY,
        "Content-Type": "audio/wav",
    }
    async with ClientSession(
        f"https://{config.SPEECH_REGION}.stt.speech.microsoft.com"
    ) as session:
        res = await session.post(
            "/speech/recognition/conversation/cognitiveservices/v1?language=en-US&format=simple",
            data=await speech.read(),
            headers=header,
        )
        res.raise_for_status()
        jobj: dict = await res.json()
        # print(jobj)
    return {
        "status": 200,
        "content": json.dumps(
            {
                "text": jobj.get("DisplayText", "Recognized speech fail"),
                "recognize": jobj["RecognitionStatus"] == "Success",
            }
        ),
    }


@router.post("/chat/{vocabulary}")
async def azure_chat(chat: ChatIn, vocabulary: str):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    prompt = (
        chat.text
        if chat.is_help
        else f"Does he make a correct example sentence for {vocabulary}? He said '{chat.text}'. Please just answer yes or no. If the answer is no, give the reasons."
    )
    body = {
        "messages": [
            {
                "role": "system",
                "content": "You are an English tutor. Please keep patience to teach students understand and know English grammar",
            },
            {
                "role": "system",
                "content": f"You need to guide students to know how to use the vocabulary '{vocabulary}'. You can't give any example to student, you should guide them to do it themselves",
            },
            {
                "role": "assistant",
                "content": f"Hello Students. We are going to learn the word '{vocabulary}'. I will watch you make a sentence or paragraph using this word.",
            },
            {"role": "user", "content": prompt},
        ]
    }
    async with ClientSession(host) as session:
        res = await session.post(endpoint, json=body, headers=headers)
        jobj: dict = await res.json()
        # print(jobj)
        talk = jobj["choices"][0]["message"]["content"]
        created = jobj["created"]
        # print("OpenAI said:\x1b[32m%s\x1b[0m" % talk)
    micro_now = datetime.now().microsecond
    created = created * 1000 + micro_now // 1000
    ans = {
        "quiz": "Yes" in talk,
        "answer": talk,
        "created": created,
        "user_id": config.CHAT_BOT_UUID,
    }
    # print(json.dumps(ans))
    # return {"status": 200, "content": json.dumps(ans)}
    return ans


def convert2wav(file: IO[bytes], format: str):
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
        res = await session.post(
            "/chat/speech",
            # headers={"Content-Type": "multipart/form-data"},
            # data=await f.read(),
            data=form,
        )
        jobj = await res.json()
        print(jobj)


if __name__ == "__main__":
    vocabulary = "apple"
    # prompt = "I like apple company because their products are great and legendary."
    # prompt = "I eat apple juice this morning."
    # prompt = "apple juice"  # correct
    # prompt = "I like the flavor of apples."  # correct
    # prompt = "Can you explain the definition of this word?"
    # prompt = "Can you give me some examples of sentences with the word apple?"
    # prompt = "I am like a peace of shit"
    # prompt = "She always poop apples everyday."
    # asyncio.run(chat_azure(ChatIn(text=prompt), vocabulary))

    help = "Can you give me tips to help me to do a sentence?"
    # asyncio.run(azure_chat(ChatIn(text=help, is_help=True), vocabulary))
    # asyncio.run(test_upload("audio_test/whatstheweatherlike.wav"))
    asyncio.run(test_upload("audio_test/fuck_mom.wav"))
    # with open("audio_test/fuck_mom.m4a", "rb") as f:
    #     convert2wav(f, "m4a")
