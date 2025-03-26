import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

/**
 * Auth callback component that handles redirects after authentication
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const returnToParam = searchParams.get('returnTo');
    
    // Determine where to navigate after auth processing
    let navigateTo = '/';
    
    // If we have a returnTo parameter, decode it and use that for navigation
    if (returnToParam) {
      navigateTo = decodeURIComponent(returnToParam);
    }
    
    // Redirect after a short delay to let auth state update
    const timer = setTimeout(() => {
      navigate(navigateTo, { replace: true });
    }, 300);
    
    return () => clearTimeout(timer);
  }, [navigate, searchParams]);
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">Processing Authentication</h2>
        <p className="text-gray-600">Please wait...</p>
      </div>
    </div>
  );
}