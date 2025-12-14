# Como Obter as Credenciais do Cloudflare R2

Você já tem a URL do bucket:
- Bucket: `hackas-bucket`
- Account ID: `7df0d23556ddbea3607ced2ccfacb19d`
- Endpoint: `https://7df0d23556ddbea3607ced2ccfacb19d.r2.cloudflarestorage.com`

Agora você precisa obter as **credenciais de API** (Access Key ID e Secret Access Key).

## Passo a Passo:

1. **Acesse o Cloudflare Dashboard**
   - Vá para: https://dash.cloudflare.com/

2. **Navegue até R2**
   - No menu lateral, clique em **R2** (ou procure por "R2" na busca)
   - Ou acesse diretamente: https://dash.cloudflare.com/?to=/:account/r2

3. **Vá em "Manage R2 API Tokens"**
   - Você verá uma opção para gerenciar tokens de API
   - Clique em **Create API token** ou **Create R2 API Token**

4. **Configure o Token**
   - **Token name**: Dê um nome (ex: `hackas-storage-token`)
   - **Permissions**: Selecione **Object Read & Write** ou **Admin Read & Write**
   - **TTL**: Deixe em branco (não expira) ou defina um tempo
   - **R2 Buckets**: Selecione o bucket `hackas-bucket`
   - Clique em **Create API Token**

5. **Copie as Credenciais**
   - Você verá:
     - **Access Key ID**: Uma string longa (ex: `abc123def456...`)
     - **Secret Access Key**: Outra string longa
   - **⚠️ IMPORTANTE**: Copie e salve a Secret Access Key AGORA
     - Você não poderá vê-la novamente depois!
     - Se perder, terá que criar um novo token

6. **Atualize o docker-compose.override.yml**

   Substitua no arquivo:
   ```yaml
   - S3_ACCESS_KEY_ID=sua-access-key-id
   - S3_SECRET_ACCESS_KEY=sua-secret-access-key
   ```
   
   Por:
   ```yaml
   - S3_ACCESS_KEY_ID=cole-aqui-o-access-key-id
   - S3_SECRET_ACCESS_KEY=cole-aqui-o-secret-access-key
   ```

## Local Alternativo no Dashboard

Se não encontrar "Manage R2 API Tokens" no menu principal:
- Clique no bucket `hackas-bucket`
- Vá na aba **Settings** ou **API**
- Procure por **API Tokens** ou **Access Keys**
- Crie um novo token lá

## Verificar se Funcionou

Após configurar as credenciais:

1. Reinicie o backend:
   ```bash
   docker-compose restart backend
   ```

2. Verifique os logs:
   ```bash
   docker-compose logs backend | grep -i storage
   ```

3. Teste fazendo upload de um arquivo via API

## Se Ainda Não Encontrar

O caminho exato pode variar. Tente:
- Dashboard → R2 → Settings → API Tokens
- Ou pesquise por "API token" no dashboard
- Ou acesse: https://dash.cloudflare.com/?to=/:account/r2/api-tokens
