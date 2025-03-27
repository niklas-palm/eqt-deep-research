// Authentication configuration for AWS Cognito with react-oidc-context

interface AuthConfig {
  authority: string;
  client_id: string;
  redirect_uri: string;
  response_type: string;
  scope: string;
  apiUrl: string;
  automaticSilentRenew: boolean;
  loadUserInfo: boolean;
  monitorSession: boolean;
  silentRequestTimeout: number;
  onSigninCallback: () => void;
  onSigninError: (error: Error) => void;
}

// IMPORTANT: Replace these placeholders with your managed Cognito values
// The redirect_uri must match exactly what's configured in your Cognito app client

const config = {
  development: {
    // Cognito User Pool URL
    authority: "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_ZglCV4T4H",
    // Cognito App Client ID
    client_id: "77qrii4qtkdps60jnum4ifuesd",
    // This must match exactly what's configured in the Cognito App Client
    redirect_uri: "http://localhost:5173/",
    response_type: "code",
    scope: "phone openid email",
    // API Gateway URL
    apiUrl: "https://t9ufzhrbo3.execute-api.eu-west-1.amazonaws.com/Prod",
  },
  production: {
    // Same values for production by default
    authority: "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_ZglCV4T4H",
    client_id: "77qrii4qtkdps60jnum4ifuesd",
    redirect_uri: window.location.origin,
    response_type: "code",
    scope: "phone openid email",
    apiUrl: "https://t9ufzhrbo3.execute-api.eu-west-1.amazonaws.com/Prod",
  },
};

// Get the environment
const env =
  import.meta.env.MODE === "production" ? "production" : "development";
const baseConfig = config[env];

export const authConfig: AuthConfig = {
  ...baseConfig,
  // These are recommended settings for react-oidc-context
  automaticSilentRenew: true, // Automatically renew tokens when they're about to expire
  loadUserInfo: true, // Load the user's profile info after login
  monitorSession: true, // Monitor the user's session
  silentRequestTimeout: 10000, // Timeout for silent renewal (in ms)
  onSigninCallback: () => {
    // After login, redirect to the page before login or home page
    window.history.replaceState({}, document.title, window.location.pathname);
  },
  // Handle errors like expired tokens
  onSigninError: (error) => {
    // If token is expired, trigger silent renew
    if (error.message.includes("expired")) {
      window.location.reload(); // Reload as a simple fix
    }
  },
};
