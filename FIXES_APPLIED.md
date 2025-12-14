# Correções Aplicadas - Producer Profile 404 e IA não gerando

## Problemas Identificados

1. **Producer Profile retornando 404**: O perfil não estava sendo criado porque:
   - DAP/CAF era obrigatório mas pode não estar preenchido durante onboarding
   - CPF era obrigatório mas não é mais coletado no onboarding (vem do login)
   - Validação muito restritiva no `get_profile_by_user`

2. **IA não gerando**: As funcionalidades GenAI dependiam do perfil existir, mas o perfil não estava sendo criado.

## Correções Aplicadas

### 1. Schema de Producer Profile
- ✅ `dap_caf_number` agora é opcional (`str | None`)
- ✅ Validação de CPF removida (vem do login/auth)
- ✅ Validação de DAP/CAF removida durante onboarding

### 2. Criação de Perfil
- ✅ Perfil agora é criado mesmo sem DAP/CAF
- ✅ Perfil pode ser criado sem CPF (vem do login)
- ✅ Perfil mínimo é criado após onboarding completo

### 3. Busca de Perfil
- ✅ `get_profile_by_user` agora aceita perfil sem DAP/CAF
- ✅ Tenta buscar CPF do documento de usuário se não estiver no perfil
- ✅ Retorna perfil mesmo se alguns campos opcionais estiverem faltando

### 4. Funcionalidades GenAI
- ✅ **Guia Personalizado**: Funciona mesmo sem perfil completo (usa onboarding answers)
- ✅ **Chatbot**: Funciona mesmo sem perfil (busca contexto de onboarding se perfil não existe)
- ✅ **Validação de Documentos**: Funciona independente do perfil
- ✅ **Projeto de Venda**: Funciona mesmo sem perfil completo

## Como Testar

1. **Complete o onboarding** (mesmo sem DAP/CAF)
2. **Verifique se o perfil foi criado**:
   ```bash
   curl http://localhost:8000/producer-profile \
     -H "Authorization: Bearer SEU_TOKEN"
   ```
   Não deve mais retornar 404.

3. **Teste o Guia Personalizado**:
   - Vá para um item da checklist
   - Clique em "Gerar Guia"
   - Deve gerar um guia personalizado

4. **Teste o Chatbot**:
   - Clique no ícone de chat
   - Envie uma mensagem
   - Deve receber resposta da IA

## Próximos Passos

Se ainda houver problemas:

1. **Verificar logs do backend**:
   ```bash
   docker-compose logs -f backend | grep -i "error\|profile\|ai"
   ```

2. **Verificar se OpenAI key está configurada**:
   ```bash
   docker-compose exec backend env | grep OPENAI
   ```

3. **Testar endpoint de guia diretamente**:
   ```bash
   curl -X POST http://localhost:8000/ai/formalization/guide \
     -H "Authorization: Bearer SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"requirement_id": "dap_caf"}'
   ```
