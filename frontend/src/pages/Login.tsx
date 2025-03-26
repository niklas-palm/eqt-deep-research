import { useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { useNavigate, useSearchParams } from 'react-router-dom';
import NavBar from '@/components/NavBar';

export default function Login() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Get return URL from query params or default to home
  const returnTo = searchParams.get('returnTo') || '/';
  const expired = searchParams.get('expired') === 'true';
  
  // Redirect authenticated users
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(returnTo, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, returnTo]);

  return (
    <div className="min-h-screen bg-white">
      <NavBar />
      
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <div className="w-full max-w-md px-8 py-12 bg-white shadow-sm border border-eqt-gray-200">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-eqt-dark uppercase tracking-wide">
              Welcome to EQT Deep Research
            </h2>
            <div className="h-1 w-16 bg-eqt-primary mx-auto my-4"></div>
            <p className="mt-4 text-eqt-gray-700">
              Sign in to access the portfolio research tool
            </p>
            {expired && (
              <p className="mt-3 text-eqt-primary font-medium">
                Your session has expired. Please sign in again.
              </p>
            )}
          </div>
          
          <button
            onClick={login}
            className="w-full bg-eqt-primary text-white py-3 px-4 hover:bg-eqt-orange-700 transition-colors focus:outline-none uppercase text-sm tracking-wider font-medium"
          >
            Sign in
          </button>
          
          <div className="mt-8 text-center text-sm text-eqt-gray-500">
            <p>
              You will be redirected to the authentication provider for secure sign in.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}