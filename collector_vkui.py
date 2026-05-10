#!/usr/bin/env python3
import requests, re, time, csv, os

OWNER = "VKCOM"
REPO = "VKUI"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
SINCE = "2024-01-01"
UNTIL = "2026-04-30"
DELAY = 0.5
ISSUE_RE = re.compile(r"#(\d+)")
FIXES_RE = re.compile(r"(?:fix|fixes|close|closes)[\s#:]*(#?\d+)", re.I)

def api_get(url, label):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - int(time.time()), 0) + 5
            print(f"  [{label}] Rate limit! Ждём {wait} сек...")
            time.sleep(wait)
            return None
        if resp.status_code != 200:
            print(f"  [{label}] HTTP {resp.status_code}")
            return None
        return resp.json()
    except Exception as e:
        print(f"  [{label}] Exception: {e}")
        return None

def fetch_issues():
    issues = []
    page = 1
    print("[Issues] Сбор...")
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues?state=all&since={SINCE}T00:00:00Z&per_page=100&page={page}"
        batch = api_get(url, "Issues")
        if batch is None:
            continue
        if not batch:
            break
        for item in batch:
            if "pull_request" in item:
                continue
            issues.append({
                "issue_number": item.get("number"),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "created_at": item.get("created_at", ""),
                "closed_at": item.get("closed_at", ""),
                "author": item.get("user", {}).get("login", ""),
                "assignee": item.get("assignee", {}).get("login", "") if item.get("assignee") else "",
                "labels": ",".join([l["name"] for l in item.get("labels", [])]),
            })
        if len(batch) < 100:
            break
        page += 1
        print(f"  Собрано issues: {len(issues)}")
        time.sleep(DELAY)
    return issues

def fetch_commits():
    commits = []
    page = 1
    print("[Commits] Сбор...")
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits?since={SINCE}T00:00:00Z&until={UNTIL}T23:59:59Z&per_page=100&page={page}"
        batch = api_get(url, "Commits")
        if batch is None:
            continue
        if not batch:
            break
        for item in batch:
            commit = item.get("commit", {})
            author = commit.get("author", {})
            msg = commit.get("message", "")
            match = ISSUE_RE.search(msg)
            commits.append({
                "sha": item.get("sha", "")[:12],
                "message": msg,
                "author_name": author.get("name", ""),
                "author_email": author.get("email", ""),
                "commit_date": author.get("date", ""),
                "issue_number": int(match.group(1)) if match else None,
            })
        if len(batch) < 100:
            break
        page += 1
        print(f"  Собрано commits: {len(commits)}")
        time.sleep(DELAY)
    return commits

def fetch_prs():
    prs = []
    page = 1
    print("[PRs] Сбор...")
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=all&per_page=100&page={page}"
        batch = api_get(url, "PRs")
        if batch is None:
            continue
        if not batch:
            break
        for item in batch:
            body = item.get("body") or ""
            match = FIXES_RE.search(body)
            prs.append({
                "pr_number": item.get("number"),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "created_at": item.get("created_at", ""),
                "merged_at": item.get("merged_at", ""),
                "closed_at": item.get("closed_at", ""),
                "author": item.get("user", {}).get("login", ""),
                "issue_number": int(match.group(1).replace("#", "")) if match else None,
            })
        if len(batch) < 100:
            break
        page += 1
        print(f"  Собрано PRs: {len(prs)}")
        time.sleep(DELAY)
    return prs

def save_csv(data, filename):
    if not data:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"[Сохранено] {filename}: {len(data)} строк")

def main():
    print("=" * 50)
    print(f"ETL: {OWNER}/{REPO}")
    print("=" * 50)
    issues = fetch_issues()
    commits = fetch_commits()
    prs = fetch_prs()
    save_csv(issues, "/opt/airflow/scripts/vkui_raw_issues.csv")
    save_csv(commits, "/opt/airflow/scripts/vkui_raw_commits.csv")
    save_csv(prs, "/opt/airflow/scripts/vkui_raw_prs.csv")
    linked = sum(1 for c in commits if c.get("issue_number"))
    print(f"\nИТОГО: Issues {len(issues)}, Commits {len(commits)} (linked {linked}), PRs {len(prs)}")

if __name__ == "__main__":
    main(