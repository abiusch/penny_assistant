#!/bin/bash
# cleanup_repository.sh
# Penny Repository Cleanup Script
# Duration: ~30 minutes

set -e

echo "🧹 Penny Repository Cleanup Script"
echo "===================================="
echo ""
echo "This script will:"
echo "  1. Create organized directory structure"
echo "  2. Move test files to tests/"
echo "  3. Move experiments to experiments/"
echo "  4. Archive completed docs to docs/archive/phases/"
echo "  5. Consolidate databases to data/"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "Starting cleanup..."

# 1. Create directory structure
echo "📁 Creating directories..."
mkdir -p tests/unit tests/integration
mkdir -p experiments/
mkdir -p docs/archive/phases
mkdir -p data/

# 2. Move test files
echo "🧪 Moving test files..."
find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/ \; 2>/dev/null || true
test_count=$(find tests/ -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $test_count test files"

# 3. Move experimental scripts
echo "🔬 Moving experimental scripts..."
find . -maxdepth 1 -name "*_demo.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "demo_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "adaptive_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "cj_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "enhanced_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "integrated_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
exp_count=$(find experiments/ -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $exp_count experimental scripts"

# 4. Archive completed docs
echo "📄 Archiving completed docs..."
find . -maxdepth 1 -name "WEEK*_COMPLETE.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "PHASE*_COMPLETE*.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_COMPLETE.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_SUMMARY.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "ACTION_PLAN*.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
docs_count=$(find docs/archive/phases/ -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Archived $docs_count docs"

# 5. Move databases
echo "💾 Moving databases..."
find . -maxdepth 1 -name "*.db" -exec mv {} data/ \; 2>/dev/null || true
db_count=$(find data/ -name "*.db" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $db_count databases"

# 6. Create ENTRY_POINTS.md
echo "📌 Creating ENTRY_POINTS.md..."
cat > ENTRY_POINTS.md << 'EOFENTRY'
# Penny Canonical Entry Points

## Production Entry Points

**Voice Mode:** `python penny.py`
**Chat Mode:** `python chat_penny.py`
**Research Pipeline:** `python research_first_pipeline.py`
**Web Interface:** `cd web_interface && python server.py`

## Development

**Tests:** `pytest tests/ -v`
**Health Check:** `python check_health.py`

## Documentation

Start here: `NEXT_PHASE_TASKS.md`

**Do NOT use files in `/experiments/` for production!**
EOFENTRY

echo "✅ Cleanup complete!"
echo ""
echo "Next: Run 'pytest tests/' to verify nothing broke"
