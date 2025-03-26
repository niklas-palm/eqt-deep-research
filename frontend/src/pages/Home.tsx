import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import NavBar from '@/components/NavBar';
import { useApi } from '@/lib/api';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

export default function Home() {
  const { isAuthenticated, user } = useAuth();
  const { createResearch, getResearchStatus } = useApi();
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState('');
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);
  const [isDeepResearch, setIsDeepResearch] = useState(false); // Toggle for deep research
  
  // Log authentication status on component mount
  useEffect(() => {
    console.log('Home component - auth status:', { 
      isAuthenticated, 
      user: user ? 'User present' : 'No user',
      userId: user?.sub
    });
  }, [isAuthenticated, user]);
  
  // Create a flag to identify hot module reloads
  // When the module reloads, this value will start as false again
  const didCleanupForHotReload = useRef(false);
  
  // Effect for handling HMR (Hot Module Replacement) specifically
  useEffect(() => {
    // Check for existing active job that needs to continue polling
    if (activeJobId && !didCleanupForHotReload.current) {
      console.log(`HMR detected, restarting polling for job: ${activeJobId}`);
      
      // Update the job ID ref to match the active job ID
      jobIdRef.current = activeJobId;
      
      // Reset interval if it was running before hot reload
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
      }
      
      // Start a new interval for the active job
      const interval = setInterval(() => {
        if (jobIdRef.current) {
          console.log(`Polling job after HMR: ${jobIdRef.current}`);
          pollJobStatus(jobIdRef.current);
        }
      }, 2000);
      
      // Store new interval
      intervalIdRef.current = interval;
      setPollingInterval(interval);
      
      // Mark that we've handled this HMR cycle
      didCleanupForHotReload.current = true;
      
      // Make an immediate status check when restoring polling
      if (activeJobId) {
        pollJobStatus(activeJobId);
      }
    }
    
    // Cleanup function for component unmount or before next effect run
    return () => {
      console.log("Component cleanup - HMR or unmount");
      // Only do actual cleanup for real unmount, not for hot reloads
      // In development mode, assume unmount is due to hot reload
      // In a Vite app, we should use import.meta.env instead of process.env
      if (import.meta.env.MODE !== 'development') {
        const currentInterval = intervalIdRef.current;
        if (currentInterval) {
          console.log("Cleaning up interval on actual unmount");
          clearInterval(currentInterval);
          intervalIdRef.current = null;
        }
      }
    };
  }, [activeJobId]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check authentication first
    if (!isAuthenticated) {
      console.error('User not authenticated! Cannot submit research request.');
      toast.error('Authentication Required', {
        description: 'Please sign in to use the research feature.'
      });
      return;
    }
    
    if (!query.trim() || isLoading) return;
    
    // Clean up any existing interval first using both state and ref
    // Store local references to avoid race conditions
    const currentStateInterval = pollingInterval;
    const currentRefInterval = intervalIdRef.current;
    
    // Clear references first
    setPollingInterval(null);
    intervalIdRef.current = null;
    setActiveJobId(null); // Reset the active job ID to prevent any lingering polls
    
    // Then clear the actual intervals
    if (currentStateInterval) {
      console.log("Cleaning up previous polling interval from state");
      clearInterval(currentStateInterval);
    }
    if (currentRefInterval) {
      console.log("Cleaning up previous polling interval from ref");
      clearInterval(currentRefInterval);
    }
    
    setIsLoading(true);
    setResult('');
    setStatus('Preparing your research...');
    
    try {
      const response = await createResearch(query.trim(), isDeepResearch);
      
      if (response.job_id) {
        
        // First set the job ID in state
        setActiveJobId(response.job_id);
        setStatus('Starting analysis...');
        
        console.log(`Starting polling for job: ${response.job_id}`);
        
        // Store the job ID in ref for future use in intervals
        jobIdRef.current = response.job_id;
        
        // Make the first polling call immediately
        pollJobStatus(response.job_id);
        
        // Cancel any existing interval
        if (intervalIdRef.current) {
          clearInterval(intervalIdRef.current);
          intervalIdRef.current = null;
        }
        
        // Create a new interval that uses the jobIdRef
        const interval = setInterval(() => {
          // Use the job ID from ref to avoid closure issues
          if (jobIdRef.current) {
            console.log(`Polling job from interval: ${jobIdRef.current}`);
            pollJobStatus(jobIdRef.current);
          } else {
            console.log('No active job ID in ref - stopping polling');
            clearInterval(interval);
          }
        }, 2000);
        
        // Store the interval ID both in state and in ref for reliable cleanup
        setPollingInterval(interval);
        intervalIdRef.current = interval;
      } else {
        // Error case - no job ID
        toast.error('Research Error', {
          description: 'Failed to start research process.'
        });
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Research query failed:', error);
      toast.error('Research Error', {
        description: 'Failed to process your request. Please try again.'
      });
      setIsLoading(false);
    }
  };
  
  // Store interval ID outside of React state for immediate access
  const intervalIdRef = useRef<number | null>(null);
  // Keep the job ID in a ref to avoid closure issues
  const jobIdRef = useRef<string | null>(null);
  
  const pollJobStatus = async (jobId: string) => {
    // Update the job ID ref with the latest value
    jobIdRef.current = jobId;
    console.log(`Attempting to poll job status for ${jobId}`);
    
    // Verify authentication before polling
    if (!isAuthenticated) {
      console.error('Cannot poll job status: User is not authenticated!');
      
      // Clear polling since it won't work without auth
      const currentStateInterval = pollingInterval;
      const currentRefInterval = intervalIdRef.current;
      
      intervalIdRef.current = null;
      setPollingInterval(null);
      
      // Clear job ID from state and ref
      setActiveJobId(null);
      jobIdRef.current = null;
      
      if (currentRefInterval) clearInterval(currentRefInterval);
      if (currentStateInterval) clearInterval(currentStateInterval);
      
      setStatus('Authentication error');
      setIsLoading(false);
      
      toast.error('Authentication Required', {
        description: 'Please sign in to continue monitoring your research.'
      });
      return;
    }
    
    try {
      console.log(`Calling getResearchStatus for job ${jobId}`);
      const status = await getResearchStatus(jobId);
      
      // Debug logging
      console.log("Job status response:", status);
      console.log("Status field:", status.status);
      console.log("Has result:", !!status.result);
      console.log("Current interval:", pollingInterval !== null ? "active" : "none");
      
      // Update status message
      if (status.message) {
        setStatus(status.message);
      }
      
      // Check if status contains "COMPLETED" or "FAILED" (using includes for case insensitivity and to handle different formats)
      const statusStr = String(status.status).toUpperCase();
      const isCompleted = statusStr.includes('COMPLETED');
      const isFailed = statusStr.includes('FAILED');
      
      // Always clear polling interval first if job is completed or failed
      if ((isCompleted && status.result) || isFailed) {
        console.log(`Job ${isCompleted ? 'completed' : 'failed'}! Stopping polling.`);
        
        // Get references to current intervals to avoid timing issues
        const currentIntervalRef = intervalIdRef.current;
        const currentIntervalState = pollingInterval;
        
        // Clear references first to prevent any new polling from starting
        intervalIdRef.current = null;
        setPollingInterval(null);
        
        // Then clear the actual intervals
        if (currentIntervalRef) {
          console.log("Clearing polling interval from ref");
          clearInterval(currentIntervalRef);
        }
        
        if (currentIntervalState) {
          console.log("Clearing polling interval from state");
          clearInterval(currentIntervalState);
        }
        
        // Clear the active job ID from both state and ref
        setActiveJobId(null);
        jobIdRef.current = null;
        
        // Then handle the specific status
        if (isCompleted && status.result) {
          // Job complete
          setResult(status.result);
          setIsLoading(false);
          console.log('Job completed successfully - clearing job ID and stopping polling');
        } else if (isFailed) {
          // Job failed
          setStatus('Research failed');
          setResult(`Error: ${status.error || 'Something went wrong with your research request.'}`);
          setIsLoading(false);
          console.log('Job failed - clearing job ID and stopping polling');
          
          toast.error('Research Error', {
            description: status.error || 'Something went wrong with your research request.'
          });
        }
      }
    } catch (error) {
      console.error('Error polling job status:', error);
      // Don't clear the polling interval on errors - it might be a temporary network issue
      // Just log the error and let the next polling interval try again
      
      // Update the status to show there was an error
      setStatus('Error checking status - will retry');
    }
  };
  
  const startNewQuery = () => {
    setQuery('');
    setResult('');
    setStatus('');
    setIsLoading(false);
    setActiveJobId(null);
    jobIdRef.current = null;
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex flex-col">
      <NavBar />
      
      <main className="flex-grow flex flex-col items-center py-8 px-4">
        <div className="w-full max-w-3xl">
          {!result && (
            <>
              <div className="text-center mb-10 pt-12">
                <h1 className="text-3xl font-semibold text-gray-800 mb-4">
                  EQT Portfolio Research
                </h1>
                <p className="text-slate-500">
                  Ask about any EQT portfolio company to get comprehensive insights
                </p>
              </div>
          
              <form onSubmit={handleSubmit} className="w-full">
                <div className="relative">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isLoading}
                    placeholder="What would you like to know about an EQT portfolio company?"
                    className="w-full py-4 px-5 border border-slate-200 rounded-xl shadow-sm 
                              focus:outline-none focus:ring-2 focus:ring-eqt-primary focus:border-transparent
                              disabled:opacity-50 text-gray-800 placeholder-gray-400"
                  />
                  <button
                    type="submit"
                    disabled={!query.trim() || isLoading}
                    className="absolute right-3 top-1/2 -translate-y-1/2 bg-eqt-primary text-white px-4 py-2 rounded-lg
                              hover:bg-eqt-orange-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Research
                  </button>
                </div>
                
                <div className="mt-4 flex items-center">
                  <label className="inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer"
                      checked={isDeepResearch}
                      onChange={(e) => setIsDeepResearch(e.target.checked)}
                      disabled={isLoading}
                    />
                    <div className="relative w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-eqt-primary 
                                  peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-eqt-primary-light
                                  after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
                                  after:bg-white after:border-gray-300 after:border after:rounded-full 
                                  after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full">
                    </div>
                    <span className="ml-3 text-sm font-medium text-gray-700">Deep Research</span>
                  </label>
                  
                  {isDeepResearch && (
                    <div className="ml-3 text-xs text-amber-600">
                      Warning: Deep research may take several minutes to complete.
                    </div>
                  )}
                </div>
              </form>
            </>
          )}
          
          {isLoading && (
            <div className="mt-8 flex flex-col items-center">
              <div className="relative w-16 h-16">
                <div className="w-16 h-16 rounded-full border-4 border-slate-100 border-t-eqt-primary animate-spin"></div>
              </div>
              <p className="mt-4 text-slate-600 text-center">{status || 'Processing your request...'}</p>
            </div>
          )}
          
          {result && (
            <div className="mt-6">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
                <div className="prose prose-slate max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                  >
                    {result}
                  </ReactMarkdown>
                </div>
              </div>
              
              <div className="flex justify-center">
                <button
                  onClick={startNewQuery}
                  className="bg-eqt-primary text-white px-5 py-2.5 rounded-lg 
                            hover:bg-eqt-orange-700 transition-colors duration-200"
                >
                  New Research Query
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Footer - simplified */}
      <footer className="bg-eqt-dark text-gray-300 py-2 text-center text-xs mt-auto w-full">
        <p>EQT Deep Research | {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}