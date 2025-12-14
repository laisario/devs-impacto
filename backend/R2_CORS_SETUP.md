# Configurar CORS no Cloudflare R2

Você está tendo erros de CORS porque o bucket R2 não está configurado para permitir requisições do seu frontend.

## Solução: Configurar CORS no Bucket R2

### Opção 1: Via Dashboard do Cloudflare (Mais Fácil)

1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Vá em **R2** → Selecione seu bucket `hackas-bucket`
3. Vá na aba **Settings** (ou **Configurações**)
4. Role até a seção **CORS Policy** (ou **Política CORS**)
5. Clique em **Add CORS policy** ou **Edit CORS policy**

6. Configure a política CORS:

```json
[
  {
    "AllowedOrigins": ["http://localhost:5173", "http://localhost:3000", "*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

**Para produção**, substitua `"*"` pelos seus domínios específicos:
```json
[
  {
    "AllowedOrigins": [
      "https://seu-dominio.com",
      "https://www.seu-dominio.com"
    ],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

7. Clique em **Save** ou **Salvar**

### Opção 2: Via API/CLI (Avançado)

Se preferir usar a API:

```bash
curl -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/<account-id>/r2/buckets/hackas-bucket/cors" \
  -H "Authorization: Bearer <api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }'
```

### Configuração Recomendada para Desenvolvimento

Para desenvolvimento local, use:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:5173",
      "http://localhost:3000",
      "http://127.0.0.1:5173",
      "http://127.0.0.1:3000"
    ],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

### Explicação dos Campos

- **AllowedOrigins**: Origens permitidas (domínios do frontend)
  - `"*"` permite todas (não recomendado para produção)
  - Especifique domínios exatos para produção
  
- **AllowedMethods**: Métodos HTTP permitidos
  - `PUT` é necessário para upload via presigned URL
  - `GET` é necessário para download
  
- **AllowedHeaders**: Headers permitidos
  - `"*"` permite todos (ok para presigned URLs)
  
- **ExposeHeaders**: Headers expostos ao frontend
  - `ETag` é útil para verificar integridade
  
- **MaxAgeSeconds**: Tempo de cache da política CORS (1 hora = 3600)

## Verificar se Funcionou

Após configurar:

1. Tente fazer upload novamente no frontend
2. Abra o DevTools (F12) → Network
3. Verifique a requisição PUT para o R2
4. Deve retornar status 200 sem erros de CORS

## Troubleshooting

### Ainda tem erro de CORS?

1. **Verifique se salvou a configuração**: Recarregue a página do dashboard
2. **Aguarde alguns segundos**: CORS pode levar alguns segundos para propagar
3. **Limpe o cache do navegador**: Ctrl+Shift+R (ou Cmd+Shift+R no Mac)
4. **Verifique a origem**: O erro no console mostra qual origem está sendo bloqueada

### Erro: "No 'Access-Control-Allow-Origin' header"

Significa que o CORS não está configurado ou a origem não está na lista de permitidas.

### Erro: "Method PUT not allowed"

Certifique-se de que `PUT` está na lista de `AllowedMethods`.

## Segurança em Produção

⚠️ **Nunca use `"*"` em produção!**

Sempre especifique os domínios exatos:
```json
{
  "AllowedOrigins": [
    "https://seu-app.com",
    "https://www.seu-app.com"
  ]
}
```
