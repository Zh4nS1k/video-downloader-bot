import tempfile
from pathlib import Path
from pytube import YouTube
import subprocess
from .base import DownloadRequest, DownloadResult, DownloaderBackend

def _has_ffmpeg() -> bool:
    from shutil import which
    return which("ffmpeg") is not None

class PytubeBackend(DownloaderBackend):
    name = "pytube"

    def download(self, req: DownloadRequest) -> DownloadResult:
        if req.platform != "youtube":
            raise RuntimeError("pytube supports only YouTube")
        tmp = Path(tempfile.mkdtemp(prefix="yt_"))
        yt = YouTube(req.url)
        if req.mode == "audio":
            a = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            p = Path(a.download(output_path=str(tmp)))
            if _has_ffmpeg():
                out = p.with_suffix(".mp3")
                subprocess.run(["ffmpeg","-y","-i",str(p),"-codec:a","libmp3lame","-b:a","320k",str(out)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p.unlink(missing_ok=True)
                p = out
            return DownloadResult(p, p.name)
        # video
        if _has_ffmpeg():
            v = yt.streams.filter(adaptive=True, type="video").order_by("resolution").desc().first()
            a = yt.streams.filter(adaptive=True, type="audio").order_by("abr").desc().first()
            v_path = Path(v.download(output_path=str(tmp), filename="video"))
            a_path = Path(a.download(output_path=str(tmp), filename="audio")) if a else None
            out = tmp / "merged.mp4"
            cmd = ["ffmpeg","-y","-i",str(v_path)] + (["-i",str(a_path)] if a_path else []) + ["-c","copy",str(out)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return DownloadResult(out, out.name)
        else:
            s = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
            p = Path(s.download(output_path=str(tmp)))
            return DownloadResult(p, p.name)
