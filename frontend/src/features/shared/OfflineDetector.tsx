import { useEffect, useState } from 'react';

export function useOfflineDetection() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false);
      setWasOffline(true);
      // Reset after showing message
      setTimeout(() => setWasOffline(false), 3000);
    };

    const handleOffline = () => {
      setIsOffline(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOffline, wasOffline };
}

export function OfflineBanner() {
  const { isOffline, wasOffline } = useOfflineDetection();

  if (!isOffline && !wasOffline) return null;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 p-4 text-center text-white font-medium ${
        isOffline ? 'bg-red-600' : 'bg-green-600'
      }`}
    >
      {isOffline ? (
        <p>Sem conexão com a internet. Verifique sua conexão e tente novamente.</p>
      ) : (
        <p>Conexão restaurada! Você pode continuar.</p>
      )}
    </div>
  );
}
