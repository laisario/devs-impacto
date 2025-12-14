"""
Formalization diagnosis logic (pure function).
Calculates eligibility for selling to public programs based on onboarding answers.
"""

from typing import Any


def calculate_eligibility(responses: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate eligibility for selling to public programs (PNAE, etc.).

    This is a pure function - no side effects, no external dependencies.
    Based on onboarding answers, determines:
    - Eligibility level (eligible, partially_eligible, not_eligible)
    - Score (0-100)
    - Requirements met
    - Requirements missing
    - Recommendations

    Args:
        responses: Dictionary mapping question_id to answer

    Returns:
        Dictionary with eligibility information:
        {
            "is_eligible": bool,
            "eligibility_level": str,  # "eligible", "partially_eligible", "not_eligible"
            "score": int,  # 0-100
            "requirements_met": list[str],
            "requirements_missing": list[str],
            "recommendations": list[str],
        }
    """
    # Extract answers with defaults
    has_cpf = responses.get("has_cpf", False)
    has_dap_caf = responses.get("has_dap_caf", False)
    has_cnpj = responses.get("has_cnpj", False)
    producer_type_pref = responses.get("producer_type_preference", "").lower()
    has_previous_public_sales = responses.get("has_previous_public_sales", False)
    has_bank_account = responses.get("has_bank_account", False)
    has_organized_documents = responses.get("has_organized_documents", False)

    requirements_met: list[str] = []
    requirements_missing: list[str] = []
    recommendations: list[str] = []

    # Essential requirements (must have)
    if has_cpf:
        requirements_met.append("CPF cadastrado")
    else:
        requirements_missing.append("CPF cadastrado")
        recommendations.append("Obtenha seu CPF na Receita Federal")

    if has_dap_caf:
        requirements_met.append("DAP ou CAF")
    else:
        requirements_missing.append("DAP ou CAF")
        recommendations.append(
            "Obtenha sua DAP (Declaração de Aptidão ao Pronaf) na Emater ou órgão similar"
        )

    # Type-specific requirements
    is_formal = producer_type_pref in ["cooperativa/associação", "cooperativa", "associação"]
    if is_formal:
        if has_cnpj:
            requirements_met.append("CNPJ (para cooperativa/associação)")
        else:
            requirements_missing.append("CNPJ (para cooperativa/associação)")
            recommendations.append("Registre CNPJ para sua cooperativa ou associação")

    # Important but not blocking
    if has_bank_account:
        requirements_met.append("Conta bancária")
    else:
        requirements_missing.append("Conta bancária")
        recommendations.append("Abra uma conta bancária para receber pagamentos")

    if has_organized_documents:
        requirements_met.append("Documentos organizados")
    else:
        requirements_missing.append("Documentos organizados")
        recommendations.append("Organize seus documentos (CPF, DAP, comprovante de endereço)")

    # Calculate score (0-100)
    # Essential requirements: 60 points (30 each)
    # Type-specific: 20 points
    # Nice to have: 20 points (10 each)
    score = 0

    if has_cpf:
        score += 30
    if has_dap_caf:
        score += 30
    if is_formal and has_cnpj:
        score += 20
    elif not is_formal:
        score += 20  # Not required for individual/informal

    if has_bank_account:
        score += 10
    if has_organized_documents:
        score += 10
    if has_previous_public_sales:
        score += 5  # Bonus for experience

    # Determine eligibility level
    # Eligible: Has CPF and DAP/CAF (and CNPJ if formal) + at least 60 points
    # Partially eligible: Has essential docs but missing some requirements (50-79 points)
    # Not eligible: Missing essential docs (< 50 points)

    essential_ok = has_cpf and has_dap_caf and (not is_formal or has_cnpj)

    if essential_ok and score >= 80:
        eligibility_level = "eligible"
        is_eligible = True
    elif essential_ok and score >= 50:
        eligibility_level = "partially_eligible"
        is_eligible = False  # Needs improvements but can start
    else:
        eligibility_level = "not_eligible"
        is_eligible = False

    # Add experience recommendation
    if not has_previous_public_sales and is_eligible:
        recommendations.append(
            "Considere participar de pequenas chamadas para ganhar experiência"
        )

    return {
        "is_eligible": is_eligible,
        "eligibility_level": eligibility_level,
        "score": min(100, max(0, score)),  # Ensure 0-100 range
        "requirements_met": requirements_met,
        "requirements_missing": requirements_missing,
        "recommendations": recommendations,
    }


def generate_formalization_tasks(diagnosis: dict[str, Any], responses: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Generate list of formalization tasks based on diagnosis.

    Args:
        diagnosis: Result from calculate_eligibility()
        responses: Original responses dictionary

    Returns:
        List of task dictionaries with:
        {
            "task_id": str,
            "title": str,
            "description": str,
            "category": str,  # "document", "registration", "preparation"
            "priority": str,  # "high", "medium", "low"
        }
    """
    tasks: list[dict[str, Any]] = []

    # High priority tasks (blocking requirements)
    for req in diagnosis["requirements_missing"]:
        if "CPF" in req:
            tasks.append(
                {
                    "task_id": "obtain_cpf",
                    "title": "Obter CPF",
                    "description": "Cadastre-se na Receita Federal para obter seu CPF",
                    "category": "document",
                    "priority": "high",
                }
            )
        elif "DAP" in req or "CAF" in req:
            tasks.append(
                {
                    "task_id": "obtain_dap_caf",
                    "title": "Obter DAP ou CAF",
                    "description": "Obtenha sua Declaração de Aptidão ao Pronaf na Emater ou órgão similar da sua região",
                    "category": "document",
                    "priority": "high",
                }
            )
        elif "CNPJ" in req:
            tasks.append(
                {
                    "task_id": "obtain_cnpj",
                    "title": "Registrar CNPJ",
                    "description": "Registre CNPJ para sua cooperativa ou associação na Receita Federal",
                    "category": "registration",
                    "priority": "high",
                }
            )

    # Medium priority tasks (important but not blocking)
    if "Conta bancária" in diagnosis["requirements_missing"]:
        tasks.append(
            {
                "task_id": "open_bank_account",
                "title": "Abrir conta bancária",
                "description": "Abra uma conta bancária para receber pagamentos dos programas públicos",
                "category": "preparation",
                "priority": "medium",
            }
        )

    if "Documentos organizados" in diagnosis["requirements_missing"]:
        tasks.append(
            {
                "task_id": "organize_documents",
                "title": "Organizar documentos",
                "description": "Organize e digitalize seus documentos: CPF, DAP/CAF, comprovante de endereço",
                "category": "preparation",
                "priority": "medium",
            }
        )

    # Low priority tasks (nice to have)
    if not responses.get("has_previous_public_sales", False):
        tasks.append(
            {
                "task_id": "learn_public_programs",
                "title": "Conhecer programas públicos",
                "description": "Pesquise sobre programas como PNAE e PAA para entender o processo",
                "category": "preparation",
                "priority": "low",
            }
        )

    return tasks
