# Como Rodar os Testes do Backend

## Problema Comum

Se você encontrar o erro `ModuleNotFoundError: No module named 'motor'`, é porque o pytest está sendo executado fora do ambiente virtual.

## Soluções

### Opção 1: Ativar o ambiente virtual manualmente

```bash
# Do diretório raiz do projeto
source .venv/bin/activate
cd backend
python -m pytest tests/integration/
```

### Opção 2: Usar o script helper

```bash
# Do diretório backend
./run_tests.sh tests/integration/

# Ou com opções
./run_tests.sh tests/integration/ -v
./run_tests.sh tests/ --cov=app
```

### Opção 3: Usar Makefile (recomendado)

```bash
# Do diretório backend
make test-integration
make test-unit
make test
make coverage
```

### Opção 4: Usar python -m pytest diretamente

```bash
# Do diretório backend (com venv ativado)
python -m pytest tests/integration/
```

## Verificar Ambiente

Para verificar se está usando o pytest correto:

```bash
# Com venv ativado
which pytest
# Deve mostrar: /home/lucas/hackathon/.venv/bin/pytest

# Versão do pytest
python -m pytest --version
```

## Instalação de Dependências

Se as dependências não estiverem instaladas:

```bash
# Do diretório raiz
source .venv/bin/activate
cd backend
pip install -e ".[dev]"
```
