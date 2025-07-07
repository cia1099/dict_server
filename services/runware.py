if __name__ == "__main__":
    import os, sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
import json, base64
from io import BytesIO
from pathlib import Path
from datetime import datetime
from aiofiles import open
from aiohttp import ClientResponseError, ClientSession
from fastapi import HTTPException
from uuid import uuid4

from config import config


async def runware_imagen(prompt: str, steps: int = 16):
    host = "https://api.runware.ai"
    endpoint = "/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.RUNWARE_KEY}",
    }
    body = [
        {
            "taskType": "imageInference",
            "model": "civitai:4201@130072",  # "runware:100@1",
            "taskUUID": str(uuid4()),
            "positivePrompt": prompt,
            "outputType": "base64Data",
            "outputFormat": "JPG",
            "scheduler": "EULER A",
            "width": 512,  # 1024
            "height": 512,
            "steps": steps,
            "numberResults": 1,
        }
    ]
    async with ClientSession(host) as session:
        async with session.post(endpoint, json=body, headers=headers) as res:
            try:
                res.raise_for_status()
            except ClientResponseError as e:
                raise HTTPException(e.status, e.message)
            jobj: dict = await res.json()
    # print(json.dumps(jobj))
    data = jobj["data"][0]
    bytes = base64.b64decode(data["imageBase64Data"])

    return BytesIO(bytes)


if __name__ == "__main__":
    prompt = "Daylight came in through a chink between the curtains."
    # prompt = "There is an apple juice on table."
    import asyncio, time
    from PIL import Image

    tic = time.perf_counter()
    fp = asyncio.run(runware_imagen(prompt, 8))
    print("elapsed = %.2fs" % (time.perf_counter() - tic))
    img = Image.open(fp)
    img.show()
    fp.close()
