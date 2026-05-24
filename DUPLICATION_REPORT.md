# Duplication Refactoring Report

## 1. HTML Layout Consolidation
**Status**: COMPLETED

### Duplication Found:
- Dashboard sidebar (45+ lines) repeated in `index.html`, `recruiter.html`, `admin.html`, and `recruiter_results.html`.
- Cursor dot/ring and grain overlay (3 lines) repeated in every dashboard.
- Chart.js CDN script import repeated in every dashboard.
- Common HTML structure (`app-layout`, `main-content`) repeated.

### Solution:
- Created [base.html](file:///c:/Users/Shuddhodhan/.gemini/antigravity/scratch/careerforge 2- Copy/templates/base.html) as a master template.
- Refactored all dashboard templates to inherit from `base.html` using Jinja2 `{% extends %}`.
- Total lines removed: ~360 lines of redundant HTML boilerplate.
- Unified sidebar active state management using `active_page` variable passed from Flask.

## 2. JavaScript Deduplication
**Status**: COMPLETED

### Duplication Found:
- Repeated `Chart.js` initialization logic with similar options (responsive, grid colors, etc.) (6+ instances).
- Multiple `fetch('/api/...')` patterns with inconsistent error handling and `.json()` parsing.
- Scattered state resetting logic.

### Solution:
- Created `getChartDefaults(type, overrides)` in `script.js` to provide consistent styling (font colors, grid layouts) and reduce boilerplate by ~15 lines per chart.
- Created `cfFetch(url, options)` as a unified API wrapper that handles JSON parsing and standardizes HTTP error reporting.
- Refactored `clearPreviousResults()` to be more aggressive, resetting all dashboard containers and hiding temporary UI elements.
- Applied `.finally()` blocks to all major async operations to ensure loaders are cleared reliably.

## 3. Backend Logic (Planned)
### Duplication Found:
- Session check and role validation repeated in dashboard routes.
- `db_get_resumes` often called for the same owner.

### Solution:
- (Optional) Use a decorator or utility to fetch dashboard context.
