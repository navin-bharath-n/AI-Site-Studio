"use client";

/**
 * Preview Builder Page — multi-step form to generate a watermarked live preview (React JSX).
 */

export const dynamic = "force-dynamic";

import { useState, Suspense } from "react";
import { navigate } from "@/components/Link";
const useRouter = () => ({
  push: (to) => navigate(to),
  replace: (to) => navigate(to),
});
const useSearchParams = () => new URLSearchParams(window.location.search);
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import Image from "@/components/Image";
import { useAppUser } from "@/lib/auth";
import {
  Sparkles, ArrowRight, ArrowLeft, Eye, Loader2,
  Building2, Palette, FileText,
} from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import { api } from "@/lib/api";
import "./Page.css";

const schema = z.object({
  business_name: z.string().min(1, "Business name is required"),
  industry: z.string().min(1, "Industry is required"),
  primary_color: z.string(),
  secondary_color: z.string(),
  about: z.string().optional(),
  location: z.string().optional(),
  ai_fill: z.boolean(),
});

const STEPS = [
  { id: 1, title: "Business Info", icon: Building2, description: "Tell us about your business" },
  { id: 2, title: "Brand Colors", icon: Palette, description: "Choose your brand colors" },
  { id: 3, title: "Content", icon: FileText, description: "Add your content or use AI" },
  { id: 4, title: "Preview", icon: Eye, description: "See your preview" },
];

const INDUSTRIES = [
  "Business & Corporate", "Restaurant & Food", "Healthcare & Medical",
  "Technology & Software", "E-Commerce & Retail", "Portfolio & Creative",
  "Education & Training", "Real Estate", "Travel & Tourism", "Agency & Marketing",
];

