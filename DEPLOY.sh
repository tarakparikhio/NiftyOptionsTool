#!/bin/bash

# 🚀 ONE-LINE DEPLOYMENT GUIDE FOR GIT & STREAMLIT CLOUD
# Copy and paste these commands in order

echo "Step 1: Initialize Git Repository"
cd /Users/tarak/Documents/AIPlayGround/Trading
git init
git add .
git commit -m "feat: Nifty Options Intelligence Dashboard - Premium-aware strategies with signal validation"

echo ""
echo "✅ Git repo initialized locally"
echo ""

echo "Step 2: Create GitHub Repository"
echo "1. Go to https://github.com/new"
echo "2. Repository name: nifty-options-dashboard"
echo "3. Make it PUBLIC (required for Streamlit Cloud)"
echo "4. Do NOT initialize with README"
echo "5. Copy the HTTPS URL from the quick setup"
echo ""
read -p "Press Enter after creating GitHub repo..."

echo ""
echo "Step 3: Connect to GitHub and Push"
echo "Paste this command (replace with your actual URL):"
echo ""
echo "git remote add origin https://github.com/YOUR_USERNAME/nifty-options-dashboard.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
read -p "Press Enter after pushing to GitHub..."

echo ""
echo "Step 4: Deploy to Streamlit Cloud"
echo "1. Go to https://streamlit.io/cloud"
echo "2. Click 'Sign up' → 'Sign up with GitHub'"
echo "3. Click 'Create app'"
echo "4. Select repo: nifty-options-dashboard"
echo "5. Select branch: main"
echo "6. Select script: app_pro.py"
echo "7. Click 'Deploy'"
echo ""
echo "✅ Your app will be live at:"
echo "   https://YOUR-APP-NAME.streamlit.app"
echo ""
echo "🎉 Deployment complete!"
