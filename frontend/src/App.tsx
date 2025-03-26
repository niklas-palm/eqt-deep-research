import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import AuthCallback from "@/components/AuthCallback";
import { ProtectedRoute } from "@/components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={
        <ProtectedRoute requireAuth={false}>
          <Login />
        </ProtectedRoute>
      } />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* Catch-all route */}
      <Route path="*" element={
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-red-500 mb-4">404</h1>
            <p className="text-xl">Page not found</p>
          </div>
        </div>
      } />
    </Routes>
  );
}

export default App;