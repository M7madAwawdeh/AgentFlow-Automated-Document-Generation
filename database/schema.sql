-- AgentFlow Database Schema
-- Multi-Agent AI System for Automated Documentation and Testing

CREATE DATABASE IF NOT EXISTS agentflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agentflow;

-- Projects table - stores information about analyzed codebases
CREATE TABLE projects (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    git_repository VARCHAR(500),
    git_branch VARCHAR(100) DEFAULT 'main',
    status ENUM('pending', 'analyzing', 'completed', 'failed') DEFAULT 'pending',
    configuration JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Files table - stores individual files from projects
CREATE TABLE files (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    path VARCHAR(500) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content LONGTEXT,
    file_type VARCHAR(50),
    size_bytes BIGINT UNSIGNED,
    hash_sha256 VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_file_type (file_type),
    INDEX idx_path (path)
);

-- Agent outputs table - stores results from each AI agent
CREATE TABLE agent_outputs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    agent_type ENUM('documenter', 'tester', 'security_auditor', 'performance_optimizer') NOT NULL,
    output_type ENUM('documentation', 'tests', 'security_report', 'performance_report') NOT NULL,
    content JSON NOT NULL,
    metadata JSON,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    processing_time_ms INT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_status (status)
);

-- Documentation table - stores generated documentation
CREATE TABLE documentation (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    element_type ENUM('class', 'function', 'method', 'route', 'model', 'migration') NOT NULL,
    element_name VARCHAR(255) NOT NULL,
    element_path VARCHAR(500),
    description TEXT,
    parameters JSON,
    return_value TEXT,
    examples JSON,
    code_snippets JSON,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_element_type (element_type),
    INDEX idx_element_name (element_name)
);

-- Tests table - stores generated test files
CREATE TABLE tests (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    test_type ENUM('unit', 'integration', 'feature') NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    test_content LONGTEXT NOT NULL,
    target_element VARCHAR(255),
    test_framework ENUM('phpunit', 'pest') DEFAULT 'phpunit',
    status ENUM('generated', 'applied', 'failed') DEFAULT 'generated',
    applied_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_test_type (test_type),
    INDEX idx_status (status)
);

-- Security issues table - stores security vulnerabilities found
CREATE TABLE security_issues (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    issue_type ENUM('sql_injection', 'xss', 'csrf', 'hardcoded_secret', 'insecure_deserialization', 'other') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    line_number INT UNSIGNED,
    code_snippet TEXT,
    recommendation TEXT,
    cwe_id VARCHAR(20),
    owasp_category VARCHAR(100),
    status ENUM('open', 'in_progress', 'resolved', 'false_positive') DEFAULT 'open',
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_severity (severity),
    INDEX idx_issue_type (issue_type),
    INDEX idx_status (status)
);

-- Performance issues table - stores performance optimization suggestions
CREATE TABLE performance_issues (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    issue_type ENUM('n_plus_one_query', 'missing_index', 'inefficient_loop', 'missing_cache', 'other') NOT NULL,
    severity ENUM('low', 'medium', 'high') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    line_number INT UNSIGNED,
    current_code TEXT,
    optimized_code TEXT,
    estimated_impact VARCHAR(100),
    status ENUM('open', 'in_progress', 'resolved') DEFAULT 'open',
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_severity (severity),
    INDEX idx_issue_type (issue_type),
    INDEX idx_status (status)
);

-- Analysis sessions table - stores information about analysis runs
CREATE TABLE analysis_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    session_uuid VARCHAR(36) NOT NULL UNIQUE,
    status ENUM('started', 'in_progress', 'completed', 'failed') DEFAULT 'started',
    agents_config JSON,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    total_files INT UNSIGNED DEFAULT 0,
    processed_files INT UNSIGNED DEFAULT 0,
    error_count INT UNSIGNED DEFAULT 0,
    metadata JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_session_uuid (session_uuid),
    INDEX idx_status (status)
);

-- Audit log table - tracks all AI actions and system events
CREATE TABLE audit_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED,
    session_id BIGINT UNSIGNED,
    user_id BIGINT UNSIGNED,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id BIGINT UNSIGNED,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

-- Configuration table - stores system-wide and project-specific settings
CREATE TABLE configurations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value JSON NOT NULL,
    is_global BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_config (project_id, config_key),
    INDEX idx_project_id (project_id),
    INDEX idx_config_key (config_key)
);

-- Insert default global configurations
INSERT INTO configurations (config_key, config_value, is_global) VALUES
('default_agents', '{"documenter": true, "tester": true, "security_auditor": true, "performance_optimizer": true}', TRUE),
('default_model', '"llama-3-70b"', TRUE),
('default_tone', '"professional"', TRUE),
('max_file_size', '10485760', TRUE),
('supported_file_types', '["php", "js", "vue", "blade.php", "json", "yaml", "yml"]', TRUE);

-- Create views for easier querying
CREATE VIEW project_summary AS
SELECT 
    p.id,
    p.name,
    p.status,
    p.created_at,
    COUNT(DISTINCT f.id) as total_files,
    COUNT(DISTINCT ao.id) as total_agent_outputs,
    COUNT(DISTINCT si.id) as security_issues_count,
    COUNT(DISTINCT pi.id) as performance_issues_count,
    COUNT(DISTINCT t.id) as tests_count,
    COUNT(DISTINCT d.id) as documentation_count
FROM projects p
LEFT JOIN files f ON p.id = f.project_id
LEFT JOIN agent_outputs ao ON p.id = ao.project_id
LEFT JOIN security_issues si ON p.id = si.project_id
LEFT JOIN performance_issues pi ON p.id = pi.project_id
LEFT JOIN tests t ON p.id = t.project_id
LEFT JOIN documentation d ON p.id = d.project_id
GROUP BY p.id;

-- Create indexes for better performance
CREATE INDEX idx_agent_outputs_project_agent ON agent_outputs(project_id, agent_type);
CREATE INDEX idx_security_issues_project_severity ON security_issues(project_id, severity);
CREATE INDEX idx_performance_issues_project_severity ON performance_issues(project_id, severity);
CREATE INDEX idx_files_project_path ON files(project_id, path);
CREATE INDEX idx_audit_log_project_action ON audit_log(project_id, action);
