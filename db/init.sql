-- SQL скрипт для инициализации базы данных StereoBrother Bot

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    subscription_active BOOLEAN DEFAULT FALSE,
    subscription_plan VARCHAR(50),
    subscription_started_at TIMESTAMP WITH TIME ZONE,
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    subscription_auto_renew BOOLEAN DEFAULT TRUE,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Создание таблицы использования пользователей
CREATE TABLE IF NOT EXISTS user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daily_generations INTEGER DEFAULT 0,
    monthly_generations INTEGER DEFAULT 0,
    total_generations INTEGER DEFAULT 0,
    last_processing_date TIMESTAMP WITH TIME ZONE,
    daily_reset_date DATE DEFAULT CURRENT_DATE,
    monthly_reset_date DATE DEFAULT DATE_TRUNC('month', CURRENT_DATE),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Создание таблицы задач обработки
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    duration FLOAT,
    sample_rate INTEGER,
    channels INTEGER,
    format VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    processing_type VARCHAR(50),
    parameters JSONB,
    result_url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Создание таблицы результатов обработки
CREATE TABLE IF NOT EXISTS processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES processing_tasks(id) ON DELETE CASCADE,
    processing_type VARCHAR(50) NOT NULL,
    output_filename VARCHAR(255) NOT NULL,
    output_path VARCHAR(500),
    output_format VARCHAR(50),
    file_size BIGINT,
    duration FLOAT,
    quality_metrics JSONB,
    download_url VARCHAR(500),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы подписок
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method VARCHAR(50),
    payment_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы платежей
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_payment_id VARCHAR(255),
    provider_data JSONB,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы сессий
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500),
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_token)
);

-- Создание таблицы моделей ИИ
CREATE TABLE IF NOT EXISTS ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_size BIGINT,
    accuracy FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, version)
);

