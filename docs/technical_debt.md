# Технический долг и архитектурные компромиссы KMS

> **Для агентов:** это единый источник истины по известным проблемам, компромиссам и расхождениям в проекте. Перед финальным аудитом или написанием текста диплома — прочитать полностью.

---

## 1. Общие архитектурные решения

### 1.1 Изоляция микросервисов
- Каждый сервис — только своя БД. Прямые SQL-вызовы или HTTP-вызовы между сервисами **запрещены**.
- Связь через `module_id` (UUID) между `content` и `assessment` — eventual consistency. Content может удалить модуль, а assessment останется с висящим `module_id`. Это принятый компромисс.
- **Будущее решение:** event-driven архитектура (Kafka/RabbitMQ) или soft-delete в content-service.

### 1.2 CORS
- **Не настроен ни в одном backend-сервисе.** В production CORS обрабатывается на NGINX-шлюзе.
- В dev-режиме (Vite `:5173` → backend `:8001/8002/8003`) фронтенд-разработчик использует **Vite proxy** (`vite.config.js`) или запускает NGINX локально.

### 1.3 Ролевая модель
- Роли — фиксированный набор (`admin`, `methodist`, `seminarist`, `candidate`), хранятся как `VARCHAR(50)` в `users.role`.
- Таблицы `roles` и `user_roles` удалены (было в ранней версии диплома). Подробнее в `notes/discrepancies.md`.

---

## 2. Auth Service

### 2.1 Регистрация только по инвайту
- Первый пользователь (когда `COUNT(users)=0`) может зарегистрироваться без приглашения и автоматически получает `admin`.
- В дипломе этого не было — новая функциональность, утверждена заказчиком.

### 2.2 Иерархия пользователей
- Поля `manager_id` и `invited_by` добавлены в `users` для управления подчинением.
- Methodist (manager_id=null) управляет seminarist/candidate (manager_id=methodist.id).
- Перевод сотрудников между методистами — через `PUT /api/v1/users/{id}` (поле `manager_id`).

---

## 3. Content Service

### 3.1 Файлы презентаций
- **Не хранятся на сервере.** В БД — только URI-ссылки на «Р7-Офис», встраиваются через `<iframe>`.
- Это соответствует диплому, но стоит отметить как ограничение: нет офлайн-режима.

---

## 4. Assessment Service

### 4.1 Double commit pattern (CRUD) — ИСПРАВЛЕНО
- **Было:** каждая CRUD-функция (`create`, `update`, `delete`, `reorder`) делала `await db.commit()` внутри себя. Затем `get_db` dependency тоже коммитил. Нарушение atomicity.
- **Стало:** `commit` убран из CRUD-слоя, единая граница транзакции — только в `get_db`.
- **Коммит:** `refactor: убраны внутренние commit из CRUD-слоя`.

### 4.2 `list_questions` — ИСПРАВЛЕНО
- **Было:** `GET /api/v1/tests/{id}/questions` возвращал `list[dict]` с discriminated shape (seminarist не видел `is_correct`). Untyped в OpenAPI.
- **Стало:** endpoint ограничен `admin`/`methodist`, `response_model=list[QuestionResponse]`. Seminarist/candidate получают вопросы только через `GET /api/v1/attempts/start/{test_id}`.
- **Коммит:** `refactor: list_questions — typed response_model, доступ только admin/methodist`.

### 4.3 `question_count` — ИСПРАВЛЕНО
- **Было:** `@computed_field` читал `self.questions`, но relationship не загружался — всегда `0`.
- **Стало:** `selectinload(Test.questions)` в `get`/`get_multi` + `model_validator(mode='before')` в `TestResponse` для безопасного подсчёта.
- **Коммит:** `fix: eager loading questions для корректного question_count`.

### 4.4 `selectinload(Test.questions)` в `list_tests` — АКТУАЛЬНО
- **Проблема:** для подсчёта `question_count` в списке тестов загружаются **все вопросы всех тестов**.
- **Последствия:** при 50 тестах × 20 вопросов = 1000 лишних объектов в памяти и сериализации.
- **Причина:** `@computed_field` требует доступа к `questions` на момент валидации Pydantic.
- **Решение в будущем:** заменить на `column_property` с подзапросом `COUNT(questions.id)` в модели `Test`.
- **Статус:** 🟢 Не критично на текущих объёмах данных.

### 4.5 `module_id` без Foreign Key
- **Проблема:** `tests.module_id` — UUID без FK. Content-service может удалить модуль, assessment останется с невалидным `module_id`.
- **Причина:** изоляция микросервисов (общая БД запрещена).
- **Статус:** 🟡 Принят как architectural trade-off.
- **Решение в будущем:** event-driven синхронизация (модуль удалён → assessment получает event).

### 4.6 Future Features (не реализовано)
- **Лимиты попыток:** поле `max_attempts` в `tests`. Проверка при `start_attempt`.
- **Временные окна доступности теста:** `start_date` / `end_date`.
- **Перемешивание вопросов и вариантов** при каждой попытке.
- **Аналитика по попыткам:** время на каждый вопрос.
- Подробнее в `docs/assessment_future_features.md`.

---

## 5. Frontend

### 5.1 Текущее состояние
- React + Vite + Axios. Порт 5173 (dev) / 3000 (prod).
- **Не интегрирован с backend** (ожидает готовности API).
- **CORS в dev:** решается через Vite proxy (`vite.config.js`) или локальный NGINX.

---

## 6. Инфраструктура

### 6.1 NGINX
- **Пока не настроен** в репозитории. В `docker-compose.yml` прописан, но конфиг `infra/nginx/nginx.conf` отсутствует.
- **Нужно:** создать конфиг с маршрутизацией `/api/v1/auth → auth:8001`, `/api/v1/content → content:8002`, `/api/v1/tests|questions|attempts → assessment:8003`.

### 6.2 Docker Compose
- PostgreSQL 18, Redis 8.6, три сервиса, NGINX — всё прописано.
- **Проверено ли в docker?** Нет. Только локальный `uv run pytest` + SQLite (`aiosqlite` в dev-зависимостях).

---

## 7. Расхождения с дипломом

**Полный список:** `notes/discrepancies.md`

Кратко:
- Упрощена ролевая модель (убраны таблицы `roles`/`user_roles`, поле `role` в `users`).
- Добавлены приглашения (`invitations`) — не было в дипломе.
- Добавлена иерархия пользователей (`manager_id`) — не было в дипломе.
- Добавлена роль `admin` — не было в дипломе.
- Версионирование API `/api/v1/*` — в дипломе просто `/api/*`.
- Все изменения **согласованы с заказчиком** и отражены в `notes/discrepancies.md`.

---

## 8. Что проверить перед финальным аудитом

- [ ] Все сервисы запускаются в Docker Compose (`docker-compose up --build`)
- [ ] NGINX-конфиг создан и протестирован
- [ ] Frontend делает реальные запросы к backend через NGINX
- [ ] `assessment_future_features.md` перенесён в `technical_debt.md` (этот файл)
- [ ] `content_service_prompt.md` пересмотрен — актуален?
- [ ] `auth-integration.md` актуален для всех сервисов?
- [ ] Все secrets вынесены в `.env` (не в коде)
- [ ] Тесты проходят (`uv run pytest`) во всех трёх сервисах

---

*Документ создан: 2026-05-21*
*Последнее обновление: 2026-05-21*
