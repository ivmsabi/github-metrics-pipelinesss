# 📊 GitHub Dev Metrics Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-23.8-yellow.svg)](https://clickhouse.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.7.1-green.svg)](https://airflow.apache.org/)
[![DataLens](https://img.shields.io/badge/DataLens-OSS-orange.svg)](https://datalens.yandex.cloud/)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

**Автоматический ETL-пайплайн для сбора метрик продуктивности из GitHub и визуализации в DataLens OSS**

Система собирает данные о задачах (Issues), коммитах (Commits) и пул-реквестах (Pull Requests) из публичного репозитория GitHub, рассчитывает ключевые показатели эффективности (Lead Time, PR Merge Rate, Commits per Issue, Bug Fix Time, Closed Issues Count) и отображает их в виде дашбордов.

---

## 📦 Что вы получите после установки

- **ClickHouse** – база данных для хранения сырых данных и витрины метрик
- **Apache Airflow** – оркестратор, запускающий ETL‑скрипт каждый день в 2:00
- **DataLens OSS** – BI‑инструмент для построения дашбордов (Executive, Team Performance, Operational)
- **Python ETL‑скрипт** – для извлечения, трансформации и загрузки данных

Всё работает внутри Docker-контейнеров – не нужно устанавливать компоненты вручную.

---

## 🖥️ Требования к компьютеру

| Компонент | Минимальная версия | Примечание |
|-----------|-------------------|-------------|
| Docker Desktop | 20.10+ | [Скачать](https://www.docker.com/products/docker-desktop/) |
| Docker Compose | 2.0+ | Входит в Docker Desktop |
| Git | любая | [Скачать](https://git-scm.com/) |
| Оперативная память | 4 ГБ (рекомендуется 8 ГБ) | |
| Свободное место | 10 ГБ | |
| Интернет | стабильный | Для скачивания Docker-образов (~2 ГБ) |

---

## 🚀 Быстрый старт (для опытных)

Если вы уже знакомы с Docker, выполните эти команды в терминале:

```bash
git clone https://github.com/ivmsabi/github-metrics-pipeline
cd github-metrics-pipeline
echo "GITHUB_TOKEN=ghp_ваш_токен" > .env
docker-compose up -d
docker exec -it clickhouse clickhouse-client < sql/create_tables.sql
docker exec -it airflow python /opt/airflow/scripts/etl_github.py
```

Далее откройте в браузере:
- **Airflow**: http://localhost:8081 (логин `admin`, пароль `admin`)
- **DataLens**: http://localhost:8080 (логин `admin`, пароль `admin`)

Подробности – ниже.

---

## 📚 Полная пошаговая инструкция (для новичков)

### 1. Установите Docker Desktop

Перейдите на [docker.com](https://www.docker.com/products/docker-desktop/), скачайте версию для вашей операционной системы (Windows / macOS). Запустите установщик, следуйте стандартным шагам. После установки **запустите Docker Desktop** (он должен появиться в трее / строке меню). На Linux установите Docker Engine через пакетный менеджер.

### 2. Установите Git

Скачайте Git с [git-scm.com](https://git-scm.com/), установите с настройками по умолчанию.

### 3. Клонируйте репозиторий

Откройте **терминал** (в Windows – «Командная строка» или PowerShell, в macOS – «Терминал»). Выполните:

```bash
git clone https://github.com/ivmsabi/github-metrics-pipeline
cd github-metrics-pipeline
```

### 4. Создайте GitHub Personal Access Token

- Зайдите на [github.com](https://github.com/), авторизуйтесь.
- Нажмите на свой аватар → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
- Нажмите **Generate new token (classic)**.
- В поле **Note** напишите, например, `diploma_metrics`.
- Отметьте права: **repo** (все) и **read:user**.
- Нажмите **Generate token**, скопируйте полученный токен (начинается с `ghp_...`).

### 5. Сохраните токен в файл `.env`

В папке `github-metrics-pipeline` создайте файл `.env`:

```bash
echo "GITHUB_TOKEN=ghp_ваш_токен" > .env
```

**Важно:** не ставьте лишних пробелов, кавычек. Токен пишется сразу после `=`.

### 6. Запустите контейнеры

```bash
docker-compose up -d
```

Эта команда скачает Docker-образы (около 2 ГБ) и запустит контейнеры:

| Сервис | Назначение | Порт |
|--------|-----------|------|
| `clickhouse` | База данных | 8123 (HTTP), 9000 (TCP) |
| `postgres_airflow` | Служебная БД для Airflow | 5432 |
| `airflow` | Оркестратор ETL | 8081 |
| `datalens` | BI‑инструмент | 8080 |

Проверьте, что все контейнеры работают:

```bash
docker ps
```

Должны быть 4 контейнера в статусе `Up`.

### 7. Создайте таблицы в ClickHouse

Подключитесь к ClickHouse:

```bash
docker exec -it clickhouse clickhouse-client
```

Внутри консоли (приглашение `:)`) выполните SQL-скрипт. Для этого можно скопировать содержимое файла `sql/create_tables.sql` вручную либо выполнить одной командой (выйдите из консоли предварительно):

```bash
docker exec -i clickhouse clickhouse-client < sql/create_tables.sql
```

Проверьте, что таблицы созданы:

```sql
SHOW TABLES FROM github_metrics;
```

Ожидаемый вывод: `commits_raw`, `issues_raw`, `kpi_daily`, `prs_raw`. Выйдите из консоли:

```sql
exit;
```

### 8. Запустите ETL‑скрипт вручную (первый сбор данных)

```bash
docker exec -it airflow python /opt/airflow/scripts/etl_github.py
```

Скрипт начнёт загружать данные из GitHub API. 

Если появляется ошибка `GITHUB_TOKEN not set`, проверьте файл `.env` и перезапустите контейнеры (`docker-compose down && docker-compose up -d`).

### 9. Проверьте данные в ClickHouse

Подключитесь к ClickHouse и выполните простые запросы:

```sql
SELECT COUNT(*) FROM github_metrics.issues_raw;   -- должно быть 2365
SELECT COUNT(*) FROM github_metrics.commits_raw;  -- 2582
SELECT COUNT(*) FROM github_metrics.prs_raw;      -- 7308
SELECT * FROM github_metrics.kpi_daily LIMIT 5;   -- метрики
```

Если всё совпадает – база данных готова.

### 10. Настройте DataLens OSS

1. Откройте браузер и перейдите по адресу `http://localhost:8080`. Логин / пароль – `admin` / `admin`.
2. Нажмите **«Создать подключение»** → выберите **ClickHouse**.
3. Заполните поля:
   - **Имя хоста:** `clickhouse`
   - **Порт:** `8123`
   - **Имя базы данных:** `github_metrics`
   - **Имя пользователя:** `default`
   - **Пароль:** оставьте пустым
4. Нажмите **«Проверить подключение»** – должно быть зелёное «Успешно». Сохраните подключение как `GitHub Metrics CH`.

**Создайте три датасета** (по одному на каждый дашборд):

- **`ds_kpi`** (SQL-запрос):
  ```sql
  SELECT 
      metric_date,
      metric_name,
      AVG(metric_value) AS metric_value
  FROM github_metrics.kpi_daily
  GROUP BY metric_date, metric_name
  ORDER BY metric_date
  ```

- **`ds_issues`** (SQL-запрос):
  ```sql
  SELECT 
      issue_number,
      title,
      state,
      created_at,
      closed_at,
      dateDiff('day', created_at, closed_at) AS cycle_time_days,
      author,
      assignee,
      labels,
      multiIf(position(labels, 'bug') > 0, 'Bug',
              position(labels, 'feature') > 0, 'Feature',
              position(labels, 'enhancement') > 0, 'Enhancement',
              'Other') AS issue_type
  FROM github_metrics.issues_raw
  WHERE created_at IS NOT NULL
  ```

- **`ds_commits`** (SQL-запрос):
  ```sql
  SELECT 
      toDate(commit_date) AS date,
      author_name,
      count() AS commits_count,
      countIf(issue_number IS NOT NULL) AS linked_issues,
      round(countIf(issue_number IS NOT NULL) / count(), 2) AS linked_ratio
  FROM github_metrics.commits_raw
  WHERE commit_date IS NOT NULL
    AND author_name NOT LIKE '%bot%'
    AND author_name NOT IN ('dependabot[bot]', 'github-actions[bot]')
  GROUP BY date, author_name
  ORDER BY date DESC
  ```

**Постройте дашборды.** Детальные инструкции по созданию чартов (линейные графики, круговые диаграммы, таблицы) приведены в дипломной работе (раздел 3.3). Основные дашборды:

- **Executive Dashboard** – тренды Lead Time, PR Merge Rate, коммиты, закрытые задачи, топ‑5 контрибьюторов.
- **Team Performance Dashboard** – распределение типов задач, активность по авторам, долгие задачи, топ контрибьюторов.
- **Operational Dashboard** – открытые задачи, затянутые (>7 дней), накопленные коммиты.

### 11. Автоматизация с Airflow

Airflow уже настроен. Осталось включить DAG и проверить его работу.

1. Откройте `http://localhost:8081`, логин/пароль – `admin` / `admin` (возможно, `sabina` / `sabina123` – если вы создавали другого пользователя).
2. На главной странице найдите DAG с именем `github_metrics_daily`.
3. Включите его (переключатель «Off» → «On»).
4. Нажмите на название DAG, затем кнопку **Trigger DAG** (треугольник) для ручного запуска.
5. После выполнения проверьте логи (зелёный кружок → Log) – должен быть вывод, аналогичный пункту 8.

Теперь DAG будет запускаться **каждый день в 2:00** по расписанию.

---

## 🧪 Тестирование

### Модульные тесты (pytest)

```bash
docker exec -it airflow pytest /opt/airflow/tests -v
```

Вывод должен быть зелёным (все тесты пройдены).

### Data Quality тесты

Выполните в ClickHouse:

```sql
-- Дубликаты issue_number (должно быть 0)
SELECT issue_number, count() FROM issues_raw GROUP BY issue_number HAVING count() > 1;

-- NULL в created_at (0)
SELECT count() FROM issues_raw WHERE created_at IS NULL;

-- Отрицательный lead_time (0)
SELECT count() FROM kpi_daily WHERE metric_name='lead_time_hours' AND metric_value < 0;
```

### Тест производительности

Замерьте время выполнения полного ETL‑цикла (из логов Airflow). Ожидаемые значения:
- Полная историческая загрузка – **< 3 минут**.
- Инкрементальный запуск – **< 20 секунд**.

### Тест восстановления

Во время работы ETL‑скрипта (в другом терминале) выполните `docker stop clickhouse`. Скрипт должен упасть, но Airflow повторит задачу через 5 минут. После перезапуска ClickHouse (`docker start clickhouse`) задача завершится успешно.

---

## 📁 Структура репозитория

```
.
├── .github/workflows/        # CI/CD (GitHub Actions) – опционально
├── dags/                     # DAG Airflow
│   └── github_dag.py
├── scripts/                  # ETL-скрипты
│   ├── etl_github.py
│   ├── requirements.txt
│   └── last_run.txt (создаётся автоматически)
├── sql/                      # SQL для ClickHouse
│   └── create_tables.sql
├── tests/                    # Модульные тесты
│   └── test_etl_functions.py
├── docker-compose.yml
├── .env (не в репозитории)
├── .gitignore
└── README.md
```

---

## 🐛 Частые проблемы и их решение

| Проблема | Вероятная причина | Решение |
|----------|------------------|---------|
| `Cannot connect to the Docker daemon` | Docker Desktop не запущен | Запустите Docker Desktop |
| `Error response from daemon: denied` при pull образа DataLens | Проблемы с GitHub Container Registry | Повторите попытку позже или используйте DataLens Cloud (см. диплом) |
| `GITHUB_TOKEN not set` | Нет файла `.env` или он не смонтирован | Создайте `.env`, перезапустите контейнеры |
| `Table github_metrics.issues_raw does not exist` | Не созданы таблицы в ClickHouse | Выполните `sql/create_tables.sql` |
| Airflow веб-интерфейс не открывается (порт 8081) | Нехватка памяти | Увеличьте память в Docker Desktop (Settings → Resources → Memory до 4-6 ГБ) |
| DataLens не подключается к ClickHouse | Неправильный хост или порт | В подключении укажите хост `clickhouse`, порт `8123` |

---

## 📌 Примечание

Данная система является дипломной работой и предназначена для демонстрации автоматизированного сбора и анализа метрик продуктивности команд разработки.
