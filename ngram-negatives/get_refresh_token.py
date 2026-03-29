#!/usr/bin/env python3
"""
One-time OAuth flow to get a Google Ads API refresh token.

1. Opens a browser for you to sign in with marketing@jetfuel.agency
2. Captures the auth code via a local HTTP server
3. Exchanges it for a refresh token
4. Saves it to .env as GOOGLE_ADS_REFRESH_TOKEN
"""

import http.server
import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR.parent.parent.parent / ".env"

# Use the same OAuth client as workspace-mcp
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8765/oauth2callback"
SCOPE = "https://www.googleapis.com/auth/adwords"

auth_code = None


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        auth_code = params.get("code", [""])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Success! You can close this window.</h2><p>Refresh token is being saved...</p>")

    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    # Build the OAuth URL
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    })
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{params}"

    print(f"\nOpening browser for Google Ads authorization...")
    print(f"Sign in with: marketing@jetfuel.agency\n")
    webbrowser.open(auth_url)

    # Start local server to capture the redirect
    server = http.server.HTTPServer(("localhost", 8765), OAuthHandler)
    print("Waiting for authorization...")
    server.handle_request()

    if not auth_code:
        print("ERROR: No auth code received.", file=sys.stderr)
        sys.exit(1)

    # Exchange code for refresh token
    print("Exchanging auth code for refresh token...")
    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("ERROR: No refresh token in response.", file=sys.stderr)
        print(json.dumps(tokens, indent=2))
        sys.exit(1)

    # Save to .env
    env_content = ENV_PATH.read_text()
    if "GOOGLE_ADS_REFRESH_TOKEN=" in env_content:
        # Replace existing
        lines = env_content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("GOOGLE_ADS_REFRESH_TOKEN="):
                new_lines.append(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
            else:
                new_lines.append(line)
        ENV_PATH.write_text("\n".join(new_lines) + "\n")
    else:
        # Append
        with open(ENV_PATH, "a") as f:
            f.write(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}\n")

    print(f"\nRefresh token saved to .env")
    print("You can now run: python ngram_miner.py --mode mine")


if __name__ == "__main__":
    main()
