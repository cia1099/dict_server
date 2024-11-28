if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

import asyncio
from io import BytesIO
from pathlib import Path
from aiofiles import open
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from aiohttp import ClientSession
from fastapi.responses import StreamingResponse
from __init__ import config

router = APIRouter()


async def chat_azure(prompt: str, vocabulary: str, isHelp=False):
    host = "https://imagener.openai.azure.com"
    endpoint = "/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": config.AZURE_OPENAI_API_KEY,
    }
    if not isHelp:
        prompt = f"Does he make a correct example sentence for {vocabulary}? He said '{prompt}'. Please just answer yes or no. If the answer is no, give the reasons."
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
        print("OpenAI said:\x1b[32m%s\x1b[0m" % talk)


if __name__ == "__main__":
    vocabulary = "apple"
    # prompt = "I like apple company because their products are great and legendary."
    # prompt = "I eat apple juice this morning."
    # prompt = "apple juice"  # correct
    # prompt = "I like the flavor of apples."  # correct
    # prompt = "Can you explain the definition of apple?"
    # prompt = "Can you give me some examples of sentences with the word apple?"
    prompt = "I am like a peace of shit"
    # prompt = "She always poop apples everyday."
    asyncio.run(chat_azure(prompt, vocabulary))

    # help = "Can you give me tips to help me to do a sentence?"
    # asyncio.run(chat_azure(help, vocabulary, isHelp=True))
    # check = f"Does he make a correct example sentence for {vocabulary}? He has written '{prompt}'. Please answer yes or no and give reasons."
    # asyncio.run(chat_azure(check, vocabulary))
