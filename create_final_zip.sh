#!/bin/bash
# Script to create the final ZIP file with all modifications

echo "Creating her-final-replacements.zip..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy current files to temp directory preserving structure
FILES=(
    "REQ_CHECKLIST.md"
    "TODO_PLAN.md"
    "src/her/embeddings/_resolve.py"
    "src/her/embeddings/query_embedder.py"
    "src/her/embeddings/element_embedder.py"
    "src/her/embeddings/cache.py"
    "src/her/bridge/cdp_bridge.py"
    "src/her/bridge/snapshot.py"
    "src/her/session/manager.py"
    "src/her/rank/heuristics.py"
    "src/her/rank/fusion.py"
    "src/her/locator/synthesize.py"
    "src/her/locator/verify.py"
    "src/her/executor/actions.py"
    "src/her/recovery/self_heal.py"
    "src/her/recovery/promotion.py"
    "src/her/parser/intent.py"
    "src/her/cli_api.py"
    "src/her/cli.py"
    "src/her/gateway_server.py"
    "scripts/install_models.sh"
    "scripts/install_models.ps1"
    ".github/workflows/ci.yml"
    "tests/test_embeddings.py"
    "tests/test_bridge.py"
    "tests/test_session.py"
    "tests/test_rank.py"
    "tests/test_locator.py"
    "tests/test_cli_api.py"
    "tests/test_recovery.py"
    "tests/test_parser.py"
)

for FILE in "${FILES[@]}"; do
    if [ -f "$FILE" ]; then
        # Create directory structure in temp
        DIR=$(dirname "$FILE")
        mkdir -p "$TEMP_DIR/$DIR"
        # Copy file
        cp "$FILE" "$TEMP_DIR/$FILE"
        echo "Added: $FILE"
    else
        echo "Warning: $FILE not found"
    fi
done

# Create ZIP file
cd "$TEMP_DIR"
zip -r her-final-replacements.zip *
mv her-final-replacements.zip "$OLDPWD/"
cd "$OLDPWD"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ ZIP file created: her-final-replacements.zip"
echo "Size: $(du -h her-final-replacements.zip | cut -f1)"
echo ""
echo "To extract the files into your project:"
echo "  unzip -o her-final-replacements.zip"