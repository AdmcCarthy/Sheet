"""Spike A / parity reference: render a 1:1 window of a Relief demo texture with Relief's own WebGL shader in
headless Chromium. Usage: webgl_ref.py RELIEF_DIR REGION OUT.png X0 Y0 W H   (texel units)."""

import functools
import http.server
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

relief, region, out = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
x0, y0, w, h = (int(v) for v in sys.argv[4:8])
HTML = """<!doctype html><meta charset=utf-8><canvas id=c></canvas><script type=module>
import { createRenderer, loadImage } from '/preview/relief.js';
import { detunedStyle } from '/preview/palette.js';
window.run = async (region, x0, y0, w, h) => {
  const d = `/data/out/${region}/demo/`;
  const meta = await (await fetch(d + 'meta.json')).json();
  const [elev, zones] = await Promise.all([loadImage(d + 'elev.webp'), loadImage(d + 'zones.png')]);
  const r = createRenderer(); const [W, H] = meta.size;
  const c = document.getElementById('c'); c.width = w; c.height = h;
  const t = r.draw(c, { key: region, elev, ice: null, zones, size: meta.size, cell: meta.cell, base: meta.encoding.base, step: meta.encoding.step,
    view: [x0 / W, y0 / H, (x0 + w) / W, (y0 + h) / H] }, detunedStyle('light'));
  return { ms: t, png: c.toDataURL('image/png') };
};
document.title = 'ready';
</script>"""


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/_harness"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
            return
        super().do_GET()


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(relief)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/_harness"
with sync_playwright() as pw:
    b = pw.chromium.launch(
        args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
    )
    p = b.new_page()
    p.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
    p.on("pageerror", lambda e: print("pageerror:", e))
    p.goto(url)
    p.wait_for_function("window.run !== undefined", timeout=20000)
    t = time.perf_counter()
    r = p.evaluate(f"window.run('{region}', {x0}, {y0}, {w}, {h})")
    import base64

    Path(out).write_bytes(base64.b64decode(r["png"].split(",")[1]))
    print("draw ms", round(r["ms"]), "wall s", round(time.perf_counter() - t, 1))
    b.close()
