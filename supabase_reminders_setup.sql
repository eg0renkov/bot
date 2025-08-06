-- Создание таблицы для напоминаний
-- Выполнить этот скрипт в SQL Editor вашего Supabase проекта

-- Таблица для хранения напоминаний
CREATE TABLE IF NOT EXISTS reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    remind_at TIMESTAMPTZ NOT NULL,
    repeat_type TEXT DEFAULT 'none', -- none, daily, weekly, monthly, yearly
    repeat_interval INTEGER DEFAULT 0, -- Интервал повторения в зависимости от типа
    repeat_days TEXT[], -- Дни недели для еженедельных напоминаний ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    is_active BOOLEAN DEFAULT TRUE,
    is_completed BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    last_notified_at TIMESTAMPTZ
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active, is_completed);
CREATE INDEX IF NOT EXISTS idx_reminders_notification ON reminders(is_active, notification_sent, remind_at);

-- Таблица для настроек напоминаний пользователя
CREATE TABLE IF NOT EXISTS reminder_settings (
    user_id BIGINT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    default_notification_time TIME DEFAULT '09:00:00',
    timezone TEXT DEFAULT 'Europe/Moscow',
    sound_enabled BOOLEAN DEFAULT TRUE,
    advance_notification INTEGER DEFAULT 10, -- За сколько минут до события напоминать
    daily_summary BOOLEAN DEFAULT FALSE, -- Ежедневная сводка напоминаний
    daily_summary_time TIME DEFAULT '08:00:00',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Функция для получения активных напоминаний
CREATE OR REPLACE FUNCTION get_active_reminders(
    user_id_param BIGINT DEFAULT NULL,
    time_window_minutes INTEGER DEFAULT 5
)
RETURNS TABLE (
    id BIGINT,
    user_id BIGINT,
    title TEXT,
    description TEXT,
    remind_at TIMESTAMPTZ,
    repeat_type TEXT,
    is_active BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.user_id,
        r.title,
        r.description,
        r.remind_at,
        r.repeat_type,
        r.is_active
    FROM reminders r
    INNER JOIN reminder_settings rs ON r.user_id = rs.user_id
    WHERE 
        r.is_active = TRUE
        AND r.is_completed = FALSE
        AND r.notification_sent = FALSE
        AND rs.enabled = TRUE
        AND r.remind_at <= NOW() + INTERVAL '1 minute' * time_window_minutes
        AND r.remind_at >= NOW() - INTERVAL '1 minute'
        AND (user_id_param IS NULL OR r.user_id = user_id_param)
    ORDER BY r.remind_at ASC;
END;
$$;

-- Функция для создания следующего повторяющегося напоминания
CREATE OR REPLACE FUNCTION create_next_recurring_reminder(reminder_id BIGINT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    old_reminder RECORD;
    new_remind_at TIMESTAMPTZ;
    new_reminder_id BIGINT;
BEGIN
    -- Получаем текущее напоминание
    SELECT * INTO old_reminder FROM reminders WHERE id = reminder_id;
    
    -- Если напоминание не повторяющееся, выходим
    IF old_reminder.repeat_type = 'none' OR old_reminder.repeat_type IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Вычисляем время следующего напоминания
    CASE old_reminder.repeat_type
        WHEN 'daily' THEN
            new_remind_at := old_reminder.remind_at + INTERVAL '1 day' * COALESCE(old_reminder.repeat_interval, 1);
        WHEN 'weekly' THEN
            new_remind_at := old_reminder.remind_at + INTERVAL '1 week' * COALESCE(old_reminder.repeat_interval, 1);
        WHEN 'monthly' THEN
            new_remind_at := old_reminder.remind_at + INTERVAL '1 month' * COALESCE(old_reminder.repeat_interval, 1);
        WHEN 'yearly' THEN
            new_remind_at := old_reminder.remind_at + INTERVAL '1 year' * COALESCE(old_reminder.repeat_interval, 1);
        ELSE
            RETURN NULL;
    END CASE;
    
    -- Создаем новое напоминание
    INSERT INTO reminders (
        user_id, title, description, remind_at, 
        repeat_type, repeat_interval, repeat_days,
        is_active, is_completed, notification_sent
    ) VALUES (
        old_reminder.user_id,
        old_reminder.title,
        old_reminder.description,
        new_remind_at,
        old_reminder.repeat_type,
        old_reminder.repeat_interval,
        old_reminder.repeat_days,
        TRUE,
        FALSE,
        FALSE
    ) RETURNING id INTO new_reminder_id;
    
    RETURN new_reminder_id;
END;
$$;

-- Функция для пометки напоминания как отправленного
CREATE OR REPLACE FUNCTION mark_reminder_sent(reminder_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE reminders 
    SET 
        notification_sent = TRUE,
        last_notified_at = NOW(),
        updated_at = NOW()
    WHERE id = reminder_id;
    
    -- Если напоминание повторяющееся, создаем следующее
    PERFORM create_next_recurring_reminder(reminder_id);
END;
$$;

-- Функция для получения статистики напоминаний пользователя
CREATE OR REPLACE FUNCTION get_user_reminder_stats(user_id_param BIGINT)
RETURNS TABLE (
    total_reminders INTEGER,
    active_reminders INTEGER,
    completed_reminders INTEGER,
    upcoming_today INTEGER,
    upcoming_week INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_reminders,
        COUNT(*) FILTER (WHERE is_active = TRUE AND is_completed = FALSE)::INTEGER as active_reminders,
        COUNT(*) FILTER (WHERE is_completed = TRUE)::INTEGER as completed_reminders,
        COUNT(*) FILTER (
            WHERE is_active = TRUE 
            AND is_completed = FALSE 
            AND remind_at >= NOW() 
            AND remind_at <= NOW() + INTERVAL '1 day'
        )::INTEGER as upcoming_today,
        COUNT(*) FILTER (
            WHERE is_active = TRUE 
            AND is_completed = FALSE 
            AND remind_at >= NOW() 
            AND remind_at <= NOW() + INTERVAL '7 days'
        )::INTEGER as upcoming_week
    FROM reminders
    WHERE user_id = user_id_param;
END;
$$;

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reminders_updated_at BEFORE UPDATE ON reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reminder_settings_updated_at BEFORE UPDATE ON reminder_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();