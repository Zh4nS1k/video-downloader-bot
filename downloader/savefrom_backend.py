import tempfile, requests, re, json
from pathlib import Path
from .base import DownloadRequest, DownloadResult, DownloaderBackend

class SaveFromBackend(DownloaderBackend):
    name = "savefrom"

    def download(self, req: DownloadRequest) -> DownloadResult:
        tmp = Path(tempfile.mkdtemp(prefix="sf_"))
        url = req.url
        headers = {"User-Agent": "Mozilla/5.0"}

        # try simple API (may change often)
        dl = None
        try:
            resp = requests.post("https://api.savefrom.net/v1/source/convert", json={"url": url},
                                 headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                links = data.get("links", []) or data.get("data", {}).get("links", [])
                if links:
                    if req.mode == "audio":
                        for l in links:
                            if "audio" in (l.get("type") or "") or "audio" in (l.get("format") or ""):
                                dl = l.get("url") or l.get("downloadUrl"); break
                    if not dl:
                        dl = links[0].get("url") or links[0].get("downloadUrl")
        except Exception:
            pass

        if not dl:
            # fallback: parse page
            page = requests.get(f"https://savefrom.net/#url={url}", headers=headers, timeout=20)
            m = re.findall(r'(https?://[^"\s]+\.(?:mp4|webm|mp3|m4a)[^"\s]*)', page.text)
            if m: dl = m[0]

        if not dl:
            raise RuntimeError("savefrom: no link")

        r = requests.get(dl, stream=True, timeout=60, headers=headers)
        r.raise_for_status()
        # guess ext
        ct = r.headers.get("Content-Type","")
        ext = ".mp3" if req.mode == "audio" else ".mp4"
        if "webm" in ct: ext = ".webm"
        out = tmp / f"download{ext}"
        with out.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        return DownloadResult(out, out.name)
