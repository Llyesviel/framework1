# Defects Control — система регистрации и контроля дефектов

Проект на Django/DRF для управления строительными объектами: проекты, этапы, дефекты, вложения, отчёты и аналитика. Есть веб-интерфейс и REST API с JWT-аутентификацией и встроенной документацией.

## Возможности
- Управление проектами, этапами и дефектами (веб и API)
- Переходы статусов дефектов по ролям (менеджер/инженер/наблюдатель)
- Комментарии и вложения к дефектам (фото/файлы)
- Экспорт CSV/Excel по дефектам и проектам
- Панель отчётов с графиками (Chart.js)
- JWT-аутентификация и Swagger UI для API

## Технологии
- Django 5, Django REST Framework
- SimpleJWT, django-filter, drf-spectacular
- Chart.js для графиков, WhiteNoise для статики

## Структура проекта
- `backend/manage.py` — точка входа в Django (`backend/manage.py:6`)
- `backend/config/settings.py` — настройки (БД, аутентификация, CSRF, REST) (`backend/config/settings.py:56-166`)
- `backend/config/urls.py` — маршруты веб/API/документации (`backend/config/urls.py:10-24`)
- Приложения: `users`, `projects`, `defects`, `reports`
- Веб-шаблоны: `backend/templates/...` (например, база и графики `backend/templates/base.html:9`, `backend/templates/reports/dashboard.html`)

## Быстрый старт (Windows PowerShell)
1. Установить зависимости
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Выбрать базу
- SQLite (локально):
```powershell
$env:DJANGO_USE_SQLITE="1"
```
- PostgreSQL (по умолчанию): задайте переменные окружения при необходимости:
```powershell
$env:POSTGRES_DB="app"
$env:POSTGRES_USER="app"
$env:POSTGRES_PASSWORD="app"
$env:POSTGRES_HOST="db"
$env:POSTGRES_PORT="5432"
```
3. Миграции и сборка статики
```powershell
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
```
4. Загрузка демо-данных (необязательно)
```powershell
python manage.py loaddata data.json
```
Если нужно задать пароль демо-пользователям:
```powershell
python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u=U.objects.get(username='manager'); u.set_password('x'); u.save(); print('ok')"
```
5. Запуск сервера разработки
```powershell
python manage.py runserver 0.0.0.0:8000
```

## Вход и роли
- Веб-страница входа: `/login/` (`backend/users/web_urls.py:4-12`)
- Роли пользователя: `manager`, `engineer`, `observer`
  - Менеджер: создаёт/редактирует проекты/этапы/дефекты, закрывает дефекты
  - Инженер: принимает дефект, добавляет отчёт, переводит в проверку
  - Наблюдатель: просмотр

## Веб-интерфейс
- Проекты: `/projects/` (`backend/projects/web_urls.py:18-36`)
- Дефекты: `/defects/` (фильтры по проекту/статусу/приоритету/исполнителю, поиск) (`backend/defects/web_views.py:31-55`)
- Отчёты: `/reports/dashboard/` — графики статусов/приоритетов/активности
- Экспорты:
  - `/defects/export/csv/`, `/defects/export/xls/` — все дефекты
  - `/defects/<id>/export/csv|xls/` — один дефект
  - `/projects/export/projects/csv|xls/` — список проектов
  - Экспорт дефектов по проекту: `/projects/<id>/export/defects/csv|xls/`

## REST API
- Документация: `/api/docs/` (Swagger UI), схема: `/api/schema/`
- Аутентификация:
  - `POST /api/auth/login/` — получить `access`/`refresh`
  - `POST /api/auth/refresh/` — обновить `access`
- Основные ресурсы:
  - `GET/POST /api/projects/`, `GET /api/projects/{id}/stages/`
  - `GET/POST /api/defects/` (фильтры: `project`, `performer`, `status`, `priority`; сортировка: `created_at`, `updated_at`, `deadline`) (`backend/defects/views.py:12-18`)
  - `POST /api/defects/{id}/change_status/` — переход статуса по правилам (`backend/defects/services.py:16-37`)
  - `GET/POST /api/defects/{id}/attachments/` — вложения (multipart)
  - `POST /api/defects/{id}/comments/` — комментарии
  - Отчёты: `GET /api/reports/summary`, `GET /api/reports/by_project?project_id=...`, `GET /api/reports/by_engineer?engineer_id=...`

Пример входа и запроса:
```powershell
$resp = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/login/ -ContentType application/json -Body '{"username":"manager","password":"x"}'
$token = $resp.access
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/defects/?status=new" -Headers @{ Authorization = "Bearer $token" }
```

## Тесты
- Все тесты:
```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings"; $env:DJANGO_USE_SQLITE="1"; python -m pytest -q
```
- Веб-слой:
```powershell
python -m pytest -q -k web_
```
- API-слой:
```powershell
python -m pytest -q -k api_
```
- Интеграционные (помечены `@pytest.mark.integration`):
```powershell
python -m pytest -q -m integration
```

## Безопасность
- Пароли: Argon2, если установлен пакет `argon2-cffi` (`backend/config/settings.py:97-114`). Установка (рекомендовано для продакшена):
```powershell
pip install argon2-cffi
```
Проверка тестом: `backend/users/tests.py:50`.
- CSRF: включён мидлвар `CsrfViewMiddleware` (`backend/config/settings.py:27-36`), формы содержат `{% csrf_token %}`.
- XSS: автоэкранирование шаблонов; данные в JS — через `json_script` (`backend/templates/defects/assign.html`, `backend/templates/reports/dashboard.html`). Тест: `backend/defects/tests.py:206`.
- SQL-инъекции: фильтры DRF/Django ORM параметризованные; тесты веб и API есть (`backend/defects/tests.py:220`, `backend/defects/tests.py:247`).

## Производительность
- Индексы на поля фильтров: `status`, `priority`, `created_at` уже индексированы (`backend/defects/models.py:31-36`).
- Рекомендуется добавить индекс на `deadline` и составные индексы для частых комбинаций (`project,status` / `performer,status`) в продакшене.
- Для поиска `q` — включить GIN+`pg_trgm` на `title`/`description` в PostgreSQL.

## Развёртывание
- Статика: `collectstatic` + WhiteNoise (`backend/config/settings.py:125-132`).
- База: используйте PostgreSQL в продакшене (`backend/config/settings.py:66-75`).
- Gunicorn (Linux):
```bash
gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 4
```
- Windows: можно использовать `runserver` для простого запуска.

## Экспорт и аналитика
- Экспорт CSV/Excel для дефектов и проектов реализован во веб-слое (`backend/defects/web_views.py:316-430`, `backend/projects/web_views.py:160-295`).
- Панель отчётов на `/reports/dashboard/` строит графики по статусам/приоритетам и активности по дням.

## Лицензия
- Внутренний учебный проект; используйте на свой риск.