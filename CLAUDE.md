# AI Agent Orchestrator - Project Guide

이 프로젝트는 20개 전문 에이전트가 협력하는 동적 AI 자동화 프레임워크입니다.
MCP, Skills, Agent, Harness를 상황에 맞게 최적으로 연결하고 동적으로 변동합니다.

## Project Info

- **Language**: python
- **Framework**: unknown
- **Files**: 49
- **Branch**: `claude/ai-agent-automation-dG9xU`
- **Remote**: `http://local_proxy@127.0.0.1:43333/git/hisosic/port_check`

## Available Agents (20 Specialists)

| Agent | Priority | Capabilities |
|-------|----------|-------------|
| **context_engine** | 100 | context, project_detection, language_detection, framework_detection |
| **workflow_coordinator** | 95 | workflow, orchestration, multi_step, coordination |
| **code_analyzer** | 85 | code_analysis, static_analysis, ast, complexity |
| **security_auditor** | 85 | security, vulnerability, audit, secrets |
| **error_diagnostor** | 80 | error, bug, diagnose, traceback |
| **mcp_connector** | 80 | mcp, server_discovery, tool_discovery, integration |
| **test_orchestrator** | 80 | test, testing, unittest, pytest |
| **skill_composer** | 75 | skill, chain, compose, pipeline |
| **code_reviewer** | 70 | review, quality, convention, lint |
| **performance_optimizer** | 70 | performance, optimization, profiling, speed |
| **dependency_manager** | 65 | dependency, dependencies, package, library |
| **cicd_integrator** | 60 | ci, cd, pipeline, github_actions |
| **refactor_advisor** | 60 | refactor, restructure, simplify, extract |
| **api_architect** | 55 | api, endpoint, rest, route |
| **config_optimizer** | 55 | config, configuration, settings, env |
| **deploy_manager** | 55 | deploy, deployment, release, kubernetes |
| **doc_generator** | 55 | documentation, docs, readme, docstring |
| **data_flow_tracer** | 45 | dataflow, data_flow, trace, flow |
| **log_analyzer** | 45 | log, logging, error_log, monitor |
| **resource_monitor** | 40 | resource, memory, cpu, disk |

## Quick Start

```bash
# Analyze a project
python -m ai_orchestrator --task "analyze this project"

# Run specific agents
python -m ai_orchestrator --run-agents security_auditor,code_analyzer

# Generate MCP and Claude configs
python -m ai_orchestrator --generate-config

# Start as MCP server
python -m ai_orchestrator --mcp-server context_engine

# List all agents
python -m ai_orchestrator --list-agents
```

## Architecture

```
Task → Router (capability scoring) → Execution Plan (DAG)
  ↓
Context Engine → [Agent Group 1] → [Agent Group 2] → ... → Results
  ↕                    ↕                    ↕
         Event Bus (async pub/sub for inter-agent communication)
```

### Core Components

- **Engine**: Central orchestrator - discovers, registers, and executes agents
- **Router**: Scores agents by capability match and builds execution plans
- **Registry**: Dynamic agent store with health tracking
- **Event Bus**: Async pub/sub for decoupled agent communication
- **Context**: Shared data bag that flows through the agent pipeline
- **Plugin Loader**: Auto-discovers agents at startup (supports external plugins)

## MCP Integration

Agents that expose `as_mcp_tools()` are automatically available as MCP servers.
The framework generates `settings.json` with all MCP server entries.

MCP-enabled agents:
- **code_analyzer**: analyze_code
- **config_optimizer**: optimize_config
- **context_engine**: analyze_project
- **error_diagnostor**: diagnose_error
- **mcp_connector**: discover_mcp_servers, generate_mcp_config
- **security_auditor**: security_audit
- **skill_composer**: compose_skill, list_skills
- **test_orchestrator**: run_tests
- **workflow_coordinator**: plan_workflow, list_patterns

## Adding New Agents

1. Create a new file in `ai_orchestrator/agents/`
2. Subclass `BaseAgent` and implement `execute()`
3. Declare `name`, `capabilities`, `input_types`, `output_types`, `priority`
4. The agent is auto-discovered on next startup - zero config needed

For external plugins, set `AI_ORCHESTRATOR_PLUGINS=/path/to/plugins`
