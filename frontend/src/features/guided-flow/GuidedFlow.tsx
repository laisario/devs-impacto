import { useState, useEffect } from 'react';
import { OnboardingScreen } from './OnboardingScreen';
import { OnboardingCompleteScreen } from './OnboardingCompleteScreen';
import { TaskListScreen } from './TaskListScreen';
import { TaskDetailScreen } from './TaskDetailScreen';
import { DocumentUploadScreen } from './DocumentUploadScreen';
import { TaskCompleteScreen } from './TaskCompleteScreen';
import { EligibilityScreen } from './EligibilityScreen';
import { SalesProjectScreen } from './SalesProjectScreen';
import { AllCompleteScreen } from './AllCompleteScreen';
import { SimpleChat } from '../shared/SimpleChat';
import { OfflineBanner } from '../shared/OfflineDetector';
import { getFormalizationTasks, getFormalizationStatus, updateTaskStatus } from '../../services/api/formalization';
import { getOnboardingStatus } from '../../services/api/onboarding';
import { ApiClientError } from '../../services/api/client';
import type { ChecklistItem } from '../../domain/models';
import type { FormalizationTaskUserResponse } from '../../services/api/types';

type FlowScreen =
  | 'welcome'
  | 'onboarding'
  | 'onboarding-complete'
  | 'task-list'
  | 'task-detail'
  | 'document-upload'
  | 'task-complete'
  | 'eligibility'
  | 'sales-project'
  | 'all-complete';

interface GuidedFlowProps {
  user: { name?: string } | null;
  onLogout?: () => void;
}

