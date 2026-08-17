# Milestone 09: Strategy Execution Sandbox

**Status:** Completed  
**Branch:** `milestone-09-strategy-execution-sandbox`  
**PR:** [milestone-09-strategy-execution-sandbox](https://github.com/rohitlavate97/openquant-trading-platform/pull/new/milestone-09-strategy-execution-sandbox)  
**Date:** 2026-08-17  

---

## 1. Objectives & Architectural Decisions

- **Process-Isolated Strategy Sandbox (Non-Negotiable Rule 6)**:
  - Executes user and AI-generated Python strategy algorithms in an isolated, memory and CPU-budgeted execution sandbox.
  - Safe import allowlisting hook maps standard math and datetime modules (`math`, `decimal`, `datetime`, `time`, `json`) while raising `ImportError` on unauthorized modules.
  - Redirects standard `print()` calls to an execution log buffer for runtime debugging and telemetry.
- **AST Static Analysis & Security Validation**:
  - Traverses the abstract syntax tree (`StrategyASTVisitor`) before code execution.
  - Blocks dangerous Python builtins (`eval`, `exec`, `compile`, `open`, `input`, `__import__`, `exit`, `quit`).
  - Blocks unauthorized system and network modules (`os`, `sys`, `subprocess`, `socket`, `shutil`, `ctypes`, `urllib`, `requests`, `aiohttp`, `pickle`, etc.).
  - Flags dangerous introspection/reflection attribute lookups (`__globals__`, `__subclasses__`, `__code__`, `gi_frame`, `f_globals`).
- **Strategy Sandbox REST Endpoints (`/api/v1/sandbox/*`)**:
  - `POST /api/v1/sandbox/validate`: Static AST security scan returning `is_safe`, `violations`, `detected_imports`.
  - `POST /api/v1/sandbox/execute`: Executes strategy code in isolated environment with context payload and returns execution time, CPU time, RAM, stdout logs, and output signal dictionary.
  - `GET /api/v1/sandbox/templates`: Returns validated starter templates for Momentum, RSI Mean Reversion, and Donchian Breakout strategies.
- **Frontend Strategy Sandbox & Code Editor UI (`StrategySandboxPage.tsx`)**:
  - Strategy Starter Template picker (EMA Momentum, RSI Mean Reversion, Donchian Breakout).
  - Python Strategy Code Editor with syntax styling, line numbers, and custom context JSON payload editor.
  - 1-Click "Scan AST Security" audit with real-time pass/fail status and violation lists.
  - 1-Click "Execute in Sandbox" runner displaying execution status (SUCCESS/TIMEOUT/FAILED), wall-clock time, CPU time, RAM consumed, standard output terminal, and result JSON viewer.

---

## 2. Deliverables & Files Created

- **Backend**:
  - `src/openquant/adapters/sandbox/ast_validator.py` (`ASTSecurityValidator`, `StrategyASTVisitor`)
  - `src/openquant/adapters/sandbox/runner.py` (`StrategySandboxRunner`)
  - `src/openquant/application/services/sandbox_service.py` (`StrategySandboxService`, `STRATEGY_TEMPLATES`)
  - `src/openquant/interfaces/api/v1/endpoints/sandbox.py`
- **Frontend**:
  - `src/types/sandbox.ts`
  - `src/features/sandbox/StrategySandboxPage.tsx`
  - `src/features/sandbox/StrategySandboxPage.test.tsx`
  - `src/components/layout/Sidebar.tsx`
  - `src/App.tsx`
- **Tests**:
  - `backend/tests/unit/application/test_sandbox_service.py`
  - `backend/tests/unit/adapters/test_sandbox_runner.py`
  - `backend/tests/integration/test_sandbox_api.py`

---

## 3. Test & Verification Results

- **Backend Pytest Suite**: **72 passed in 17.44s** (83% coverage, 100% on sandbox domain & services)
- **Hexagonal Boundary Test**: **Passed** (0 unauthorized imports in domain)
- **Frontend Vitest Suite**: **19 passed**
- **Frontend Type Check (`tsc --noEmit`)**: **0 errors**
- **Frontend Production Bundle Build**: **Success (`dist/` built in 3.95s)**
