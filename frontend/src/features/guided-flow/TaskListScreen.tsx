import React from 'react';
import { CheckCircle2, TrendingUp, AlertCircle, FileText, Clock, ArrowRight } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import type { ChecklistItem } from '../../domain/models';

interface TaskListScreenProps {
  tasks: ChecklistItem[];
  onStartFirstTask: () => void;
  onViewResult?: () => void;
  onTaskClick?: (taskId: string) => void;
  onBack?: () => void;
  score?: number;
  eligibilityLevel?: 'eligible' | 'partially_eligible' | 'not_eligible';
}

export function TaskListScreen({ tasks, onStartFirstTask, onViewResult, onTaskClick, onBack, score = 0, eligibilityLevel = 'not_eligible' }: TaskListScreenProps) {
  const completedCount = tasks.filter((t) => t.status === 'done').length;
  const totalCount = tasks.length;
  const pendingTasks = tasks.filter((t) => t.status !== 'done');
  const progressPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const scorePercentage = score;

  // Determine colors based on score
  const getScoreBgColor = () => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 50) return 'bg-yellow-50 border-yellow-200';
    return 'bg-orange-50 border-orange-200';
  };

  const getScoreTextColor = () => {
    if (score >= 80) return 'text-green-800';
    if (score >= 50) return 'text-yellow-800';
    return 'text-orange-800';
  };

  const getScoreBarColor = () => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const scoreBgColor = getScoreBgColor();
  const scoreTextColor = getScoreTextColor();
  const scoreBarColor = getScoreBarColor();

  return (
    <ScreenWrapper
      title="O que você precisa fazer"
      subtitle={`Você tem ${totalCount} ${totalCount === 1 ? 'coisa' : 'coisas'} para completar. Vamos fazer uma de cada vez.`}
      primaryAction={{
        label: pendingTasks.length > 0 ? 'Começar primeira tarefa' : 'Ver resultado',
        onClick: pendingTasks.length > 0 ? onStartFirstTask : (onViewResult || onStartFirstTask),
        disabled: totalCount === 0,
      }}
      showBack={!!onBack}
      onBack={onBack}
    >
      {/* Score Progress Bar */}
      <div className={`mb-6 p-5 rounded-xl border-2 ${scoreBgColor} shadow-sm`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className={`h-5 w-5 ${scoreTextColor}`} />
            <p className={`font-bold text-lg ${scoreTextColor}`}>
              Sua nota: {score}/100
            </p>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-bold ${
            score >= 80 ? 'bg-green-600 text-white' :
            score >= 50 ? 'bg-yellow-600 text-white' :
            'bg-orange-600 text-white'
          }`}>
            {score >= 80 ? 'Ótimo!' : score >= 50 ? 'Bom' : 'Em progresso'}
          </div>
        </div>
        
        {/* Visual Progress Bar */}
        <div className="relative w-full h-6 bg-white rounded-full overflow-hidden border-2 border-white shadow-inner">
          <div
            className={`h-full ${scoreBarColor} transition-all duration-1000 ease-out rounded-full relative overflow-hidden`}
            style={{ width: `${scorePercentage}%` }}
          >
            {/* Animated shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
          </div>
        </div>
        
        <div className="mt-3 flex items-center justify-between text-xs">
          <span className={`font-medium ${scoreTextColor}`}>
            {completedCount} de {totalCount} tarefas concluídas
          </span>
          <span className={`font-bold ${scoreTextColor}`}>
            {progressPercentage}%
          </span>
        </div>
      </div>

      {/* Pending Tasks */}
      {pendingTasks.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-600" />
            Tarefas para fazer
          </h3>
          <div className="space-y-3">
            {pendingTasks.map((task, index) => {
              const taskNumber = tasks.findIndex((t) => t.id === task.id) + 1;
              return (
                <div
                  key={task.id}
                  onClick={() => onTaskClick?.(task.id)}
                  className={`group relative p-5 rounded-xl border-2 transition-all cursor-pointer active:scale-[0.98] ${
                    task.priority === 'high'
                      ? 'bg-orange-50 border-orange-300 shadow-md'
                      : 'bg-white border-slate-200 hover:border-green-300 hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-full font-bold flex items-center justify-center text-base ${
                        task.priority === 'high'
                          ? 'bg-orange-600 text-white'
                          : 'bg-green-600 text-white'
                      }`}
                    >
                      {taskNumber}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="font-bold text-base text-slate-800 leading-tight">
                          {task.title}
                        </h4>
                        {task.priority === 'high' && (
                          <div className="flex items-center gap-1 bg-orange-100 text-orange-700 px-2 py-1 rounded-full text-xs font-bold">
                            <AlertCircle className="h-3 w-3" />
                            Importante
                          </div>
                        )}
                      </div>
                      {task.description && (
                        <p className="text-sm text-slate-600 leading-relaxed mb-3">
                          {task.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        {task.needUpload && (
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            <span>Precisa de documento</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-green-600 transition-colors flex-shrink-0 mt-1" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Completed Tasks */}
      {completedCount > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-bold text-slate-600 mb-3 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Tarefas concluídas ({completedCount})
          </h3>
          <div className="space-y-2">
            {tasks
              .filter((t) => t.status === 'done')
              .map((task) => {
                const taskNumber = tasks.findIndex((t) => t.id === task.id) + 1;
                return (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 p-4 rounded-lg bg-green-50 border border-green-200 opacity-75"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 text-white font-bold flex items-center justify-center text-sm">
                      {taskNumber}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm text-slate-500 line-through">
                        {task.title}
                      </p>
                    </div>
                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </ScreenWrapper>
  );
}