export function GuidedFlow({ user, onLogout }: GuidedFlowProps) {
  const [currentScreen, setCurrentScreen] = useState<FlowScreen | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
  const [error, setError] = useState('');
  const [eligibilityStatus, setEligibilityStatus] = useState<{
    isEligible: boolean;
    eligibilityLevel: string;
    score: number;
  } | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isCompletingTask, setIsCompletingTask] = useState(false);

  // Map backend task to frontend checklist item
  const mapTaskToChecklistItem = (task: FormalizationTaskUserResponse): ChecklistItem => ({
    id: task.id,
    title: task.title,
    description: task.description,
    priority: task.blocking ? 'high' : 'medium',
    status: task.status === 'done' ? 'done' : task.status === 'skipped' ? 'todo' : 'todo',
    taskId: task.task_code,
    category: 'document',
    requirementId: task.requirement_id || undefined,
    needUpload: false,
  });

  const loadTasks = async (retry = false) => {
    if (!retry) setError('');

    try {
      const tasks = await getFormalizationTasks();
      const mappedTasks = tasks.map(mapTaskToChecklistItem);
      const uniqueTasks = mappedTasks.map((task, index) => ({
        ...task,
        id: task.id || `task-${index}-${Date.now()}`,
      }));
      setChecklist(uniqueTasks);
      setError('');
    } catch (err) {
      if (err instanceof ApiClientError) {
        const errorMsg = err.message || 'Erro ao carregar tarefas.';
        if (!navigator.onLine) {
          setError('Sem conexão com a internet. Verifique sua conexão e tente novamente.');
        } else {
          setError(`${errorMsg} Tente novamente.`);
        }
      } else {
        if (!navigator.onLine) {
          setError('Sem conexão com a internet. Verifique sua conexão e tente novamente.');
        } else {
          setError('Erro ao carregar tarefas. Tente novamente.');
        }
      }
    }
  };

  const checkOnboarding = async () => {
    setIsInitializing(true);
    try {
      const status = await getOnboardingStatus();
      if (status.status === 'completed') {
        await loadTasks();
        // Load eligibility status for the progress bar
        try {
          const eligibility = await getFormalizationStatus();
          setEligibilityStatus({
            isEligible: eligibility.is_eligible,
            eligibilityLevel: eligibility.eligibility_level,
            score: eligibility.score,
          });
        } catch (err) {
          console.warn('Error loading eligibility status:', err);
        }
        setCurrentScreen('task-list');
      } else {
        setCurrentScreen('onboarding');
      }
    } catch (err) {
      console.warn('Error checking onboarding:', err);
      setCurrentScreen('onboarding');
    } finally {
      setIsInitializing(false);
    }
  };

  // Initialize on mount - only run once
  useEffect(() => {
    if (!currentScreen) {
      checkOnboarding();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleOnboardingComplete = async () => {
    await loadTasks();
    // After loading, the checklist will be updated, so we check in the render
    setCurrentScreen('onboarding-complete');
  };

  const handleOnboardingCompleteContinue = async () => {
    // Refresh eligibility status when going to task list
    try {
      const status = await getFormalizationStatus();
      setEligibilityStatus({
        isEligible: status.is_eligible,
        eligibilityLevel: status.eligibility_level,
        score: status.score,
      });
    } catch (err) {
      console.warn('Error loading eligibility status:', err);
    }
    setCurrentScreen('task-list');
  };

  const handleStartFirstTask = () => {
    const pendingTasks = checklist.filter((t) => t.status !== 'done');
    if (pendingTasks.length > 0) {
      const firstPendingIndex = checklist.findIndex((t) => t.id === pendingTasks[0].id);
      setCurrentTaskIndex(firstPendingIndex);
      setCurrentScreen('task-detail');
    }
  };

  const handleTaskComplete = async (taskId: string) => {
    const task = checklist.find((t) => t.id === taskId);
    if (!task || !task.taskId) return;

    setIsCompletingTask(true);
    try {
      await updateTaskStatus(task.taskId, 'done');
      const updatedChecklist = checklist.map((t) => 
        (t.id === taskId ? { ...t, status: 'done' as const } : t)
      );
      setChecklist(updatedChecklist);

      // Always update eligibility status to refresh progress bar and score
      try {
        const status = await getFormalizationStatus();
        const updatedStatus = {
          isEligible: status.is_eligible,
          eligibilityLevel: status.eligibility_level,
          score: status.score,
        };
        setEligibilityStatus(updatedStatus);

        // Check if all tasks are done
        const allDone = updatedChecklist.every((t) => t.status === 'done');
        if (allDone && updatedStatus.isEligible) {
          // All tasks done and eligible - go directly to celebration
          setCurrentScreen('all-complete');
          return;
        }
      } catch (err) {
        console.warn('Error updating eligibility status:', err);
      }

      setCurrentScreen('task-complete');
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao marcar tarefa. Tente novamente.');
      } else {
        setError('Erro ao marcar tarefa. Tente novamente.');
      }
    } finally {
      setIsCompletingTask(false);
    }
  };

  const handleNextTask = async () => {
    const pendingTasks = checklist.filter((t) => t.status !== 'done');
    if (pendingTasks.length > 0) {
      const nextTask = pendingTasks[0];
      const nextIndex = checklist.findIndex((t) => t.id === nextTask.id);
      setCurrentTaskIndex(nextIndex);
      setCurrentScreen('task-detail');
    } else {
      // All tasks completed - refresh eligibility and show celebration
      await checkEligibility();
      if (eligibilityStatus && eligibilityStatus.isEligible) {
        setCurrentScreen('all-complete');
      } else {
        setCurrentScreen('eligibility');
      }
    }
  };

  const handleViewResult = async () => {
    await checkEligibility();
    if (eligibilityStatus && eligibilityStatus.isEligible) {
      setCurrentScreen('all-complete');
    } else {
      setCurrentScreen('eligibility');
    }
  };

  const checkEligibility = async () => {
    try {
      // Force recalculation by calling status endpoint
      // The backend will recalculate based on updated onboarding answers
      const status = await getFormalizationStatus();
      const updatedStatus = {
        isEligible: status.is_eligible,
        eligibilityLevel: status.eligibility_level,
        score: status.score,
      };
      setEligibilityStatus(updatedStatus);
      
      // If all tasks are done and eligible, go to celebration screen
      const allTasksDone = checklist.every((t) => t.status === 'done');
      if (allTasksDone && updatedStatus.isEligible) {
        setCurrentScreen('all-complete');
      } else {
        setCurrentScreen('eligibility');
      }
    } catch (err) {
      console.warn('Error checking eligibility:', err);
      // Default to not eligible if error
      setEligibilityStatus({
        isEligible: false,
        eligibilityLevel: 'not_eligible',
        score: 0,
      });
      setCurrentScreen('eligibility');
    }
  };

  const handleUploadDocument = () => {
    setCurrentScreen('document-upload');
  };

  const handleDocumentUploadComplete = async () => {
    const currentTask = checklist[currentTaskIndex];
    if (currentTask) {
      await handleTaskComplete(currentTask.id);
    }
  };

  const refreshEligibilityAndGoToTaskList = async () => {
    try {
      const status = await getFormalizationStatus();
      setEligibilityStatus({
        isEligible: status.is_eligible,
        eligibilityLevel: status.eligibility_level,
        score: status.score,
      });
    } catch (err) {
      console.warn('Error loading eligibility status:', err);
    }
    setCurrentScreen('task-list');
  };

  const currentTask = checklist[currentTaskIndex];
  const completedCount = checklist.filter((t) => t.status === 'done').length;
  const totalCount = checklist.length;

  if (isInitializing || !currentScreen) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <OfflineBanner />

      {/* Global header for task-list screen */}
      {currentScreen === 'task-list' && onLogout && (
        <header className="bg-white shadow-sm sticky top-0 z-50 w-full">
          <nav className="py-2 px-6 flex justify-end items-center max-w-6xl mx-auto w-full h-12">
            <button onClick={onLogout} className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors">
              Sair
            </button>
          </nav>
        </header>
      )}

      {currentScreen === 'onboarding' && (
        <OnboardingScreen
          onComplete={handleOnboardingComplete}
        />
      )}

      {currentScreen === 'onboarding-complete' && (
        <OnboardingCompleteScreen
          taskCount={checklist.length || 0}
          onContinue={handleOnboardingCompleteContinue}
        />
      )}

      {currentScreen === 'task-list' && (
        <>
          {error && (
            <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-40 max-w-lg w-full mx-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-700 text-sm mb-2">{error}</p>
                <button
                  onClick={() => loadTasks(true)}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700"
                >
                  Tentar novamente
                </button>
              </div>
            </div>
          )}
          <TaskListScreen
            tasks={checklist}
            onStartFirstTask={handleStartFirstTask}
            onViewResult={async () => {
              await checkEligibility();
              if (eligibilityStatus && eligibilityStatus.isEligible) {
                setCurrentScreen('all-complete');
              } else {
                setCurrentScreen('eligibility');
              }
            }}
            onTaskClick={(taskId) => {
              const taskIndex = checklist.findIndex((t) => t.id === taskId);
              if (taskIndex >= 0) {
                setCurrentTaskIndex(taskIndex);
                setCurrentScreen('task-detail');
              }
            }}
            score={eligibilityStatus?.score || 0}
            eligibilityLevel={eligibilityStatus?.eligibilityLevel as 'eligible' | 'partially_eligible' | 'not_eligible' || 'not_eligible'}
          />
        </>
      )}

      {currentScreen === 'task-detail' && currentTask && (
        <TaskDetailScreen
          task={currentTask}
          taskNumber={currentTaskIndex + 1}
          totalTasks={totalCount}
          onUploadDocument={handleUploadDocument}
          onMarkComplete={() => handleTaskComplete(currentTask.id)}
          onBack={refreshEligibilityAndGoToTaskList}
          isCompleting={isCompletingTask}
        />
      )}

      {currentScreen === 'document-upload' && currentTask && (
        <DocumentUploadScreen
          taskTitle={currentTask.title}
          taskNumber={currentTaskIndex + 1}
          totalTasks={totalCount}
          onUploadComplete={handleDocumentUploadComplete}
          onBack={() => setCurrentScreen('task-detail')}
        />
      )}

      {currentScreen === 'task-complete' && (
        <TaskCompleteScreen
          completedCount={completedCount}
          totalCount={totalCount}
          onNextTask={handleNextTask}
          onViewResult={handleViewResult}
        />
      )}

      {currentScreen === 'eligibility' && eligibilityStatus && (
        <EligibilityScreen
          isEligible={eligibilityStatus.isEligible}
          eligibilityLevel={eligibilityStatus.eligibilityLevel as 'eligible' | 'partially_eligible' | 'not_eligible'}
          score={eligibilityStatus.score}
          onCreateProject={() => setCurrentScreen('sales-project')}
          onViewTasks={() => setCurrentScreen('task-list')}
          onBack={refreshEligibilityAndGoToTaskList}
        />
      )}

      {currentScreen === 'sales-project' && (
        <SalesProjectScreen
          onSave={(project) => {
            console.log('Project saved:', project);
            setCurrentScreen('all-complete');
          }}
          onBack={() => setCurrentScreen('eligibility')}
        />
      )}

      {currentScreen === 'all-complete' && (
        <AllCompleteScreen 
          score={eligibilityStatus?.score || 100}
          onViewProject={() => setCurrentScreen('sales-project')} 
        />
      )}

      <SimpleChat userName={user?.name || 'Usuário'} />
    </>
  );
}
