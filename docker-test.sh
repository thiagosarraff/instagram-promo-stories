#!/bin/bash
# Docker Setup Validation Test Script
# This script validates that the Docker setup is correctly configured

set -e

echo "========================================"
echo "Docker Setup Validation Test Script"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for test results
test_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $1"
        ((TESTS_FAILED++))
    fi
}

echo "Step 1: Checking Docker installation..."
docker --version > /dev/null
test_result "Docker is installed"

docker-compose --version > /dev/null
test_result "Docker Compose is installed"

echo ""
echo "Step 2: Checking required files..."
[ -f "Dockerfile" ]
test_result "Dockerfile exists"

[ -f "docker-compose.yml" ]
test_result "docker-compose.yml exists"

[ -f ".dockerignore" ]
test_result ".dockerignore exists"

[ -f ".env.example" ]
test_result ".env.example exists"

echo ""
echo "Step 3: Checking Dockerfile syntax..."
docker build --dry-run -t insta-stories:test . > /dev/null 2>&1
test_result "Dockerfile syntax is valid"

echo ""
echo "Step 4: Validating docker-compose.yml..."
docker-compose config > /dev/null 2>&1
test_result "docker-compose.yml is valid YAML"

echo ""
echo "Step 5: Checking .env configuration..."
if [ -f ".env" ]; then
    grep -q "INSTAGRAM_USERNAME" .env
    test_result ".env contains INSTAGRAM_USERNAME"

    grep -q "INSTAGRAM_PASSWORD" .env
    test_result ".env contains INSTAGRAM_PASSWORD"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: .env file not found (run: cp .env.example .env)"
    echo "Continuing validation..."
fi

echo ""
echo "Step 6: Checking project structure..."
[ -f "app.py" ]
test_result "app.py exists"

[ -f "requirements.txt" ]
test_result "requirements.txt exists"

[ -f "models.py" ]
test_result "models.py exists"

echo ""
echo "Step 7: Validating requirements.txt..."
grep -q "FastAPI" requirements.txt
test_result "FastAPI is in requirements.txt"

grep -q "uvicorn" requirements.txt
test_result "uvicorn is in requirements.txt"

grep -q "playwright" requirements.txt
test_result "playwright is in requirements.txt"

grep -q "instagrapi" requirements.txt
test_result "instagrapi is in requirements.txt"

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Setup environment: cp .env.example .env"
    echo "2. Add credentials: Edit .env with your Instagram account"
    echo "3. Build and run: docker-compose up --build"
    echo "4. Test API: curl http://localhost:5000/health"
    exit 0
else
    echo -e "${RED}✗ Some validation tests failed!${NC}"
    echo "Please review the errors above."
    exit 1
fi
