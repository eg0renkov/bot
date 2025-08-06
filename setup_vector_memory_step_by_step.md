# Пошаговая настройка векторной памяти в Supabase

## 1. Включение расширения pgvector
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 2. Создание основных таблиц
```sql
-- Таблица диалогов
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица базы знаний
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

-- Таблица профилей
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
```

## 3. Создание индексов
```sql
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base(user_id);

-- Векторные индексы
CREATE INDEX IF NOT EXISTS idx_conversations_embedding ON conversations 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding ON knowledge_base 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## 4. После выполнения всех команд
Перезапустите бота - векторная память должна заработать!

## Проверка готовности
В боте перейдите: Меню → Память бота → должна появиться галочка "✅ Активна"