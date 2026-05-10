#!/usr/bin/env python3
import requests, re, time, os
from datetime import datetime
from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv('/opt/airflow/.env')

OWNER = "VKCOM"
REPO = "VKUI"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
SINCE = "2024-01-01"
UNTIL = "2026-04-30"
DELAY = 0.5
ISSUE_RE = re.compile(r"#(\d+)")
FIXES_RE = re.compile(r"(?:fix|fixes|close|closes)[\s#:]*(#?\d+)", re.I)

ch = Client(host='clickhouse', port=9000, database='github_metrics')
LAST_RUN_FILE = "/opt/airflow/scripts/last_run.txt"

def get_last_run_date():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            return f.read().strip()
    return "2024-01-01"

def save_last_run_date():
    today = datetime.now().strftime("%Y-%m-%d")
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(today)

def api_get(url, label):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 403:
            reset = int(resp.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - int(time.time()), 0) + 5
            print(f"  [{label}] Rate limit! Ждём {wait} сек...")
            time.sleep(wait)
            return None
        if resp.status_code == 422:
            print(f"  [{label}] HTTP 422 – останавливаем.")
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
        data = api_get(url, "Issues")
        if data is None or not data:
            break
        for item in data:
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
        print(f"  Собрано issues: {len(issues)}")
        if len(data) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return issues

def fetch_commits():
    commits = []
    page = 1
    print("[Commits] Сбор...")
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits?since={SINCE}T00:00:00Z&until={UNTIL}T23:59:59Z&per_page=100&page={page}"
        data = api_get(url, "Commits")
        if data is None or not data:
            break
        for item in data:
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
        print(f"  Собрано commits: {len(commits)}")
        if len(data) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return commits

def fetch_prs():
    prs = []
    page = 1
    print("[PRs] Сбор...")
    while True:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=all&per_page=100&page={page}"
        data = api_get(url, "PRs")
        if data is None or not data:
            break
        for item in data:
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
        print(f"  Собрано PRs: {len(prs)}")
        if len(data) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return prs

def load_issues(issues):
    if not issues:
        return
    ch.execute("TRUNCATE TABLE issues_raw")
    ch.execute("""
        INSERT INTO issues_raw (issue_number, title, state, created_at, closed_at, author, assignee, labels)
        VALUES
    """, issues)
    print(f"  Загружено issues: {len(issues)}")

def load_commits(commits):
    if not commits:
        return
    ch.execute("TRUNCATE TABLE commits_raw")
    ch.execute("""
        INSERT INTO commits_raw (sha, message, author_name, author_email, commit_date, issue_number)
        VALUES
    """, commits)
    print(f"  Загружено commits: {len(commits)}")

def load_prs(prs):
    if not prs:
        return
    ch.execute("TRUNCATE TABLE prs_raw")
    ch.execute("""
        INSERT INTO prs_raw (pr_number, title, state, created_at, merged_at, closed_at, author, issue_number)
        VALUES
    """, prs)
    print(f"  Загружено PRs: {len(prs)}")

def calculate_kpi():
    sql = """
    INSERT INTO github_metrics.kpi_daily (metric_date, metric_name, metric_value)
    SELECT toDate(created_at), 'lead_time_hours', AVG(dateDiff('hour', created_at, closed_at))
    FROM issues_raw WHERE closed_at IS NOT NULL GROUP BY metric_date;

    INSERT INTO github_metrics.kpi_daily (metric_date, metric_name, metric_value)
    SELECT toDate(created_at), 'pr_merge_rate_pct', COUNTIf(merged_at IS NOT NULL)*100.0/COUNT(*)
    FROM prs_raw GROUP BY metric_date;

    INSERT INTO github_metrics.kpi_daily (metric_date, metric_name, metric_value)
    SELECT toDate(commit_date), 'commits_per_issue', COUNT(*)/COUNT(DISTINCT issue_number)
    FROM commits_raw WHERE issue_number IS NOT NULL GROUP BY metric_date;

    INSERT INTO github_metrics.kpi_daily (metric_date, metric_name, metric_value)
    SELECT toDate(created_at), 'bug_fix_hours', AVG(dateDiff('hour', created_at, closed_at))
    FROM issues_raw WHERE labels LIKE '%bug%' AND closed_at IS NOT NULL GROUP BY metric_date;

    INSERT INTO github_metrics.kpi_daily (metric_date, metric_name, metric_value)
    SELECT toDate(closed_at), 'closed_issues_count', COUNT(*)
    FROM issues_raw WHERE closed_at IS NOT NULL GROUP BY metric_date;
    """
    for stmt in sql.split(';'):
        if stmt.strip():
            ch.execute(stmt)
    print("  KPI пересчитаны")

def main():
    print("="*50)
    print(f"ETL (ClickHouse): {OWNER}/{REPO}")
    print("="*50)
    issues = fetch_issues()
    commits = fetch_commits()
    prs = fetch_prs()
    load_issues(issues)
    load_commits(commits)
    load_prs(prs)
    calculate_kpi()
    save_last_run_date()
    print(f"\nГотово. Данные загружены в ClickHouse. Следующий запуск с {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
