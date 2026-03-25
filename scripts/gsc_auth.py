"""
OAuth2 flow for Google Search Console API access.
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/adwords",
]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
creds = flow.run_local_server(port=8080, prompt="consent")

token_data = {
    "refresh_token": creds.refresh_token,
    "access_token": creds.token,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}
with open("scripts/gads_tokens.json", "w") as f:
    json.dump(token_data, f, indent=2)
print("Tokens saved with both Google Ads + Search Console scopes.")
