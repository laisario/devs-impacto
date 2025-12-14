# Guia de Ingestão de Documentos no RAG

Este guia explica como injetar documentos de texto limpos no sistema RAG para que o agente AI possa usá-los ao gerar guias de formalização.

**IMPORTANTE:** O sistema processa arquivos `.txt` já limpos e padronizados, não PDFs brutos.

**NOVO:** Classificação automática! O sistema agora usa LLM para determinar automaticamente `topic` e `applies_to` de cada chunk, baseado nas perguntas de onboarding existentes. Não é mais necessário mapear manualmente cada documento.

## Estrutura

```
backend/data/rag/
├── raw/                    # Original documents (HTML, PDF, DOC)
├── processed/              # Cleaned text files (.txt) - USE THIS FOR INGESTION
└── metadata/               # CSV and JSON metadata
```

**Importante:** Os arquivos devem ser arquivos `.txt` já limpos e processados. Place them in `backend/data/rag/processed/`.

## Passo a Passo

### 1. Preparar arquivos de texto limpos

Os arquivos de texto devem estar já limpos e padronizados em `backend/data/rag/processed/`:

```bash
# Criar diretório (se não existir)
mkdir -p backend/data/rag/processed

# Adicionar arquivos .txt já processados/limpos
# (arquivos devem ter sido pré-processados por scripts de limpeza)
cp /caminho/para/seu/documento.txt backend/data/rag/processed/
```

**Nota:** O script processa arquivos `.txt` já limpos, não PDFs. Se você tem PDFs, precisa primeiro convertê-los e limpá-los usando scripts de pré-processamento.

### 2. Classificação Automática (Recomendado)

O sistema agora usa **classificação automática com LLM**! Você não precisa mapear manualmente.

O script automaticamente:
1. Extrai texto dos PDFs
2. Divide em chunks
3. Usa LLM para classificar cada chunk e determinar:
   - `topic`: Tópico principal (cpf, dap_caf, cnpj, etc.)
   - `applies_to`: Lista de `requirement_id`s relevantes (baseado nas perguntas de onboarding)

**Como funciona:**
- O LLM analisa cada chunk de texto
- Compara com as perguntas de onboarding existentes
- Determina automaticamente quais `requirement_id`s se aplicam
- Um chunk pode se aplicar a múltiplos requirements (ex: um texto sobre DAP pode aplicar a `has_dap_caf` E `has_organized_documents`)

### 3. Verificar dependências

```bash
# MongoDB deve estar rodando
# Onboarding questions devem estar populadas
python scripts/dev/seed_onboarding_questions.py

# LLM configurado (opcional, mas recomendado para classificação)
# No .env: LLM_PROVIDER=openai (ou mock para testes)
```

**Notas:**
- **Arquivos de texto**: Devem estar já limpos e em formato `.txt`
- **Embeddings**: Opcionais. Se não tiver `OPENAI_API_KEY`, os chunks serão salvos sem embeddings (busca funciona por filtro de `applies_to`)
- **LLM para classificação**: Se `LLM_PROVIDER=mock`, a classificação pode ser menos precisa. Use `LLM_PROVIDER=openai` para melhor classificação.

### 4. Executar ingestão

```bash
# Popular documentos
python scripts/ops/ingest_rag_documents.py
```

O script irá:
1. Ler todos os arquivos `.txt` de `backend/data/rag/processed/`
2. Ler o conteúdo de cada arquivo (já está em texto limpo)
3. Fazer chunking (dividir em pedaços)
4. **Classificar cada chunk automaticamente** usando LLM:
   - Determina `topic`
   - Determina `applies_to` (quais requirement_ids se aplicam)
   - Baseado nas perguntas de onboarding existentes
5. Gerar embeddings (se `OPENAI_API_KEY` estiver configurada)
6. Salvar no MongoDB na collection `rag_chunks`

**Modo manual (sem classificação automática):**
```bash
python scripts/ops/ingest_rag_documents.py --manual
```
(Isso requer configuração manual, não recomendado)

## Processo de Pré-processamento (Antes da Ingestão)

Se você tem PDFs ou documentos brutos, precisa primeiro:
1. Converter para texto (se PDF)
2. Limpar e padronizar o texto (remover headers, footers, formatação)
3. Salvar como `.txt` em `backend/data/rag/processed/`

O script de ingestão espera arquivos `.txt` já limpos e prontos.

## Método Alternativo: Ingestão Programática

Você também pode injetar documentos via código Python:

