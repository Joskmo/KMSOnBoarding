# Assessment Service — Future Features

## Лимиты попыток (Attempt Limits)

**Статус:** не реализовано в текущей версии. Запланировано как будущее расширение.

**Описание:**
Добавить поле `max_attempts` (INTEGER, DEFAULT NULL или 0 = безлимитно) в таблицу `tests`.

**Поведение:**
- При `GET /api/v1/attempts/start/{test_id}` проверять: `COUNT(attempts WHERE user_id = ? AND test_id = ? AND finished_at IS NOT NULL) < max_attempts`.
- Если лимит исчерпан — вернуть `409 Conflict` с сообщением "Лимит попыток исчерпан".
- Активные (незавершённые) попытки не должны учитываться в лимите, пока не протухли.

**Миграция:**
ALTER TABLE tests ADD COLUMN max_attempts INTEGER DEFAULT NULL;

---

## Прочие идеи

- Временные окна доступности теста (дата начала / дата окончания)
- Перемешивание вопросов и вариантов ответов при каждой попытке
- Подробная аналитика по попыткам (время на каждый вопрос)
