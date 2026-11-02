import json

data = json.load(open(r"C:\Users\18111\Desktop\maah\MAA-hunDang\ci-runs.json", encoding="utf-8-sig"))
for run in data["workflow_runs"][:10]:
    print(
        f"{run['created_at']}  {run['name']:<10} branch={run['head_branch']:<6} "
        f"status={run['status']:<10} conclusion={run.get('conclusion')}  id={run['id']}"
    )
