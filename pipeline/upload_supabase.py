# data/web/의 예측·설비 JSON을 수파베이스 documents 표에 올리는 스크립트 (.env의 SUPABASE_URL, SUPABASE_ANON_KEY 사용)
import json
import os
import sys
import urllib.request


def _env():
    env = {}
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    return {**env, **os.environ}


def upsert_document(url, key, name, data):
    body = json.dumps({"key": name, "data": data}, ensure_ascii=False).encode("utf8")
    req = urllib.request.Request(
        f"{url}/rest/v1/documents?on_conflict=key", data=body, method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status


if __name__ == "__main__":
    env = _env()
    url, key = env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"]
    web_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "web")
    for name in ["forecast", "machines"]:
        data = json.load(open(os.path.join(web_dir, f"{name}.json"), encoding="utf8"))
        print(name, "→", upsert_document(url, key, name, data))
