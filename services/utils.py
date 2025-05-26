from io import BytesIO
from typing import Iterator, BinaryIO, AsyncIterator, TypeVar
import time, asyncio

T = TypeVar("T")


def iter_file(file_path: str, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    with open(file_path, mode="rb") as file_like:
        while data := file_like.read(chunk_size):
            yield data


def read_ram_chunk(
    ram: BytesIO | BinaryIO, chunk_size: int = 1024 * 1024
) -> Iterator[bytes]:
    ram.seek(0)
    while chunk := ram.read(chunk_size):
        yield chunk
    ram.close()


async def async_wrapper(sync_gen: Iterator[T]) -> AsyncIterator[T]:
    for chunk in sync_gen:
        yield chunk
        await asyncio.sleep(1e-9)  # 让出控制权


def wav_chunk(audio_source: BinaryIO, chunk_size=1024) -> Iterator[bytes]:
    # audio_source.seek(0)
    yield WaveHeader16K16BitMono
    while chunk := audio_source.read(chunk_size):
        time.sleep(chunk_size / 32000)  # to simulate human speaking rate
        yield chunk
    audio_source.close()


WaveHeader16K16BitMono = bytes(
    [
        82,
        73,
        70,
        70,
        78,
        128,
        0,
        0,
        87,
        65,
        86,
        69,
        102,
        109,
        116,
        32,
        18,
        0,
        0,
        0,
        1,
        0,
        1,
        0,
        128,
        62,
        0,
        0,
        0,
        125,
        0,
        0,
        2,
        0,
        16,
        0,
        0,
        0,
        100,
        97,
        116,
        97,
        0,
        0,
        0,
        0,
    ]
)
