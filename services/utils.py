from io import BytesIO
from typing import Iterator


def iter_file(file_path: str, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    with open(file_path, mode="rb") as file_like:
        while data := file_like.read(chunk_size):
            yield data


def read_ram_chunk(ram: BytesIO, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    ram.seek(0)
    while chunk := ram.read(chunk_size):
        yield chunk
    ram.close()
