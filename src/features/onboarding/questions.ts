import type { OnboardingQuestion } from '../../domain/models';

export const ONBOARDING_QUESTIONS: OnboardingQuestion[] = [
  {
    key: 'name',
    text: 'Olá! Vamos começar. Qual é o seu nome completo?',
    type: 'text',
    placeholder: 'Ex: João da Silva',
  },
  {
    key: 'tipo_alimento',
    text: 'Prazer! O que você produz principalmente?',
    type: 'choice',
    options: ['Frutas', 'Verduras/Legumes', 'Processados (Geleias, Conservas)', 'Origem Animal (Mel, Ovos, Queijo)'],
  },
  {
    key: 'processa_alimento',
    text: 'Você processa o alimento (corta, cozinha, embala a vácuo) antes de vender?',
    type: 'choice',
    options: ['Não, vendo in natura (como colhido)', 'Sim, faço algum processamento'],
  },
  {
    key: 'publico_alvo',
    text: 'Para quem você pretende vender?',
    type: 'choice',
    options: ['Escola Pública (PNAE)', 'Mercados/Escolas Privadas', 'Ambas'],
  },
  {
    key: 'documentacao_base',
    text: 'Como está sua documentação básica (CAF/DAP)?',
    type: 'choice',
    options: ['Tenho ativa', 'Não tenho', 'Preciso renovar'],
  },
  {
    key: 'municipio',
    text: 'Qual seu município e estado?',
    type: 'text',
    placeholder: 'Ex: Bauru - SP',
  },
];
