# Guia de Deploy no Render

## Pré-requisitos

1. Conta no [Render](https://render.com)
2. Conta no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (free tier)
3. Chave da OpenAI API (se usar LLM)

## Passo 1: Configurar MongoDB Atlas

1. Acesse [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Crie uma conta gratuita
3. Crie um cluster gratuito (M0 - Free)
4. Configure Network Access:
   - Adicione IP: `0.0.0.0/0` (permite acesso de qualquer lugar)
   - **Nota**: Para produção, restrinja aos IPs do Render
5. Crie um usuário de banco de dados:
   - Database Access → Add New Database User
   - Escolha "Password" e crie uma senha forte
   - Role: "Atlas admin" ou "Read and write to any database"
6. Obtenha a connection string:
   - Clique em "Connect" → "Connect your application"
   - Copie a string (substitua `<password>` pela senha criada)
   - Exemplo: `mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

## Passo 2: Deploy no Render

### Opção A: Via Dashboard (Recomendado)

1. Acesse [dashboard.render.com](https://dashboard.render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub/GitLab
4. Configure:
   - **Name**: `pnae-backend`
   - **Region**: `Oregon` (ou mais próximo do Brasil)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.` (ponto)
   - **Build Command**: (deixe vazio)
   - **Start Command**: (deixe vazio - usa CMD do Dockerfile)

5. Configure Environment Variables:
   ```
   MONGODB_URI=mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   DATABASE_NAME=pnae
   JWT_SECRET=<gere-uma-chave-secreta-forte>
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=1440
   STORAGE_PROVIDER=mock
   OPENAI_API_KEY=<sua-chave-openai>
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   RAG_EMBEDDING_MODEL=text-embedding-3-small
   PORT=8000
   ```

   **Dica**: Para gerar um JWT_SECRET seguro:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

6. Clique em "Create Web Service"

### Opção B: Via render.yaml (Blueprints)

1. Certifique-se de que o arquivo `render.yaml` está na raiz do projeto
2. No Render, vá em "New +" → "Blueprint"
3. Conecte o repositório
4. Render detectará automaticamente o `render.yaml`
5. Configure as variáveis de ambiente manualmente no dashboard:
   - `MONGODB_URI` (sua connection string do Atlas)
   - `OPENAI_API_KEY` (sua chave da OpenAI)

## Passo 3: Configurar CORS

O CORS já está configurado no `app/main.py` para permitir todas as origens (`allow_origins=["*"]`). 

Para produção, você pode restringir às origens específicas:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-app.netlify.app",  # URL do seu frontend
        "http://localhost:5173",  # Para desenvolvimento local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Passo 4: Atualizar Frontend

No frontend, atualize a URL da API. Crie um arquivo de configuração:

**`frontend/src/config/api.ts`**:
```typescript
export const API_URL = import.meta.env.VITE_API_URL || 'https://pnae-backend.onrender.com';
```

E configure no Netlify:
- Environment Variable: `VITE_API_URL=https://pnae-backend.onrender.com`

Ou atualize diretamente nos arquivos que fazem chamadas à API.

## Passo 5: Verificação

1. Acesse: `https://seu-app.onrender.com/health`
   - Deve retornar: `{"status": "healthy", "database": "pnae", "storage_provider": "mock"}`
2. Acesse: `https://seu-app.onrender.com/docs`
   - Deve mostrar a documentação Swagger
3. Acesse: `https://seu-app.onrender.com/`
   - Deve retornar: `{"status": "ok", "service": "PNAE Simplificado API", "version": "0.1.0"}`

## Troubleshooting

### Erro de conexão com MongoDB
- Verifique se o IP do Render está na whitelist do Atlas
- Use `0.0.0.0/0` temporariamente para testar (não recomendado para produção)
- Verifique se a connection string está correta (substitua `<password>`)

### Erro de build
- Verifique os logs no dashboard do Render
- Certifique-se de que o Dockerfile está correto
- Verifique se todas as dependências estão no `pyproject.toml`

### Timeout na primeira requisição
- Render free tier pode hibernar após 15min de inatividade
- A primeira requisição após hibernar pode demorar ~30s
- Considere usar um serviço de "ping" para manter o serviço ativo

### Erro de variável PORT
- O Dockerfile já está configurado para usar `${PORT:-8000}`
- Render define automaticamente a variável PORT

### Erro de permissão
- O Dockerfile já cria um usuário não-root (`appuser`)
- Isso deve funcionar automaticamente

## Próximos Passos

1. **Configurar domínio customizado** (opcional)
   - No Render: Settings → Custom Domain
   - Configure DNS no seu provedor

2. **Configurar storage de arquivos**
   - Opção 1: MongoDB GridFS (gratuito, limitado)
   - Opção 2: Cloudflare R2 (10GB free, compatível com S3)
   - Opção 3: AWS S3 (5GB free no primeiro ano)

3. **Configurar monitoramento**
   - Render oferece logs básicos
   - Considere Sentry para error tracking (free tier)

4. **Configurar backups do MongoDB**
   - MongoDB Atlas free tier não inclui backups automáticos
   - Considere fazer backups manuais ou upgrade

5. **Otimizar performance**
   - Configure índices no MongoDB
   - Use cache quando possível
   - Considere CDN para assets estáticos

## Limitações do Free Tier

- **750 horas/mês** de uso
- **Hibernação** após 15min de inatividade
- **512MB RAM** e **0.5 CPU**
- **Sem SSL customizado** (mas HTTPS é incluído)
- **Sem suporte prioritário**

Para produção com mais tráfego, considere upgrade para o plano pago ($7/mês).

