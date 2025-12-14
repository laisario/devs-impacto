import { useState, useEffect } from 'react';
import type { ChecklistItem, Document, UserProfile, ViewState } from '../domain/models';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { LandingPage } from '../features/landing/LandingPage';
import { LoginPage } from '../features/auth/LoginPage';
import { OnboardingFlow } from '../features/onboarding/OnboardingFlow';
import { Dashboard } from '../features/dashboard/Dashboard';
import { EscalationPage } from '../features/escalation/EscalationPage';
import { getOnboardingStatus } from '../services/api/onboarding';
import { ApiClientError } from '../services/api/client';

function AppContent() {
  const { isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const [view, setView] = useState<ViewState>('landing');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(false);
  const [hasCheckedOnboarding, setHasCheckedOnboarding] = useState(false);

  const checkOnboardingAndRedirect = async () => {
    if (!isAuthenticated) {
      return;
    }

    setIsCheckingOnboarding(true);
    setHasCheckedOnboarding(true);
    try {
      const status = await getOnboardingStatus();
      console.log('Onboarding status:', status);
      
      // If onboarding is not completed, show onboarding flow
      if (status.status === 'not_started' || status.status === 'in_progress') {
        setView('onboarding');
      } else {
        // Onboarding completed, profile should be created automatically
        // Go directly to dashboard
        setView('dashboard');
      }
    } catch (err) {
      // If there's an error, show onboarding
      console.warn('Error checking onboarding status:', err);
      setView('onboarding');
    } finally {
      setIsCheckingOnboarding(false);
    }
  };

  // Handle authentication state changes
  useEffect(() => {
    // If authenticated and just logged in, check onboarding
    if (isAuthenticated && !authLoading && !hasCheckedOnboarding) {
      checkOnboardingAndRedirect();
    }
    // If not authenticated and not on landing/login, redirect
    else if (!isAuthenticated && !authLoading && view !== 'landing' && view !== 'login') {
      setView('landing');
      setHasCheckedOnboarding(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading, view]);

  const handleLogin = () => {
    // Reset the flag so onboarding check happens when auth state updates
    setHasCheckedOnboarding(false);
    // The useEffect will detect isAuthenticated change and redirect
  };

  const handleLogout = () => {
    logout();
    setUser(null);
    setChecklist([]);
    setDocuments([]);
    setView('landing');
  };

  if (authLoading || isCheckingOnboarding) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  if (view === 'landing') {
    return (
      <LandingPage
        onStart={() => {
          if (isAuthenticated) {
            setView('dashboard');
          } else {
            setView('login');
          }
        }}
        onConsult={() => setView('escalation')}
      />
    );
  }

  if (view === 'login') {
    return <LoginPage onLogin={handleLogin} onBack={() => setView('landing')} />;
  }

  if (view === 'onboarding') {
    return (
      <OnboardingFlow
        onFinish={() => {
          // Profile is created automatically after onboarding
          setView('dashboard');
        }}
        isLoading={false}
      />
    );
  }

  if (view === 'dashboard') {
    if (!isAuthenticated) {
      setView('login');
      return null;
    }
    return (
      <Dashboard
        user={user}
        checklist={checklist}
        documents={documents}
        setChecklist={setChecklist}
        setDocuments={setDocuments}
        onEscalate={() => setView('escalation')}
        onLogout={handleLogout}
      />
    );
  }

  if (view === 'escalation') {
    return <EscalationPage onBack={() => setView(isAuthenticated ? 'dashboard' : 'landing')} />;
  }

  return null;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
