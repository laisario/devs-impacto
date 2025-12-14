#!/bin/bash
# Script helper para rodar testes do backend
# Garante que o ambiente virtual está ativado

set -e

# Ir para o diretório raiz do projeto
cd "$(dirname "$0")/.."

# Ativar ambiente virtual se existir
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Ambiente virtual ativado"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Ambiente virtual ativado"
else
    echo "⚠ Aviso: Nenhum ambiente virtual encontrado"
fi

# Voltar para o diretório backend
cd backend

# Executar pytest com os argumentos passados
python -m pytest "$@"
