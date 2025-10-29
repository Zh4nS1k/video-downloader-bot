from pathlib import Path
import tempfile, shutil
from pytube import YouTube
from .base import DownloadRequest, DownloadResult, DownloaderBackend

class PytubeBackend(DownloaderBackend):
    name = "pytube"

    def probe(self, req: DownloadRequest):
        if req.platform != "youtube": return None
        try:
            yt = YouTube(req.url)
            if req.mode == "audio":
                s = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            else:
                # progressive, чтобы не нужен был ffmpeg
                s = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
            return int(getattr(s, "filesize", None) or 0) or None
        except Exception:
            return None

    def download(self, req: DownloadRequest) -> DownloadResult:
        if req.platform != "youtube":
            raise RuntimeError("Pytube supports only YouTube")
        tmp = Path(tempfile.mkdtemp(prefix="yt_"))
        try:
            yt = YouTube(req.url)
            if req.mode == "audio":
                s = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            else:
                s = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
            p = Path(s.download(output_path=str(tmp)))
            return DownloadResult(file_path=p, filename=p.name)
        except:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
