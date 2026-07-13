import { useState, useEffect } from "react";
import { Sparkles, ArrowLeft, ArrowRight, Loader2, CheckCircle2, Image as ImageIcon, Globe, Shield } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import Navbar from "@/components/layout/Navbar";
import "./Page.css";

const GENERATION_STEPS = [
  { id: 1, label: "Parsing your vision...", duration: 2500 },
  { id: 2, label: "Crafting description & marketplace metadata...", duration: 3500 },
  { id: 3, label: "Designing developer brand logo...", duration: 2500 },
  { id: 4, label: "Generating high-fidelity page screenshots...", duration: 3500 },
  { id: 5, label: "Indexing in vector space...", duration: 2000 },
];

export default function GenerateTemplatePage() {
  const navigate = useNavigate();
  const token = useAuthStore((s) => s.token);
  const [prompt, setPrompt] = useState("");
  const [framework, setFramework] = useState("html");
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [error, setError] = useState("");
  const [generatedTemplate, setGeneratedTemplate] = useState(null);

  // Handle steps animation during generation
  useEffect(() => {
    if (!isGenerating || currentStep >= GENERATION_STEPS.length) return;

    const step = GENERATION_STEPS[currentStep];
    const timer = setTimeout(() => {
      setCompletedSteps((prev) => [...prev, step.id]);
      if (currentStep < GENERATION_STEPS.length - 1) {
        setCurrentStep((prev) => prev + 1);
      }
    }, step.duration);

    return () => clearTimeout(timer);
  }, [isGenerating, currentStep]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || prompt.length < 10) {
      setError("Please describe your template in at least 10 characters.");
      return;
    }

    setError("");
    setIsGenerating(true);
    setCurrentStep(0);
    setCompletedSteps([]);
    setGeneratedTemplate(null);

    try {
      // Initiate backend generation
      const response = await api.post("/templates/generate", { prompt, framework }, token);
      
      // Wait for all steps to finish animating if backend returns earlier
      // to maintain premium user experience
      setGeneratedTemplate(response);
    } catch (err) {
      console.error(err);
      setError(err?.message || "An error occurred during template generation. Please try again.");
      setIsGenerating(false);
    }
  };

  // If backend returns template, wait until all steps are complete before showing success
  const isGenerationComplete = generatedTemplate && completedSteps.length === GENERATION_STEPS.length;

  return (
    <>
      <Navbar />
      <div className="generate-page">
        <div className="generate-container">
          
          {/* Header */}
          <div className="generate-header">
            <Link to="/marketplace" className="back-link">
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Marketplace</span>
            </Link>
            <h1 className="generate-title">
              <Sparkles className="title-icon text-primary animate-pulse" />
              <span>AI Template Generator</span>
            </h1>
            <p className="generate-subtitle">
              Describe your website template idea, and Gemini will generate a high-fidelity marketplace listing, brand logo, and matching interior screenshots.
            </p>
          </div>

          <div className="generate-card-wrapper">
            {!isGenerating && !generatedTemplate && (
              /* Prompt Input Form */
              <form onSubmit={handleSubmit} className="prompt-form glass-panel">
                <div className="form-group">
                  <label htmlFor="prompt" className="prompt-label">
                    Describe your dream website template
                  </label>
                  <textarea
                    id="prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g., 'A premium glassmorphic portfolio for a cyber-security engineer, featuring a dark neon-blue theme, terminal-style terminal blog page, and a visual project grid...'"
                    className="prompt-textarea"
                    rows={5}
                  />
                  {error && <p className="error-text">{error}</p>}
                </div>

                <div className="form-group">
                  <label className="prompt-label">Select Code Framework</label>
                  <div className="framework-selector">
                    <button
                      type="button"
                      onClick={() => setFramework("html")}
                      className={`framework-card ${framework === "html" ? "active" : ""}`}
                    >
                      <Globe className="framework-icon" />
                      <div className="framework-text">
                        <h3>HTML5 & CSS</h3>
                        <p>Single-file responsive static page</p>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setFramework("react")}
                      className={`framework-card ${framework === "react" ? "active" : ""}`}
                    >
                      <Shield className="framework-icon" />
                      <div className="framework-text">
                        <h3>React SPA</h3>
                        <p>Modern React Vite project structure</p>
                      </div>
                    </button>
                  </div>
                </div>

                <button type="submit" className="submit-btn group">
                  <span>Generate Template Listing</span>
                  <Sparkles className="submit-btn-icon group-hover:rotate-12 transition-transform" />
                </button>
              </form>
            )}

            {isGenerating && !isGenerationComplete && (
              /* Progress Step Indicator */
              <div className="generation-loading-panel glass-panel">
                <div className="loading-title-row">
                  <Loader2 className="loading-spinner text-primary animate-spin" />
                  <h2>Generating Template</h2>
                </div>
                <p className="loading-desc">
                  Our advanced AI model is creating structure, mockups, and assets based on your prompt.
                </p>

                <div className="steps-list">
                  {GENERATION_STEPS.map((step, idx) => {
                    const isCompleted = completedSteps.includes(step.id);
                    const isActive = currentStep === idx;
                    return (
                      <div
                        key={step.id}
                        className={`step-item ${isCompleted ? "completed" : ""} ${isActive ? "active" : ""}`}
                      >
                        <div className="step-bullet">
                          {isCompleted ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-500 fill-emerald-500/10" />
                          ) : isActive ? (
                            <div className="pulse-bullet" />
                          ) : (
                            <div className="empty-bullet" />
                          )}
                        </div>
                        <span className="step-label">{step.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {isGenerationComplete && (
              /* Success template preview card */
              <div className="success-panel glass-panel">
                <div className="success-header">
                  <CheckCircle2 className="success-icon text-emerald-500 animate-bounce" />
                  <h2>Generation Successful!</h2>
                  <p>Your custom website template has been successfully generated and published to the marketplace.</p>
                </div>

                <div className="generated-preview-card">
                  <div className="card-media">
                    <img
                      src={generatedTemplate.thumbnail_url}
                      alt={generatedTemplate.title}
                      className="card-image"
                    />
                    <div className="card-badge">AI Generated</div>
                  </div>
                  <div className="card-info">
                    <div className="card-meta">
                      <span className="category-tag">{generatedTemplate.industry}</span>
                      <span className="price-tag">${generatedTemplate.price}</span>
                    </div>
                    <h3 className="card-title">{generatedTemplate.title}</h3>
                    <p className="card-desc">{generatedTemplate.short_description}</p>
                    <div className="card-tags">
                      {generatedTemplate.tags?.slice(0, 3).map((tag) => (
                        <span key={tag} className="meta-tag">#{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="success-actions">
                  <button
                    onClick={() => {
                      setIsGenerating(false);
                      setGeneratedTemplate(null);
                      setPrompt("");
                    }}
                    className="secondary-action-btn"
                  >
                    Generate Another
                  </button>
                  <Link
                    to={`/marketplace/${generatedTemplate.slug}`}
                    className="primary-action-btn"
                  >
                    <span>View Template Details</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </>
  );
}
