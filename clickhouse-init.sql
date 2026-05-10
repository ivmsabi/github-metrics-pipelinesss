CREATE DATABASE IF NOT EXISTS github_metrics;

-- Сырые данные
CREATE TABLE IF NOT EXISTS github_metrics.issues_raw (
    issue_number UInt32,
    title String,
    state String,
    created_at Nullable(DateTime),
    closed_at Nullable(DateTime),
    author String,
    assignee String,
    labels String
) ENGINE = MergeTree()
ORDER BY issue_number;

CREATE TABLE IF NOT EXISTS github_metrics.commits_raw (
    sha String,
    message String,
    author_name String,
    author_email String,
    commit_date Nullable(DateTime),
    issue_number Nullable(UInt32)
) ENGINE = MergeTree()
ORDER BY sha;

CREATE TABLE IF NOT EXISTS github_metrics.prs_raw (
    pr_number UInt32,
    title String,
    state String,
    created_at Nullable(DateTime),
    merged_at Nullable(DateTime),
    closed_at Nullable(DateTime),
    author String,
    issue_number Nullable(UInt32)
) ENGINE = MergeTree()
ORDER BY pr_number;

-- Витрина KPI
CREATE TABLE IF NOT EXISTS github_metrics.kpi_daily (
    metric_date Date,
    metric_name String,
    metric_value Nullable(Float64)
) ENGINE = MergeTree()
ORDER BY (metric_date, metric_name);

-- Представления для удобства
CREATE OR REPLACE VIEW github_metrics.v_commits_daily AS
SELECT 
    toDate(commit_date) as date,
    count() as commits_count,
    count(DISTINCT author_name) as active_contributors,
    sum(length(message)) as total_message_length
FROM github_metrics.commits_raw
WHERE commit_date IS NOT NULL
GROUP BY date
ORDER BY date;

CREATE OR REPLACE VIEW github_metrics.v_issues_stats AS
SELECT 
    issue_number,
    title,
    state,
    created_at,
    closed_at,
    dateDiff('hour', created_at, closed_at) as cycle_time_hours,
    author,
    assignee,
    labels
FROM github_metrics.issues_raw
WHERE created_at IS NOT NULL;