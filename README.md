# PNAE Simplificado - Backend MVP

API para guiar pequenos produtores (agricultura familiar) a vender para o **PNAE** (Programa Nacional de Alimentação Escolar) via **Chamada Pública**.

## Sobre o Projeto

O sistema auxilia agricultores familiares, muitos com baixa alfabetização, a:

1. **Cadastrar-se** como produtor (formal/informal/individual)
2. **Organizar documentos** necessários (Envelope 01 - habilitação)
3. **Montar o Projeto de Venda** com produtos, preços e cronograma
4. **Gerar PDF** do Projeto de Venda no formato oficial

### Referências PNAE

- Compra da agricultura familiar via dispensa de licitação (Art. 24)
- Envelope 01: Documentos de habilitação
- Envelope 02: Projeto de Venda

## Requisitos

- Docker e Docker Compose

**Ou para desenvolvimento local:**
- Python 3.12+
- MongoDB 7.0+

## Quick Start com Docker (Recomendado)

```bash
# Clonar e entrar no diretório
git clone <repo-url>
cd pnae-backend

# Iniciar todos os serviços (MongoDB + API)
docker compose up -d

# Verificar se está rodando
docker compose ps

# Ver logs
docker compose logs -f api
```

**Pronto!** A API estará disponível em:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Comandos Docker Úteis

```bash
# Popular banco com dados de teste
docker compose --profile seeds up seeds

# Parar todos os serviços
docker compose down

# Parar e remover volumes (limpa banco)
docker compose down -v

# Rebuild após mudanças
docker compose build --no-cache
docker compose up -d

# Executar testes
docker compose exec api pytest -v

# Acessar shell do container
docker compose exec api bash
```

### Produção

```bash
# Definir JWT_SECRET obrigatório
export JWT_SECRET="sua-chave-secreta-muito-segura"

# Subir com config de produção
docker compose -f docker-compose.prod.yml up -d
```

## Desenvolvimento Local (Sem Docker)

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e ".[dev]"

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com sua MONGODB_URI

# Iniciar MongoDB (precisa estar rodando)
# Exemplo: docker run -d -p 27017:27017 mongo:7

# Iniciar servidor
uvicorn app.main:app --reload

# Popular banco com dados de teste
python seeds.py
```

## Testes

```bash
# Com Docker
docker compose exec api pytest -v

# Localmente (requer MongoDB rodando)
pytest -v

# Com cobertura
pytest --cov=app
```

## Linting e Formatação

```bash
# Verificar código
ruff check .

# Formatar código
ruff format .

# Type checking
mypy app
```

## Exemplos de Requests (curl)

### Autenticação

```bash
# 1. Iniciar autenticação (envia OTP - mock: sempre 123456)
curl -X POST http://localhost:8000/auth/start \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999"}'

# Resposta: {"ok": true, "message": "OTP sent successfully"}

# 2. Verificar OTP e obter token
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999", "otp": "123456"}'

# Resposta: {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Obter dados do usuário autenticado
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Perfil do Produtor

```bash
# Criar/atualizar perfil (produtor individual)
curl -X PUT http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_type": "individual",
    "name": "João da Silva",
    "address": "Sítio Boa Vista, km 5",
    "city": "Campinas",
    "state": "SP",
    "dap_caf_number": "DAP123456789",
    "cpf": "12345678901"
  }'

# Criar perfil (cooperativa - formal)
curl -X PUT http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_type": "formal",
    "name": "Cooperativa Agricultores Unidos",
    "address": "Rua Principal, 100",
    "city": "Ribeirão Preto",
    "state": "SP",
    "dap_caf_number": "DAP987654321",
    "cnpj": "12345678000195"
  }'

# Obter perfil
curl -X GET http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Chamadas Públicas

```bash
# Listar chamadas públicas (público)
curl -X GET "http://localhost:8000/calls?skip=0&limit=10"

# Obter detalhes de uma chamada
curl -X GET http://localhost:8000/calls/CALL_ID

# Criar chamada pública (requer auth)
curl -X POST http://localhost:8000/calls \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "CP 001/2025",
    "entity_name": "Prefeitura Municipal de Exemplo",
    "entity_cnpj": "12345678000190",
    "description": "Aquisição de gêneros alimentícios",
    "products": [
      {"name": "Alface", "unit": "kg", "quantity": 100, "unit_price": 5.50},
      {"name": "Tomate", "unit": "kg", "quantity": 200, "unit_price": 8.00}
    ],
    "delivery_schedule": "Entregas semanais",
    "submission_deadline": "2025-12-31T23:59:59"
  }'
