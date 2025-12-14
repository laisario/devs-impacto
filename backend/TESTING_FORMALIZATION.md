# Como Testar o Sistema de Formalização

## 1. Popular o Banco de Dados com os CSVs

### Opção A: Via Docker (Recomendado)

```bash
# Popular tasks de formalização
docker-compose exec backend python -m app.modules.formalization.seeds

# Popular perguntas de onboarding
docker-compose exec backend python -m app.modules.onboarding.seeds
```

### Opção B: Diretamente (se estiver rodando localmente)

```bash
cd backend

# Popular tasks de formalização
python -m app.modules.formalization.seeds

# Popular perguntas de onboarding
python -m app.modules.onboarding.seeds
```

## 2. Verificar se os Dados Foram Carregados

### Verificar Tasks no MongoDB

```bash
# Via Docker
docker-compose exec backend python -c "
from app.core.db import get_database
import asyncio

async def check():
    db = get_database()
    tasks = await db.formalization_tasks_catalog.find().to_list(length=100)
    print(f'Total de tasks no catálogo: {len(tasks)}')
    for task in tasks:
        print(f'  - {task[\"code\"]}: {task[\"title\"]}')

asyncio.run(check())
"
```

### Verificar Perguntas no MongoDB

```bash
# Via Docker
docker-compose exec backend python -c "
from app.core.db import get_database
import asyncio

async def check():
    db = get_database()
    questions = await db.onboarding_questions.find().to_list(length=100)
    print(f'Total de perguntas: {len(questions)}')
    for q in questions:
        print(f'  - {q[\"question_id\"]}: {q[\"question_text\"]} (sets_flag: {q.get(\"sets_flag\")})')

asyncio.run(check())
"
```

## 3. Testar os Endpoints

### 3.1. Fazer Login e Obter Token

```bash
# Login (substitua o telefone se necessário)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "11999999999"}'

# Obter OTP (use o código mock: 123456)
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "11999999999", "otp": "123456"}'

# Salve o token retornado em uma variável
export TOKEN="seu_token_aqui"
```

### 3.2. Completar Onboarding (se necessário)

```bash
# Responder perguntas do onboarding
# Exemplo: responder que tem CPF
curl -X POST http://localhost:8000/onboarding/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question_id": "documents_1",
    "answer": "sim"
  }'

# Responder que tem cadastro como agricultor familiar
curl -X POST http://localhost:8000/onboarding/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question_id": "documents_2",
    "answer": "não"
  }'

# Responder que tem conta bancária
curl -X POST http://localhost:8000/onboarding/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question_id": "documents_3",
    "answer": "sim"
  }'

# Responder que quer vender para escolas
curl -X POST http://localhost:8000/onboarding/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question_id": "goal_1",
    "answer": "sim"
  }'
```

### 3.3. Testar Endpoints de Formalização

#### GET /formalization/tasks
```bash
curl -X GET http://localhost:8000/formalization/tasks \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado esperado:**
- Lista de tasks baseadas no perfil do usuário
- Tasks devem incluir: `task_code`, `title`, `description`, `why`, `status`, `blocking`, etc.

#### POST /formalization/tasks/regenerate
```bash
curl -X POST http://localhost:8000/formalization/tasks/regenerate \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado esperado:**
```json
{
  "message": "Tasks regenerated successfully"
}
```

#### PATCH /formalization/tasks/{task_code}
```bash
# Marcar task como done
curl -X PATCH http://localhost:8000/formalization/tasks/HAS_CPF \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "done"
  }'

# Marcar task como skipped
curl -X PATCH http://localhost:8000/formalization/tasks/HAS_BANK_ACCOUNT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "skipped"
  }'
```

## 4. Testar Regras de Ativação

### Cenário 1: Usuário sem CPF
- Responder `documents_1` com "não"
- Regenerar tasks
- **Esperado:** Task `HAS_CPF` deve aparecer

### Cenário 2: Usuário sem cadastro como agricultor familiar
- Responder `documents_2` com "não"
- Regenerar tasks
- **Esperado:** Task `HAS_FAMILY_FARMER_REGISTRATION` deve aparecer

### Cenário 3: Usuário sem conta bancária
- Responder `documents_3` com "não"
- Regenerar tasks
- **Esperado:** Task `HAS_BANK_ACCOUNT` deve aparecer

### Cenário 4: Usuário quer vender para escolas
- Responder `goal_1` com "sim"
- Regenerar tasks
- **Esperado:** Tasks `SALES_PROJECT_READY` e `PUBLIC_CALL_SUBMISSION_READY` devem aparecer

## 5. Testar Sincronização

### Teste de Preservação de Status "done"
1. Marcar uma task como "done"
2. Regenerar tasks
3. **Esperado:** Task deve continuar como "done"

### Teste de Criação de Novas Tasks
1. Completar onboarding com novas respostas
2. Regenerar tasks
3. **Esperado:** Novas tasks devem ser criadas se necessárias

### Teste de Marcação como "skipped"
1. Ter uma task ativa
2. Mudar resposta do onboarding para que a task não seja mais necessária
3. Regenerar tasks
4. **Esperado:** Task deve ser marcada como "skipped" (não deletada)

## 6. Testar via API Docs (Swagger)

1. Acesse: http://localhost:8000/docs
2. Faça login via `/auth/verify-otp`
3. Clique em "Authorize" e cole o token
4. Teste os endpoints:
   - `GET /formalization/tasks`
   - `POST /formalization/tasks/regenerate`
   - `PATCH /formalization/tasks/{task_code}`

## 7. Verificar Logs

```bash
# Ver logs do backend
docker-compose logs -f backend

# Procurar por erros relacionados a formalização
docker-compose logs backend | grep -i formalization
```

## 8. Checklist de Validação

- [ ] CSVs foram carregados no banco
- [ ] Perguntas do onboarding aparecem com `sets_flag` e `affects_task`
- [ ] Tasks do catálogo foram criadas
- [ ] Endpoint `GET /formalization/tasks` retorna tasks do usuário
- [ ] Endpoint `POST /formalization/tasks/regenerate` funciona
- [ ] Endpoint `PATCH /formalization/tasks/{task_code}` atualiza status
- [ ] Regras de ativação funcionam corretamente
- [ ] Status "done" é preservado após regeneração
- [ ] Novas tasks são criadas quando necessário
- [ ] Tasks não aplicáveis são marcadas como "skipped"

## Troubleshooting

### Erro: "Task code not found in catalog"
- Execute: `python -m app.modules.formalization.seeds`

### Erro: "Question not found"
- Execute: `python -m app.modules.onboarding.seeds`

### Tasks não aparecem
- Verifique se o `producer_profile` tem as flags necessárias
- Execute `POST /formalization/tasks/regenerate`
- Verifique os logs do backend

### Flags não estão sendo populadas
- Verifique se as perguntas do onboarding têm `sets_flag` configurado
- Verifique se as respostas estão sendo salvas corretamente
- Verifique o `producer_profile` no MongoDB
