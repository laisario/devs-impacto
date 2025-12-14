"""
Formalization rules module.
Pure functions to compute required tasks based on producer profile.
"""

from typing import Any


def compute_required_tasks(producer_profile: dict[str, Any]) -> list[str]:
    """
    Calcula quais tasks são necessárias baseado no perfil do produtor.
    
    Esta é uma função pura - não tem efeitos colaterais, apenas calcula
    quais task_codes devem ser ativados baseado nas flags do producer_profile.
    
    Regras:
    - has_cpf == False → HAS_CPF
    - has_family_farmer_registration == False → HAS_FAMILY_FARMER_REGISTRATION
    - has_bank_account == False → HAS_BANK_ACCOUNT
    - wants_to_sell_to_school == True → SALES_PROJECT_READY, PUBLIC_CALL_SUBMISSION_READY
    - PRODUCTION_IS_ELIGIBLE só aparece se houver conflito (processados não aceitos)
    
    Args:
        producer_profile: Dicionário com dados do producer_profile do MongoDB
        
    Returns:
        Lista de task_codes que devem ser ativados para este usuário
    """
    required_tasks: list[str] = []
    
    # Extrair flags com valores padrão
    has_cpf = producer_profile.get("has_cpf", True)  # CPF geralmente vem do auth
    has_family_farmer_registration = producer_profile.get("has_family_farmer_registration", False)
    has_dap_caf = producer_profile.get("has_dap_caf", False)
    has_bank_account = producer_profile.get("has_bank_account", False)
    wants_to_sell_to_school = producer_profile.get("wants_to_sell_to_school", False)
    
    # Usar has_dap_caf como fallback se has_family_farmer_registration não existir
    if not has_family_farmer_registration:
        has_family_farmer_registration = has_dap_caf
    
    # Regra 1: CPF obrigatório
    if not has_cpf:
        required_tasks.append("HAS_CPF")
    
    # Regra 2: DAP/CAF obrigatória
    if not has_family_farmer_registration:
        required_tasks.append("HAS_FAMILY_FARMER_REGISTRATION")
    
    # Regra 3: Conta bancária obrigatória
    if not has_bank_account:
        required_tasks.append("HAS_BANK_ACCOUNT")
    
    # Regra 3.5: Comprovante de endereço (importante mas não bloqueante)
    has_address_proof = producer_profile.get("has_address_proof", False)
    if not has_address_proof:
        required_tasks.append("HAS_ADDRESS_PROOF")
    
    # Regra 4: Se quer vender para escolas, precisa preparar projeto e estar pronto para submeter
    if wants_to_sell_to_school:
        required_tasks.append("SALES_PROJECT_READY")
        required_tasks.append("PUBLIC_CALL_SUBMISSION_READY")
    
    # Regra 5: PRODUCTION_IS_ELIGIBLE só aparece se houver conflito
    # Por enquanto, não implementamos detecção de conflito de produção
    # Esta task seria ativada por lógica mais complexa (ex: produtos processados não aceitos)
    # Deixamos comentado para implementação futura:
    # if production_conflict:
    #     required_tasks.append("PRODUCTION_IS_ELIGIBLE")
    
    return required_tasks
