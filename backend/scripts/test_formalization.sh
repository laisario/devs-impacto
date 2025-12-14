#!/bin/bash

# Script para testar o sistema de formalização

set -e

echo "🧪 Testando Sistema de Formalização"
echo "===================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se está rodando via Docker
if command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose exec backend"
    echo "📦 Usando Docker Compose"
else
    DOCKER_CMD=""
    echo "💻 Rodando localmente"
fi

echo ""
echo "1️⃣  Populando Tasks de Formalização..."
$DOCKER_CMD python -m app.modules.formalization.seeds
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tasks populadas com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao popular tasks${NC}"
    exit 1
fi

echo ""
echo "2️⃣  Populando Perguntas de Onboarding..."
$DOCKER_CMD python -m app.modules.onboarding.seeds
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Perguntas populadas com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao popular perguntas${NC}"
    exit 1
fi

echo ""
echo "3️⃣  Verificando dados no banco..."
$DOCKER_CMD python -c "
import asyncio
from app.core.db import get_database

async def check():
    db = get_database()
    
    # Verificar tasks
    tasks = await db.formalization_tasks_catalog.find().to_list(length=100)
    print(f'📋 Tasks no catálogo: {len(tasks)}')
    for task in tasks[:5]:
        print(f'   - {task[\"code\"]}: {task[\"title\"]}')
    if len(tasks) > 5:
        print(f'   ... e mais {len(tasks) - 5} tasks')
    
    # Verificar perguntas
    questions = await db.onboarding_questions.find().to_list(length=100)
    print(f'❓ Perguntas de onboarding: {len(questions)}')
    for q in questions[:5]:
        sets_flag = q.get('sets_flag', 'N/A')
        print(f'   - {q[\"question_id\"]}: {q[\"question_text\"][:50]}... (sets_flag: {sets_flag})')
    if len(questions) > 5:
        print(f'   ... e mais {len(questions) - 5} perguntas')

asyncio.run(check())
"

echo ""
echo -e "${GREEN}✅ Teste concluído!${NC}"
echo ""
echo "📝 Próximos passos:"
echo "   1. Acesse http://localhost:8000/docs"
echo "   2. Faça login via /auth/verify-otp (telefone: qualquer, OTP: 123456)"
echo "   3. Teste os endpoints de formalização:"
echo "      - GET /formalization/tasks"
echo "      - POST /formalization/tasks/regenerate"
echo "      - PATCH /formalization/tasks/{task_code}"
echo ""
echo "📖 Veja TESTING_FORMALIZATION.md para mais detalhes"
