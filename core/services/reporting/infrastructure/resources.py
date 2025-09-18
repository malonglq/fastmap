from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


class AssetManager:
    """Manages local/static assets and builds CDN fallback loader snippets.

    - Copies local vendor assets into an output `static/` directory.
    - Generates a <script> snippet that attempts local, then falls back to CDN URLs.
    """

    def __init__(self) -> None:
        self.manifest: Dict[str, Dict[str, object]] = {
            'chartjs': {
                'filename': 'chart.umd.min.js',
                'local_candidates': [
                    Path('core') / 'services' / 'vendor' / 'chart.umd.min.js',
                    Path('vendor') / 'chart.umd.min.js',
                ],
                'cdn': [
                    'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
                    'https://unpkg.com/chart.js@4.4.1/dist/chart.umd.min.js',
                    'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js',
                ],
            },
        }

    # ---------------- Copy assets -----------------
    def ensure_assets(self, output_dir: Path, keys: Optional[List[str]] = None) -> None:
        """Copy available local assets under `static/` next to the output file.

        Creates placeholders if no local candidate exists, so the loader will use CDN.
        """
        keys = keys or list(self.manifest.keys())
        static_dir = Path(output_dir) / 'static'
        static_dir.mkdir(parents=True, exist_ok=True)

        for key in keys:
            entry = self.manifest.get(key)
            if not entry:
                continue
            filename: str = entry['filename']  # type: ignore[assignment]
            local_candidates: List[Path] = entry.get('local_candidates', [])  # type: ignore[assignment]
            target = static_dir / filename

            src = None
            for cand in local_candidates:
                if Path(cand).exists():
                    src = cand
                    break
            if src is not None:
                if (not target.exists()) or target.stat().st_size == 0:
                    target.write_bytes(Path(src).read_bytes())
            else:
                # Write a small placeholder to make local load attempt harmless
                if not target.exists():
                    target.write_text(
                        f"/* placeholder: {filename} not bundled; CDN fallback will be used. */",
                        encoding='utf-8'
                    )

    # ---------------- Loader script -----------------
    def build_loader_script_tag(self, key: str) -> str:
        """Return a <script> tag that defines a CDN fallback loader and tries local first."""
        entry = self.manifest.get(key)
        if not entry:
            return ''
        filename: str = entry['filename']  # type: ignore[assignment]
        cdn: List[str] = entry.get('cdn', [])  # type: ignore[assignment]
        urls = [f"static/{filename}"] + cdn
        # inline loader function + invocation
        urls_js = ',\n        '.join([f"'{u}'" for u in urls])
        return (
            "<script>\n"
            "(function(){\n"
            "  window.__assetReady = window.__assetReady || {};\n"
            "  function loadScriptWithFallback(urls, onload){\n"
            "    if(!urls||urls.length===0){ if(onload) onload(); return; }\n"
            "    var head=urls[0]; var tail=urls.slice(1); var s=document.createElement('script');\n"
            "    s.src=head; s.onload=onload; s.onerror=function(){loadScriptWithFallback(tail,onload);};\n"
            "    document.head.appendChild(s);\n"
            "  }\n"
            f"  loadScriptWithFallback([\n        {urls_js}\n      ], function(){{\n"
            f"    window.__assetReady['{key}']=true;\n"
            f"    try{{ document.dispatchEvent(new CustomEvent('asset:ready:{key}')); }}catch(e){{}}\n"
            "  });\n"
            "})();\n"
            "</script>"
        )



