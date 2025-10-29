import tempfile, shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import yt_dlp
from .base import DownloadRequest, DownloadResult, DownloaderBackend

def _has_ffmpeg() -> bool:
    from shutil import which
    return which("ffmpeg") is not None

def _height(q: str):
    if q == "best": return None
    try: return int(q.replace("p",""))
    except: return None

def list_qualities(url: str, platform: str) -> List[str]:
    tmp = Path(tempfile.mkdtemp(prefix="q_"))
    try:
        opts = {"outtmpl": str(tmp / "%(title).200B-%(id)s.%(ext)s"),
                "quiet": True, "noplaylist": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            heights = {int(f["height"]) for f in info.get("formats", []) if f.get("height") and f.get("vcodec") not in (None,"none")}
        res = [f"{h}p" for h in sorted(heights, reverse=True)]
        return res or ["2160p","1440p","1080p","720p","480p","360p","240p","144p"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _format_candidates(platform: str, quality: str, mode: str) -> List[str]:
    if mode == "audio":
        return ["bestaudio[ext=m4a]/bestaudio/best", "bestaudio/best"]
    h = _height(quality)
    cand = []
    if _has_ffmpeg():
        if h:
            cand.append(f"bv*[height={h}][vcodec!=none]+ba[acodec!=none]/bv*[height<={h}][vcodec!=none]+ba[acodec!=none]/b[height<={h}]")
        else:
            cand.append("bestvideo[vcodec!=none]+bestaudio[acodec!=none]/best")
    if h:
        cand += [f"best[height={h}][vcodec!=none][acodec!=none]",
                 f"best[height<={h}][vcodec!=none][acodec!=none]",
                 f"best[height<={h}]"]
    cand += ["best[ext=mp4][vcodec!=none][acodec!=none]", "best[acodec!=none]", "best"]
    return cand

def _base_opts(tmp: Path, mode: str) -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "outtmpl": str(tmp / "%(title).200B-%(id)s.%(ext)s"),
        "noprogress": True, "quiet": True, "no_warnings": True, "noplaylist": True,
        "retries": 5, "fragment_retries": 10, "continuedl": True, "skip_unavailable_fragments": True,
        "concurrent_fragment_downloads": 3, "geo_bypass": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    post = []
    if mode == "audio":
        post.append({"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"320"})
    elif _has_ffmpeg():
        post.append({"key":"FFmpegVideoConvertor","preferedformat":"mp4"})
        opts["merge_output_format"] = "mp4"
    if post: opts["postprocessors"] = post
    return opts

class YtDlpBackend(DownloaderBackend):
    name = "yt-dlp"

    def download(self, req: DownloadRequest) -> DownloadResult:
        tmp = Path(tempfile.mkdtemp(prefix="dl_"))
        last_err = None
        try:
            base = _base_opts(tmp, req.mode)
            # try several format candidates
            for fmt in _format_candidates(req.platform, req.quality, req.mode):
                o = dict(base); o["format"] = fmt
                try:
                    with yt_dlp.YoutubeDL(o) as ydl:
                        info = ydl.extract_info(req.url, download=True)
                        if "requested_downloads" in info and info["requested_downloads"]:
                            p = Path(info["requested_downloads"][0]["_filename"])
                        else:
                            p = Path(ydl.prepare_filename(info))
                    if req.mode == "audio":
                        # find mp3 if created
                        mp3 = next((f for f in tmp.glob("*.mp3")), None)
                        if mp3: return DownloadResult(mp3, mp3.name)
                    if not p.exists():
                        fs = list(tmp.glob("*"))
                        if not fs: raise FileNotFoundError("no file")
                        p = max(fs, key=lambda x: x.stat().st_size)
                    return DownloadResult(p, p.name)
                except Exception as e:
                    last_err = e
                    continue
            raise last_err if last_err else RuntimeError("yt-dlp failed")
        finally:
            # keep tmp for sending; it will be cleaned by container recycle
            pass
