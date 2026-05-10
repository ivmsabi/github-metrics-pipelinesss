def calculate_kpi():
    print("  Расчёт KPI...")
    # 1. Lead Time
    ch.execute("""
        INSERT INTO kpi_daily (metric_date, metric_name, metric_value)
        SELECT toDate(created_at), 'lead_time_hours', AVG(dateDiff('hour', created_at, closed_at))
        FROM issues_raw
        WHERE closed_at IS NOT NULL
        GROUP BY toDate(created_at)
    """)
    # 2. PR Merge Rate
    ch.execute("""
        INSERT INTO kpi_daily (metric_date, metric_name, metric_value)
        SELECT toDate(created_at), 'pr_merge_rate_pct', COUNTIf(merged_at IS NOT NULL)*100.0/COUNT(*)
        FROM prs_raw
        GROUP BY toDate(created_at)
    """)
    # 3. Commits per Issue
    ch.execute("""
        INSERT INTO kpi_daily (metric_date, metric_name, metric_value)
        SELECT toDate(commit_date), 'commits_per_issue', COUNT(*)/COUNT(DISTINCT issue_number)
        FROM commits_raw
        WHERE issue_number IS NOT NULL
        GROUP BY toDate(commit_date)
    """)
    # 4. Bug Fix Time
    ch.execute("""
        INSERT INTO kpi_daily (metric_date, metric_name, metric_value)
        SELECT toDate(created_at), 'bug_fix_hours', AVG(dateDiff('hour', created_at, closed_at))
        FROM issues_raw
        WHERE labels LIKE '%bug%' AND closed_at IS NOT NULL
        GROUP BY toDate(created_at)
    """)
    # 5. Closed Issues Count
    ch.execute("""
        INSERT INTO kpi_daily (metric_date, metric_name, metric_value)
        SELECT toDate(closed_at), 'closed_issues_count', COUNT(*)
        FROM issues_raw
        WHERE closed_at IS NOT NULL
        GROUP BY toDate(closed_at)
    """)
    print("  KPI пересчитаны")