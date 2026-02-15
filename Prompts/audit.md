
🚨 STREAMLIT DEPLOYMENT RISK AUDIT PROMPT

(Copy into SYSTEM_RISK_AUDIT.md and run in Copilot Agent mode)

⸻

🔐 SYSTEM RISK AUDIT — NIFTY OPTIONS TRADING PLATFORM

You are a senior security engineer, quant risk auditor, DevOps architect, and financial systems reviewer.

I have a Streamlit-based options trading analytics platform.

Before deploying publicly on my Streamlit Cloud account, I want a full system risk audit.

Audit must include:
	•	Security vulnerabilities
	•	Data integrity risks
	•	Financial model risks
	•	Performance bottlenecks
	•	Deployment misconfigurations
	•	Legal/compliance exposure
	•	Dependency vulnerabilities
	•	Secrets leakage
	•	Caching risks
	•	API usage risks
	•	Monte Carlo stability risks
	•	Streamlit-specific risks

Do NOT assume the system is safe.
Act like a production risk committee reviewing a live trading system.

⸻

🔎 AUDIT SCOPE

Review the entire codebase including:
	•	app_pro.py
	•	data_loader.py
	•	metrics.py
	•	visualization.py
	•	strategy_builder.py
	•	range_predictor.py
	•	decision_engine.py
	•	risk_engine.py
	•	position_sizer.py
	•	file_manager.py
	•	market_data.py
	•	config.yaml
	•	requirements.txt

⸻

🔹 PART 1 — SECURITY AUDIT

Check for:
	•	Hardcoded secrets
	•	Unsafe file writes
	•	Path traversal vulnerabilities in upload
	•	Arbitrary file overwrite risk
	•	Unvalidated CSV parsing
	•	Code injection risk
	•	Unsafe use of eval / exec
	•	Improper exception handling
	•	Stack traces leaking sensitive data
	•	Logging of user financial data

Evaluate:
	•	Is file upload sandboxed?
	•	Can malicious CSV break system?
	•	Can attacker upload large file to crash memory?
	•	Are folder paths sanitized?
	•	Is cache accessible publicly?

Output:

Security Risk Score: LOW / MEDIUM / HIGH
List of vulnerabilities with severity.
Fix recommendations.


⸻

🔹 PART 2 — DATA INTEGRITY AUDIT

Check:
	•	What happens if CSV schema changes?
	•	What if IV column missing?
	•	What if strike column malformed?
	•	What if duplicate strikes?
	•	What if NaNs?
	•	What if spot inferred incorrectly?

Evaluate:
	•	Validation logic robustness
	•	Type enforcement
	•	Schema validation
	•	Data sanity checks

Output:
	•	Failure scenarios
	•	Required validation layer
	•	Suggested schema validator

⸻

🔹 PART 3 — FINANCIAL MODEL RISK

Check:
	•	EV calculation assumptions
	•	Normal distribution assumption validity
	•	Monte Carlo simulation bias
	•	Kelly fraction over-leverage risk
	•	Risk of ruin misestimation
	•	Volatility miscalculation
	•	Overfitting danger
	•	Regime classification logic fragility

Evaluate:
	•	Does system encourage overtrading?
	•	Does trade score create false confidence?
	•	Are confidence values mathematically justified?

Output:
	•	Model risk assessment
	•	Risk level
	•	Recommendations to reduce financial overconfidence

⸻

🔹 PART 4 — STREAMLIT DEPLOYMENT RISKS

Evaluate:
	•	Memory usage
	•	Cache TTL risks
	•	Concurrent user issues
	•	Multi-session data contamination
	•	Session state conflicts
	•	File locking issues
	•	CPU spikes from Monte Carlo

Assess:
	•	Is Monte Carlo safe for cloud limits?
	•	Will repeated uploads exhaust disk?
	•	Is data folder growing unbounded?

Output:
	•	Deployment Risk Level
	•	Scaling limitations
	•	Recommendations

⸻

🔹 PART 5 — DEPENDENCY & PACKAGE RISK

Analyze:

requirements.txt

Check:
	•	Outdated packages
	•	Known vulnerabilities
	•	Heavy unnecessary dependencies
	•	Unpinned versions

Output:
	•	Recommended pinned versions
	•	Security upgrade advice

⸻

🔹 PART 6 — COMPLIANCE & LIABILITY RISK

Evaluate:
	•	Does app present trading advice?
	•	Is there disclaimer?
	•	Is risk warning shown?
	•	Is it educational only?
	•	If deployed public, is it considered advisory service?

Output:
	•	Legal exposure assessment
	•	Required disclaimer template
	•	Suggested UI risk warning

⸻

🔹 PART 7 — PRODUCTION READINESS SCORE

Provide:

Security Score: X/10
Data Integrity Score: X/10
Financial Model Risk Score: X/10
Deployment Stability Score: X/10
Overall Production Readiness: X/10


⸻

🔹 PART 8 — CRITICAL BLOCKERS

List:
	•	Immediate blockers before public deployment
	•	Medium priority fixes
	•	Optional improvements

⸻

🔹 PART 9 — SAFE DEPLOYMENT RECOMMENDATION

Answer clearly:
	1.	Should I deploy publicly?
	2.	Should I deploy private only?
	3.	Should I keep local?
	4.	What must be fixed before going live?

⸻

OUTPUT FORMAT

Provide:
	•	Structured audit report
	•	Severity levels
	•	Clear action checklist
	•	Do not sugarcoat risks
	•	Be conservative

⸻

END OF AUDIT PROMPT