function PreviewBuilder() {
  const searchParams = useSearchParams();
  const templateId = searchParams.get("template");
  const { user } = useAppUser();
  const [step, setStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewSession, setPreviewSession] = useState(null);

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      primary_color: "#6366f1",
      secondary_color: "#8b5cf6",
      ai_fill: false,
    },
  });

  const { watch, setValue, formState: { errors } } = form;

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleGenerate = async (data) => {
    if (!templateId) return;
    setIsGenerating(true);
    try {
      const session = await api.post("/preview", {
        template_id: templateId,
        ...data,
      });
      setPreviewSession(session);
      setStep(4);
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!templateId) {
    return (
      <>
        <Navbar />
        <div className="preview-no-template-wrapper">
          <div className="preview-no-template-box">
            <p className="preview-no-template-msg">No template selected.</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="preview-page">
        <div className="preview-container">
          {/* Progress Steps */}
          <div className="preview-steps-bar">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const isActive = step === s.id;
              const isDone = step > s.id;
              return (
                <div key={s.id} className="preview-step-item">
                  <div className="preview-step-content">
                    <div
                      className={cn(
                        "preview-step-circle",
                        isActive && "active",
                        isDone && "done"
                      )}
                    >
                      <Icon className="preview-step-icon" />
                    </div>
                    <span className={cn("preview-step-label", isActive && "active")}>
                      {s.title}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={cn("preview-step-line", isDone && "done")} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Form Steps */}
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="preview-step-card"
              >
                <div>
                  <h2 className="preview-step-title">Business Information</h2>
                  <p className="preview-step-subtitle">Tell us about your business</p>
                </div>

                <div className="preview-field-group">
                  <div>
                    <label className="preview-label">Business Name *</label>
                    <input
                      {...form.register("business_name")}
                      placeholder="e.g. The Coffee Corner"
                      className="preview-input"
                    />
                    {errors.business_name && (
                      <p className="preview-form-error">{errors.business_name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="preview-label">Industry *</label>
                    <select
                      {...form.register("industry")}
                      className="preview-select"
                    >
                      <option value="">Select an industry</option>
                      {INDUSTRIES.map((ind) => (
                        <option key={ind} value={ind} style={{ backgroundColor: "hsl(var(--card))" }}>{ind}</option>
                      ))}
                    </select>
                    {errors.industry && (
                      <p className="preview-form-error">{errors.industry.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="preview-label">Location (optional)</label>
                    <input
                      {...form.register("location")}
                      placeholder="e.g. New York, NY"
                      className="preview-input"
                    />
                  </div>
                </div>

                <button
                  onClick={handleNext}
                  className="preview-btn primary"
                >
                  Next: Brand Colors <ArrowRight className="preview-arrow-icon" />
                </button>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="preview-step-card"
              >
                <div>
                  <h2 className="preview-step-title">Brand Colors</h2>
                  <p className="preview-step-subtitle">Choose colors that represent your brand</p>
                </div>

                <div className="color-picker-group">
                  <div>
                    <label className="preview-label">Primary Color</label>
                    <div className="color-input-box">
                      <input
                        type="color"
                        {...form.register("primary_color")}
                        className="color-swatch-picker"
                      />
                      <input
                        value={watch("primary_color")}
                        onChange={(e) => setValue("primary_color", e.target.value)}
                        className="preview-input"
                        style={{ fontFamily: "var(--font-mono)" }}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="preview-label">Secondary Color</label>
                    <div className="color-input-box">
                      <input
                        type="color"
                        {...form.register("secondary_color")}
                        className="color-swatch-picker"
                      />
                      <input
                        value={watch("secondary_color")}
                        onChange={(e) => setValue("secondary_color", e.target.value)}
                        className="preview-input"
                        style={{ fontFamily: "var(--font-mono)" }}
                      />
                    </div>
                  </div>
                </div>

                {/* Color Preview */}
                <div
                  className="color-gradient-preview"
                  style={{
                    background: `linear-gradient(135deg, ${watch("primary_color")}, ${watch("secondary_color")})`,
                  }}
                />

                <div className="preview-buttons-row">
                  <button onClick={handleBack} className="preview-btn secondary">
                    <ArrowLeft className="preview-arrow-icon" /> Back
                  </button>
                  <button onClick={handleNext} className="preview-btn primary">
                    Next: Content <ArrowRight className="preview-arrow-icon" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="preview-step-card"
              >
                <div>
                  <h2 className="preview-step-title">Content</h2>
                  <p className="preview-step-subtitle">Add your about text or let AI generate it</p>
                </div>

                {/* AI Fill Toggle */}
                <div className="preview-ai-toggle-box">
                  <div className="preview-ai-toggle-left">
                    <Sparkles className="preview-sparkle-icon" />
                    <div>
                      <div className="font-semibold text-sm">AI Auto-Fill</div>
                      <div className="text-xs text-muted-foreground">Let AI generate all your website content</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setValue("ai_fill", !watch("ai_fill"))}
                    className={cn("preview-toggle-switch", watch("ai_fill") && "active")}
                  >
                    <div className="preview-toggle-thumb" />
                  </button>
                </div>

                {!watch("ai_fill") && (
                  <div>
                    <label className="preview-label">About Your Business</label>
                    <textarea
                      {...form.register("about")}
                      placeholder="Tell your customers what makes your business special..."
                      rows={5}
                      className="preview-textarea"
                    />
                  </div>
                )}

                <div className="preview-buttons-row">
                  <button onClick={handleBack} className="preview-btn secondary">
                    <ArrowLeft className="preview-arrow-icon" /> Back
                  </button>
                  <button
                    onClick={form.handleSubmit(handleGenerate)}
                    disabled={isGenerating}
                    className="preview-btn primary"
                  >
                    {isGenerating ? (
                      <><Loader2 className="preview-loader-icon animate-spin" /> Generating Preview…</>
                    ) : (
                      <><Eye className="preview-arrow-icon" /> Generate Preview</>
                    )}
                  </button>
                </div>
              </motion.div>
            )}

            {step === 4 && previewSession && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="preview-result-container"
              >
                <div className="preview-step-card text-center">
                  <h2 className="preview-step-title">Your Preview is Ready! 🎉</h2>
                  <p className="preview-step-subtitle">
                    This is a watermarked preview. Purchase to download the full clean version.
                  </p>
                </div>

                {previewSession.preview_image_url && (
                  <div className="preview-image-wrapper">
                    <Image
                      src={previewSession.preview_image_url}
                      alt="Watermarked preview"
                      width={1200}
                      height={750}
                      className="preview-image-el"
                    />
                    {/* Watermark overlay */}
                    <div className="preview-watermark-overlay">
                      <div className="preview-watermark-text">
                        <div>AI SITE STUDIO</div>
                        <div style={{ fontSize: "1.25rem", marginTop: "0.25rem" }}>PREVIEW ONLY</div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="preview-buttons-row">
                  <button onClick={() => { setStep(1); setPreviewSession(null); }} className="preview-btn secondary">
                    Start Over
                  </button>
                  <a
                    href={`/marketplace/${templateId}`}
                    className="preview-btn primary text-center"
                    style={{ textDecoration: "none" }}
                  >
                    Purchase Template
                  </a>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}

export default function PreviewPage() {
  return (
    <Suspense fallback={
      <div className="preview-loading-screen">
        <div className="preview-loading-box">
          <Loader2 className="preview-big-loader animate-spin" />
          <p className="text-muted-foreground text-sm">Loading preview builder...</p>
        </div>
      </div>
    }>
      <PreviewBuilder />
    </Suspense>
  );
}
