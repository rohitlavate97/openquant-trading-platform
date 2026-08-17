# Milestone 15: AI Advisory Suite

**Status:** Completed  
**Branch:** `milestone-15-ai-advisory-suite`  
**PR:** [milestone-15-ai-advisory-suite](https://github.com/rohitlavate97/openquant-trading-platform/pull/new/milestone-15-ai-advisory-suite)  
**Date:** 2026-08-17  

---

## 1. Objectives & Architectural Decisions

- **Non-Negotiable Rule 3 Guardrail Implementation**:
  - AI Output is strictly advisory. AI-generated code is forbidden from direct execution into live or paper trading.
  - All generated code is tagged with `review_status = PENDING_HUMAN_REVIEW` and requires explicit human review and sign-off before importing as a DRAFT strategy.
  - Strategies must strictly progress through the 7-stage promotion gate (Draft → Backtested → Paper → Live).
- **AI Strategy Code Generator ([`ai_advisory_engine.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/adapters/ai/ai_advisory_engine.py))**:
  - Synthesizes robust Python quant strategy source conforming to `BaseStrategy` lifecycle hooks (`on_start`, `on_bar`, `on_stop`).
  - Automatically runs Sandbox AST Static Analysis ([`ast_validator.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/adapters/sandbox/ast_validator.py)) before presenting code to the user, verifying that no prohibited builtins, reflection attributes, or unauthorized I/O modules are included.
- **AI Log & Telemetry Analyzer ([`ai_advisory_service.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/application/services/ai_advisory_service.py))**:
  - Scans system and trading telemetry logs for operational anomalies:
    - Pre-trade risk rejection clusters (`RISK_REJECTION_CLUSTER`).
    - Emergency trading halts (`KILL_SWITCH_TRIGGERED`).
    - Market data staleness warnings (`DATA_STALENESS_WARNING`).
  - Computes platform health score (0.0 to 100.0%) and provides root-cause diagnosis with recommended remediation actions.
- **Explainable Risk Advisor**:
  - Translates cryptic risk engine rejection reasons (Rules 2, 4, 5, 7, 8) into plain-English explanations.
  - Generates actionable parameter adjustment recommendations with expected safety score impact.
- **AI Advisory REST API ([`ai_advisory.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/interfaces/api/v1/endpoints/ai_advisory.py))**:
  - `POST /api/v1/ai/generate-strategy`: Generate quant strategy with AST validation.
  - `POST /api/v1/ai/approve/{generation_id}`: Mandatory human sign-off & import as draft strategy.
  - `POST /api/v1/ai/analyze-logs`: Automated log anomaly scanning.
  - `POST /api/v1/ai/explain-risk`: Explainable risk diagnostics.
- **Frontend AI Advisory Suite UI ([`AIAdvisorySuitePage.tsx`](file:///D:/Projects/AI/openquant-trading-platform/frontend/src/features/ai-advisory/AIAdvisorySuitePage.tsx))**:
  - Strategy Code Generator with AST Compliance Badge and Human Sign-Off button.
  - Log & Telemetry Analyzer with health score gauge and anomaly root-cause breakdown.
  - Explainable Risk Advisor with risk breach simulation and suggested parameter pills.

---

## 2. Deliverables & Files Created

- **Backend**:
  - `src/openquant/domain/models/ai_advisory.py`
  - `src/openquant/domain/ports/ai_advisory_port.py`
  - `src/openquant/adapters/ai/ai_advisory_engine.py`
  - `src/openquant/application/services/ai_advisory_service.py`
  - `src/openquant/interfaces/api/v1/endpoints/ai_advisory.py`
- **Frontend**:
  - `src/types/ai_advisory.ts`
  - `src/features/ai-advisory/AIAdvisorySuitePage.tsx`
  - `src/features/ai-advisory/AIAdvisorySuitePage.test.tsx`
  - `src/components/layout/Sidebar.tsx`
  - `src/App.tsx`
- **Tests**:
  - `backend/tests/unit/domain/test_ai_advisory_models.py`
  - `backend/tests/unit/adapters/test_ai_advisory_engine.py`
  - `backend/tests/unit/application/test_ai_advisory_service.py`
  - `backend/tests/integration/test_ai_advisory_api.py`

---

## 3. Test & Verification Results

- **Backend Pytest Suite**: **126 passed in 24.81s** (85% code coverage)
- **Hexagonal Boundary Test**: **Passed** (0 unauthorized imports in domain)
- **Frontend Vitest Suite**: **33 passed in 9.40s**
- **Frontend Type Check (`tsc --noEmit`)**: **0 errors**
- **Frontend Production Bundle Build**: **Success (`dist/` built in 5.24s)**
