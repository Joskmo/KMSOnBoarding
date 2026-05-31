# Дизайн: Назначение модулей кандидатам и семинаристам

## Дата: 2026-05-31

---

## 1. Цель

Реализовать возможность назначения published-модулей конкретным пользователям (candidate, seminarist). После реализации кандидаты и семинаристы видят **только** те модули, которые им явно назначил методист или админ.

---

## 2. Модель данных

### 2.1 Новая таблица `module_assignments` (БД `kms_content`)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | Автогенерация |
| `module_id` | UUID FK → `modules.id` ON DELETE CASCADE | Связь с модулем |
| `user_id` | UUID (без FK) | Кому назначен. Без FK, т.к. users в `auth`-сервисе |
| `assigned_by` | UUID (без FK) | Кто назначил. Без FK, т.к. users в `auth`-сервисе |
| `created_at` | datetime | Автозаполнение |

- `UniqueConstraint(module_id, user_id)` — один модуль один раз на пользователя.
- `ON DELETE CASCADE` на `module_id` — при удалении модуля назначения удаляются автоматически.
- `user_id` и `assigned_by` — **нет внешних ключей**. В микросервисной архитектуре таблица `users` живёт в другой БД. При удалении пользователя cleanup выполняется через cross-service вызов (см. раздел 6).

### 2.2 Relationship в `Module`

```python
assignments: Mapped[list["ModuleAssignment"]] = relationship(
    "ModuleAssignment", back_populates="module", cascade="all, delete-orphan"
)
```

---

## 3. Схемы (Pydantic)

```python
class ModuleAssignmentCreate(BaseModel):
    user_ids: list[UUID]

class ModuleAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    module_id: UUID
    user_id: UUID
    assigned_by: UUID
    created_at: datetime
```

---

## 4. API эндпоинты (content-сервис)

### 4.1 Назначение модулей

**`POST /api/v1/modules/{module_id}/assignments`**
- Тело: `{"user_ids": ["uuid", ...]}`
- Права: `admin` — любой модуль; `methodist` — только свой (`author_id == current_user.id`)
- Валидация: модуль должен быть `published` → 422 если нет
- Идемпотентность: если запись уже есть — пропускаем, не ошибка
- Возвращает `list[ModuleAssignmentResponse]`

**`DELETE /api/v1/modules/{module_id}/assignments/{user_id}`**
- Права: `admin` — любой модуль; `methodist` — только свой модуль
- Удаляет конкретное назначение

**`GET /api/v1/modules/{module_id}/assignments`**
- Права: `admin` — любой модуль; `methodist` — только свой модуль
- Возвращает `list[ModuleAssignmentResponse]`

### 4.2 Cleanup эндпоинт (для auth-сервиса)

**`DELETE /api/v1/module-assignments/user/{user_id}`**
- Права: `admin` only
- Удаляет ВСЕ записи `module_assignments WHERE user_id = {user_id}`
- Вызывается auth-сервисом при удалении пользователя

### 4.3 Изменения в существующих эндпоинтах

**`GET /api/v1/modules` (list_modules)** — для `seminarist`/`candidate`:
- Убираем фильтр `manager_id == current_user.manager_id`
- Вместо этого: `JOIN module_assignments ON module_id = modules.id WHERE user_id = current_user.id AND status = 'published'`
- Для `admin`/`methodist` — логика без изменений

**`GET /api/v1/modules/{module_id}` (get_module)** — для `seminarist`/`candidate`:
- Доступ только если существует запись в `module_assignments` для `user_id == current_user.id`

**Вложенные эндпоинты** (`/lessons`, `/heuristics`) — используют `_can_access_module`, обновляется аналогично.

---

## 5. CRUD (`app/crud/assignment.py`)

- `create_assignments(db, module_id, user_ids, assigned_by)` — bulk insert с `ON CONFLICT DO NOTHING`
- `delete_assignment(db, module_id, user_id)`
- `get_by_module(db, module_id)` — список назначенных пользователей
- `get_modules_for_user(db, user_id)` — module_ids пользователя (для `list_modules`)
- `delete_by_user(db, user_id)` — удалить все назначения пользователя

