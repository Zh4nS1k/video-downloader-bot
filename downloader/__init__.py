from .base import DownloadRequest, DownloadResult, DownloaderBackend
from .yt_dlp_backend import YtDlpBackend, list_qualities as yt_list_qualities
from .pytube_backend import PytubeBackend
from .savefrom_backend import SaveFromBackend

BACKENDS = [YtDlpBackend(), PytubeBackend(), SaveFromBackend()]

def list_available_qualities(url: str, platform: str):
    try:
        return yt_list_qualities(url, platform)
    except Exception:
        # fallback defaults
        return ["2160p","1440p","1080p","720p","480p","360p","240p","144p"]
