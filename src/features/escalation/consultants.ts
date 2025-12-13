export interface Consultant {
  id: number;
  name: string;
  role: string;
  region: string;
  specialty: string;
  price: string;
}

export const MOCK_CONSULTANTS: Consultant[] = [
  {
    id: 1,
    name: 'Ana Silva',
    role: 'Eng. de Alimentos',
    region: 'Sul',
    specialty: 'Processamento e Rotulagem',
    price: '$$',
  },
  {
    id: 2,
    name: 'Carlos Rural',
    role: 'Técnico Agrícola',
    region: 'Nordeste',
    specialty: 'CAF e DAP',
    price: '$',
  },
  {
    id: 3,
    name: 'Regulariza Agro',
    role: 'Consultoria',
    region: 'Sudeste',
    specialty: 'MAPA e SIF',
    price: '$$$',
  },
];
