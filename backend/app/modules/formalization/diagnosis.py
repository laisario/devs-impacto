"""
Formalization diagnosis logic (pure function).
Calculates eligibility for selling to public programs based on onboarding answers.
"""

from typing import Any

from app.modules.onboarding.schemas import OnboardingQuestion, QuestionType
from app.modules.formalization.producer_utils import (
    is_formal_producer,
    is_individual_producer,
)


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
    # Note: CPF is not checked here as it comes from login/auth
    has_dap_caf = responses.get("has_dap_caf", False)
    has_cnpj = responses.get("has_cnpj", False)
    producer_type_pref = responses.get("producer_type")
    has_previous_public_sales = responses.get("has_previous_sales", False)
    has_bank_account = responses.get("has_bank_account", False)
    has_address_proof = responses.get("has_address_proof", False)

    requirements_met: list[str] = []
    requirements_missing: list[str] = []
    recommendations: list[str] = []

    # Essential requirements (must have)
    # CPF is assumed to be present (from login), so we don't check it here
    if has_dap_caf:
        requirements_met.append("DAP ou CAF")
    else:
        requirements_missing.append("DAP ou CAF")
        recommendations.append(
            "Obtenha sua DAP (Declaração de Aptidão ao Pronaf) na Emater ou órgão similar"
        )

    # Type-specific requirements
    is_formal = is_formal_producer(producer_type_pref)
    if is_formal:
        if has_cnpj:
            requirements_met.append("CNPJ (para grupo formal)")
        else:
            requirements_missing.append("CNPJ (para grupo formal)")
            recommendations.append("Registre CNPJ para sua cooperativa ou associação")

    # Important but not blocking
    if has_bank_account:
        requirements_met.append("Conta bancária")
    else:
        requirements_missing.append("Conta bancária")
        recommendations.append("Abra uma conta bancária para receber pagamentos")

    if has_address_proof:
        requirements_met.append("Comprovante de endereço")
    else:
        requirements_missing.append("Comprovante de endereço")
        recommendations.append("Tenha um comprovante de endereço atualizado")

    # Calculate score (0-100)
    # Essential requirements: 50 points (DAP/CAF)
    # Type-specific: 20 points (CNPJ if formal)
    # Important: 20 points (bank account, address proof)
    # Nice to have: 10 points (experience)
    score = 0

    # CPF is assumed present (from login) - 30 points
    score += 30
    if has_dap_caf:
        score += 30
    if is_formal and has_cnpj:
        score += 20
    elif not is_formal:
        score += 20  # Not required for individual/informal

    if has_bank_account:
        score += 10
    if has_address_proof:
        score += 10
    if has_previous_public_sales:
        score += 5  # Bonus for experience

    # Determine eligibility level
    # Eligible: Has DAP/CAF (and CNPJ if formal) + at least 70 points
    # Partially eligible: Has essential docs but missing some requirements (50-69 points)
    # Not eligible: Missing essential docs (< 50 points)

    essential_ok = has_dap_caf and (not is_formal or has_cnpj)

    if essential_ok and score >= 70:
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


def map_onboarding_answers_to_requirements(
    answers: dict[str, Any],
    questions: dict[str, OnboardingQuestion],
) -> dict[str, bool]:
    """
    Mapeia respostas de onboarding para requirements.
    
    Args:
        answers: Dictionary mapping question_id to answer value
        questions: Dictionary mapping question_id to OnboardingQuestion
    
    Returns:
        Dict mapping requirement_id to bool (True = met, False = missing)
    """
    requirements_status: dict[str, bool] = {}
    
    for question_id, answer in answers.items():
        question = questions.get(question_id)
        if not question or not question.requirement_id:
            continue
            
        requirement_id = question.requirement_id
        
        # Lógica de matching baseada no tipo de pergunta
        if question.question_type == QuestionType.BOOLEAN:
            requirements_status[requirement_id] = bool(answer)
        elif question.question_type == QuestionType.CHOICE:
            # Para choice, considerar como metido se respondeu
            # Se allow_multiple, answer pode ser uma lista
            if question.allow_multiple:
                # Para multi-select, considerar metido se lista não está vazia
                if isinstance(answer, list):
                    requirements_status[requirement_id] = len(answer) > 0
                else:
                    requirements_status[requirement_id] = bool(answer)
            else:
                # Para single choice, considerar como metido se respondeu
                requirements_status[requirement_id] = bool(answer)
        elif question.question_type == QuestionType.TEXT:
            # Para text, considerar como metido se não está vazio
            requirements_status[requirement_id] = bool(str(answer).strip())
    
    return requirements_status


