# AgentFlow - Multi-Agent AI System for Automated Documentation and Testing

🤖 **An AI engineering team that reviews, documents, tests, and secures your code — without human intervention.**

## 🌟 Overview

AgentFlow is an intelligent, autonomous system that analyzes Laravel (or any backend) codebases using a team of AI agents to automatically generate:

- 📄 **Interactive documentation** - Clear explanations for every function, class, and route
- ✅ **Unit and integration tests** - Comprehensive test coverage with edge cases
- 🔒 **Security vulnerability reports** - OWASP Top 10 compliance and risk assessment
- ⚡ **Performance optimization suggestions** - Database queries, caching, and efficiency improvements

## 🏗️ System Architecture

AgentFlow is a hybrid **Laravel-Python** system:

- **Laravel (PHP 8.3+)**: Frontend/backend for user interaction, project management, and API gateway
- **Python AI Agents**: Backend using LangChain + LangGraph for intelligent code analysis
- **MySQL**: Central database storing code metadata, agent outputs, and user projects
- **OpenRouter**: LLM provider with models like Llama-3-70b, Mixtral, or Mistral-Large
- **Docker**: Multi-container deployment (Laravel, Python, MySQL)

## 🤖 The AI Agent Team

### 1. **AI Documenter Agent**
- Parses PHP code using AST/regex analysis
- Generates interactive documentation with examples
- Creates browsable `/docs` pages in Laravel

### 2. **Test Generator Agent**
- Identifies uncovered functions and logic
- Generates PHPUnit/Pest tests with edge cases
- Suggests optimal test file structure

### 3. **Security Auditor Agent**
- Detects SQL injection, XSS, CSRF vulnerabilities
- Scans for hardcoded secrets and insecure patterns
- References OWASP Top 10 standards

### 4. **Performance Optimizer Agent**
- Identifies N+1 queries and Eloquent anti-patterns
- Suggests caching, indexing, and eager loading
- Estimates performance impact of optimizations

### 5. **Orchestrator Agent (LangGraph Core)**
- Manages the workflow graph and agent coordination
- Handles dependencies and execution order
- Enables human-in-the-loop review

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd agentFlow-automated-document-generation
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your OpenRouter API key and other settings
```

3. **Start the system**
```bash
docker-compose up -d
```

4. **Access the application**
- Laravel App: http://localhost:8000
- Python API: http://localhost:5000
- Database: localhost:3306

### First Run

1. Visit http://localhost:8000
2. Create a new project
3. Upload your Laravel codebase
4. Watch the AI agents analyze and generate reports!

## 📁 Project Structure

```
agentflow/
├── laravel-app/                 # Laravel application
│   ├── app/Http/Controllers/   # Controllers including AIController
│   ├── resources/views/        # Blade templates
│   └── database/migrations/    # Database schema
├── python-agents/              # Python AI engine
│   ├── agents/                 # Individual AI agents
│   ├── orchestrator/           # LangGraph workflow
│   └── api/                    # FastAPI server
├── docker/                     # Docker configuration
├── config/                     # Configuration files
└── database/                   # Database schema
```

## ⚙️ Configuration

Create `.agentflow.yaml` in your project root:

```yaml
agents:
  documenter: true
  tester: true
  security: high
  performance: medium
model: llama-3-70b
tone: professional
```

## 🔌 API Integration

### Laravel → Python
```json
POST /api/analyze
{
  "project_id": 1,
  "files": [
    {"path": "app/User.php", "content": "<?php ..."},
    {"path": "routes/web.php", "content": "..."}
  ]
}
```

### Python → Laravel
```json
{
  "documentation": { ... },
  "tests": [ ... ],
  "security": [ ... ],
  "performance": [ ... ]
}
```

## 🎯 Core Features

- **Project Onboarding**: Upload codebases or connect via Git
- **AI Agent Pipeline**: Parallel execution with LangGraph orchestration
- **Interactive Dashboard**: Browsable documentation with collapsible insights
- **Comprehensive Reports**: Docs, tests, security, and performance analysis
- **One-Click Apply**: Preview and apply AI-generated improvements
- **Audit Logging**: Track all AI actions and version history

## 🛠️ Technology Stack

- **Backend**: Laravel 11, PHP 8.3+
- **Frontend**: Blade Templates, Livewire
- **AI Engine**: Python 3.11+, LangChain, LangGraph
- **LLM Provider**: OpenRouter
- **Code Analysis**: nikic/PHP-Parser, tree-sitter
- **Database**: MySQL 8.0
- **Deployment**: Docker, Docker Compose

## 🚧 Development

### Running Tests
```bash
# Laravel tests
docker-compose exec laravel-app php artisan test

# Python tests
docker-compose exec python-agents python -m pytest
```

### Adding New Agents
1. Create agent class in `python-agents/agents/`
2. Add to orchestrator workflow in `python-agents/orchestrator/graph.py`
3. Update API endpoints in `python-agents/api/server.py`

## 📊 Performance & Scaling

- **Task Queue**: Supervisor for long-running agent jobs
- **Caching**: Redis for agent outputs and analysis results
- **Parallel Processing**: LangGraph enables concurrent agent execution
- **Resource Management**: Docker resource limits and monitoring

## 🔮 Future Features

- GitHub/GitLab integration for PR analysis
- Laravel Horizon for job monitoring
- Agent self-improvement via user feedback
- OpenAPI spec generation from routes
- Multi-language support (Node.js, Python, Go)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **Community**: Join our discussions

---

**Built with ❤️ using Laravel, Python, LangChain, and LangGraph**

*Transform your codebase into a living, self-documenting, and self-testing ecosystem!*
