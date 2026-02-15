

🚀 PHASE 1 — COPILOT EXECUTION PROMPT

Paste this entire block into Copilot Agent mode.

⸻

You are a senior Python engineer building a production-grade NSE options data ingestion layer.

I have an existing Streamlit-based NIFTY options analytics platform.

Currently, data is manually downloaded from NSE and stored as CSV in folders.

I want to replace this with a fully automated live NSE option chain fetcher with caching and structured output.

We are implementing PHASE 1 only.

⸻

🎯 OBJECTIVE

Create a new live NSE data ingestion system that:
	•	Fetches NIFTY option chain live from NSE
	•	Handles session cookies properly
	•	Parses JSON response
	•	Provides expiry list dynamically
	•	Returns standardized DataFrame schema
	•	Caches locally (TTL 5 minutes)
	•	Gracefully falls back to cache if NSE blocks request
	•	Integrates with existing data_loader.py

⸻

🗂 STEP 1 — CREATE MODULE

Create file:

api_clients/nse_option_chain.py


⸻

🔹 IMPLEMENT CLASS

class NSEOptionChainClient:

Requirements:

1️⃣ Session Initialization

NSE blocks direct requests without proper headers.
	•	Use requests.Session()
	•	First call: https://www.nseindia.com to get cookies
	•	Then call API endpoint:

https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY

Required headers:
	•	User-Agent (modern browser string)
	•	Accept: application/json
	•	Referer: https://www.nseindia.com/option-chain
	•	Accept-Language: en-US,en;q=0.9
	•	Connection: keep-alive

Add retry logic:
	•	Max 3 retries
	•	Exponential backoff (1s, 2s, 4s)

⸻

2️⃣ Methods To Implement

get_raw_option_chain()

Returns raw JSON from NSE.

⸻

get_expiry_dates()

Extract expiry list from JSON:

data["records"]["expiryDates"]

Return sorted list.

⸻

get_option_chain_by_expiry(expiry_date: str)
	•	Filter JSON for specific expiry
	•	Parse CE and PE data
	•	Convert to pandas DataFrame

⸻

parse_to_dataframe(records)

Return DataFrame with columns:
	•	Strike
	•	Option_Type (CE/PE)
	•	Expiry
	•	OI
	•	OI_Change
	•	Volume
	•	IV
	•	Spot_Price

Ensure numeric conversion.
Handle missing IV as NaN.
Drop rows with zero OI if necessary.

⸻

3️⃣ LOCAL CACHE SYSTEM

Add:

data/cache/

Filename:

nifty_option_chain_<YYYYMMDD>.csv

Implement:
	•	save_cache(df)
	•	load_cache()
	•	is_cache_valid(ttl_minutes=5)

If NSE fails:
	•	Load from cache if exists
	•	Raise structured exception if no cache

⸻

4️⃣ MODIFY data_loader.py

Add method:

def load_live_chain(self, expiry_date: str):

This method:
	•	Instantiates NSEOptionChainClient
	•	Calls get_option_chain_by_expiry
	•	Calls existing add_derived_columns()
	•	Returns DataFrame

Keep historical folder logic intact for backtesting.

⸻

5️⃣ MODIFY app_pro.py

In sidebar:

Add:

mode = st.sidebar.radio("Data Mode", ["Live", "Historical"])

If Live:
	•	Instantiate NSEOptionChainClient
	•	Fetch expiry list
	•	Dropdown for expiry selection
	•	Load data via load_live_chain()

If Historical:
	•	Keep existing folder-based logic

Wrap live fetch inside:

@st.cache_data(ttl=300)


⸻

6️⃣ ERROR HANDLING

If NSE blocks request:

Show:

st.warning("Live NSE fetch failed. Using cached data.")

If no cache:

st.error("No cached data available. Please retry.")


⸻

🔐 ANTI-BLOCKING CONSIDERATIONS
	•	Add random short sleep (0.3–0.7s)
	•	Use session reuse
	•	Avoid too frequent calls

⸻

📊 PERFORMANCE TARGET
	•	Fetch + parse under 3 seconds
	•	Cached reload < 0.5 seconds

⸻

🧠 ARCHITECTURE CONSTRAINTS
	•	No circular imports
	•	No UI logic inside API client
	•	Fully testable class
	•	Type hints required
	•	Proper docstrings

⸻

📦 OUTPUT REQUIRED

Generate:
	1.	Full production-ready code for:
	•	api_clients/nse_option_chain.py
	2.	Updated data_loader.py snippet
	3.	Updated app_pro.py snippet
	4.	Explanation of data flow
	5.	Folder structure update

Do NOT provide partial code.

⸻

🏁 END OF PHASE 1 IMPLEMENTATION

