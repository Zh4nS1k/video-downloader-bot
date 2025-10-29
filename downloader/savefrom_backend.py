import tempfile, shutil, requests
from pathlib import Path
from typing import Optional
import re
import json

from .base import DownloadRequest, DownloadResult, DownloaderBackend

class SaveFromBackend(DownloaderBackend):
	"""Резервный бэкенд через savefrom.net"""
	name = "savefrom"

	def probe(self, req: DownloadRequest) -> Optional[int]:
		return None  # SaveFrom не поддерживает probe

	def download(self, req: DownloadRequest) -> DownloadResult:
		"""Скачивание через savefrom.net"""
		tmp = Path(tempfile.mkdtemp(prefix="sf_"))
		try:
			url = req.url
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
				"Accept-Language": "en-US,en;q=0.5",
			}
			
			# Пробуем несколько вариантов API
			download_url = None
			
			# Вариант 1: Прямой парсинг страницы
			try:
				sf_url = f"https://savefrom.net/#url={url}"
				page_resp = requests.get(sf_url, headers=headers, timeout=20, allow_redirects=True)
				
				# Ищем JSON данные в странице
				json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', page_resp.text, re.DOTALL)
				if json_match:
					page_data = json.loads(json_match.group(1))
					download_url = page_data.get("downloadUrl") or page_data.get("url")
				
				# Ищем прямые ссылки на скачивание
				if not download_url:
					matches = re.findall(r'(https?://[^"\s]+\.(?:mp4|mp3|m4a|webm)[^"\s]*)', page_resp.text)
					if matches:
						download_url = matches[0]
			except Exception:
				pass
			
			# Вариант 2: API endpoint (если есть)
			if not download_url:
				try:
					api_url = "https://api.savefrom.net/v1/source/convert"
					api_resp = requests.post(
						api_url,
						json={"url": url},
						headers={"User-Agent": headers["User-Agent"], "Content-Type": "application/json"},
						timeout=20
					)
					if api_resp.status_code == 200:
						data = api_resp.json()
						links = data.get("links", []) or data.get("data", {}).get("links", [])
						if links:
							if req.mode == "audio":
								for link in links:
									if link.get("type") == "audio" or "audio" in str(link.get("format", "")).lower():
										download_url = link.get("url") or link.get("downloadUrl")
										break
							if not download_url and links:
								download_url = links[0].get("url") or links[0].get("downloadUrl")
				except Exception:
					pass
			
			if not download_url:
				raise RuntimeError("Не удалось получить ссылку через SaveFrom")
			
			# Скачиваем файл
			file_resp = requests.get(download_url, stream=True, timeout=60, headers=headers)
			file_resp.raise_for_status()
			
			# Определяем расширение
			content_type = file_resp.headers.get("Content-Type", "")
			if req.mode == "audio":
				ext = ".mp3"
			elif "video/mp4" in content_type:
				ext = ".mp4"
			elif "video/webm" in content_type:
				ext = ".webm"
			else:
				ext = Path(download_url.split('?')[0]).suffix or (".mp3" if req.mode == "audio" else ".mp4")
			
			output_file = tmp / f"download{ext}"
			
			with output_file.open('wb') as f:
				for chunk in file_resp.iter_content(chunk_size=8192):
					if chunk:
						f.write(chunk)
			
			if not output_file.exists() or output_file.stat().st_size == 0:
				raise RuntimeError("Скачанный файл пуст")
			
			return DownloadResult(file_path=output_file, filename=output_file.name)
		except Exception as e:
			shutil.rmtree(tmp, ignore_errors=True)
			raise RuntimeError(f"SaveFrom error: {str(e)}")

