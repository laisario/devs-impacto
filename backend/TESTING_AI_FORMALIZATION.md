# Como Testar o Módulo AI Formalization

## Preparação

### 1. Popular dados necessários

```bash
# Popular perguntas de onboarding
python seeds_onboarding.py

# (Opcional) Popular chunks RAG se tiver documentos
python scripts/ingest_rag_documents.py
```

### 2. Configurar variáveis de ambiente

**Para desenvolvimento/testes (usa mock - não precisa API key):**
```bash
# No .env ou export:
LLM_PROVIDER=mock
```

**Para testar com OpenAI real:**
```bash
# No .env:
OPENAI_API_KEY=sk-sua-chave-aqui
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

## Teste Manual via API

### 1. Iniciar servidor

```bash
# Com Docker
docker compose up

# Ou localmente
uvicorn app.main:app --reload
```

### 2. Autenticar e obter token

```bash
# Iniciar autenticação
curl -X POST http://localhost:8000/auth/start \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999"}'

# Verificar OTP (mock sempre aceita 123456)
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999", "otp": "123456"}'

# Resposta contém access_token - guarde para usar abaixo
# Exemplo: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Testar geração de guia

```bash
# Gerar guia para requisito "has_cpf"
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement_id": "has_cpf"
  }'

# Resposta esperada:
# {
#   "summary": "...",
#   "steps": [
#     {"step": 1, "title": "...", "description": "..."},
#     ...
#   ],
#   "estimated_time_days": 7,
#   "where_to_go": [...],
#   "confidence_level": "high"
# }
```

### 4. Testar outros requirement_ids

```bash
# has_dap_caf
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_dap_caf"}'

# has_cnpj
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_cnpj"}'

# has_bank_account
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_bank_account"}'

# has_organized_documents
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_organized_documents"}'
```

### 5. Testar cenários de erro

```bash
# Requirement ID inexistente (deve retornar 404)
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "requirement_inexistente"}'

# Sem autenticação (deve retornar 401)
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_cpf"}'
```

## Teste Automatizado

### Executar testes existentes

```bash
# Todos os testes
pytest -v

# Apenas testes do módulo AI (quando criados)
pytest tests/test_ai_formalization/ -v

# Com cobertura
pytest --cov=app/modules/ai_formalization tests/test_ai_formalization/
```

## Verificar Requisitos Disponíveis

Para ver quais `requirement_id`s estão disponíveis, você pode verificar as perguntas de onboarding:

```bash
# Ver perguntas (via código ou banco)
# As perguntas com requirement_id definido podem receber guias
```

Ou no MongoDB:
```javascript
db.onboarding_questions.find({requirement_id: {$ne: null}})
```

## Preparar Dados RAG (Opcional)

Para testar com chunks RAG reais:

1. Coloque PDFs em `data/rag_documents/`
2. Execute ingestão:
```bash
python scripts/ingest_rag_documents.py
```

3. Configure no script quais requirement_ids cada documento se aplica

## Verificar Logs

Se usar OpenAI real, verifique logs para ver:
- Requests enviados
- Respostas recebidas
- Erros de API

## Troubleshooting

### Erro: "Requirement not found"
- Verifique se rodou `python seeds_onboarding.py`
- Confirme que a pergunta tem `requirement_id` definido

### Erro: "OpenAI API key required"
- Se `LLM_PROVIDER=openai`, precisa definir `OPENAI_API_KEY`
- Para testes, use `LLM_PROVIDER=mock`

### Resposta vazia ou inválida
- Mock sempre retorna resposta válida
- OpenAI pode ter problemas de conectividade ou quota
- Fallback genérico deve ser retornado se LLM falhar

### Steps não aparecem
- Service sempre retorna pelo menos 3 steps (fallback)
- Verifique logs para erros de parse JSON
