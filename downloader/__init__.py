from .base import DownloadRequest, DownloadResult, DownloaderBackend
from .yt_dlp_backend import YtDlpBackend
from .pytube_backend import PytubeBackend

try:
	from .savefrom_backend import SaveFromBackend
	BACKENDS = [YtDlpBackend(), PytubeBackend(), SaveFromBackend()]  # порядок = приоритет
except ImportError:
	BACKENDS = [YtDlpBackend(), PytubeBackend()]  # без savefrom если нет requests
