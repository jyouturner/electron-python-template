#!/bin/bash
# scripts/build.sh

# Exit on error
set -e

echo "Cleaning previous builds..."
rm -rf dist build

# Build Python executable
echo "Building Python application..."
poetry run pyinstaller src/main/api.py \
    --add-data "src/main/*.py:." \
    --add-data "src/jobs:jobs" \
    --hidden-import=fastapi \
    --hidden-import=uvicorn \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols \
    --hidden-import=uvicorn.protocols.http \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=sqlalchemy \
    --hidden-import=apscheduler \
    --hidden-import=apscheduler.triggers.cron \
    --hidden-import=websockets \
    --hidden-import=websockets.legacy.server \
    --hidden-import=websockets.legacy.protocol \
    --hidden-import=uvicorn.lifespan.on \
    --hidden-import=uvicorn.lifespan.off \
    --collect-all=starlette \
    --collect-all=fastapi \
    --noconfirm \
    --clean \
    --onefile \
    --name api

echo "Creating electron-builder configuration..."
cat > electron-builder.yml << EOF
appId: com.example.python-electron-app
productName: Python Electron App
directories:
  output: dist
  buildResources: build
files:
  - "src/electron/**/*"
  - "src/static/**/*"
  - "package.json"
extraResources:
  - from: "dist/api"
    to: "api"
    filter:
      - "api*"
mac:
  target: dmg
  category: public.app-category.developer-tools
win:
  target: nsis
linux:
  target: AppImage
  category: Development
EOF

# Build Electron app
echo "Building Electron application..."
npm install
npx electron-builder build --mac --win --linux

echo "Build complete! Check the dist directory for the packaged applications."