/**
 * Producer Profile Form component
 */

import { useState, useEffect } from 'react';
import { Save, User, MapPin, Building2, FileText, CreditCard } from 'lucide-react';
import { getProducerProfile, createOrUpdateProducerProfile } from '../../services/api/producer';
import { ApiClientError } from '../../services/api/client';
import type { ProducerProfileCreate, ProducerType, Member } from '../../services/api/types';

interface ProducerProfileFormProps {
  onSave?: () => void;
  onCancel?: () => void;
}

export function ProducerProfileForm({ onSave, onCancel }: ProducerProfileFormProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<ProducerProfileCreate>({
    producer_type: 'individual',
    name: '',
    address: '',
    city: '',
    state: '',
    dap_caf_number: '',
    cpf: '',
    bank_name: '',
    bank_agency: '',
    bank_account: '',
  });
  const [members, setMembers] = useState<Member[]>([]);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profile = await getProducerProfile();
        if (profile) {
          setFormData({
            producer_type: profile.producer_type,
            name: profile.name,
            address: profile.address,
            city: profile.city,
            state: profile.state,
            dap_caf_number: profile.dap_caf_number,
            cnpj: profile.cnpj || undefined,
            cpf: profile.cpf || undefined,
            members: profile.members || undefined,
            bank_name: profile.bank_name || undefined,
            bank_agency: profile.bank_agency || undefined,
            bank_account: profile.bank_account || undefined,
          });
          if (profile.members) {
            setMembers(profile.members);
          }
        }
      } catch (err) {
        console.warn('Could not load profile:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSaving(true);

    try {
      const submitData: ProducerProfileCreate = {
        ...formData,
        members: formData.producer_type === 'informal' ? members : undefined,
      };

      await createOrUpdateProducerProfile(submitData);
      if (onSave) onSave();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao salvar perfil. Verifique os dados e tente novamente.');
      } else {
        setError('Erro ao salvar perfil. Tente novamente.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const addMember = () => {
    setMembers([...members, { name: '', cpf: '', dap_caf_number: '' }]);
  };

  const updateMember = (index: number, field: keyof Member, value: string) => {
    const updated = [...members];
    updated[index] = { ...updated[index], [field]: value };
    setMembers(updated);
  };

  const removeMember = (index: number) => {
    setMembers(members.filter((_, i) => i !== index));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8 border border-slate-200">
          <h1 className="text-2xl font-bold text-slate-800 mb-6">Perfil do Produtor</h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Producer Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Tipo de Produtor *
              </label>
              <select
                value={formData.producer_type}
                onChange={(e) => setFormData({ ...formData, producer_type: e.target.value as ProducerType })}
                className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              >
                <option value="individual">Individual</option>
                <option value="informal">Grupo Informal</option>
                <option value="formal">Cooperativa/Associação (Formal)</option>
              </select>
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <User className="h-4 w-4" />
                Nome/Razão Social *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>

            {/* Address */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Endereço *
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* City */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Cidade *</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>

              {/* State */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Estado (UF) *</label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value.toUpperCase().slice(0, 2) })}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  maxLength={2}
                  required
                />
              </div>
            </div>

            {/* DAP/CAF */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Número DAP/CAF *
              </label>
              <input
                type="text"
                value={formData.dap_caf_number}
                onChange={(e) => setFormData({ ...formData, dap_caf_number: e.target.value })}
                className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>

            {/* CNPJ (for formal) */}
            {formData.producer_type === 'formal' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  CNPJ * (apenas números)
                </label>
                <input
                  type="text"
                  value={formData.cnpj || ''}
                  onChange={(e) => setFormData({ ...formData, cnpj: e.target.value.replace(/\D/g, '').slice(0, 14) })}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  maxLength={14}
                  required
                />
              </div>
            )}

            {/* CPF (for individual/informal) */}
            {(formData.producer_type === 'individual' || formData.producer_type === 'informal') && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">CPF * (apenas números)</label>
                <input
                  type="text"
                  value={formData.cpf || ''}
                  onChange={(e) => setFormData({ ...formData, cpf: e.target.value.replace(/\D/g, '').slice(0, 11) })}
                  className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  maxLength={11}
                  required
                />
              </div>
            )}

            {/* Members (for informal) */}
            {formData.producer_type === 'informal' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Membros do Grupo *</label>
                {members.map((member, index) => (
                  <div key={index} className="mb-4 p-4 border border-slate-200 rounded-lg">
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-sm font-medium text-slate-600">Membro {index + 1}</span>
                      {members.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeMember(index)}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Remover
                        </button>
                      )}
                    </div>
                    <div className="space-y-3">
                      <input
                        type="text"
                        placeholder="Nome completo"
                        value={member.name}
                        onChange={(e) => updateMember(index, 'name', e.target.value)}
                        className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        required
                      />
                      <input
                        type="text"
                        placeholder="CPF (apenas números)"
                        value={member.cpf}
                        onChange={(e) => updateMember(index, 'cpf', e.target.value.replace(/\D/g, '').slice(0, 11))}
                        className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        maxLength={11}
                        required
                      />
                      <input
                        type="text"
                        placeholder="DAP/CAF (opcional)"
                        value={member.dap_caf_number || ''}
                        onChange={(e) => updateMember(index, 'dap_caf_number', e.target.value)}
                        className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMember}
                  className="text-sm text-green-600 hover:text-green-700 font-medium"
                >
                  + Adicionar Membro
                </button>
                {members.length < 2 && (
                  <p className="text-xs text-slate-500 mt-2">Grupo informal deve ter pelo menos 2 membros</p>
                )}
              </div>
            )}

            {/* Bank Info */}
            <div className="border-t border-slate-200 pt-6">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Dados Bancários (opcional)
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Banco</label>
                  <input
                    type="text"
                    value={formData.bank_name || ''}
                    onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Agência</label>
                  <input
                    type="text"
                    value={formData.bank_agency || ''}
                    onChange={(e) => setFormData({ ...formData, bank_agency: e.target.value })}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Conta</label>
                  <input
                    type="text"
                    value={formData.bank_account || ''}
                    onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-6 border-t border-slate-200">
              {onCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  className="flex-1 px-6 py-3 border border-slate-300 rounded-lg text-slate-700 font-medium hover:bg-slate-50 transition"
                >
                  Cancelar
                </button>
              )}
              <button
                type="submit"
                disabled={isSaving}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Salvando...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-5 w-5" />
                    <span>Salvar Perfil</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
