import json
import time
import urllib.request

RUN_ID = "41486857863"  # build-apk @ v2.0.3
API = f"https://api.github.com/repos/liao-2004/MAA-hunDang/actions/runs/{RUN_ID}"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "doubao-agent"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


deadline = time.time() + 1200
while time.time() < deadline:
    run = get(API)
    status = run["status"]
    if status == "completed":
        print(f"COMPLETED conclusion={run.get('conclusion')}")
        print(run["html_url"])
        jobs = get(run["jobs_url"])
        for job in jobs["jobs"]:
            print(f"  job {job['name']:<28} {job['status']} {job.get('conclusion')}")
            for step in job.get("steps", []):
                print(f"    step {step['name'][:60]:<62} {step['status']} {step.get('conclusion')}")
        break
    print(f"polling... status={status} ({time.strftime('%H:%M:%S')})")
    time.sleep(30)
else:
    print("TIMEOUT still running")