---

## 6. Cross-service cleanup при удалении пользователя

**Проблема:** пользователь удаляется в `auth`-сервисе, но его `user_id` висят в `module_assignments` content-сервиса.

**Решение:**

1. В `content`-сервисе — эндпоинт `DELETE /api/v1/module-assignments/user/{user_id}` (см. 4.2).

2. В `auth`-сервисе (`delete_user`) **после** `await db.commit()`:
   - Делаем `httpx.AsyncClient().delete(f"{API_GATEWAY_URL}/api/v1/module-assignments/user/{user_id}", headers=...)` с текущими auth-заголовками.
   - Если запрос не удался — логируем `logger.warning(...)`, но **не откатываем** удаление пользователя.
   - Добавить `httpx` в production-зависимости `auth/pyproject.toml`.

3. В `.env.example` добавляем/проверяем:
   ```
   API_GATEWAY_URL=http://api-gateway
   ```

---

## 7. Фронтенд

### 7.1 Новые API-функции (`frontend/src/api/content.ts`)

```typescript
export const getModuleAssignments = (moduleId: string) => ...
export const assignModule = (moduleId: string, userIds: string[]) => ...
export const unassignModule = (moduleId: string, userId: string) => ...
```

### 7.2 Новый тип (`frontend/src/types/index.ts`)

```typescript
export interface ModuleAssignment {
  id: string;
  module_id: string;
  user_id: string;
  assigned_by: string;
  created_at: string;
}
```

### 7.3 UI в `ModuleDetailPage.tsx` (только для `admin`/`methodist`)

- Секция «Назначения» под заголовком модуля.
- Таблица назначенных пользователей с кнопкой «Отозвать».
- Кнопка «Назначить пользователей» — открывает модал.
- В модале: список пользователей с чекбоксами:
  - Методист видит только своих подчинённых (`role=candidate|seminarist`, `manager_id == current_user.id`).
  - Админ видит всех пользователей.
- Кнопки массового выбора:
  - Методист: «Выбрать всех подчинённых»
  - Админ: «Выбрать всех пользователей»
- Кнопка «Назначить выбранным».

---

## 8. Тесты (`tests/test_assignments.py`)

- admin назначает модуль → 201
- methodist свой модуль → 201
- methodist чужой модуль → 403
- draft модуль → 422
- Идемпотентность: повторное назначение тому же user → OK
- seminarist видит только назначенные в `list_modules`
- seminarist не видит не назначенный published модуль → total=0
- seminarist 403 на не назначенный модуль по ID
- Уроки/эвристики только для назначенного модуля
- Удаление назначения
- Cleanup endpoint: admin удаляет user_id → все его назначения удалены

---

## 9. Порядок коммитов

1. `content: добавлена таблица module_assignments` — миграция + модель
2. `content: CRUD и схемы для module_assignments` — `crud/assignment.py` + schemas
3. `content: API endpoints для назначения модулей` — роутеры + изменения в list/get
4. `content: тесты для назначения модулей` — `test_assignments.py`
5. `auth: добавлен httpx для cleanup-вызовов` — `pyproject.toml`
6. `auth: cleanup module_assignments при удалении пользователя` — `delete_user`
7. `frontend: типы и API для module assignments` — `types` + `api/content.ts`
8. `frontend: UI назначения модулей в ModuleDetailPage` — модал + таблица
9. `fix: lint и форматирование` — ruff

---

## 10. Архитектурные ограничения

- `content-service` не имеет таблицы `users`. Валидация того, что назначаемый `user_id` существует и является подчинённым методиста, **делегируется фронтенду** (который показывает только валидных кандидатов/семинаристов из `GET /users`). Это соответствует текущей архитектуре проекта (например, `assessment-service` записывает `user_id` в `attempts` без cross-service валидации).
- При удалении пользователя из auth — cleanup через HTTP-вызов к content. Если content недоступен, назначения становятся «осиротевшими», но это не ломает систему (seminarist/candidate просто не видит модули, которых уже нет). При необходимости можно добавить периодическую очистку.
