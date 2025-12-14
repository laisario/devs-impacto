import type { ChecklistItem, Document, UserProfile, ProducerType } from '../../domain/models';

export interface PlanResult {
  user: UserProfile;
  checklist: ChecklistItem[];
  documents: Document[];
}

export function generatePlan(answers: Record<string, string>): PlanResult {
  const riskFlags: string[] = [];
  let caseType: UserProfile['caseType'] = 'in_natura';

  if (answers.processa_alimento?.includes('Sim') || answers.tipo_alimento?.includes('Processados')) {
    riskFlags.push('Processamento Detectado');
    caseType = 'needs_human';
  }
  if (answers.tipo_alimento?.includes('Animal')) {
    riskFlags.push('Origem Animal');
    caseType = 'needs_human';
  }

  const documents: Document[] = [
    { id: 'd1', type: 'cpf', name: 'RG/CPF', status: 'missing' },
    {
      id: 'd2',
      type: 'dap_caf',
      name: 'CAF/DAP',
      status: answers.documentacao_base === 'Tenho ativa' ? 'uploaded' : 'missing',
    },
    { id: 'd3', type: 'proof_address', name: 'Comprovante Residência', status: 'missing' },
    { id: 'd4', type: 'other', name: 'Nota Fiscal de Produtor (Exemplo)', status: 'missing' },
  ];

  const checklist: ChecklistItem[] = [
    {
      id: '1',
      title: 'Regularizar Documentos Pessoais',
      description: 'RG, CPF do produtor e cônjuge.',
      priority: 'medium',
      status: 'done',
      detailedSteps: [
        { text: 'Verifique se o RG tem menos de 10 anos de emissão.' },
        { text: 'Certifique-se de que o CPF está regular na Receita Federal.' },
        { text: 'Digitalize ou tire foto frente e verso.' },
      ],
      relatedDocId: 'd1',
    },
  ];

  if (answers.documentacao_base !== 'Tenho ativa') {
    checklist.push({
      id: '2',
      title: 'Obter ou Renovar CAF/DAP',
      description: 'Documento essencial para agricultura familiar.',
      priority: 'high',
      status: 'todo',
      detailedSteps: [
        {
          text: 'Procure o sindicato rural ou escritório da Emater/Epagri do seu município.',
          helpContent: {
            type: 'tip',
            title: 'Como encontrar?',
            description:
              'Busque na internet por "Sindicato Rural" ou "Emater" seguido do nome da sua cidade. Geralmente ficam próximos à Secretaria de Agricultura.',
          },
        },
        { text: 'Leve RG, CPF e documentos da terra (Escritura, Contrato de Arrendamento ou Comodato).' },
        { text: 'Agende uma visita técnica do extensionista na sua propriedade.' },
        { text: 'Após a visita, o documento será emitido e deve ser assinado.' },
      ],
      relatedDocId: 'd2',
    });
  }

  checklist.push({
    id: '3',
    title: 'Habilitar Nota Fiscal de Produtor',
    description: 'Necessário para receber pagamentos oficiais.',
    priority: 'high',
    status: 'todo',
    detailedSteps: [
      { text: 'Vá ao setor de tributos da Prefeitura Municipal.' },
      { text: 'Solicite o cadastro de Produtor Rural (leve a CAF/DAP e documentos da terra).' },
      {
        text: 'Peça o talão de notas físicas ou acesso ao sistema de Nota Fiscal Eletrônica (NFP-e).',
        helpContent: {
          type: 'tip',
          title: 'Sobre o Formulário',
          description:
            'Você deverá preencher o "Formulário de Inscrição Cadastral" (FAC). Ele solicita dados pessoais, documentos da terra e qual será sua atividade principal (ex: Agricultura).',
        },
      },
      {
        text: 'Faça uma nota de teste (simbólica) para aprender o preenchimento.',
        helpContent: {
          type: 'tip',
          title: 'Dica de Preenchimento',
          description:
            'Atenção aos campos: "Valor Unitário" (preço por kg ou unidade) e "Quantidade". A descrição deve ser exata conforme o produto (ex: Alface Crespa - Maço).',
        },
      },
    ],
    relatedDocId: 'd4',
  });

  if (answers.publico_alvo?.includes('Pública') || answers.publico_alvo?.includes('Ambas')) {
    checklist.push({
      id: '4',
      title: 'Cadastro de Fornecedor na Prefeitura',
      description: 'Ir à secretaria de educação ou agricultura.',
      priority: 'medium',
      status: 'todo',
      detailedSteps: [
        {
          text: 'Localize o setor de compras ou a Secretaria de Educação.',
          helpContent: {
            type: 'tip',
            title: 'Dica de Localização',
            description: 'Pergunte na recepção da prefeitura pelo "Setor de Licitações" ou "Comissão de Compras do PNAE".',
          },
        },
        { text: 'Preencha a ficha de cadastro de fornecedor.' },
        { text: 'Entregue cópias da CAF/DAP, RG, CPF e Projeto de Venda (quando houver chamada).' },
      ],
    });

    checklist.push({
      id: '5',
      title: 'Mapear Chamadas Públicas',
      description: 'Ficar atento aos editais do PNAE.',
      priority: 'medium',
      status: 'todo',
      detailedSteps: [
        { text: 'Acesse o site da prefeitura semanalmente na área de "Licitações" ou "Chamadas Públicas".' },
        { text: 'Entre em contato com nutricionistas da rede municipal.' },
        { text: 'Verifique os produtos solicitados no edital e veja se você tem produção suficiente.' },
      ],
    });
  }

  if (caseType === 'needs_human') {
    checklist.unshift({
      id: '0',
      title: 'Consultoria Sanitária',
      description: 'Seu caso exige aprovação da Vigilância ou MAPA.',
      priority: 'high',
      status: 'todo',
      detailedSteps: [
        {
          text: 'Identifique se seu produto precisa de SIM (Municipal), SIE (Estadual) ou SIF (Federal).',
          helpContent: {
            type: 'tip',
            title: 'Qual selo eu preciso?',
            description:
              'SIM: Venda apenas no seu município. SIE: Venda em todo o estado. SIF: Venda no Brasil todo. Produtos animais sempre exigem um destes.',
          },
        },
        { text: 'Contrate um Responsável Técnico (RT) se exigido.' },
        { text: 'Adeque a estrutura física (cozinha, área de processamento) conforme normas.' },
      ],
    });
  }

  // Map answer to ProducerType
  const getProducerType = (tipo: string | undefined): ProducerType => {
    if (tipo?.includes('Individual') || tipo?.includes('Pessoa Física')) return 'individual';
    if (tipo?.includes('Cooperativa') || tipo?.includes('Associação')) return 'formal';
    return 'individual'; // Default
  };

  const user: UserProfile = {
    name: answers.name ?? '',
    producerType: getProducerType(answers.tipo_alimento),
    city: answers.municipio ?? '',
    answers,
    riskFlags,
    caseType,
  };

  return { user, checklist, documents };
}
