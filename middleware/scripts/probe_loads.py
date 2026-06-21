import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path("src")))

from common.tms_client import TMSClient
from common.tms_faults import TMSError

client = TMSClient(
    host=os.environ.get("TMS_HOST", "tramway.proxy.rlwy.net"),
    port=int(os.environ.get("TMS_PORT", "17159")),
    auth_token=os.environ.get("TMS_AUTH_TOKEN", "hr-fde-cristinasandoval-2026"),
)

queries = [
    ("solo EQTYPE:DRY_VAN", {"EQTYPE": "DRY_VAN"}),
    ("solo ORIG_STATE:GA", {"ORIG_STATE": "GA"}),
    ("Miami REEFER (ejemplo del manual)", {"ORIG_CITY": "Miami", "EQTYPE": "REEFER"}),
    ("GA->TX DRY_VAN (sin MAX_RESULTS)", {"ORIG_STATE": "GA", "DEST_STATE": "TX", "EQTYPE": "DRY_VAN"}),
    ("solo DEST_STATE:TX", {"DEST_STATE": "TX"}),
]

for label, filters in queries:
    try:
        loads = client.load_query(filters, retries=1)
        print(f"[{label}] -> {len(loads)} resultado(s)")
        for l in loads[:3]:
            print("   ", l.get("LOAD_ID"), l.get("ORIG_CITY","").strip(), "->", l.get("DEST_CITY","").strip(), l.get("EQTYPE","").strip())
    except TMSError as exc:
        print(f"[{label}] -> ERROR: {exc}")