def generate_formalization_tasks(
    diagnosis: dict[str, Any],
    responses: dict[str, Any],
    questions: dict[str, OnboardingQuestion] | None = None,
) -> list[dict[str, Any]]:
    """
    Generate list of formalization tasks based on diagnosis AND onboarding answers.

    Note: CNPJ tasks are only generated for formal producers (cooperatives/associations).

    Args:
        diagnosis: Result from calculate_eligibility()
        responses: Original responses dictionary
        questions: Dictionary mapping question_id to OnboardingQuestion (optional)

    Returns:
        List of task dictionaries with:
        {
            "task_id": str,
            "title": str,
            "description": str,
            "category": str,  # "document", "registration", "preparation"
            "priority": str,  # "high", "medium", "low"
            "requirement_id": str,  # ID do requirement associado
        }
    """
    tasks: list[dict[str, Any]] = []
    
    # Determine producer type from responses or profile
    producer_type_pref = responses.get("producer_type") if responses else None
    # Check if producer is individual - if so, NEVER show CNPJ task
    is_individual = is_individual_producer(producer_type_pref)
    is_formal = is_formal_producer(producer_type_pref)
    
    # Mapear requirement_id para tasks (comum para ambos os caminhos)
    requirement_to_task = {
        "dap_caf": {
            "task_id": "obtain_dap_caf",
            "title": "Obter DAP ou CAF",
            "description": "Obtenha sua Declaração de Aptidão ao Pronaf na Emater ou órgão similar da sua região",
            "category": "document",
            "priority": "high",
        },
        "cnpj": {
            "task_id": "obtain_cnpj",
            "title": "Registrar CNPJ",
            "description": "Registre CNPJ para sua cooperativa ou associação na Receita Federal",
            "category": "registration",
            "priority": "high",
        },
        "proof_address": {
            "task_id": "obtain_address_proof",
            "title": "Obter comprovante de endereço",
            "description": "Tenha um comprovante de endereço atualizado",
            "category": "document",
            "priority": "medium",
        },
        "bank_statement": {
            "task_id": "open_bank_account",
            "title": "Abrir conta bancária",
            "description": "Abra uma conta bancária para receber pagamentos dos programas públicos",
            "category": "preparation",
            "priority": "medium",
        },
    }
    
    # Se temos questions, fazer matching direto baseado em requirement_id
    if questions and len(questions) > 0:
        requirements_status = map_onboarding_answers_to_requirements(responses, questions)
        
        # Se não há respostas ou requirements_status está vazio, usar diagnosis como fallback
        # requirements_status pode estar vazio se não há respostas ou se não há questions com requirement_id
        if len(responses) == 0 or len(requirements_status) == 0:
            # Fallback: usar diagnosis para determinar o que está faltando
            for req in diagnosis["requirements_missing"]:
                if "DAP" in req or "CAF" in req:
                    if "dap_caf" in requirement_to_task:
                        task_data = requirement_to_task["dap_caf"].copy()
                        task_data["requirement_id"] = "dap_caf"
                        tasks.append(task_data)
                elif "CNPJ" in req:
                    # Only generate CNPJ task for formal producers
                    if is_formal and "cnpj" in requirement_to_task:
                        task_data = requirement_to_task["cnpj"].copy()
                        task_data["requirement_id"] = "cnpj"
                        tasks.append(task_data)
                elif "Conta bancária" in req:
                    if "bank_statement" in requirement_to_task:
                        task_data = requirement_to_task["bank_statement"].copy()
                        task_data["requirement_id"] = "bank_statement"
                        tasks.append(task_data)
                elif "Comprovante de endereço" in req:
                    if "proof_address" in requirement_to_task:
                        task_data = requirement_to_task["proof_address"].copy()
                        task_data["requirement_id"] = "proof_address"
                        tasks.append(task_data)
        else:
            # Usar mapeamento normal quando há respostas
            for requirement_id, is_met in requirements_status.items():
                # NUNCA gerar tarefa de CNPJ para produtores individuais
                if requirement_id == "cnpj" and not is_formal:
                    continue  # Skip CNPJ task for individual/informal producers
                
                if not is_met and requirement_id in requirement_to_task:
                    task_data = requirement_to_task[requirement_id].copy()
                    task_data["requirement_id"] = requirement_id
                    tasks.append(task_data)
    
    # Fallback para lógica antiga se não tiver questions (compatibilidade)
    else:
        # Determine producer type for fallback logic
        producer_type_pref = responses.get("producer_type") if responses else None
        is_formal = is_formal_producer(producer_type_pref)
        is_individual = is_individual_producer(producer_type_pref)
        
        # High priority tasks (blocking requirements)
        for req in diagnosis["requirements_missing"]:
            if "DAP" in req or "CAF" in req:
                tasks.append(
                    {
                        "task_id": "obtain_dap_caf",
                        "title": "Obter DAP ou CAF",
                        "description": "Obtenha sua Declaração de Aptidão ao Pronaf na Emater ou órgão similar da sua região",
                        "category": "document",
                        "priority": "high",
                        "requirement_id": "dap_caf",
                    }
                )
            elif "CNPJ" in req:
                # Only generate CNPJ task for formal producers (NEVER for individual)
                if is_formal and not is_individual:
                    tasks.append(
                        {
                            "task_id": "obtain_cnpj",
                            "title": "Registrar CNPJ",
                            "description": "Registre CNPJ para sua cooperativa ou associação na Receita Federal",
                            "category": "registration",
                            "priority": "high",
                            "requirement_id": "cnpj",
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
                    "requirement_id": "bank_statement",
                }
            )

        if "Comprovante de endereço" in diagnosis["requirements_missing"]:
            tasks.append(
                {
                    "task_id": "obtain_address_proof",
                    "title": "Obter comprovante de endereço",
                    "description": "Tenha um comprovante de endereço atualizado",
                    "category": "document",
                    "priority": "medium",
                    "requirement_id": "proof_address",
                }
            )

    # Removed "learn_public_programs" task - not useful, simplifies the checklist

    return tasks
