# Documentação de Endpoints - PNAE Simplificado API

Esta documentação lista todos os endpoints da API com exemplos de payload e resposta.

**Base URL**: `http://localhost:8000` (ou a URL do seu ambiente)

**Autenticação**: A maioria dos endpoints requer um token JWT no header:
```
Authorization: Bearer <access_token>
```

---

## Índice

1. [Health Check](#health-check)
2. [Autenticação](#autenticação)
3. [Perfil do Produtor](#perfil-do-produtor)
4. [Documentos](#documentos)
5. [Onboarding](#onboarding)
6. [Formalização](#formalização)
7. [IA - Guia de Formalização](#ia---guia-de-formalização)

---

## Health Check

### GET `/`
Health check básico.

**Resposta:**
```json
{
  "status": "ok",
  "service": "PNAE Simplificado API",
  "version": "0.1.0"
}
```

### GET `/health`
Health check detalhado.

**Resposta:**
```json
{
  "status": "healthy",
  "database": "pnae_db",
  "storage_provider": "local"
}
```

---

## Autenticação

### POST `/auth/start`
Inicia o processo de autenticação enviando OTP para o telefone.

**Payload:**
```json
{
  "phone_e164": "+5511999999999"
}
```

**Resposta:**
```json
{
  "ok": true,
  "message": "OTP sent successfully"
}
```

**Nota**: Em modo de desenvolvimento, o OTP é sempre `123456`.

---

### POST `/auth/verify`
Verifica o código OTP e retorna o token JWT.

**Payload:**
```json
{
  "phone_e164": "+5511999999999",
  "otp": "123456"
}
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### GET `/auth/me`
Retorna informações do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "phone_e164": "+5511999999999",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

## Perfil do Produtor

### PUT `/producer-profile`
Cria ou atualiza o perfil do produtor.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload (Tipo Formal):**
```json
{
  "producer_type": "formal",
  "name": "Cooperativa Agrícola do Vale",
  "address": "Rua das Flores, 123",
  "city": "São Paulo",
  "state": "SP",
  "dap_caf_number": "DAP-123456",
  "cnpj": "12345678000190",
  "bank_name": "Banco do Brasil",
  "bank_agency": "1234-5",
  "bank_account": "12345-6"
}
```

**Payload (Tipo Informal):**
```json
{
  "producer_type": "informal",
  "name": "Grupo de Agricultores Familiares",
  "address": "Estrada Rural, Km 5",
  "city": "Campinas",
  "state": "SP",
  "dap_caf_number": "DAP-789012",
  "cpf": "12345678901",
  "members": [
    {
      "name": "João Silva",
      "cpf": "12345678901",
      "dap_caf_number": "DAP-789012"
    },
    {
      "name": "Maria Santos",
      "cpf": "98765432109",
      "dap_caf_number": "DAP-789013"
    }
  ],
  "bank_name": "Caixa Econômica",
  "bank_agency": "5678",
  "bank_account": "98765-4"
}
```

**Payload (Tipo Individual):**
```json
{
  "producer_type": "individual",
  "name": "José da Silva",
  "address": "Sítio São José, Zona Rural",
  "city": "Ribeirão Preto",
  "state": "SP",
  "dap_caf_number": "DAP-456789",
  "cpf": "11122233344",
  "bank_name": "Banco do Brasil",
  "bank_agency": "1111-2",
  "bank_account": "22222-3"
}
```

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "producer_type": "formal",
  "name": "Cooperativa Agrícola do Vale",
  "address": "Rua das Flores, 123",
  "city": "São Paulo",
  "state": "SP",
  "dap_caf_number": "DAP-123456",
  "cnpj": "12345678000190",
  "cpf": null,
  "members": null,
  "bank_name": "Banco do Brasil",
  "bank_agency": "1234-5",
  "bank_account": "12345-6",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "onboarding_status": null,
  "onboarding_completed_at": null
}
```

---

### GET `/producer-profile`
Retorna o perfil do produtor do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "producer_type": "formal",
  "name": "Cooperativa Agrícola do Vale",
  "address": "Rua das Flores, 123",
  "city": "São Paulo",
  "state": "SP",
  "dap_caf_number": "DAP-123456",
  "cnpj": "12345678000190",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### GET `/producer-profile/{profile_id}`
Retorna um perfil específico por ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:** (mesmo formato do GET `/producer-profile`)

---

## Documentos

### POST `/documents/presign`
Gera uma URL pré-assinada para upload de documento.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload:**
```json
{
  "filename": "dap_caf.pdf",
  "content_type": "application/pdf"
}
```

**Resposta:**
```json
{
  "upload_url": "https://storage.example.com/upload?signature=...",
  "file_url": "https://storage.example.com/files/user123/dap_caf.pdf",
  "file_key": "user123/dap_caf_20250115_103000.pdf"
}
```

**Fluxo:**
1. Cliente chama este endpoint para obter a URL pré-assinada
2. Cliente faz upload do arquivo diretamente para `upload_url`
3. Cliente chama `POST /documents` com os metadados

---

### POST `/documents`
Cria metadados do documento após o upload.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload:**
```json
{
  "doc_type": "dap_caf",
  "file_url": "https://storage.example.com/files/user123/dap_caf.pdf",
  "file_key": "user123/dap_caf_20250115_103000.pdf",
  "original_filename": "dap_caf.pdf"
}
```

**Tipos de documento (`doc_type`):**
- `dap_caf`: Declaração de Aptidão ao Pronaf
- `cpf`: CPF
- `cnpj`: CNPJ
- `proof_address`: Comprovante de endereço
- `bank_statement`: Extrato bancário
- `statute`: Estatuto social (cooperativas)
- `minutes`: Ata de assembleia
- `other`: Outro

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439014",
  "user_id": "507f1f77bcf86cd799439011",
  "doc_type": "dap_caf",
  "file_url": "https://storage.example.com/files/user123/dap_caf.pdf",
  "file_key": "user123/dap_caf_20250115_103000.pdf",
  "original_filename": "dap_caf.pdf",
  "uploaded_at": "2025-01-15T10:30:00Z"
}
```

---

### GET `/documents`
Lista todos os documentos do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (int, opcional): Número de itens para pular (padrão: 0)
- `limit` (int, opcional): Número de itens para retornar (padrão: 20, máximo: 100)

**Resposta:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439014",
      "user_id": "507f1f77bcf86cd799439011",
      "doc_type": "dap_caf",
      "file_url": "https://storage.example.com/files/user123/dap_caf.pdf",
      "file_key": "user123/dap_caf_20250115_103000.pdf",
      "original_filename": "dap_caf.pdf",
      "uploaded_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

### GET `/documents/{document_id}`
Retorna um documento específico por ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:** (mesmo formato do item no array de `GET /documents`)

---

## Onboarding

### POST `/onboarding/answer`
Cria um novo projeto de venda (Envelope 02).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload:**
```json
{
  "call_id": "507f1f77bcf86cd799439013",
  "items": [
    {
      "product_name": "Arroz",
      "unit": "kg",
      "quantity": 500.0,
      "unit_price": 5.00,
      "delivery_schedule": "Março/2025, Abril/2025, Maio/2025"
    },
    {
      "product_name": "Feijão",
      "unit": "kg",
      "quantity": 300.0,
      "unit_price": 7.50,
      "delivery_schedule": "Março/2025, Abril/2025"
    },
    {
      "product_name": "Banana",
      "unit": "kg",
      "quantity": 1000.0,
      "unit_price": 3.00,
      "delivery_schedule": "Março/2025 até Novembro/2025"
    }
  ]
}
```

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439015",
  "user_id": "507f1f77bcf86cd799439011",
  "call_id": "507f1f77bcf86cd799439013",
  "producer_profile_id": "507f1f77bcf86cd799439012",
  "items": [
    {
      "product_name": "Arroz",
      "unit": "kg",
      "quantity": 500.0,
      "unit_price": 5.00,
      "delivery_schedule": "Março/2025, Abril/2025, Maio/2025",
      "total": 2500.0
    },
    {
      "product_name": "Feijão",
      "unit": "kg",
      "quantity": 300.0,
      "unit_price": 7.50,
      "delivery_schedule": "Março/2025, Abril/2025",
      "total": 2250.0
    },
    {cy": 1000.0,
      "unit_price": 3.00,
      "delivery_schedule": "Março/2025 até Novembro/2025",
      "total": 3000.0
    }
  ],
  "total_value": 7750.0,
  "status": "draft",
  "generated_pdf_url": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### GET `/sales-projects/{project_id}`
Retorna um projeto de venda específico.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:** (mesmo formato do POST `/sales-projects`)

---

### POST `/sales-projects/{project_id}/generate-pdf`
Gera o PDF do projeto de venda.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "pdf_url": "https://storage.example.com/pdfs/projeto_venda_507f1f77bcf86cd799439015.pdf",
  "message": "PDF gerado com sucesso"
}
```

O PDF gerado contém:
- Identificação da proposta (número da chamada)
- Identificação da entidade executora
- Identificação do fornecedor (produtor)
- Lista de produtos com quantidades, preços e cronograma
- Valor total
- Área para assinatura

---

## Onboarding

### POST `/onboarding/answer`
Submete uma resposta a uma pergunta do onboarding.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload:**
```json
{
  "question_id": "has_dap_caf",
  "answer": true
}
```

**Resposta:**
```json
{
  "id": "507f1f77bcf86cd799439016",
  "user_id": "507f1f77bcf86cd799439011",
  "question_id": "has_dap_caf",
  "answer": true,
  "answered_at": "2025-01-15T10:30:00Z"
}
```

**Nota**: O tipo de `answer` varia conforme o tipo da pergunta:
- `boolean`: `true` ou `false`
- `choice`: string com a opção escolhida
- `text`: string com texto livre

---

### GET `/onboarding/status`
Retorna o status atual do onboarding.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "status": "in_progress",
  "progress_percentage": 45.5,
  "total_questions": 20,
  "answered_questions": 9,
  "next_question": {
    "question_id": "has_cnpj",
    "question_text": "Você possui CNPJ?",
    "question_type": "boolean",
    "options": null,
    "order": 10,
    "required": true,
    "requirement_id": "cnpj_registration"
  },
  "completed_at": null
}
```

**Status possíveis:**
- `not_started`: Onboarding não iniciado
- `in_progress`: Em andamento
- `completed`: Concluído

---

### GET `/onboarding/summary`
Retorna um resumo agregado do onboarding e formalização do produtor.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "onboarding_status": "in_progress",
  "onboarding_completed_at": null,
  "onboarding_progress": 45.5,
  "formalization_eligible": false,
  "formalization_score": 35,
  "has_profile": true,
  "total_answers": 9,
  "total_tasks": 5,
  "completed_tasks": 2
}
```

---

## Formalização

### GET `/formalization/status`
Retorna o diagnóstico de elegibilidade para vender em programas públicos.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
{
  "is_eligible": false,
  "eligibility_level": "partially_eligible",
  "score": 65,
  "requirements_met": [
    "Possui DAP/CAF",
    "Possui CPF",
    "Endereço cadastrado"
  ],
  "requirements_missing": [
    "CNPJ não registrado",
    "Estatuto social não apresentado"
  ],
  "recommendations": [
    "Registrar CNPJ na Receita Federal",
    "Elaborar e registrar estatuto social",
    "Obter certidões negativas"
  ],
  "diagnosed_at": "2025-01-15T10:30:00Z"
}
```

**Níveis de elegibilidade (`eligibility_level`):**
- `eligible`: Totalmente elegível
- `partially_eligible`: Parcialmente elegível
- `not_eligible`: Não elegível

---

### GET `/formalization/tasks`
Retorna a lista de tarefas de formalização baseadas no diagnóstico.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Resposta:**
```json
[
  {
    "id": "507f1f77bcf86cd799439017",
    "user_id": "507f1f77bcf86cd799439011",
    "task_id": "register_cnpj",
    "title": "Registrar CNPJ na Receita Federal",
    "description": "É necessário registrar um CNPJ para operar como pessoa jurídica. Procure um contador ou acesse o site da Receita Federal.",
    "category": "registration",
    "priority": "high",
    "completed": false,
    "completed_at": null,
    "created_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": "507f1f77bcf86cd799439018",
    "user_id": "507f1f77bcf86cd799439011",
    "task_id": "create_statute",
    "title": "Elaborar Estatuto Social",
    "description": "Para cooperativas e associações, é necessário ter um estatuto social registrado.",
    "category": "document",
    "priority": "medium",
    "completed": false,
    "completed_at": null,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

**Categorias (`category`):**
- `document`: Documento necessário
- `registration`: Registro/formalização
- `preparation`: Preparação/documentação

**Prioridades (`priority`):**
- `high`: Alta prioridade
- `medium`: Média prioridade
- `low`: Baixa prioridade

---

## IA - Guia de Formalização

### POST `/ai/formalization/guide`
Gera um guia personalizado passo a passo para cumprir um requisito de formalização usando IA e RAG.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Payload:**
```json
{
  "requirement_id": "cnpj_registration"
}
```

**Resposta:**
```json
{
  "summary": "Para registrar um CNPJ, você precisa seguir alguns passos junto à Receita Federal. Este processo é essencial para operar como pessoa jurídica e participar de programas públicos como o PNAE.",
  "steps": [
    {
      "step": 1,
      "title": "Verificar pré-requisitos",
      "description": "Antes de iniciar, verifique se você possui: CPF válido, comprovante de endereço atualizado, e definição do tipo de empresa (MEI, EIRELI, etc.)."
    },
    {
      "step": 2,
      "title": "Escolher o tipo de empresa",
      "description": "Decida qual o melhor enquadramento para seu negócio. Para agricultura familiar, o MEI (Microempreendedor Individual) é uma opção simples e com menos burocracia."
    },
    {
      "step": 3,
      "title": "Acessar o portal da Receita Federal",
      "description": "Acesse o site da Receita Federal (www.gov.br/receitafederal) e faça login com seu CPF. Se não tiver cadastro, crie uma conta no Portal Gov.br."
    },
    {
      "step": 4,
      "title": "Preencher o formulário de abertura",
      "description": "Preencha o formulário de abertura de empresa com todas as informações solicitadas: nome da empresa, endereço, atividade econômica, etc."
    },
    {
      "step": 5,
      "title": "Aguardar análise e receber o CNPJ",
      "description": "Após o envio, aguarde a análise da Receita Federal. O CNPJ geralmente é emitido em até 5 dias úteis. Você receberá o número do CNPJ por e-mail ou poderá consultar no portal."
    }
  ],
  "estimated_time_days": 7,
  "where_to_go": [
    "Receita Federal - Portal Gov.br (www.gov.br/receitafederal)",
    "Posto de Atendimento da Receita Federal (se necessário)"
  ],
  "confidence_level": "high"
}
```

**Níveis de confiança (`confidence_level`):**
- `high`: Alta confiança - informações bem fundamentadas
- `medium`: Confiança média - algumas informações podem precisar de verificação
- `low`: Baixa confiança - recomenda-se verificar informações adicionais

---

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Dados inválidos na requisição
- `401 Unauthorized`: Token ausente ou inválido
- `404 Not Found`: Recurso não encontrado
- `422 Unprocessable Entity`: Erro de validação
- `500 Internal Server Error`: Erro interno do servidor

---

## Observações Importantes

1. **Autenticação**: A maioria dos endpoints requer autenticação via JWT token no header `Authorization: Bearer <token>`.

2. **Formato de Telefone**: Use o formato E.164 (ex: `+5511999999999`).

3. **Formato de CPF/CNPJ**: Sempre sem pontuação (apenas números).

4. **Datas**: Use formato ISO 8601 (ex: `2025-01-15T10:30:00Z`).

5. **Paginação**: Endpoints que retornam listas usam `skip` e `limit` para paginação.

6. **Upload de Documentos**: O fluxo é em duas etapas:
   - Primeiro, obtenha a URL pré-assinada com `POST /documents/presign`
   - Faça upload do arquivo para a URL retornada
   - Depois, registre os metadados com `POST /documents`

7. **Modo de Desenvolvimento**: Em desenvolvimento, o OTP é sempre `123456`.

---

## Documentação Interativa

A API também possui documentação interativa disponível em:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

Essas interfaces permitem testar os endpoints diretamente no navegador.
