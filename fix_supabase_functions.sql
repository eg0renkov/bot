-- Исправление SQL функций для векторной памяти

-- 1. Исправляем функцию get_user_stats (проблема с типами данных)
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
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM conversations WHERE user_id = user_id_param),
        (SELECT COUNT(*) FROM knowledge_base WHERE user_id = user_id_param),
        (SELECT COALESCE(AVG(LENGTH(user_message) + LENGTH(ai_response))::DOUBLE PRECISION, 0) FROM conversations WHERE user_id = user_id_param),
        (SELECT MIN(created_at) FROM conversations WHERE user_id = user_id_param),
        (SELECT MAX(created_at) FROM conversations WHERE user_id = user_id_param);
END;
$$;

-- 2. Исправляем функцию search_knowledge_base (устраняем неоднозначность колонки id)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    user_id_param BIGINT,
    match_threshold FLOAT DEFAULT 0.8,
    match_count INTEGER DEFAULT 3
)
RETURNS TABLE (
    id BIGINT,
    topic TEXT,
    content TEXT,
    similarity FLOAT,
    importance_score FLOAT,
    last_accessed TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Обновляем счетчик доступа для найденных записей
    UPDATE knowledge_base kb_update
    SET 
        access_count = access_count + 1,
        last_accessed = NOW()
    WHERE kb_update.id IN (
        SELECT kb_inner.id
        FROM knowledge_base kb_inner
        WHERE 
            kb_inner.user_id = user_id_param
            AND kb_inner.embedding IS NOT NULL
            AND (1 - (kb_inner.embedding <=> query_embedding)) > match_threshold
        ORDER BY kb_inner.embedding <=> query_embedding
        LIMIT match_count
    );

    RETURN QUERY
    SELECT 
        kb_main.id,
        kb_main.topic,
        kb_main.content,
        (1 - (kb_main.embedding <=> query_embedding)) AS similarity,
        kb_main.importance_score,
        kb_main.last_accessed
    FROM knowledge_base kb_main
    WHERE 
        kb_main.user_id = user_id_param
        AND kb_main.embedding IS NOT NULL
        AND (1 - (kb_main.embedding <=> query_embedding)) > match_threshold
    ORDER BY 
        (1 - (kb_main.embedding <=> query_embedding)) DESC,
        kb_main.importance_score DESC
    LIMIT match_count;
END;
$$;