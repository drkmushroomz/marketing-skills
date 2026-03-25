"""Find the MCC that manages account 909-908-1672."""
import json
from google.ads.googleads.client import GoogleAdsClient

DEVELOPER_TOKEN = "mwAphl3Sdh0IUMPoOf342g"
TARGET = "9099081672"

with open("scripts/gads_tokens.json") as f:
    tokens = json.load(f)

accessible = ["3681115524", "1874174744", "6123946535", "1331263092", "2474830596", "2006547901"]

for mcc_id in accessible:
    config = {
        "developer_token": DEVELOPER_TOKEN,
        "client_id": tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "login_customer_id": mcc_id,
        "use_proto_plus": True,
    }
    client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    # Try to query the target account using this MCC as login
    query = "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"
    try:
        response = ga_service.search_stream(customer_id=TARGET, query=query)
        for batch in response:
            for row in batch.results:
                print(f"SUCCESS! MCC {mcc_id} can access {TARGET}")
                print(f"  Account name: {row.customer.descriptive_name}")
                print(f"  Account ID: {row.customer.id}")
        break
    except Exception as e:
        err_msg = str(e)
        if "PERMISSION_DENIED" in err_msg or "USER_PERMISSION_DENIED" in err_msg:
            print(f"  {mcc_id} - no access to {TARGET}")
        else:
            print(f"  {mcc_id} - error: {err_msg[:100]}")
