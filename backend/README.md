# ArthAgent Backend — AI Financial Planning System

Multi-agent financial planning system for the ET AI Hackathon 2026.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with:
- `GROQ_API_KEY`: Get from https://console.groq.com
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com

### 3. Run Tests

```bash
pytest tests/ -v
```

Expected output: All tax and FIRE calculations pass.

### 4. Start Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```

Health status — use to verify server is running.

### WebSocket: Agent Execution Stream
```
WebSocket ws://localhost:8000/ws/agent-stream?session_id=<SESSION_ID>
```

**Real-time financial plan generation.** Connect to this endpoint, and receive live agent step updates and final plan JSON.

**Message Format:**
```json
{"type": "init", "session_id": "...", "timestamp": "..."}
{"type": "agent_step", "step": "calculation_agent", "status": "started", "detail": "...", "timestamp": "..."}
...
{"type": "plan_complete", "plan": {...}, "session_id": "...", "timestamp": "..."}
```

### REST Endpoints (Placeholders for frontend integration)

**POST /api/session** — Create planning session
**POST /api/profile** — Submit user financial profile
**GET /api/plan/{session_id}** — Retrieve completed plan (WebSocket is primary)
**POST /api/cams-upload** — Upload CAMS PDF for portfolio X-ray
**POST /api/scenario** — Submit what-if scenario request

## System Architecture

### Agents (Sequential Pipeline)

1. **IntakeAgent** (`intake_agent.py`)
   - Extracts structured profile from freeform input via Groq/Llama
   - Validates Pydantic models
   
2. **CalculationAgent** (`calculation_agent.py`)
   - Runs deterministic Python math: tax, FIRE, SIP projections
   - Produces tax_analysis and fire_plan dicts

3. **RegulatoryAgent** (`regulatory_agent.py`)
   - Queries ChromaDB knowledge base for SEBI/IT Act rules
   - Flags compliance issues and missed deductions

4. **ScenarioAgent** (`scenario_agent.py`)
   - Pre-computes 3 what-if scenarios (early retirement, income bump, tax switch)
   - Enables dynamic plan re-computation without full re-run

5. **SynthesisAgent** (`synthesis_agent.py`)
   - Calls Claude Sonnet to generate structured, narrative financial plan
   - Returns JSON with executive summary, action items, implementation steps

6. **DisclaimerAgent** (`disclaimer_agent.py`)
   - Appends hardcoded SEBI disclaimer (never LLM-generated)
   - Ensures regulatory compliance

### Key Modules

- **models/** — Pydantic schemas (UserProfile, FinancialPlan, ScenarioRequest)
- **calculations/** — Pure deterministic math (tax.py, investments.py)
- **knowledge/** — ChromaDB RAG (loader.py, query.py)
- **agents/** — LangGraph nodes (all 6 agents)

## Mandatory Judging Scenarios

### 1. FIRE Plan
```python
# Inputs: age 34, ₹24L income, ₹1.8L MF, ₹6L PPF, retire at 50, ₹1.5L/month target
# Output: Monthly SIP ~₹55-65K, corpus ~₹6Cr, asset allocation glidepath
```

Run via WebSocket:
```json
{"session_id": "fire_test", "profile": {...}}
```

### 2. Tax Edge Case
```python
# Inputs: ₹18L base + ₹3.6L HRA, ₹1.5L 80C, ₹50K NPS, ₹40K home loan interest
# Output: Old regime tax ₹3.66L, New regime ₹2.3L → Recommend new regime
```

### 3. MF Portfolio X-Ray
```python
# Upload CAMS PDF → XIRR, overlap analysis, rebalancing plan
# (Portfolio module in progress)
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tax.py -v

# Run specific test
pytest tests/test_tax.py::test_tax_edge_case_old_vs_new_regime -v
```

**Expected:** All tests pass with exact numbers validated against FY 2025-26 tax slabs.

## Troubleshooting

### ChromaDB initialization fails
```bash
rm -rf backend/knowledge/db
# Restart server to reinitialize
```

### Groq/Anthropic API errors
- Verify API keys in `.env`
- Check API quota on respective dashboards
- See `audit_log` in WebSocket response for detailed errors

### Tests fail on tax calculations
- Verify you're using FY 2025-26 slabs (not outdated rates)
- Run: `pytest tests/test_tax.py -v` to see exact failures

## Production Deployment

1. Set `FASTAPI_ENV=production` in `.env`
2. Use `gunicorn` instead of `uvicorn`:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
3. Deploy to AWS Lambda, Google Cloud Run, or Docker
4. Ensure API keys are in secure environment variables (not .env file)

## Next Steps

- Build React frontend (WebSocket integration + forms)
- Implement portfolio parsing (pdfplumber CAMS extraction)
- Add couple's planning (joint income optimization)
- Mobile app (React Native)

---

**Built with ❤️ for the ET AI Hackathon 2026**
