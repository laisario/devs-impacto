# 🚀 Quick Start - Como Rodar o Sistema

## Passo 1: Configurar OpenAI API Key

### Opção A: Usando docker-compose.override.yml (Recomendado)

Edite o arquivo `docker-compose.override.yml` e descomente/adicione:

```yaml
services:
  backend:
    environment:
      - OPENAI_API_KEY=sk-sua-chave-aqui  # 👈 SUA CHAVE AQUI
      - LLM_PROVIDER=openai                # 👈 Mude de "mock" para "openai"
```

**Importante:** Substitua `sk-sua-chave-aqui` pela sua chave real da OpenAI.

### Opção B: Variável de Ambiente no Terminal

```bash
export OPENAI_API_KEY=sk-sua-chave-aqui
export LLM_PROVIDER=openai
docker-compose up
```

### Opção C: Arquivo .env no backend

Crie `backend/.env`:
```
OPENAI_API_KEY=sk-sua-chave-aqui
LLM_PROVIDER=openai
```

## Passo 2: Rodar o Sistema

```bash
# Iniciar tudo (primeira vez pode demorar para buildar)
docker-compose up

# Ou em background
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

**Nota:** Na primeira execução, o Docker vai:
1. Baixar imagens base
2. Instalar dependências do backend e frontend
3. Pode levar alguns minutos

## Passo 3: Acessar

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Funcionalidades GenAI Disponíveis

Após configurar a OpenAI key, você terá acesso a:

1. ✅ **Guia Contextual Personalizado** - Guias adaptados ao seu perfil
2. ✅ **Chatbot PNAE** - Assistente conversacional
3. ✅ **Validação de Documentos** - Análise automática de DAP, comprovantes, etc.
4. ✅ **Projeto de Venda** - Geração automática de projeto de venda

## Sem OpenAI Key?

O sistema funciona sem OpenAI key, mas as funcionalidades GenAI usarão respostas mockadas (para desenvolvimento/testes).

**Para usar as funcionalidades GenAI reais, você PRECISA configurar a OpenAI key!**

### O que funciona sem OpenAI:
- ✅ Onboarding
- ✅ Checklist de tarefas
- ✅ Upload de documentos
- ✅ Dashboard básico

### O que PRECISA de OpenAI:
- ❌ Guia Personalizado (usa mock)
- ❌ Chatbot (usa mock)
- ❌ Validação de Documentos (não valida)
- ❌ Projeto de Venda (não gera)

## Verificar se está funcionando

### 1. Verificar se os serviços estão rodando

```bash
docker-compose ps
```

Deve mostrar `backend` e `frontend` como "Up".

### 2. Verificar logs

```bash
# Logs do backend
docker-compose logs -f backend

# Procurar por erros de OpenAI
docker-compose logs backend | grep -i openai
```

### 3. Testar API

```bash
# Health check
curl http://localhost:8000/health

# Deve retornar: {"status": "healthy", ...}
```

### 4. Testar no navegador

1. Abra http://localhost:5173
2. Faça login (CPF: qualquer número válido, OTP: 123456)
3. Complete o onboarding
4. No dashboard, clique em um item da checklist
5. Clique em "Gerar Guia" - deve gerar um guia personalizado
6. Use o chatbot (ícone de mensagem no canto inferior direito)

## Troubleshooting

### OpenAI não está funcionando?
1. Verifique se `OPENAI_API_KEY` está configurada no `docker-compose.override.yml`
2. Verifique se `LLM_PROVIDER=openai` (não "mock")
3. Reinicie o container: `docker-compose restart backend`
4. Veja os logs: `docker-compose logs backend | grep -i openai`
5. Teste a chave: `curl https://api.openai.com/v1/models -H "Authorization: Bearer sua-chave"`

### MongoDB não conecta?
- O docker-compose já está configurado com MongoDB Atlas
- Se quiser usar local, mude `MONGODB_URI` no docker-compose.yml

### Frontend não conecta ao backend?
- Verifique se `VITE_API_BASE_URL=http://localhost:8000` está correto
- Veja os logs: `docker-compose logs frontend`
- Verifique se o backend está rodando: `curl http://localhost:8000/health`

### Erro "Module not found" no backend?
```bash
# Rebuild o container
docker-compose build backend
docker-compose up -d backend
```

### Porta já em uso?
```bash
# Ver o que está usando a porta
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Ou mude as portas no docker-compose.yml
```
