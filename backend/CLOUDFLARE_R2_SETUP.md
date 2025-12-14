# Cloudflare R2 Setup Guide

Este guia explica como configurar o Cloudflare R2 para armazenamento de arquivos.

## Por que R2?

- **Compatível com S3**: Usa a mesma API, então funciona com boto3
- **Mais fácil**: Não precisa de configuração complexa como GCS
- **Custo**: Mais barato ou gratuito para hackathons
- **Sem egress fees**: Diferente do S3, não cobra por tráfego de saída

## Passo 1: Criar um Bucket no Cloudflare

1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Vá em **R2** no menu lateral (ou procure por "R2" na busca)
3. Clique em **Create bucket**
4. Dê um nome ao bucket (ex: `pnae-hackathon-storage`)
5. Escolha a localização (região mais próxima dos usuários)
6. Clique em **Create bucket**

## Passo 2: Obter Credenciais de API

1. No dashboard do R2, vá em **Manage R2 API Tokens**
2. Clique em **Create API token**
3. Configure:
   - **Token name**: Dê um nome (ex: `pnae-storage-token`)
   - **Permissions**: Selecione **Object Read & Write**
   - **TTL**: Opcional, deixe em branco para não expirar (ou defina um tempo)
   - **R2 Buckets**: Selecione o bucket que você criou
4. Clique em **Create API Token**
5. **Importante**: Copie e salve:
   - **Access Key ID**
   - **Secret Access Key**
   - Você não poderá ver a Secret novamente!

## Passo 3: Obter o Endpoint URL

1. No dashboard do R2, vá em **Manage R2 API Tokens** novamente
2. Você verá o **Account ID** no topo
3. O endpoint será: `https://<account-id>.r2.cloudflarestorage.com`
   - Exemplo: `https://abc123def456.r2.cloudflarestorage.com`

## Passo 4: Configurar URL Pública (Opcional mas Recomendado)

### Opção A: Usar URL padrão do R2

A URL pública padrão é:
```
https://<bucket-name>.<account-id>.r2.cloudflarestorage.com
```

Exemplo:
```
https://pnae-hackathon-storage.abc123def456.r2.cloudflarestorage.com
```

### Opção B: Configurar Custom Domain (Recomendado)

1. No dashboard do R2, vá no seu bucket
2. Vá na aba **Settings**
3. Em **Public Access**, configure um domínio customizado
4. Siga as instruções para configurar DNS

## Passo 5: Habilitar Acesso Público (se necessário)

1. No bucket, vá em **Settings**
2. Em **Public Access**, configure:
   - **Public Access**: Enable
   - Configure as permissões desejadas

**Nota**: Se você usar presigned URLs (que é o caso), não precisa habilitar acesso público ao bucket inteiro.

## Passo 6: Configurar no Projeto

Atualize seu `docker-compose.override.yml`:

```yaml
services:
  backend:
    environment:
      - STORAGE_PROVIDER=s3
      - S3_BUCKET_NAME=pnae-hackathon-storage  # Nome do seu bucket
      - S3_ENDPOINT_URL=https://abc123def456.r2.cloudflarestorage.com  # Seu endpoint
      - S3_REGION_NAME=auto  # R2 sempre usa "auto"
      - S3_ACCESS_KEY_ID=sua-access-key-id-aqui
      - S3_SECRET_ACCESS_KEY=sua-secret-access-key-aqui
      - S3_PUBLIC_URL=https://pnae-hackathon-storage.abc123def456.r2.cloudflarestorage.com
```

Ou use variáveis de ambiente no `.env`:

```env
STORAGE_PROVIDER=s3
S3_BUCKET_NAME=pnae-hackathon-storage
S3_ENDPOINT_URL=https://abc123def456.r2.cloudflarestorage.com
S3_REGION_NAME=auto
S3_ACCESS_KEY_ID=sua-access-key-id
S3_SECRET_ACCESS_KEY=sua-secret-access-key
S3_PUBLIC_URL=https://pnae-hackathon-storage.abc123def456.r2.cloudflarestorage.com
```

## Passo 7: Testar

1. Reinicie o backend:
   ```bash
   docker-compose restart backend
   ```

2. Verifique os logs:
   ```bash
   docker-compose logs backend | grep -i storage
   ```

3. Teste fazendo upload de um arquivo via API

## Troubleshooting

### Erro: "S3 bucket name is required"
- Verifique se `S3_BUCKET_NAME` está configurado
- Nome deve corresponder exatamente ao bucket no R2

### Erro: "Access Denied" ou "403 Forbidden"
- Verifique se `S3_ACCESS_KEY_ID` e `S3_SECRET_ACCESS_KEY` estão corretos
- Verifique se o token tem permissões de "Object Read & Write"
- Verifique se o bucket está selecionado nas permissões do token

### Erro: "Endpoint connection failed"
- Verifique se `S3_ENDPOINT_URL` está correto
- Deve ser: `https://<account-id>.r2.cloudflarestorage.com`
- Não inclua o nome do bucket no endpoint

### Arquivos fazem upload mas URLs retornam 404
- Verifique se `S3_PUBLIC_URL` está configurado corretamente
- Formato: `https://<bucket>.<account-id>.r2.cloudflarestorage.com`
- Ou configure um custom domain no R2

### URLs públicas não funcionam
- Verifique se o bucket tem acesso público habilitado (se necessário)
- Ou use apenas presigned URLs (mais seguro)

## Segurança

- **Nunca commite** as credenciais no git
- Use variáveis de ambiente ou secrets management
- Tokens de API devem ter permissões mínimas necessárias
- Considere usar presigned URLs ao invés de acesso público total

## Custo

Cloudflare R2 oferece:
- **10 GB de armazenamento**: Gratuito/mês
- **1 milhão de operações Class A (write)**: Gratuito/mês
- **10 milhões de operações Class B (read)**: Gratuito/mês
- **Sem custo de egress**: Diferente do S3!

Perfeito para hackathons! 🚀
