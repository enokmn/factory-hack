#!/bin/bash
set -e

echo "🔧 Setting up .NET environment for Challenge 2 and 3..."

# Ensure global .NET tools are available in all shells (aspire CLI is installed as a dotnet tool).
DOTNET_TOOLS_DIR="$HOME/.dotnet/tools"
mkdir -p "$DOTNET_TOOLS_DIR"
export PATH="$DOTNET_TOOLS_DIR:$PATH"
for shell_rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$shell_rc" ] && ! grep -q 'export PATH="$HOME/.dotnet/tools:$PATH"' "$shell_rc"; then
        echo 'export PATH="$HOME/.dotnet/tools:$PATH"' >> "$shell_rc"
    fi
done

# Create a temporary project to restore packages
TEMP_DIR="/tmp/dotnet-setup"
mkdir -p $TEMP_DIR
cd $TEMP_DIR

echo "📦 Creating temporary .NET project to cache NuGet packages..."
dotnet new console -n TempSetup --force

echo "📥 Installing required NuGet packages..."

# Azure SDKs
dotnet add package Microsoft.Azure.Cosmos
dotnet add package Azure.AI.Inference --version 1.0.0-beta.4
dotnet add package Azure.AI.Projects --version 1.2.0-beta.5
dotnet add package Azure.Identity

# Configuration
dotnet add package Microsoft.Extensions.Configuration
dotnet add package Microsoft.Extensions.Configuration.EnvironmentVariables
dotnet add package Microsoft.Extensions.Configuration.Json

# Logging
dotnet add package Microsoft.Extensions.Logging.Console

# JSON handling
dotnet add package System.Text.Json
dotnet add package Newtonsoft.Json

echo "🔄 Restoring packages to cache..."
dotnet restore

echo "🧹 Cleaning up temporary project..."
cd /
rm -rf $TEMP_DIR

echo "✅ .NET environment setup complete!"
echo "📌 .NET SDK $(dotnet --version) is ready"
echo "📦 All required NuGet packages are cached and ready to use"

if command -v aspire >/dev/null 2>&1; then
    echo "✅ Aspire CLI found: $(aspire --version 2>/dev/null || echo 'installed')"
else
    echo "⚠️ Aspire CLI not found in PATH. Open a new shell (PATH is now configured) and try 'aspire --version'."
fi
