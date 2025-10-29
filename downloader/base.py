from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

@dataclass
class DownloadRequest:
    url: str
    platform: str
    mode: str       # "video" | "audio"
    quality: str    # "best" | "1080p" | ...

@dataclass
class DownloadResult:
    file_path: Path
    filename: str
    est_size: Optional[int] = None

class DownloaderBackend:
    """Интерфейс загрузчика."""
    name: str = "base"

    def probe(self, req: DownloadRequest) -> Optional[int]:
        """Вернуть примерный размер (байты) или None, если не удалось оценить."""
        return None

    def download(self, req: DownloadRequest) -> DownloadResult:
        """Скачать и вернуть путь к файлу. Бросает исключение при неудаче."""
        raise NotImplementedError
