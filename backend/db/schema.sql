CREATE TABLE IF NOT EXISTS knowledge_nodes (
    node_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    name TEXT NOT NULL,
    grade INTEGER,
    semester INTEGER,
    chapter TEXT,
    prerequisites TEXT DEFAULT '[]',
    exam_weight TEXT DEFAULT 'medium',
    exam_points TEXT,
    estimated_minutes INTEGER DEFAULT 30,
    courseware_path TEXT,
    teachany_node TEXT,                 -- 官方TeachAny课件挂载点(node_id)
    curriculum_points TEXT DEFAULT '[]', -- 课标要求(JSON)，供课件生成与教材对齐
    domain TEXT                         -- 领域(number-algebra/geometry/statistics等)，知识地图分组用
);

CREATE TABLE IF NOT EXISTS mastery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    question_id TEXT,
    correct INTEGER NOT NULL,
    time_spent_sec INTEGER,
    error_type TEXT,
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

CREATE TABLE IF NOT EXISTS mastery_summary (
    node_id TEXT PRIMARY KEY,
    mastery REAL DEFAULT 0,
    status TEXT DEFAULT 'not_started',
    last_practice TEXT,
    total_attempts INTEGER DEFAULT 0,
    correct_rate REAL DEFAULT 0,
    next_review TEXT,
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    source TEXT,
    type TEXT DEFAULT 'choice',
    difficulty INTEGER DEFAULT 1,
    question TEXT NOT NULL,
    options TEXT,
    answer TEXT NOT NULL,
    steps TEXT,
    common_errors TEXT,
    tags TEXT DEFAULT '[]',
    exam_frequency INTEGER DEFAULT 0,
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

CREATE TABLE IF NOT EXISTS error_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    first_error_time TEXT DEFAULT (datetime('now')),
    error_count INTEGER DEFAULT 1,
    error_type TEXT,
    review_stage INTEGER DEFAULT 0,
    next_review TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS daily_plans (
    date TEXT PRIMARY KEY,
    plan TEXT NOT NULL,
    actual TEXT,
    total_minutes INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,
    math_minutes INTEGER DEFAULT 0,
    physics_minutes INTEGER DEFAULT 0,
    english_minutes INTEGER DEFAULT 0,
    math_correct_rate REAL,
    physics_correct_rate REAL,
    english_correct_rate REAL,
    questions_total INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    nodes_learned TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'custom',   -- practice/courseware/memory/custom
    subject TEXT,
    node_id TEXT,
    target_count INTEGER DEFAULT 0,
    deadline TEXT NOT NULL,                 -- YYYY-MM-DD
    repeat_frequency TEXT,                  -- null/daily/weekly
    repeat_end TEXT,
    note TEXT,
    status TEXT DEFAULT 'active',           -- active/completed/expired
    created_at TEXT DEFAULT (datetime('now','localtime')),
    completed_at TEXT,
    result_data TEXT                        -- JSON: {correct_rate, time_spent, ...}
);

CREATE TABLE IF NOT EXISTS memory_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    category TEXT,                          -- vocab/grammar/reading_words/poem/facts
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    audio_url TEXT,
    source TEXT,
    difficulty INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memory_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    stage INTEGER DEFAULT 0,               -- 0-6
    review_date TEXT NOT NULL,             -- YYYY-MM-DD
    correct_streak INTEGER DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    last_reviewed TEXT,
    FOREIGN KEY (card_id) REFERENCES memory_cards(id)
);
