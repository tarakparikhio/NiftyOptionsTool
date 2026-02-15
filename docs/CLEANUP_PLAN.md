# 🔥 PHASE 2: Reduction & Refactoring Plan
**Status:** Ready for Execution  
**Risk Level:** Medium (with backups)  
**Estimated Impact:** -32% codebase, +clarity

---

## EXECUTION STRATEGY

1. **Create safety backup** (`git commit` or branch)
2. **Delete dead code** (zero risk)
3. **Archive legacy** (move, don't delete)
4. **Merge duplicates** (test after each)
5. **Refactor monolith** (gradual)
6. **Consolidate docs** (low risk)
7. **Test & validate** (critical)

---

## 🔴 SECTION A: DELETE (Dead Code - Zero Dependencies)

### Files to DELETE Immediately

```bash
# These have ZERO imports and are provably unused
rm dashboards/plots.py                    # 544 lines - duplicate, never imported
rm analysis/metrics.py                    # 484 lines - exact duplicate of metrics.py

# Total: 1,028 lines deleted
```

**Risk:** ✅ **ZERO** - No imports found, safe to delete

**Verification:**
```bash
# Before deleting, confirm zero imports:
grep -r "from dashboards.plots import" --include="*.py"
grep -r "from dashboards import plots" --include="*.py"
grep -r "from analysis.metrics import" --include="*.py"
# All should return empty
```

---

## 🟡 SECTION B: ARCHIVE (Legacy Code - Keep for Reference)

### Create Archive Structure

```bash
mkdir -p archive/legacy_v1.0
```

### Files to ARCHIVE (Move to archive/)

```bash
# Legacy dashboards (replaced by app_pro.py)
mv app.py archive/legacy_v1.0/
mv dashboards/streamlit_app.py archive/legacy_v1.0/

# Old strategy builder (will be replaced by v2)
mv analysis/strategy_builder.py archive/legacy_v1.0/strategy_builder_old.py

# Total: ~1,771 lines archived
```

**Risk:** 🟡 **LOW** - app.py still referenced in start.sh, need to update

**Required Changes:**
1. Update `start.sh` - remove or comment option 2 (Legacy dashboard)
2. Update imports in files that use old strategy_builder

---

## 🟢 SECTION C: MIGRATION TASKS

### C1: Migrate Old Strategy Builder Users to V2

**Files depending on old `strategy_builder.py`:**
1. `app_pro.py` (line 27)
2. `analysis/directional_workflow.py` (line 18)
3. `tests/test_directional_engine.py` (lines 24, 106)

**Migration Strategy:**

#### **Option A: Create Compatibility Shim (Fast)**

```python
# In analysis/strategy_builder.py (replace old file)
"""
Compatibility shim - redirects to strategy_builder_v2
"""
from analysis.strategy_builder_v2 import Strategy, OptionLeg

# Legacy class names for backward compatibility
class StrategyTemplate:
    """Deprecated: Use Strategy from strategy_builder_v2"""
    def __init__(self, *args, **kwargs):
        raise DeprecationWarning(
            "StrategyTemplate is deprecated. Use Strategy from strategy_builder_v2"
        )

# Legacy preset factories (simplified wrappers)
def IronCondor(spot, wing_width=300, **kwargs):
    """Legacy wrapper for Iron Condor preset"""
    from analysis.strategy_builder_v2 import create_iron_condor
    return create_iron_condor(spot, wing_width, **kwargs)

def Strangle(spot, offset=200, **kwargs):
    """Legacy wrapper for Strangle preset"""
    from analysis.strategy_builder_v2 import create_strangle
    return create_strangle(spot, offset, **kwargs)

def Straddle(spot, **kwargs):
    """Legacy wrapper for Straddle preset"""
    from analysis.strategy_builder_v2 import create_straddle
    return create_straddle(spot, **kwargs)
```

**Risk:** 🟡 **MEDIUM** - Requires testing, but maintains API compatibility

---

#### **Option B: Direct Migration (Clean)**

**app_pro.py changes:**
```python
# Line 27 - OLD:
from analysis.strategy_builder import StrategyTemplate, IronCondor, Strangle, Straddle

# Line 27 - NEW:
from analysis.strategy_builder_v2 import Strategy, create_iron_condor, create_strangle, create_straddle
```

Then update all calls to use new API.

**Risk:** 🔴 **HIGH** - Requires updating multiple call sites, testing each

**Recommendation:** Use Option A (shim) initially, then refactor over time

---

### C2: Rename strategy_builder_v2 → strategy_builder

After migration complete:

```bash
mv analysis/strategy_builder.py archive/legacy_v1.0/strategy_builder_old.py
mv analysis/strategy_builder_v2.py analysis/strategy_builder.py

# Update imports:
# strategy_builder_v2 → strategy_builder (in strategy_ui.py)
```

---

## 🏗️ SECTION D: REFACTOR app_pro.py MONOLITH

### Current: 1566 lines in one file

### Target Structure:

```
ui/
    ├── dashboard.py          # Main Streamlit entry (routing only)
    ├── components/
    │   ├── summary.py        # TAB 1: Quick Summary
    │   ├── range_analysis.py # TAB 2: Range & Volatility
    │   ├── positioning.py    # TAB 3: Options Positioning
    │   └── strategy.py       # TAB 5: Strategy Builder (simplified)
core/
    ├── data_engine.py        # CSV loading + caching
    ├── signal_engine.py      # PCR, RSI, directional bias
    ├── risk_engine.py        # Existing, maybe enhance
    └── metrics_engine.py     # OI, IV, Greeks calculations
```

### Migration Steps:

#### **Step 1: Extract Utility Functions**

Move from `app_pro.py` to `core/data_engine.py`:
- `load_data()` function
- `load_historical_nifty()` function  
- Any CSV parsing logic

#### **Step 2: Extract Tab Renderers**

Move each TAB block to separate file in `ui/components/`:

**File:** `ui/components/summary.py`
```python
import streamlit as st
from core.signal_engine import get_directional_bias
from core.metrics_engine import calculate_pcr

def render_quick_summary(data, spot, vix):
    """Render TAB 1: Quick Summary"""
    st.header("📊 Market Snapshot")
    # ... existing TAB 1 logic ...
```

Similar for:
- `ui/components/range_analysis.py` (TAB 2)
- `ui/components/positioning.py` (TAB 3)
- `ui/components/strategy.py` (TAB 5, wraps strategy_ui)

#### **Step 3: Create Thin Dashboard Router**

**File:** `ui/dashboard.py` (new main entry, ~150 lines)
```python
"""
Streamlit Dashboard - Main Entry Point
Clean, modular architecture
"""
import streamlit as st
from core.data_engine import load_data
from ui.components import summary, range_analysis, positioning, strategy

# Page config
st.set_page_config(page_title="Nifty Options Intelligence", layout="wide")

# Mobile detection
mobile_mode = st.session_state.get('mobile_mode', False)

# Load data
data = load_data()

# Tab structure
if mobile_mode:
    tabs = st.tabs(["Summary", "Range", "Positioning"])
    with tabs[0]:
       summary.render_quick_summary(data)
    with tabs[1]:
        range_analysis.render_range_volatility(data)
    with tabs[2]:
        positioning.render_options_positioning(data)
else:
    tabs = st.tabs(["Summary", "Range", "Positioning", "Strategy"])
    # ... render all tabs ...
```

**Result:**
- `app_pro.py` (1566 lines) → Becomes `ui/dashboard.py` (~150 lines)
- Logic split into 4-5 component files (~200-300 lines each)
- Total: Similar LOC but **massively** more maintainable

---

## 📚 SECTION E: DOCUMENTATION CONSOLIDATION

### Current: 38 markdown files → Target: 10-12 files

### Files to DELETE:

```bash
rm docs/PHASE1_SUMMARY.md
rm docs/PHASE2_STATUS.md
rm docs/DATA_UPDATE_SUMMARY.md
rm docs/MOBILE_IMPLEMENTATION_SUMMARY.md
rm docs/STRATEGY_BUILDER_UPGRADE.md
rm docs/MANUAL_UPDATE_FEATURE.md
rm docs/AUTO_FETCH_FEATURE.md
rm docs/CHANGELOG_V2.1.md  # Merge into main CHANGELOG.md
```

### Files to CONSOLIDATE:

#### **Create:** `CHANGELOG.md` (consolidate all phase summaries)

```markdown
# Changelog

## v2.0.0 (Feb 2026) - Architecture Cleanup
- Removed 32% of codebase
- Eliminated duplicate files
- Simplified UX to 3-4 tabs
- Modular architecture
[Previous phase summaries merged here]

## v1.0.0-alpha (Feb 2026)
- Strategy Builder V2
- Directional signal engine
...
```

#### **Create:** `USER_GUIDE.md` (single source of truth)

Merge:
- `QUICK_START.md`
- `docs/MOBILE_MODE_GUIDE.md`
- Relevant parts of `docs/COMPLETE_FEATURE_MAP.md`

#### **Keep & Update:**
- `README.md` (main entry point)
- `docs/ARCHITECTURE.md` (update with v2 structure)
- `docs/MATH_VERIFICATION_AUDIT.md` (important for credibility)
- `docs/NSE_API_STATUS.md` (current status)
- `docs/DEPLOYMENT.md` (for production)

### Archive Folder:
```bash
mv docs/archive/* archive/legacy_v1.0/docs/
```

---

## 🧪 SECTION F: TESTING & VALIDATION PLAN

After each major change, run:

### Automated Tests:
```bash
# 1. Syntax check
python3 -m py_compile ui/dashboard.py

# 2. Import test
python3 -c "import ui.dashboard"

# 3. Existing test suite
python3 tests/test_strategy_logic.py
python3 tests/test_directional_engine.py

# 4. Strategy builder tests
python3 tests/test_strategy_logic.py
```

### Manual Tests:
1. ✅ Dashboard loads
2. ✅ CSV upload works
3. ✅ All tabs render
4. ✅ Strategy builder functional
5. ✅ Mobile mode works
6. ✅ No console errors

### Rollback Plan:
```bash
git checkout HEAD~1  # Revert last commit if issues
# OR
git checkout v1.0-alpha  # Return to alpha tag
```

---

## 📊 SECTION G: EXECUTION ORDER (Safest Path)

### **Stage 1: Low-Risk Cleanup (Day 1)**
1. ✅ Delete dead code (plots.py, analysis/metrics.py)
2. ✅ Archive legacy dashboards (app.py, streamlit_app.py)
3. ✅ Consolidate documentation (delete/merge 10-15 files)
4. ✅ Run tests, ensure nothing breaks

**Expected Result:** -2,800 lines, zero functional impact

---

### **Stage 2: Strategy Builder Migration (Day 2)**
1. ⚠️ Create compatibility shim in old strategy_builder.py
2. ⚠️ Test app_pro.py still works
3. ⚠️ Rename strategy_builder_v2 → strategy_builder
4. ⚠️ Update imports in strategy_ui.py
5. ⚠️ Full regression test

**Expected Result:** Unified strategy builder, -450 lines

---

### **Stage 3: Monolith Refactor (Day 3-5)**
1. 🔴 Create new folder structure (ui/, core/)
2. 🔴 Extract data loading to core/data_engine.py
3. 🔴 Extract tab components to ui/components/
4. 🔴 Create thin dashboard router ui/dashboard.py
5. 🔴 Update start.sh to use ui/dashboard.py
6. 🔴 Extensive testing

**Expected Result:** Modular architecture, same features, better DX

---

### **Stage 4: UX Simplification (Day 6-7)**
1. 🟡 Remove TAB 4 (Historical Comparison) - optional feature
2. 🟡 Merge TAB 6 into TAB 1/5 (consolidate decision logic)
3. 🟡 Simplify strategy builder presets (focus on Long Call/Put)
4. 🟡 Reduce metrics displayed in each tab
5. 🟡 Test mobile experience

**Expected Result:** 3-tab mobile, 4-tab desktop, cleaner UX

---

### **Stage 5: Final Polish (Day 8)**
1. ✅ Update all remaining documentation
2. ✅ Create v2.0 release notes
3. ✅ Tag release: `v2.0.0`
4. ✅ Deploy and monitor

---

## 📋 PRE-EXECUTION CHECKLIST

Before starting:
- [ ] **Backup:** `git commit -am "Pre-cleanup snapshot - v1.0-alpha"`
- [ ] **Tag:** `git tag v1.0-alpha`  
- [ ] **Branch:** `git checkout -b cleanup/v2.0` (work on branch)
- [ ] **Test Dashboard:** Verify current state works
- [ ] **Document:** Current feature list for regression testing
- [ ] **Disk Space:** Ensure enough space for venv + backups

---

## 🎯 SUCCESS CRITERIA (v2.0)

| Metric | v1.0-alpha | v2.0 Target | Status |
|--------|------------|-------------|--------|
| Total LOC | 14,606 | <10,000 | - |
| Python Files | 35 | ~20 | - |
| Markdown Docs | 38 | 10-12 | - |
| Dead Code | 4,750 lines | 0 | - |
| Dashboard Tabs | 6 | 3-4 | - |
| app_pro.py Size | 1,566 | Split (<500 main) | - |
| Test Pass Rate | 100% | 100% | - |
| Dashboard Load Time | ~3s | <2s | - |

---

## 🚨 RISK MITIGATION

### High-Risk Changes:
1. **Monolith refactor** - Gradual, test after each extraction
2. **Strategy builder migration** - Use shim for compatibility
3. **Import path changes** - Search/replace carefully

### Safety Measures:
1. **Git branch** for all work
2. **Commit after each stage** for rollback points
3. **Keep original files** in archive/ (don't permanently delete)
4. **Parallel testing** - keep v1.0 running while testing v2.0

---

## 📞 DECISION POINTS

**User must approve:**
- [ ] **Delete dead code** (Section A) - Safe
- [ ] **Archive legacy** (Section B) - Need update start.sh
- [ ] **Migrate strategy builder** (Section C) - Medium risk
- [ ] **Refactor monolith** (Section D) - High effort
- [ ] **Simplify UX** (Section F - Stage 4) - Changes user experience

**Recommendation:** Execute Stages 1-2 first (low-risk), then review before Stage 3.

---

**Status:** 📋 **PLAN READY**  
**Next:** Await approval to execute Stage 1 (Low-Risk Cleanup)
