import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Sparkles, AlertCircle, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useAppUser } from "@/lib/auth";
import { cn } from "@/lib/utils";
import "./Page.css";

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0, transition: { delay, duration: 0.45 } },
});

const isCompanyEmail = (email) => {
  if (!email || !email.includes("@")) return false;
  const domain = email.split("@").pop().toLowerCase();
  const publicDomains = new Set([
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "zoho.com", "protonmail.com", "proton.me", "mail.com",
    "yandex.com", "gmx.com", "live.com", "msn.com"
  ]);
  return !publicDomains.has(domain);
};

export default function SignInPage({ isRegister = false }) {
  const navigate = useNavigate();
  const location = useLocation();
  const from = new URLSearchParams(location.search).get("from") || "/dashboard";
  const initialRole = new URLSearchParams(location.search).get("role") || "buyer";
  const urlError = new URLSearchParams(location.search).get("error") || "";

  const { isSignedIn, isLoaded } = useAppUser();

  const [role, setRole] = useState(initialRole);
  const [agreed, setAgreed] = useState(true);
  const [error, setError] = useState(urlError);
  const [oauthLoading, setOauthLoading] = useState(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate(from, { replace: true });
    }
  }, [isLoaded, isSignedIn, navigate, from]);

  // Sync role when initialRole query parameter changes
  useEffect(() => {
    if (initialRole) {
      setRole(initialRole);
    }
  }, [initialRole]);

  const beginGoogleAuth = useAuthStore((s) => s.beginGoogleAuth);
  const beginFacebookAuth = useAuthStore((s) => s.beginFacebookAuth);
  const signInWithEmail = useAuthStore((s) => s.signInWithEmail);
  const registerWithEmail = useAuthStore((s) => s.registerWithEmail);

  const handleOAuth = async (provider) => {
    setOauthLoading(provider);
    const fn = provider === "google" ? beginGoogleAuth : beginFacebookAuth;
    fn(role);
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    if (!email || !password) return;
    setError("");
    setAuthLoading(true);

    if (role === "seller" && !isCompanyEmail(email)) {
      setError("Sellers must use a company email address (not public domains like Gmail).");
      setAuthLoading(false);
      return;
    }

    try {
      if (isRegister) {
        if (!agreed) {
          setError("You must agree to the Terms of Service and Privacy Policy to register.");
          setAuthLoading(false);
          return;
        }
        await registerWithEmail({ email, password, role });
      } else {
        await signInWithEmail({ email, password });
      }
    } catch (err) {
      console.error(err);
      setError(err?.response?.data?.detail || err?.message || "Authentication failed. Please verify your credentials.");
    } finally {
      setAuthLoading(false);
    }
  };

  if (!isLoaded) {
    return (
      <div className="auth-loading-state">
        <div className="loader-spinner-container">
          <div className="loader-spinner-bg" />
          <div className="loader-spinner-bar" />
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page-container">
      {/* Left visual panel */}
      <div className="auth-left-panel">
        <div className="auth-glow-top" />
        <div className="auth-glow-bottom" />

        {/* Logo */}
        <div className="auth-brand-logo">
          <img
            src="/logo.png"
            alt="AI Site Studio Logo"
            className="navbar-logo-img"
            width={40}
            height={40}
          />
          <span className="auth-logo-text">
            AI Site Studio
          </span>
        </div>

        {/* Testimonial */}
        <div className="auth-testimonial-section">
          <blockquote className="auth-blockquote">
            "Launched my portfolio in{" "}
            <span style={{ color: "hsl(var(--primary))" }}>under 10 minutes</span> — AI
            filled in the copy and it looked stunning."
          </blockquote>
          <div className="auth-testimonial-author">
            <img
              src="https://picsum.photos/seed/testimonial1/48"
              alt="Sarah Chen"
              className="auth-testimonial-avatar"
            />
            <div>
              <p className="auth-testimonial-name">Sarah Chen</p>
              <p className="auth-testimonial-title">Freelance Designer</p>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="auth-stats-row">
          {[
            { label: "Templates", value: "500+" },
            { label: "Customers", value: "12K+" },
            { label: "Rating", value: "4.9 ★" },
          ].map((s) => (
            <div key={s.label}>
              <p className="auth-stat-value">{s.value}</p>
              <p className="auth-stat-label">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-right-panel">
        <div className="auth-form-wrapper">
          {/* Mobile logo */}
          <div className="auth-brand-logo-mobile">
            <img src="/logo.png" alt="AI Site Studio Logo" className="navbar-logo-img" width={32} height={32} />
            <span className="auth-logo-text">
              AI Site Studio
            </span>
          </div>

          <motion.div {...fadeUp(0)}>
            <h1 className="auth-form-title">
              {isRegister ? "Create an account" : "Welcome back"}
            </h1>
            <p className="auth-form-subtitle">
              Sign in securely using Google or Facebook. No extra passwords needed.
            </p>
          </motion.div>

          <motion.div {...fadeUp(0.04)} className="role-selection-wrapper">
            <label className="auth-label">
              I want to use AI Site Studio as a:
            </label>
            <div className="role-btn-group">
              <button
                onClick={() => setRole("buyer")}
                className={cn(
                  "auth-role-btn",
                  role === "buyer" && "active buyer"
                )}
              >
                Buyer
              </button>
              <button
                onClick={() => setRole("seller")}
                className={cn(
                  "auth-role-btn",
                  role === "seller" && "active seller"
                )}
              >
                Seller
              </button>
            </div>
            {role === "seller" && (
              <p className="seller-notice-text">
                ℹ️ Sellers must use a <strong>company email address</strong> (public domains like Gmail, Yahoo, etc. are not allowed).
              </p>
            )}
          </motion.div>

          {/* Social Buttons */}
          <motion.div {...fadeUp(0.08)} className="auth-social-group">
            <button
              onClick={() => handleOAuth("google")}
              disabled={!!oauthLoading}
              className="social-btn"
            >
              {oauthLoading === "google" ? (
                <span className="auth-btn-loader social" />
              ) : (
                <svg className="social-svg-icon" viewBox="0 0 48 48">
                  <path fill="#4285F4" d="M44.5 20H24v8.5h11.7C34.3 33.1 30 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 2.9l6-6C34.5 6.3 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c11 0 20-9 20-20 0-1.3-.1-2.7-.5-4z" />
                  <path fill="#34A853" d="M6.3 14.7l7 5.1C15 16.8 19.2 14 24 14c3.1 0 5.8 1.1 8 2.9l6-6C34.5 6.3 29.6 4 24 4c-7.7 0-14.4 4.4-17.7 10.7z" />
                  <path fill="#FBBC05" d="M24 44c5.9 0 11-2 14.7-5.4l-6.8-5.5C30 34.6 27.1 36 24 36c-6 0-10.3-2.9-11.7-7.5l-7 5.4C8.5 40.1 15.6 44 24 44z" />
                  <path fill="#EA4335" d="M43.6 20H24v8.5h11.7c-1 2.7-2.7 5-5 6.6l6.8 5.5C41.7 37.5 44 31.2 44 24c0-1.3-.1-2.7-.4-4z" />
                </svg>
              )}
              Continue with Google
            </button>

            <button
              onClick={() => handleOAuth("facebook")}
              disabled={!!oauthLoading}
              className="social-btn"
            >
              {oauthLoading === "facebook" ? (
                <span className="auth-btn-loader social" />
              ) : (
                <svg className="social-svg-icon fb" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
              )}
              Continue with Facebook
            </button>
          </motion.div>
          {/* Divider */}
          <motion.div {...fadeUp(0.07)} className="auth-divider">
            <div className="auth-divider-line"></div>
            <span className="auth-divider-text">Or continue with</span>
          </motion.div>

          {/* Email/Password Form */}
          <motion.form {...fadeUp(0.12)} onSubmit={handleEmailAuth} className="auth-email-form">
            <div>
              <label className="auth-input-label" htmlFor="email-input">
                Email Address
              </label>
              <input
                id="email-input"
                type="email"
                required
                className="auth-input-field"
                placeholder={role === "seller" ? "username@company.com" : "you@example.com"}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="auth-input-label" htmlFor="password-input">
                Password
              </label>
              <div className="auth-password-wrapper">
                <input
                  id="password-input"
                  type={showPassword ? "text" : "password"}
                  required
                  className="auth-input-field"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
            </div>

            {isRegister && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem", marginBottom: "0.25rem" }}>
                <input
                  id="agreed-checkbox"
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  style={{ width: "1rem", height: "1rem", cursor: "pointer" }}
                />
                <label htmlFor="agreed-checkbox" style={{ fontSize: "0.75rem", color: "hsl(var(--muted-foreground))", cursor: "pointer" }}>
                  I agree to the Terms of Service and Privacy Policy
                </label>
              </div>
            )}

            <button
              type="submit"
              disabled={authLoading}
              className="auth-submit-btn"
            >
              {authLoading ? (
                <span className="auth-btn-loader" />
              ) : isRegister ? (
                "Create Account"
              ) : (
                "Sign In"
              )}
            </button>
          </motion.form>

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="auth-error-alert"
            >
              <AlertCircle className="auth-error-icon" />
              {error}
            </motion.div>
          )}

          <motion.p {...fadeUp(0.16)} className="auth-footer-text">
            {isRegister ? (
              <>
                Already have an account?{" "}
                <Link
                  to={`/sign-in?role=${role}`}
                  className="auth-footer-link"
                >
                  Sign in
                </Link>
              </>
            ) : (
              <>
                Don't have an account?{" "}
                <Link
                  to={`/register?role=${role}`}
                  className="auth-footer-link"
                >
                  Create account
                </Link>
              </>
            )}
          </motion.p>
        </div>
      </div>
    </div>
  );
}
