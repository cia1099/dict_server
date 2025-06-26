import json, base64, os
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

from io import BytesIO
from pathlib import Path
from datetime import datetime
from aiofiles import open
from aiohttp import ClientSession
from fastapi import HTTPException

from PIL import Image

from config import config


async def vertex_imagen(prompt: str) -> BytesIO:
    locate = "asia-east1"  # "us-central1"
    host = f"https://{locate}-aiplatform.googleapis.com"
    model = "imagen-3.0-fast-generate-001"  # "imagegeneration@002"outdate 9/24/2025
    endpoint = f"/v1/projects/china-wall-over/locations/{locate}/publishers/google/models/{model}:predict"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "enhancePrompt": False,
            "safetySetting": "block_few",
        },
    }

    credentials = Credentials.from_service_account_file(
        config.GCLOUD_SERVICE_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    # print(f"get token = {credentials.token}")
    headers.update({"Authorization": f"Bearer {credentials.token}"})

    async with ClientSession(host) as session:
        async with session.post(endpoint, json=body, headers=headers) as res:
            res.raise_for_status()
            jobj: dict = await res.json()
    pred = jobj.get("predictions")
    if pred:
        bytes = base64.b64decode(pred[0]["bytesBase64Encoded"])
        fp = BytesIO(bytes)
        # pred[0].update({"bytesBase64Encoded": None})
        # print(json.dumps(pred, indent=4))
    else:
        # print(json.dumps(jobj, indent=4))
        # from router.img import generate_error_img
        # fp = generate_error_img(jobj["error"]["message"])
        err = jobj["error"]
        raise HTTPException(jobj["code"], err["message"])

    if pred and __name__ == "__main__":
        img = Image.open(fp)
        img.show()

    return fp


async def create_punch_cards(filename: str):
    locate = "asia-east1"  # "us-central1"
    host = f"https://{locate}-aiplatform.googleapis.com"
    model = "imagen-3.0-generate-002"
    endpoint = f"/v1/projects/china-wall-over/locations/{locate}/publishers/google/models/{model}:predict"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    prompt = "Generate cute animals to encourage people to finish daily task\
            of memorizing vocabulary.\nThe slogan could be:\n\
            AI Vocabulary Punch Card\nMemorize words\nI'm memorizing words with AI Vocabulary, punch with me!"
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 7,
            "aspectRatio": "3:4",
            "personGeneration": "dont_allow",
            "enhancePrompt": False,
        },
    }

    credentials = Credentials.from_service_account_file(
        config.GCLOUD_SERVICE_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    headers.update({"Authorization": f"Bearer {credentials.token}"})

    async with ClientSession(host) as session:
        async with session.post(endpoint, json=body, headers=headers) as res:
            res.raise_for_status()
            jobj: dict = await res.json()
    preds = jobj.get("predictions")
    if preds:
        gen_byte = (base64.b64decode(pred["bytesBase64Encoded"]) for pred in preds)
        f_ptrs = (BytesIO(byte) for byte in gen_byte)
        for i, fp in enumerate(f_ptrs):
            async with open(f"punch_card/{filename}_{i:02}.png", "wb") as f:
                await f.write(fp.getvalue())
    else:
        error = jobj["error"]
        raise HTTPException(error["code"], error["message"])
    remove_past3month_cards()


def remove_past3month_cards():
    def past3months():
        now = datetime.now()
        this_year = now.year
        this_month = now.month
        for i in range(3, 6):
            month = this_month - i + (12 if this_month <= i else 0)
            year = this_year + (-1 if this_month <= i else 0)
            yield f"{year}{month:02}"

    for m in past3months():
        os.system(f"rm -f punch_card/{m}*.png")
        # for file in Path("punch_card").glob(f"{m}*.png"):
        #     file.unlink(missing_ok=True)
