-- Настройка Supabase для векторной памяти AI бота
-- Выполнить этот скрипт в SQL Editor вашего Supabase проекта

-- Включаем расширение pgvector для работы с векторами
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблица для хранения диалогов с векторными embeddings
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embeddings размерность 1536
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для долгосрочной памяти (knowledge base)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    importance_score FLOAT DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для профилей пользователей
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    preferences JSONB DEFAULT '{}',
    personality_summary TEXT,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_topic ON knowledge_base(topic);

-- Векторные индексы для семантического поиска
CREATE INDEX IF NOT EXISTS idx_conversations_embedding ON conversations 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding ON knowledge_base 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Функция для поиска похожих диалогов
CREATE OR REPLACE FUNCTION search_similar_conversations(
    query_embedding vector(1536),
    user_id_param BIGINT,
    match_threshold FLOAT DEFAULT 0.8,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id BIGINT,
    user_message TEXT,
    ai_response TEXT,
    similarity FLOAT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.user_message,
        c.ai_response,
        (1 - (c.embedding <=> query_embedding)) AS similarity,
        c.created_at
    FROM conversations c
    WHERE 
        c.user_id = user_id_param
        AND c.embedding IS NOT NULL
        AND (1 - (c.embedding <=> query_embedding)) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Функция для поиска в базе знаний
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
    UPDATE knowledge_base 
    SET 
        access_count = access_count + 1,
        last_accessed = NOW()
    WHERE id IN (
        SELECT kb.id
        FROM knowledge_base kb
        WHERE 
            kb.user_id = user_id_param
            AND kb.embedding IS NOT NULL
            AND (1 - (kb.embedding <=> query_embedding)) > match_threshold
        ORDER BY kb.embedding <=> query_embedding
        LIMIT match_count
    );

    RETURN QUERY
    SELECT 
        kb.id,
        kb.topic,
        kb.content,
        (1 - (kb.embedding <=> query_embedding)) AS similarity,
        kb.importance_score,
        kb.last_accessed
    FROM knowledge_base kb
    WHERE 
        kb.user_id = user_id_param
        AND kb.embedding IS NOT NULL
        AND (1 - (kb.embedding <=> query_embedding)) > match_threshold
    ORDER BY 
        (1 - (kb.embedding <=> query_embedding)) DESC,
        kb.importance_score DESC
    LIMIT match_count;
END;
$$;

-- Функция для получения статистики пользователя
CREATE OR REPLACE FUNCTION get_user_stats(user_id_param BIGINT)
RETURNS TABLE (
    total_conversations BIGINT,
    knowledge_entries BIGINT,
    avg_conversation_length FLOAT,
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
        (SELECT AVG(LENGTH(user_message) + LENGTH(ai_response)) FROM conversations WHERE user_id = user_id_param),
        (SELECT MIN(created_at) FROM conversations WHERE user_id = user_id_param),
        (SELECT MAX(created_at) FROM conversations WHERE user_id = user_id_param);
END;
$$;

-- Функция для очистки старых данных
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Удаляем старые разговоры
    DELETE FROM conversations 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Удаляем неиспользуемые записи из базы знаний
    DELETE FROM knowledge_base 
    WHERE 
        last_accessed < NOW() - INTERVAL '1 day' * (days_to_keep * 2)
        AND access_count < 3
        AND importance_score < 0.5;
    
    RETURN deleted_count;
END;
$$;

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Создание политик безопасности (Row Level Security)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Политики доступа (пользователи видят только свои данные)
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (user_id = (current_setting('app.current_user_id'))::BIGINT);

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (user_id = (current_setting('app.current_user_id'))::BIGINT);

CREATE POLICY "Users can view own knowledge" ON knowledge_base
    FOR ALL USING (user_id = (current_setting('app.current_user_id'))::BIGINT);

CREATE POLICY "Users can view own profile" ON user_profiles
    FOR ALL USING (user_id = (current_setting('app.current_user_id'))::BIGINT);

-- Создание задачи для автоматической очистки (если доступен pg_cron)
-- SELECT cron.schedule('cleanup-old-conversations', '0 2 * * *', 'SELECT cleanup_old_data(90);');

-- Вставка тестовых данных (опционально)
INSERT INTO user_profiles (user_id, username, first_name, preferences) 
VALUES (12345, 'testuser', 'Test User', '{"language": "ru", "voice_enabled": true}')
ON CONFLICT (user_id) DO NOTHING;

-- Вывод информации о созданных объектах
SELECT 'Векторная база данных настроена успешно!' AS status;
SELECT 'Таблицы созданы: conversations, knowledge_base, user_profiles' AS tables;
SELECT 'Функции созданы: search_similar_conversations, search_knowledge_base, get_user_stats, cleanup_old_data' AS functions;