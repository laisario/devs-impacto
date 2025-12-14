import { useState } from 'react';
import type { ChecklistItem, Document, UserProfile, ViewState } from '../domain/models';
import { LandingPage } from '../features/landing/LandingPage';
import { OnboardingFlow } from '../features/onboarding/OnboardingFlow';
import { Dashboard } from '../features/dashboard/Dashboard';
import { EscalationPage } from '../features/escalation/EscalationPage';
import { generatePlan } from '../features/plan/generatePlan';

export default function App() {
  const [view, setView] = useState<ViewState>('landing');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);

  const handleGeneratePlan = (answers: Record<string, string>) => {
    setLoading(true);

    window.setTimeout(() => {
      const plan = generatePlan(answers);
      setUser(plan.user);
      setChecklist(plan.checklist);
      setDocuments(plan.documents);
      setLoading(false);
      setView('dashboard');
    }, 1500);
  };

  if (view === 'landing') {
    return <LandingPage onStart={() => setView('onboarding')} onConsult={() => setView('escalation')} />;
  }

  if (view === 'onboarding') {
    return <OnboardingFlow onFinish={handleGeneratePlan} isLoading={loading} />;
  }

  if (view === 'dashboard' && user) {
    return (
      <Dashboard
        user={user}
        checklist={checklist}
        documents={documents}
        setChecklist={setChecklist}
        setDocuments={setDocuments}
        onEscalate={() => setView('escalation')}
        onLogout={() => {
          setUser(null);
          setChecklist([]);
          setDocuments([]);
          setView('landing');
        }}
      />
    );
  }

  if (view === 'escalation') {
    return <EscalationPage onBack={() => setView(user ? 'dashboard' : 'landing')} />;
  }

  return null;
}
