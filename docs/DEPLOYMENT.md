# 🚀 Streamlit Cloud Deployment Guide

## Quick Start (5 minutes)

### 1. Prerequisites
- GitHub account
- Streamlit Cloud account (free tier available at [share.streamlit.io](https://share.streamlit.io))
- This repository pushed to GitHub

### 2. Deploy Steps

#### Option A: New Repository
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Nifty Options Intelligence Dashboard"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/nifty-options-dashboard.git
git branch -M main
git push -u origin main
```

#### Option B: Existing Repository
```bash
git add .
git commit -m "feat: professional dashboard ready for deployment"
git push
```

### 3. Deploy on Streamlit Cloud

1. **Visit**: [share.streamlit.io](https://share.streamlit.io)
2. **Click**: "New app"
3. **Select**:
   - Repository: `YOUR_USERNAME/nifty-options-dashboard`
   - Branch: `main`
   - Main file path: `app_pro.py`
4. **Click**: "Deploy!"

⏱️ Deployment takes ~2-3 minutes.

### 4. Configure Data Upload

Since data files are ignored (see `.gitignore`), users must upload their own CSV files:

**In the deployed app**:
1. Select "📤 Upload" in sidebar
2. Upload option chain CSV files
3. Analysis begins automatically

---

## Local Testing

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app_pro.py
```

### Access
Open browser to: `http://localhost:8501`

---

## File Structure

```
Trading/
├── app_pro.py              # Main dashboard (Streamlit Cloud entry point)
├── data_loader.py          # CSV parser for NSE option chains
├── metrics.py              # PCR, Max Pain, IV calculations
├── visualization.py        # Plotly charts
├── insights.py             # Pattern detection
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── analysis/
│   ├── range_predictor.py # Next-day range predictions
│   ├── strategy_builder.py # Option strategies
│   └── comparisons.py     # Week-over-week analysis
└── utils/
    ├── assertion_rules.py  # Market regime rules
    ├── config_loader.py    # YAML config
    └── date_utils.py       # Date helpers
```

---

## Configuration

### Streamlit Cloud Settings

**Advanced Settings** (in deployment panel):
- Python version: `3.10` or higher
- Secrets: Not required (all data uploaded by user)
- Resources: Default (512 MB memory sufficient)

### Custom Theme

Theme is configured in `.streamlit/config.toml`:
- Primary color: Blue (`#1f77b4`)
- Background: White
- Font: Sans serif

To customize, edit before deployment.

---

## Data Format

### Required CSV Structure

NSE option chain format with columns:
```
CALLS_OI | CALLS_Chng_in_OI | CALLS_Volume | CALLS_IV | ... | STRIKE | ... | PUTS_OI | PUTS_Chng_in_OI | ...
```

**Column separation**: `STRIKE` column separates call data (left) from put data (right).

### Sample Data

For testing, use included samples:
```
Options/Monthly/Feb14/option-chain-ED-NIFTY-30-Mar-2026.csv
```

---

## Troubleshooting

### Issue: "No data found"
**Solution**: Ensure CSV files are uploaded or folder path is correct.

### Issue: "Module not found"
**Solution**: Check `requirements.txt` includes all dependencies. Redeploy.

### Issue: Charts not rendering
**Solution**: Clear browser cache. Check if data has required columns.

### Issue: Slow performance
**Solution**: 
- Reduce strike range in sidebar
- Use fewer weeks for historical analysis
- Streamlit Cloud free tier has memory limits (consider upgrading)

---

## Performance Optimization

### Implemented
✅ `@st.cache_data` on data loading (1-hour TTL)  
✅ Lazy loading of charts (only render active tab)  
✅ Efficient Plotly rendering  
✅ Minimal state management  

### Future Enhancements
- [ ] Persistent storage (cloud database)
- [ ] Real-time API integration (Yahoo Finance cached)
- [ ] WebSocket for live updates
- [ ] Redis caching layer

---

## Security Notes

🔒 **Data Privacy**: All uploaded files are processed in-memory only. No data persists after session ends.

🚫 **No Secrets**: Dashboard requires no API keys or credentials (unless adding real-time data).

⚠️ **Public Access**: Streamlit Cloud apps are public by default. For private deployment:
1. Enable authentication in Streamlit Cloud settings
2. Share with specific email addresses only

---

## Updating the Dashboard

### Push Updates
```bash
# Make changes locally
git add .
git commit -m "feat: add new feature"
git push

# Streamlit Cloud auto-detects changes and redeploys
```

⏱️ Auto-deployment takes ~1-2 minutes.

### Force Restart
In Streamlit Cloud dashboard:
1. Click "Manage app"
2. Click "Reboot app"

---

## Monitoring

### Streamlit Cloud Dashboard
- View logs
- Monitor resource usage
- Check visitor analytics

### Local Logs
```bash
tail -f nohup.out
```

---

## Cost

### Free Tier (Sufficient for most users)
- 1 app
- Public repository required
- 1 GB storage
- Unlimited viewers

### Pro Tier ($20/month)
- 3 apps
- Private repositories
- 10 GB storage
- Custom authentication

---

## Support

- **Documentation**: [docs.streamlit.io](https://docs.streamlit.io)
- **Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **Issues**: GitHub Issues tab

---

## Next Steps

After deployment:
1. ✅ Test all 5 tabs with sample data
2. ✅ Share public URL with team
3. ✅ Add to bookmarks
4. 🎉 Start analyzing Nifty options!

**Example URL**: `https://YOUR_USERNAME-nifty-options-dashboard-app-pro-abc123.streamlit.app`

---

*Built with ❤️ using Streamlit*
