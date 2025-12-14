# Configuração do Google Cloud Speech & TTS

Este guia explica como configurar o Google Cloud Speech-to-Text e Text-to-Speech para o chatbot.

## 1. Criar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Anote o **Project ID**

## 2. Habilitar APIs

Habilite as seguintes APIs no seu projeto:

- **Cloud Speech-to-Text API**
- **Cloud Text-to-Speech API**

```bash
# Via gcloud CLI (opcional)
gcloud services enable speech.googleapis.com
gcloud services enable texttospeech.googleapis.com
```

## 3. Criar Service Account

1. Vá em **IAM & Admin** > **Service Accounts**
2. Clique em **Create Service Account**
3. Dê um nome (ex: `pnae-chatbot-audio`)
4. Conceda as roles:
   - `Cloud Speech Client`
   - `Cloud Text-to-Speech API User`
   - `Storage Admin` (ou `Storage Object Admin` para mais segurança, se usar GCS)
5. Clique em **Create Key** > **JSON**
6. Salve o arquivo JSON (ex: `google-credentials.json`)

## 4. Configurar no Projeto

### Opção A: Via arquivo de credenciais (recomendado para desenvolvimento)

1. Coloque o arquivo `google-credentials.json` em `backend/credentials/`
2. Configure no `docker-compose.override.yml`:

```yaml
services:
  backend:
    volumes:
      - ./backend/credentials:/app/credentials:ro
    environment:
      - AUDIO_PROVIDER=google
      - GOOGLE_CLOUD_PROJECT_ID=seu-project-id-aqui
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
```

### Opção B: Via variável de ambiente JSON (recomendado para produção/Render)

Esta é a forma mais segura para produção, especialmente no Render ou outros serviços de hospedagem.

1. Abra o arquivo `google-credentials.json` e copie **todo o conteúdo** (incluindo as chaves `{}`)

2. No Render (ou outro serviço):
   - Vá em **Environment** > **Environment Variables**
   - Adicione uma nova variável:
     - **Key:** `GOOGLE_CREDENTIALS_JSON`
     - **Value:** Cole o JSON completo diretamente (pode ser multi-linha)
   
3. Configure também estas variáveis:
   ```
   AUDIO_PROVIDER=google
   GOOGLE_CLOUD_PROJECT_ID=automatic-array-276122
   ```

**Exemplo de como ficaria no Render:**
```
GOOGLE_CREDENTIALS_JSON={
  "type": "service_account",
  "project_id": "automatic-array-276122",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  ...
}
```

**Nota:** No Render, você pode colar o JSON completo com quebras de linha. O sistema automaticamente criará um arquivo temporário com essas credenciais.

### Opção C: Via arquivo (legado, não recomendado)

1. Configure a variável `GOOGLE_APPLICATION_CREDENTIALS` apontando para o arquivo JSON
2. Ou use Application Default Credentials (ADC) se estiver rodando no Google Cloud

## 5. Instalar Dependências

As dependências já estão no `pyproject.toml`:

```toml
"google-cloud-speech>=2.28.0",
"google-cloud-texttospeech>=2.18.0",
```

Instale com:

```bash
pip install google-cloud-speech google-cloud-texttospeech
```

## 6. Testar

Após configurar, reinicie o backend. O serviço de áudio detectará automaticamente o Google Cloud se:

- `AUDIO_PROVIDER=google` estiver configurado
- `GOOGLE_CLOUD_PROJECT_ID` estiver definido
- As credenciais estiverem acessíveis

## Fallback

Se o Google Cloud não estiver configurado, o sistema usa:
1. OpenAI (se `AUDIO_PROVIDER=openai` e `OPENAI_API_KEY` configurado)
2. Mock (para desenvolvimento)

## Custos

Google Cloud oferece tier gratuito:
- **Speech-to-Text**: 60 minutos/mês grátis
- **Text-to-Speech**: 4 milhões de caracteres/mês grátis

Após o tier gratuito, os custos são baixos (verifique na [página de preços](https://cloud.google.com/speech-to-text/pricing)).

---

## Configuração do Google Cloud Storage (GCS)

Para usar o GCS como provider de armazenamento de arquivos:

### 1. Criar Bucket no GCS

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Vá em **Cloud Storage** > **Buckets**
3. Clique em **Create Bucket**
4. Dê um nome único (ex: `pnae-hackathon-storage`)
5. Escolha a localização
6. **Importante**: Configure o bucket para permitir acesso público de leitura:
   - Vá em **Permissions** do bucket
   - Adicione o principal `allUsers` com a role `Storage Object Viewer`
   - Ou configure "Uniform bucket-level access" se preferir

### 2. Configurar no Projeto

1. Configure as variáveis de ambiente:

```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - STORAGE_PROVIDER=gcs
      - GCS_BUCKET_NAME=seu-bucket-name-aqui
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
```

2. As mesmas credenciais do Google Cloud usadas para Speech/TTS funcionam para Storage

### 3. Testar

Após configurar, reinicie o backend. O sistema usará GCS para:
- Upload de documentos
- Upload de áudios do chat
- Geração de URLs públicas para acesso aos arquivos

### Notas

- O GCS gera presigned URLs para uploads seguros (válidas por 1 hora)
- Os arquivos ficam armazenados no bucket configurado
- URLs públicas seguem o formato: `https://storage.googleapis.com/{bucket}/{file_key}`
