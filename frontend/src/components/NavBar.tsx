import { Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';

export default function NavBar() {
  const { isAuthenticated, user, login, logout } = useAuth();
  
  return (
    <nav className="bg-white border-b border-eqt-gray-200">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between h-14">
          <div className="flex items-center">
            <Link to="/" className="font-medium">
              <span className="text-eqt-primary">EQT</span> Deep Research
            </Link>
          </div>

          <div className="flex items-center">
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-eqt-gray-600 hidden sm:inline">
                  {user?.email || 'User'}
                </span>
                <button
                  onClick={logout}
                  className="text-eqt-gray-600 hover:text-eqt-dark text-sm"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <button
                onClick={login}
                className="bg-eqt-primary text-white px-4 py-1 text-sm"
              >
                Sign in
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}