```

### Documentos

```bash
# 1. Obter URL para upload
curl -X POST http://localhost:8000/documents/presign \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "dap.pdf", "content_type": "application/pdf"}'

# Resposta: {"upload_url": "...", "file_url": "...", "file_key": "..."}

# 2. Fazer upload para upload_url (simulado em mock)

# 3. Registrar documento após upload
curl -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "dap_caf",
    "file_url": "URL_RETORNADA",
    "file_key": "KEY_RETORNADA",
    "original_filename": "dap.pdf"
  }'

# Listar documentos
curl -X GET http://localhost:8000/documents \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Projeto de Venda

```bash
# Criar projeto de venda
curl -X POST http://localhost:8000/sales-projects \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "CALL_ID_AQUI",
    "items": [
      {
        "product_name": "Alface Crespa",
        "unit": "kg",
        "quantity": 50,
        "unit_price": 5.00,
        "delivery_schedule": "Março/2025, Abril/2025"
      },
      {
        "product_name": "Tomate Salada",
        "unit": "kg",
        "quantity": 100,
        "unit_price": 7.50,
        "delivery_schedule": "Março/2025"
      }
    ]
  }'

# Obter projeto
curl -X GET http://localhost:8000/sales-projects/PROJECT_ID \
  -H "Authorization: Bearer SEU_TOKEN"

# Gerar PDF do projeto
curl -X POST http://localhost:8000/sales-projects/PROJECT_ID/generate-pdf \
  -H "Authorization: Bearer SEU_TOKEN"

# Resposta: {"pdf_url": "...", "message": "PDF gerado com sucesso"}
```

## Estrutura do Projeto

```
├── Dockerfile              # Multi-stage build (dev + prod)
├── docker-compose.yml      # Desenvolvimento
├── docker-compose.prod.yml # Produção
├── app/
│   ├── main.py             # FastAPI app
│   ├── core/
│   │   ├── config.py       # Configurações (env vars)
│   │   ├── security.py     # JWT auth
│   │   ├── db.py           # MongoDB connection
│   │   └── errors.py       # Exception handlers
│   ├── modules/
│   │   ├── auth/           # Autenticação OTP + JWT
│   │   ├── producers/      # Perfil do produtor
│   │   ├── calls/          # Chamadas públicas
│   │   ├── documents/      # Upload de documentos
│   │   └── sales_projects/ # Projeto de venda + PDF
│   └── shared/
│       ├── pagination.py   # Paginação
│       └── utils.py        # Utilitários
├── tests/
├── seeds.py                # Dados de teste
└── pyproject.toml
```

## Tipos de Produtor

| Tipo | Descrição | Documentos Obrigatórios |
|------|-----------|------------------------|
| `individual` | Agricultor familiar individual | CPF, DAP/CAF |
| `formal` | Cooperativa ou Associação | CNPJ, DAP/CAF, Estatuto |
| `informal` | Grupo informal | CPFs dos membros, DAP/CAF |

## Tipos de Documentos (Envelope 01)

- `dap_caf` - DAP/CAF (Declaração de Aptidão ao Pronaf)
- `cpf` - CPF
- `cnpj` - CNPJ
- `proof_address` - Comprovante de endereço
- `bank_statement` - Dados bancários
- `statute` - Estatuto social
- `minutes` - Ata de assembleia
- `other` - Outros

## API Endpoints

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/auth/start` | Iniciar autenticação | Não |
| POST | `/auth/verify` | Verificar OTP | Não |
| GET | `/auth/me` | Dados do usuário | Sim |
| PUT | `/producer-profile` | Criar/atualizar perfil | Sim |
| GET | `/producer-profile` | Obter perfil | Sim |
| POST | `/calls` | Criar chamada | Sim |
| GET | `/calls` | Listar chamadas | Não |
| GET | `/calls/{id}` | Detalhes da chamada | Não |
| POST | `/documents/presign` | URL para upload | Sim |
| POST | `/documents` | Registrar documento | Sim |
| GET | `/documents` | Listar documentos | Sim |
| POST | `/sales-projects` | Criar projeto | Sim |
| GET | `/sales-projects/{id}` | Obter projeto | Sim |
| POST | `/sales-projects/{id}/generate-pdf` | Gerar PDF | Sim |

## Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `MONGODB_URI` | URI de conexão MongoDB | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Nome do banco | `pnae_dev` |
| `JWT_SECRET` | Chave secreta JWT | (obrigatório em prod) |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Expiração do token | `1440` (24h) |
| `STORAGE_PROVIDER` | Provider de storage | `mock` |

## Licença

MIT