```python
import asyncio
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.ai_formalization.rag import RAGChunk, RAGService, generate_embedding

async def ingest_custom():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    rag_service = RAGService(db)
    
    # Criar chunks manualmente
    chunks = [
        RAGChunk(
            content="Para obter CPF, vá até a Receita Federal...",
            topic="cpf",
            applies_to=["has_cpf"],
            source="manual_entry.txt",
        ),
        # ... mais chunks
    ]
    
    await rag_service.add_chunks(chunks)
    client.close()

asyncio.run(ingest_custom())
```

## Verificar Documentos Ingestados

### Via MongoDB shell:

```javascript
// Ver todos os chunks
db.rag_chunks.find().pretty()

// Ver chunks por requirement
db.rag_chunks.find({applies_to: "has_cpf"}).count()

// Ver por topic
db.rag_chunks.find({topic: "dap_caf"}).pretty()

// Ver distribuição de topics
db.rag_chunks.aggregate([
  {$group: {_id: "$topic", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

### Via código:

```python
from app.core.db import get_database
from app.modules.ai_formalization.rag import RAGService

db = get_database()
rag_service = RAGService(db)

# Listar todos os chunks
chunks = await rag_service.get_all_chunks()
print(f"Total chunks: {len(chunks)}")

# Buscar por requirement
relevant = await rag_service.search_relevant_chunks("has_cpf", limit=10)
print(f"Chunks para has_cpf: {len(relevant)}")
```

## Requirement IDs Disponíveis

- `has_cpf` - CPF cadastrado
- `has_dap_caf` - DAP ou CAF
- `has_cnpj` - CNPJ (para cooperativas)
- `has_bank_account` - Conta bancária
- `has_organized_documents` - Documentos organizados

## Exemplo Completo

```bash
# 1. Criar estrutura
mkdir -p backend/data/rag/processed

# 2. Adicionar arquivos de texto limpos
# (arquivos devem estar pré-processados e limpos)
cp seus_documentos_limpos.txt backend/data/rag/processed/

# 3. Popular perguntas de onboarding (se ainda não fez)
python scripts/dev/seed_onboarding_questions.py

# 4. Executar ingestão com classificação automática
python scripts/ops/ingest_rag_documents.py

# 5. Verificar
# Os chunks estarão no MongoDB, prontos para uso pelo AI agent
# Cada chunk terá topic e applies_to determinados automaticamente
```

## Troubleshooting

### Erro: "No .txt files found"
- Verifique se os arquivos estão em `backend/data/rag/processed/`
- Verifique se os arquivos têm extensão `.txt`
- Certifique-se de que os arquivos foram pré-processados e estão limpos

### Embeddings não são gerados
- Verifique se `OPENAI_API_KEY` está configurada no `.env`
- Chunks funcionam sem embeddings (usa filtro por `applies_to`)

### Chunks duplicados
- O script não remove chunks existentes
- Se reexecutar, pode criar duplicatas
- Para limpar: `db.rag_chunks.delete_many({})` no MongoDB

### Classificação não funciona
- Verifique se perguntas de onboarding estão populadas (`python scripts/dev/seed_onboarding_questions.py`)
- Verifique se `LLM_PROVIDER` está configurado (use `openai` para melhor classificação)
- Chunks com classificação falha usarão `topic="general"` como fallback

## Reingestão

Para reingerir documentos (atualizar chunks):

1. Limpar chunks antigos (opcional):
```javascript
// No MongoDB shell
db.rag_chunks.delete_many({topic: "seu_topic"})

// Ou limpar tudo
db.rag_chunks.delete_many({})
```

2. Executar ingestão novamente:
```bash
python scripts/ops/ingest_rag_documents.py
```

## Como a Classificação Automática Funciona

1. Para cada chunk de texto, o sistema:
   - Envia o chunk + lista de perguntas de onboarding para o LLM
   - LLM analisa o conteúdo e determina:
     - `topic`: Tópico principal (ex: "cpf", "dap_caf")
     - `applies_to`: Lista de requirement_ids relevantes
     - `confidence`: Nível de confiança (high/medium/low)

2. O LLM usa as perguntas de onboarding como referência:
   - Compara o conteúdo do chunk com cada pergunta
   - Determina quais requirements o chunk ajuda a resolver
   - Pode identificar múltiplos requirements se o conteúdo for relevante

3. Validação automática:
   - Garante que `applies_to` contém apenas requirement_ids válidos
   - Se classificação falhar, usa fallback (`topic="general"`)

Isso permite que documentos que se sobrepõem sejam classificados corretamente, sem necessidade de mapeamento manual!
