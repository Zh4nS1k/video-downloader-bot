import tempfile, shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import yt_dlp

from .base import DownloadRequest, DownloadResult, DownloaderBackend

def _has_ffmpeg() -> bool:
	from shutil import which
	return which("ffmpeg") is not None

def _height(quality: str) -> Optional[int]:
	if quality == "best":
		return None
	try:
		return int(quality.replace("p",""))
	except:
		return None

def _format_candidates(platform: str, quality: str, mode: str) -> List[str]:
	if mode == "audio":
		if platform == "youtube":
			return ["bestaudio[ext=m4a]/bestaudio/best", "bestaudio/best"]
		return ["bestaudio/best", "best"]
	if platform == "youtube":
		h = _height(quality)
		cand = []
		ffmpeg_ok = _has_ffmpeg()
		if ffmpeg_ok:
			if h:
				cand.append(f"bv*[height<={h}][vcodec!=none]+ba[acodec!=none]/b[height<={h}]")
			else:
				cand.append("bestvideo[vcodec!=none]+bestaudio[acodec!=none]/best")
		if h:
			cand.extend([
				f"best[height<={h}][vcodec!=none][acodec!=none]",
				f"best[height<={h}]"
			])
		cand.extend([
			"best[ext=mp4][vcodec!=none][acodec!=none]",
			"best[acodec!=none]",
			"best"
		])
		return cand
	# tiktok
	if quality == "best":
		return ["b/best","best"]
	h = _height(quality) or 9999
	return [f"b[height<={h}]","b","best"]

def _base_opts(tmp: Path, mode: str) -> Dict[str, Any]:
	opts: Dict[str, Any] = {
		"outtmpl": str(tmp / "%(title).200B-%(id)s.%(ext)s"),
		"noprogress": True,
		"quiet": True,
		"no_warnings": True,
		"noplaylist": True,
		"retries": 5,
		"fragment_retries": 10,
		"continuedl": True,
		"skip_unavailable_fragments": True,
		"concurrent_fragment_downloads": 3,
		"nocheckcertificate": True,
		"geo_bypass": True,
		"http_headers": {"User-Agent": "Mozilla/5.0"},
		"format_sort": ["res", "fps", "vbr", "abr", "ext:mp4:m4v:webm"] if mode != "audio" else ["abr", "asr"],
	}
	post = []
	if mode == "audio":
		post.append({"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"})
	elif _has_ffmpeg():
		post.append({"key":"FFmpegVideoConvertor","preferedformat":"mp4"})
		opts["merge_output_format"] = "mp4"
	if post:
		opts["postprocessors"] = post
	return opts

class YtDlpBackend(DownloaderBackend):
	name = "yt-dlp"

	def _extractor_args(self, platform: str, strategy: int = 1) -> Dict[str, Any]:
		"""3 стратегии для разных player_client"""
		args = {}
		if platform == "tiktok":
			args["tiktok"] = {"without_watermark":["true"]}
		if platform == "youtube":
			if strategy == 1:
				args["youtube"] = {"player_client":["android"]}
			elif strategy == 2:
				args["youtube"] = {"player_client":["web"]}
			elif strategy == 3:
				# последняя попытка без специального client
				pass
		return args

	def probe(self, req: DownloadRequest) -> Optional[int]:
		tmp = Path(tempfile.mkdtemp(prefix="probe_"))
		try:
			opts = _base_opts(tmp, req.mode)
			for strategy in (1, 2, 3):
				opts["extractor_args"] = self._extractor_args(req.platform, strategy)
				for fmt in _format_candidates(req.platform, req.quality, req.mode):
					o = dict(opts); o["format"] = fmt
					try:
						with yt_dlp.YoutubeDL(o) as ydl:
							info = ydl.extract_info(req.url, download=False)
						est = info.get("filesize") or info.get("filesize_approx")
						if not est and info.get("requested_formats"):
							est = sum((x.get("filesize") or x.get("filesize_approx") or 0) for x in info["requested_formats"])
						if est:
							return int(est)
					except Exception:
						continue
			return None
		finally:
			shutil.rmtree(tmp, ignore_errors=True)

	def download(self, req: DownloadRequest) -> DownloadResult:
		tmp = Path(tempfile.mkdtemp(prefix="dl_"))
		try:
			base = _base_opts(tmp, req.mode)
			last_err = None
			# 3 попытки с разными стратегиями
			for strategy in (1, 2, 3):
				base["extractor_args"] = self._extractor_args(req.platform, strategy)
				for fmt in _format_candidates(req.platform, req.quality, req.mode):
					o = dict(base); o["format"] = fmt
					try:
						with yt_dlp.YoutubeDL(o) as ydl:
							info = ydl.extract_info(req.url, download=True)
							if "requested_downloads" in info and info["requested_downloads"]:
								p = Path(info["requested_downloads"][0]["_filename"])
							else:
								p = Path(ydl.prepare_filename(info))
						# Ищем файл после постобработки (для аудио - ищем mp3)
						if req.mode == "audio":
							mp3 = next(iter(tmp.glob(f"{p.stem}.mp3")), None)
							if mp3 and mp3.exists():
								return DownloadResult(file_path=mp3, filename=mp3.name)
							# fallback на исходный файл если mp3 не найден
							for f in tmp.glob("*"):
								if f.suffix.lower() in (".mp3", ".m4a", ".webm", ".opus"):
									return DownloadResult(file_path=f, filename=f.name)
						if not p.exists():
							files = list(tmp.glob("*"))
							if not files:
								raise FileNotFoundError("no file")
							p = max(files, key=lambda x: x.stat().st_size)
						return DownloadResult(file_path=p, filename=p.name)
					except Exception as e:
						last_err = e
						continue
			raise last_err if last_err else RuntimeError("all formats and strategies failed")
		except:
			shutil.rmtree(tmp, ignore_errors=True)
			raise
