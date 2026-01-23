#!/bin/bash

# StereoBrother Bot - Quick Setup Script for Apple Silicon M2
# This script automates the installation and setup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only"
    exit 1
fi

# Check if running on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    print_warning "This script is optimized for Apple Silicon (M1/M2)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_info "==================================="
print_info "StereoBrother Bot Setup for M2"
print_info "==================================="
echo

# Step 1: Check Homebrew
print_info "Step 1: Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for Apple Silicon
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    print_info "Homebrew already installed"
    brew update
fi

# Step 2: Install system dependencies
print_info "Step 2: Installing system dependencies..."
brew install python@3.11 postgresql@15 redis ffmpeg libsndfile portaudio || true

# Step 3: Start services
print_info "Step 3: Starting PostgreSQL and Redis..."
brew services start postgresql@15
brew services start redis

# Wait for services to start
sleep 3

# Step 4: Create Python virtual environment
print_info "Step 4: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    print_info "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Step 5: Install Python dependencies
print_info "Step 5: Installing Python dependencies..."
print_warning "This may take several minutes..."

# Install dependencies in stages to avoid conflicts
pip install --no-cache-dir numpy==1.26.4
pip install --no-cache-dir scipy==1.13.1
pip install torch torchvision torchaudio

# Install remaining dependencies
pip install -r requirements.txt

# Step 6: Setup database
print_info "Step 6: Setting up database..."

# Check if database exists
DB_EXISTS=$(psql -U $USER postgres -tAc "SELECT 1 FROM pg_database WHERE datname='stereobrother_db'")

if [ "$DB_EXISTS" != "1" ]; then
    print_info "Creating database..."
    psql -U $USER postgres << EOF
CREATE DATABASE stereobrother_db;
CREATE USER stereobrother WITH PASSWORD 'stereobrother_dev';
GRANT ALL PRIVILEGES ON DATABASE stereobrother_db TO stereobrother;
ALTER DATABASE stereobrother_db OWNER TO stereobrother;
EOF
    print_info "Database created successfully"
else
    print_info "Database already exists"
fi

# Step 7: Setup .env file
print_info "Step 7: Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp env.example .env

    # Generate random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

    # Update .env file with Mac-specific settings
    sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=postgresql://stereobrother:stereobrother_dev@localhost:5432/stereobrother_db|g" .env
    sed -i '' "s|WORKERS=.*|WORKERS=2|g" .env

    print_info ".env file created and configured"
else
    print_info ".env file already exists"
fi

# Step 8: Create necessary directories
print_info "Step 8: Creating directories..."
mkdir -p storage temp logs models
touch storage/.gitkeep temp/.gitkeep logs/.gitkeep models/.gitkeep
chmod 755 storage temp logs models

# Step 9: Initialize database tables
print_info "Step 9: Initializing database tables..."
python3 << EOF
import asyncio
from src.database import init_db

async def main():
    try:
        await init_db()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

asyncio.run(main())
EOF

# Step 10: Download AI models (optional)
print_info "Step 10: Downloading AI models..."
read -p "Download Demucs model for audio separation? (~2GB) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 << EOF
import demucs.pretrained
print("Downloading Demucs htdemucs model...")
try:
    demucs.pretrained.get_model('htdemucs')
    print("Model downloaded successfully")
except Exception as e:
    print(f"Error downloading model: {e}")
EOF
else
    print_info "Skipping model download"
fi

# Step 11: Run tests
print_info "Step 11: Running tests..."
pytest tests/ -v --tb=short || print_warning "Some tests failed"

# Summary
echo
print_info "==================================="
print_info "Setup completed successfully!"
print_info "==================================="
echo
print_info "Next steps:"
echo "1. Review and update .env file if needed"
echo "2. Start the API server:"
echo "   source venv/bin/activate"
echo "   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo
echo "3. In a new terminal, start Celery worker:"
echo "   source venv/bin/activate"
echo "   celery -A src.tasks.celery_app worker --loglevel=info --concurrency=2"
echo
echo "4. In a new terminal, start Celery beat:"
echo "   source venv/bin/activate"
echo "   celery -A src.tasks.celery_app beat --loglevel=info"
echo
echo "5. Access the API at: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo
print_info "For more details, see INSTALL_M2.md"
echo

# Check system resources
print_info "System Information:"
echo "CPU: $(sysctl -n machdep.cpu.brand_string)"
echo "Cores: $(sysctl -n hw.ncpu)"
echo "Memory: $(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}')"
echo "Python: $(python3 --version)"
echo "PostgreSQL: $(psql --version)"
echo "Redis: $(redis-server --version)"
echo

print_info "Setup complete! Happy coding! 🚀"
