#!/bin/bash
# Script rápido para testar o módulo AI Formalization

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
PHONE="${PHONE:-+5511999999999}"

echo "🧪 Testando AI Formalization Module"
echo "===================================="
echo ""

# 1. Autenticar
echo "1️⃣  Autenticando..."
START_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/start" \
  -H "Content-Type: application/json" \
  -d "{\"phone_e164\": \"$PHONE\"}")

echo "   ✓ Auth start: $START_RESPONSE"

# 2. Verificar OTP
echo ""
echo "2️⃣  Verificando OTP (mock: 123456)..."
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/verify" \
  -H "Content-Type: application/json" \
  -d "{\"phone_e164\": \"$PHONE\", \"otp\": \"123456\"}")

TOKEN=$(echo $VERIFY_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "   ✗ Erro ao obter token"
    echo "   Resposta: $VERIFY_RESPONSE"
    exit 1
fi

echo "   ✓ Token obtido: ${TOKEN:0:20}..."

# 3. Testar geração de guia
echo ""
echo "3️⃣  Testando geração de guia para 'has_cpf'..."
GUIDE_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/formalization/guide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_cpf"}')

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/ai/formalization/guide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "has_cpf"}')

if [ "$STATUS_CODE" = "200" ]; then
    echo "   ✓ Status: 200 OK"
    echo ""
    echo "   Resposta:"
    echo "$GUIDE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GUIDE_RESPONSE"
else
    echo "   ✗ Erro: Status $STATUS_CODE"
    echo "   Resposta: $GUIDE_RESPONSE"
    exit 1
fi

# 4. Testar requirement inválido
echo ""
echo "4️⃣  Testando requirement_id inválido (deve retornar 404)..."
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/ai/formalization/guide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirement_id": "requirement_inexistente"}')

HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "404" ]; then
    echo "   ✓ Status 404 (esperado)"
else
    echo "   ✗ Esperado 404, recebido $HTTP_CODE"
fi

echo ""
echo "✅ Testes concluídos!"
