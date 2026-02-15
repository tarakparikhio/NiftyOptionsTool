#!/bin/bash
# Quick data refresh script for NIFTY historical data

echo "🔄 NIFTY Data Refresh Utility"
echo "================================"
echo ""

# Check if new CSV file exists
if [ -f "data/reference/NIFTY 50-14-02-2025-to-14-02-2026.csv" ]; then
    echo "✅ Found new NSE data file"
    echo "🔧 Processing and cleaning..."
    python utils/nifty_data_manager.py
    echo ""
    echo "✅ Data refresh complete!"
    echo ""
else
    echo "❌ No new NSE data file found"
    echo ""
    echo "📥 To update:"
    echo "   1. Download latest NIFTY data from NSE"
    echo "   2. Save to: data/reference/NIFTY 50-14-02-2025-to-14-02-2026.csv"
    echo "   3. Run this script again"
    echo ""
    echo "Or add single day manually:"
    echo ""
    echo "   python scripts/daily_update.py \\"
    echo "     --date '14-Feb-2026' \\"
    echo "     --open 25500 \\"
    echo "     --high 25700 \\"
    echo "     --low 25400 \\"
    echo "     --close 25650 \\"
    echo "     --volume 450000000"
fi

echo ""
echo "📊 Current data summary:"
python -c "from utils.nifty_data_manager import NiftyDataManager; NiftyDataManager().get_summary()"
