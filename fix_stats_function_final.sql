-- Полное исправление функции статистики

-- Сначала удаляем старую функцию
DROP FUNCTION IF EXISTS get_user_stats(BIGINT);

-- Создаем новую функцию с правильными типами
CREATE OR REPLACE FUNCTION get_user_stats(user_id_param BIGINT)
RETURNS TABLE (
    total_conversations BIGINT,
    knowledge_entries BIGINT,
    avg_conversation_length DOUBLE PRECISION,
    first_interaction TIMESTAMPTZ,
    last_interaction TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_conv BIGINT;
    knowledge_count BIGINT;
    avg_length DOUBLE PRECISION;
    first_interaction_date TIMESTAMPTZ;
    last_interaction_date TIMESTAMPTZ;
BEGIN
    -- Получаем количество разговоров
    SELECT COUNT(*) INTO total_conv
    FROM conversations 
    WHERE user_id = user_id_param;
    
    -- Получаем количество записей в базе знаний
    SELECT COUNT(*) INTO knowledge_count
    FROM knowledge_base 
    WHERE user_id = user_id_param;
    
    -- Получаем среднюю длину сообщений
    SELECT COALESCE(AVG(LENGTH(user_message) + LENGTH(ai_response)), 0)::DOUBLE PRECISION INTO avg_length
    FROM conversations 
    WHERE user_id = user_id_param;
    
    -- Получаем первое взаимодействие
    SELECT MIN(created_at) INTO first_interaction_date
    FROM conversations 
    WHERE user_id = user_id_param;
    
    -- Получаем последнее взаимодействие
    SELECT MAX(created_at) INTO last_interaction_date
    FROM conversations 
    WHERE user_id = user_id_param;
    
    -- Возвращаем результат
    RETURN QUERY
    SELECT 
        total_conv,
        knowledge_count,
        avg_length,
        first_interaction_date,
        last_interaction_date;
END;
$$;