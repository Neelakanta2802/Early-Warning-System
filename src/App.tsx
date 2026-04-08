import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import StudentsPage from './pages/StudentsPage';
import StudentProfile from './pages/StudentProfile';
import AlertsPage from './pages/AlertsPage';
import InterventionsPage from './pages/InterventionsPage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';
import PlanningAnalyticsPage from './pages/PlanningAnalyticsPage';
import ReportsPage from './pages/ReportsPage';
import DataUploadPage from './pages/DataUploadPage';
import SettingsPage from './pages/SettingsPage';
import HelpPage from './pages/HelpPage';

function AppContent() {
  const { user, loading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  
  // CRITICAL FIX: Listen for navigation events from upload page
  useEffect(() => {
    const handleNavigateTo = (event: CustomEvent) => {
      const page = event.detail;
      if (page && typeof page === 'string') {
        console.log(`🔄 Navigating to ${page} page...`);
        setCurrentPage(page);
      }
    };
    
    window.addEventListener('navigateTo', handleNavigateTo as EventListener);
    
    return () => {
      window.removeEventListener('navigateTo', handleNavigateTo as EventListener);
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-slate-900 border-r-transparent mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    if (!showLogin) {
      return <LandingPage onGetStarted={() => setShowLogin(true)} />;
    }
    return <LoginPage />;
  }

  const handleViewStudent = (studentId: string) => {
    setSelectedStudentId(studentId);
    setCurrentPage('student-profile');
  };

  const handleBackToStudents = () => {
    setSelectedStudentId(null);
    setCurrentPage('students');
  };

  const renderPage = () => {
    if (currentPage === 'student-profile' && selectedStudentId) {
      return <StudentProfile studentId={selectedStudentId} onBack={handleBackToStudents} />;
    }

    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'students':
        return <StudentsPage onViewStudent={handleViewStudent} />;
      case 'risk-analysis':
        return <RiskAnalysisPage />;
      case 'planning-analytics':
        return <PlanningAnalyticsPage />;
      case 'interventions':
        return <InterventionsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'data-upload':
        return <DataUploadPage />;
      case 'alerts':
        return <AlertsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'help':
        return <HelpPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <ErrorBoundary>
      <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
        {renderPage()}
      </Layout>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