-- Создание таблицы метрик обработки
CREATE TABLE IF NOT EXISTS processing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES processing_tasks(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    processing_type VARCHAR(50) NOT NULL,
    duration_ms INTEGER NOT NULL,
    input_file_size BIGINT,
    output_file_size BIGINT,
    quality_score FLOAT,
    model_id UUID REFERENCES ai_models(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы системных логов
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,
    module VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для улучшения производительности

-- Индексы для таблицы users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_subscription_active ON users(subscription_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Индексы для таблицы user_usage
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_daily_reset_date ON user_usage(daily_reset_date);
CREATE INDEX IF NOT EXISTS idx_user_usage_monthly_reset_date ON user_usage(monthly_reset_date);

-- Индексы для таблицы processing_tasks
CREATE INDEX IF NOT EXISTS idx_processing_tasks_user_id ON processing_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_created_at ON processing_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_processing_type ON processing_tasks(processing_type);

-- Индексы для таблицы processing_results
CREATE INDEX IF NOT EXISTS idx_processing_results_task_id ON processing_results(task_id);
CREATE INDEX IF NOT EXISTS idx_processing_results_processing_type ON processing_results(processing_type);
CREATE INDEX IF NOT EXISTS idx_processing_results_created_at ON processing_results(created_at);

-- Индексы для таблицы subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(period_end);

-- Индексы для таблицы payments
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);

-- Индексы для таблицы user_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_revoked ON user_sessions(revoked);

-- Индексы для таблицы processing_metrics
CREATE INDEX IF NOT EXISTS idx_processing_metrics_user_id ON processing_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_created_at ON processing_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_processing_type ON processing_metrics(processing_type);

-- Индексы для таблицы system_logs
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);

-- Создание триггеров для автоматического обновления updated_at

-- Триггер для таблицы users
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Триггер для таблицы user_usage
CREATE OR REPLACE FUNCTION update_user_usage_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_usage_updated_at
    BEFORE UPDATE ON user_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_user_usage_updated_at();

-- Триггер для таблицы processing_tasks
CREATE OR REPLACE FUNCTION update_processing_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_processing_tasks_updated_at
    BEFORE UPDATE ON processing_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_processing_tasks_updated_at();

-- Триггер для таблицы subscriptions
CREATE OR REPLACE FUNCTION update_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_subscriptions_updated_at();

-- Создание представлений для удобства

-- Представление для статистики пользователей
CREATE OR REPLACE VIEW user_statistics AS
SELECT
    u.id,
    u.email,
    u.username,
    u.created_at,
    u.subscription_active,
    u.subscription_ends_at,
    COALESCE(uu.daily_generations, 0) as daily_generations,
    COALESCE(uu.monthly_generations, 0) as monthly_generations,
    COALESCE(uu.total_generations, 0) as total_generations,
    COUNT(DISTINCT pt.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN pt.status = 'completed' THEN pt.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN pt.status = 'failed' THEN pt.id END) as failed_tasks
FROM users u
LEFT JOIN user_usage uu ON u.id = uu.user_id
LEFT JOIN processing_tasks pt ON u.id = pt.user_id
GROUP BY u.id, uu.daily_generations, uu.monthly_generations, uu.total_generations;

-- Представление для статистики обработки
CREATE OR REPLACE VIEW processing_statistics AS
SELECT
    DATE(created_at) as processing_date,
    processing_type,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
    AVG(progress) as avg_progress,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_processing_time_seconds
FROM processing_tasks
GROUP BY DATE(created_at), processing_type;

-- Вставка тестовых данных (только для разработки)

-- Тестовый пользователь
INSERT INTO users (id, email, username, password_hash, is_active, is_verified, subscription_active, subscription_plan, subscription_ends_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'test@stereobrother.com',
    'testuser',
    -- Пароль: Test123! (хеш bcrypt)
    '$2b$12$LQv3c1yqBWVHxkd0qB6gB.Ff6uVrJYIVFjLJZf8W8n8nL9dZQY8W2',
    TRUE,
    TRUE,
    TRUE,
    'premium',
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (email) DO NOTHING;

-- Тестовые данные использования
INSERT INTO user_usage (user_id, daily_generations, monthly_generations, total_generations, last_processing_date)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    5,
    25,
    100,
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
) ON CONFLICT (user_id) DO NOTHING;

-- Тестовые модели ИИ
INSERT INTO ai_models (name, version, model_type, description, is_active)
VALUES
    ('demucs', 'v4', 'stem_separation', 'Модель для разделения аудио на дорожки', TRUE),
    ('spleeter', '2.4.0', 'stem_separation', 'Модель для разделения аудио на дорожки', TRUE),
    ('audio_enhancer', '1.0', 'enhancement', 'Модель для улучшения качества аудио', TRUE),
    ('noise_reduction', '1.2', 'denoise', 'Модель для удаления шумов', TRUE),
    ('ai_mastering', '2.0', 'mastering', 'Модель для автоматического мастеринга', TRUE)
ON CONFLICT (name, version) DO NOTHING;

-- Создание пользователя для приложения (если нужно)
-- CREATE USER stereobrother_app WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE stereobrother_db TO stereobrother_app;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stereobrother_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO stereobrother_app;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Таблица пользователей системы';
COMMENT ON TABLE user_usage IS 'Таблица использования лимитов пользователями';
COMMENT ON TABLE processing_tasks IS 'Таблица задач обработки аудио';
COMMENT ON TABLE processing_results IS 'Таблица результатов обработки аудио';
COMMENT ON TABLE subscriptions IS 'Таблица подписок пользователей';
COMMENT ON TABLE payments IS 'Таблица платежей';
COMMENT ON TABLE user_sessions IS 'Таблица сессий пользователей';
COMMENT ON TABLE ai_models IS 'Таблица моделей искусственного интеллекта';
COMMENT ON TABLE processing_metrics IS 'Таблица метрик обработки';
COMMENT ON TABLE system_logs IS 'Таблица системных логов';

-- Проверка создания таблиц
SELECT 'База данных StereoBrother успешно инициализирована' as message;
