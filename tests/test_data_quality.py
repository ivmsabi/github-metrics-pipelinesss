import pytest
from clickhouse_driver import Client

ch = Client(host='localhost', port=9000, database='github_metrics')

def test_no_duplicate_issues():
    res = ch.execute("SELECT count() FROM (SELECT issue_number, count() FROM issues_raw GROUP BY issue_number HAVING count() > 1)")[0][0]
    assert res == 0, "Найдены дубликаты issue_number"

def test_no_null_created_at():
    res = ch.execute("SELECT count() FROM issues_raw WHERE created_at IS NULL")[0][0]
    assert res == 0, "Есть задачи без даты создания"

def test_lead_time_non_negative():
    res = ch.execute("SELECT count() FROM kpi_daily WHERE metric_name='lead_time_hours' AND metric_value < 0")[0][0]
    assert res == 0, "Отрицательный lead_time"