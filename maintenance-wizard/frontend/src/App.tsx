import { Navigate, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from './auth/ProtectedRoute';
import { AppShell } from './components/shell/AppShell';
import AssistantPage from './pages/AssistantPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/assistant" replace />} />
        <Route path="/assistant" element={<AssistantPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
