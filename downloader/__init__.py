from .base import DownloadRequest, DownloadResult, DownloaderBackend
from .yt_dlp_backend import YtDlpBackend
from .pytube_backend import PytubeBackend

BACKENDS = [YtDlpBackend(), PytubeBackend()]  # порядок = приоритет
