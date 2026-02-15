# Nifty Options Intelligence

Professional analytics dashboard for discretionary options traders.

---

## 🚀 Quick Start

```bash
./start.sh
```

**Interactive menu** with options to:
- Start professional dashboard
- Verify installation  
- View logs
- Stop dashboard

**Quick commands**:
```bash
./start.sh pro      # Start dashboard
./start.sh stop     # Stop dashboard
./start.sh verify   # Check installation
```

---

## 📊 Access Dashboard

**Professional Version**: http://localhost:8501  
**Legacy Version**: http://localhost:8502

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Complete file-to-feature mapping for development |
| **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Streamlit Cloud deployment guide |
| **[CHANGELOG_V2.1.md](docs/CHANGELOG_V2.1.md)** | Version 2.1 changes and improvements |
| **[NSE_API_STATUS.md](docs/NSE_API_STATUS.md)** | NSE API status and workarounds |
| **[PHASE1_SUMMARY.md](docs/PHASE1_SUMMARY.md)** | Phase 1 implementation details |

---

## 🛠️ Development

**Add features**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md) extension points  
**Data format**: NSE option chain CSV (merged CALLS | STRIKE | PUTS)  
**Key files**: `app_pro.py`, `data_loader.py`, `metrics.py`, `visualization.py`

---

## 📁 Data Setup

Place CSV files in:
```
data/raw/monthly/WeekName/*.csv
```

Or upload via dashboard sidebar.

---

**Version**: 2.1 Professional | **Python**: 3.10+ | **License**: MIT
