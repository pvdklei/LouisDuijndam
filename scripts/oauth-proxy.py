#!/usr/bin/env python3
"""Minimal OAuth proxy for Decap CMS <-> GitHub."""
import json
import os
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
CLIENT_SECRET = os.environ["GITHUB_CLIENT_SECRET"]

CALLBACK_HTML = """<!DOCTYPE html>
<html><body><script>
(function() {
  function recieveMessage(e) {
    window.opener.postMessage(
      'authorization:PROVIDER:success:{"token":"TOKEN","provider":"PROVIDER"}',
      e.origin
    );
  }
  window.addEventListener("message", recieveMessage, false);
  window.opener.postMessage("authorizing:PROVIDER", "*");
})();
</script></body></html>"""


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/auth":
            gh_url = (
                "https://github.com/login/oauth/authorize"
                "?client_id=" + CLIENT_ID + "&scope=repo,user"
            )
            self.send_response(302)
            self.send_header("Location", gh_url)
            self.end_headers()

        elif parsed.path == "/api/auth/callback":
            code = params.get("code", [None])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                return

            data = urllib.parse.urlencode({
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
            }).encode()

            req = urllib.request.Request(
                "https://github.com/login/oauth/access_token",
                data=data,
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                token_data = json.loads(resp.read())

            token = token_data.get("access_token", "")
            html = CALLBACK_HTML.replace("TOKEN", token).replace("PROVIDER", "github")

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "4567"))
    server = HTTPServer(("127.0.0.1", port), OAuthHandler)
    print(f"OAuth proxy on 127.0.0.1:{port}")
    server.serve_forever()
