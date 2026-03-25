"""List all Google Ads accounts accessible by this login."""
import json
from google.ads.googleads.client import GoogleAdsClient

DEVELOPER_TOKEN = "mwAphl3Sdh0IUMPoOf342g"

with open("scripts/gads_tokens.json") as f:
    tokens = json.load(f)

config = {
    "developer_token": DEVELOPER_TOKEN,
    "client_id": tokens["client_id"],
    "client_secret": tokens["client_secret"],
    "refresh_token": tokens["refresh_token"],
    "use_proto_plus": True,
}

client = GoogleAdsClient.load_from_dict(config)
customer_service = client.get_service("CustomerService")

try:
    accessible = customer_service.list_accessible_customers()
    print("Accessible accounts:")
    for resource_name in accessible.resource_names:
        cid = resource_name.split("/")[-1]
        print(f"  {cid}")
except Exception as e:
    print(f"Error: {e}")
