import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from 'sonner'
import { useAppUser } from './lib/auth.jsx'
import { useAuthStore } from './store/authStore.js';
import SupportButton from './components/support/SupportButton.jsx';
import Home from './app/page.jsx'
import Marketplace from './app/marketplace/page.jsx'
import Dashboard from './app/dashboard/page.jsx'
import Checkout from './app/checkout/page.jsx'
import GetStarted from './app/get-started/page.jsx'
import SignIn from './app/sign-in/page.jsx'
import Register from './app/register/page.jsx'
import Onboarding from './app/onboarding/page.jsx'
import AdminPanel from './app/admin/page.jsx'
import TemplateDetailsPage from './app/marketplace/[slug]/page.jsx'
import PreviewPage from './app/preview/page.jsx'
import PricingPage from './app/pricing/page.jsx'
import AboutPage from './app/about/page.jsx'
import ContactPage from './app/contact/page.jsx'

/** Handles the post-OAuth soft redirect without a full page reload */
function OAuthRedirectHandler() {
  const navigate = useNavigate();
  const pendingRedirect = useAuthStore((s) => s.pendingRedirect);
  const clearPendingRedirect = useAuthStore((s) => s.clearPendingRedirect);

  useEffect(() => {
    if (pendingRedirect) {
      clearPendingRedirect();
      navigate(pendingRedirect, { replace: true });
    }
  }, [pendingRedirect, navigate, clearPendingRedirect]);

  return null;
}

function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAppUser();
  const location = useLocation();
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <div className="relative w-12 h-12">
          <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
          <div className="absolute inset-0 rounded-full border-4 border-t-primary animate-spin" />
        </div>
      </div>
    );
  }
  if (!isSignedIn) {
    return <Navigate to={`/sign-in?from=${encodeURIComponent(location.pathname)}`} replace />;
  }
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <OAuthRedirectHandler />
      <div className="flex-1 flex flex-col w-full relative min-h-screen bg-background text-foreground selection:bg-primary/20">
        {/* Premium Dark Background glow effects */}
        <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full blur-[150px] pointer-events-none" style={{ background: "rgba(37, 99, 235, 0.03)" }} />
        <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full blur-[150px] pointer-events-none" style={{ background: "rgba(13, 148, 136, 0.03)" }} />
        <div className="fixed top-[40%] left-[60%] w-[30%] h-[30%] rounded-full blur-[150px] pointer-events-none" style={{ background: "rgba(14, 165, 233, 0.02)" }} />

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/marketplace/:slug" element={<TemplateDetailsPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/get-started" element={<GetStarted />} />
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/sign-up" element={<Navigate to="/register" replace />} />
          <Route path="/register" element={<Register />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/preview" element={<PreviewPage />} />
          <Route path="/checkout" element={<ProtectedRoute><Checkout /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminPanel /></ProtectedRoute>} />
        </Routes>
        <Toaster richColors position="top-center" theme="dark" />
      </div>
        <SupportButton />
    </BrowserRouter>
  )
}

export default App
