#!/bin/bash

echo "🚀 Setting up PR-Agent locally..."

# -------------------------
# 1. Clone the repository
# -------------------------
if [ ! -d "pr-agent" ]; then
  echo "📥 Cloning repo..."
  git clone https://github.com/Blackbox-ai/pr-agent.git
else
  echo "📂 Repo already exists. Pulling latest changes..."
  cd pr-agent
  git pull
  cd ..
fi

cd pr-agent

# -------------------------
# 2. Create virtual environment
# -------------------------
echo "🐍 Creating Python virtual environment..."
python3 -m venv .venv

echo "🔌 Activating environment..."
source .venv/bin/activate

# -------------------------
# 3. Install dependencies
# -------------------------
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

# -------------------------
# 4. Setup PR-Agent config
# -------------------------
echo "⚙️ Creating local config file (pr_agent.toml)..."

cat <<EOF > pr_agent.toml
[general]
log_level = "info"

[llm]
provider = "openai"
model = "gpt-4o"
# Add your API key here or via environment variable
api_key = ""

[review]
enable_auto_review = true
EOF

echo "✅ Created pr_agent.toml"

# -------------------------
# 5. Test PR-Agent command
# -------------------------
echo "🧪 Testing if pr-agent CLI is installed..."
if command -v pr-agent &> /dev/null
then
  echo "🎉 PR-Agent installed successfully!"
else
  echo "⚠️ pr-agent executable not found."
  echo "Try: source .venv/bin/activate"
fi

echo "✨ Setup complete!"
echo "👉 To activate environment later, run: source pr-agent/.venv/bin/activate"
