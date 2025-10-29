from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class DownloadRequest:
    url: str
    platform: str  # 'youtube' | 'tiktok'
    mode: str      # 'video' | 'audio'
    quality: str   # 'best' or '1080p' etc.

@dataclass
class DownloadResult:
    file_path: Path
    filename: str
    est_size: Optional[int] = None

class DownloaderBackend:
    name: str = "base"
    def probe(self, req: DownloadRequest) -> Optional[int]:
        return None
    def download(self, req: DownloadRequest) -> DownloadResult:
        raise NotImplementedError
