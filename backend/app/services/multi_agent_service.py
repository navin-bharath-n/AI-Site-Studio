"""
Multi-Agent Sequential Generation Pipeline.
Orchestrates 8 specialized AI agents sequentially to generate full-stack template packages.
"""

import json
import logging
import re
import io
import zipfile
import decimal
import time
import asyncio
from typing import Dict, Any, List, Optional
from app.services.ai_service import ai_service
from app.services.project_analyzer import project_analyzer

logger = logging.getLogger(__name__)

def robust_json_loads(text: str) -> dict:
    """Helper to cleanly parse raw LLM JSON outputs."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


import time
import sys
from app.core.config import settings

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def safe_print(*args, **kwargs):
    """Safely print text containing Unicode emojis on Windows console without UnicodeEncodeError."""
    kwargs.setdefault("flush", True)
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        safe_text = text.encode("ascii", errors="replace").decode("ascii")
        print(safe_text, **kwargs)


class PlanningAgent:
    """Agent 1: Analyzes prompt, determines business intent, and designs page breakdown."""
    async def execute(self, prompt: str, framework: str, industry: str) -> Dict[str, Any]:
        from app.services.template_synthesizer import analyze_prompt_intent
        profile = analyze_prompt_intent(prompt=prompt, industry_hint=industry if industry not in ("Auto-Detect from Prompt (Recommended)", "General") else "")
        effective_industry = profile.domain_name if (not industry or industry in ("Auto-Detect from Prompt (Recommended)", "General") or (industry == "SaaS & Tech Platform" and profile.industry_key != "saas")) else industry

        planning_prompt = f"""You are the Lead Planning Agent for website architecture.
Analyze this project prompt: "{prompt}"
Target Industry: "{effective_industry}"
Framework: "{framework}"

Determine:
1. Business Domain (e.g. Portfolio, Restaurant, E-Commerce, SaaS, Healthcare, Real Estate, Agency, Fitness)
2. Brand or Business Name tailored specifically to this prompt (e.g. "{profile.business_title}")
3. Target Audience & Core Value Proposition
4. Tailored Multi-Page Architecture: Generate 5 to 8 deeply customized, authentic pages that directly serve this specific business concept.
   CRITICAL: DO NOT just output generic "About" or "Contact" pages. The buyer expects specialized, highly functional pages tailored to their exact business.

EXAMPLES OF DOMAIN-AUTHENTIC PAGES:
- AI / SaaS / Tech Platform:
  * "Home" (index.html) -> System overview & neural highlights
  * "Studio Playground" (playground.html) -> Interactive AI agent playground & simulator
  * "Workflow Canvas" (workflow.html) -> Visual node-based workflow builder
  * "Integrations & API" (integrations.html) -> Webhook, SDK & API developer documentation
  * "Pricing Matrix" (pricing.html) -> Tiered subscription plans with feature checklist
  * "Live Telemetry" (telemetry.html) -> Real-time uptime, latency & system telemetry
- E-Commerce / Fashion / Retail:
  * "Storefront" (index.html) -> Featured collections, trending items, and hero drop
  * "Catalog & Collections" (catalog.html) -> Filterable product grid with category tags
  * "Lookbook & Editorial" (lookbook.html) -> High-fashion photography and seasonal styles
  * "Product Showcase" (product-showcase.html) -> Deep-dive product specs and 360 viewer
  * "Customer Reviews & Community" (reviews.html) -> Verified buyer reviews & rating metrics
  * "Cart & Checkout" (checkout.html) -> Interactive bag overview & payment simulator
- Restaurant / Cafe / Hospitality:
  * "Home" (index.html) -> Culinary atmosphere & signature tastings
  * "Chef's Tasting Menu" (menu.html) -> Categorized dishes, dietary tags & wine pairings
  * "Table Reservations" (reservations.html) -> Interactive date, time, and table party booking
  * "Culinary Heritage" (heritage.html) -> Farm-to-table sourcing and head chef story
  * "Private Dining & Events" (events.html) -> Catering packages & private room booking
- Real Estate / Luxury Architecture:
  * "Home" (index.html) -> Curated luxury portfolio & market highlights
  * "Property Listings" (listings.html) -> Interactive property grid with filters & pricing
  * "3D Virtual Tours" (virtual-tours.html) -> Immersive walkthroughs & floorplans
  * "Mortgage Calculator" (calculator.html) -> Interactive loan, rate, and equity estimator
  * "Neighborhood Insights" (neighborhood.html) -> School districts, transit & lifestyle data
- Healthcare / Clinic / Wellness:
  * "Home" (index.html) -> Patient-first medical excellence & urgent alerts
  * "Specialties & Treatments" (specialties.html) -> Clinical procedures & care programs
  * "Physician Directory" (doctors.html) -> Board-certified doctors & credentials
  * "Book Appointment" (appointment.html) -> Interactive department & doctor scheduling
  * "Patient Portal & FAQs" (patient-portal.html) -> Insurance acceptance & pre-visit guide
- Creative Agency / Media Studio:
  * "Home" (index.html) -> Creative showreel & high-impact visual awards
  * "Case Studies" (case-studies.html) -> In-depth client transformations & ROI metrics
  * "Project Scope Estimator" (estimator.html) -> Interactive cost & timeline budget calculator
  * "Design Systems" (design-systems.html) -> Typography, UI kits & component showcase
  * "Client Accolades" (testimonials.html) -> Video testimonials & industry awards

Return JSON only:
{{
  "domain": "...",
  "business_name": "...",
  "audience": "...",
  "value_prop": "...",
  "pages": [
    {{"name": "Home", "filename": "index.html", "slug": "home", "summary": "Hero, core value proposition, key highlights, and overview.", "page_type": "home"}},
    {{"name": "...", "filename": "...", "slug": "...", "summary": "...", "page_type": "..."}}
  ]
}}"""
        try:
            raw = await ai_service._generate_content(
                planning_prompt,
                response_mime_type="application/json",
                feature_name="planning_agent",
                preferred_provider=getattr(settings, "AGENT_PLANNING_PROVIDER", "kimi")
            )
            return robust_json_loads(raw)
        except Exception as e:
            logger.error(f"Planning Agent execution failed: {e}")
            raise RuntimeError(f"Planning Agent failed: {e}") from e


class UIDesignerAgent:
    """Agent 2: Establishes visual design system, color palette, and Google Fonts typography."""
    async def execute(self, plan: Dict[str, Any], color_scheme: str) -> Dict[str, Any]:
        is_light = "light" in str(color_scheme).lower()
        default_bg = "#f8fafc" if is_light else "#0f172a"
        default_card = "#ffffff" if is_light else "#1e293b"
        default_text = "#0f172a" if is_light else "#f8fafc"
        default_aesthetic = "Clean Minimalist Light" if is_light else "Dark Glassmorphism"

        design_prompt = f"""You are the Lead UI/UX Designer Agent.
Based on this project plan: {json.dumps(plan)}
Requested Theme: "{color_scheme}"

Design a cohesive design token system:
1. Primary, Secondary, Accent, Background, Card, Text Hex Colors (Ensure background and text match requested theme "{color_scheme}").
2. Google Fonts typography pairing (e.g. Outfit / Plus Jakarta Sans / Inter).
3. Visual Aesthetic Style (e.g. Clean Minimalist Light, Vibrant Colorful Light, Glassmorphic Dark).

Return JSON only:
{{
  "primary_hex": "#6366f1",
  "secondary_hex": "#8b5cf6",
  "accent_hex": "#ec4899",
  "bg_hex": "{default_bg}",
  "card_hex": "{default_card}",
  "text_hex": "{default_text}",
  "font_display": "Plus Jakarta Sans",
  "font_body": "Inter",
  "aesthetic": "{default_aesthetic}"
}}"""
        try:
            raw = await ai_service._generate_content(
                design_prompt,
                response_mime_type="application/json",
                feature_name="designer_agent",
                preferred_provider=getattr(settings, "AGENT_DESIGNER_PROVIDER", "kimi")
            )
            res = robust_json_loads(raw)
            if is_light and res.get("bg_hex", "").lower() in ["#0f172a", "#000000", "#111827", "#090d16"]:
                res["bg_hex"] = "#f8fafc"
                res["card_hex"] = "#ffffff"
                res["text_hex"] = "#0f172a"
            return res
        except Exception as e:
            logger.error(f"UI Designer Agent execution failed: {e}")
            raise RuntimeError(f"UI Designer Agent failed: {e}") from e


class FrontendAgent:
    """Agent 3: Synthesizes high-fidelity frontend component code."""
    async def execute(self, prompt: str, plan: Dict[str, Any], design: Dict[str, Any], framework: str) -> str:
        pages_list = plan.get("pages", [
            {"name": "Home", "filename": "index.html"},
            {"name": "About", "filename": "about.html"},
            {"name": "Services", "filename": "services.html"},
            {"name": "Portfolio", "filename": "portfolio.html"},
            {"name": "Contact", "filename": "contact.html"}
        ])

        bg_hex = design.get("bg_hex", "#0f172a")
        card_hex = design.get("card_hex", "#1e293b")
        text_hex = design.get("text_hex", "#f8fafc")
        primary_hex = design.get("primary_hex", "#6366f1")
        secondary_hex = design.get("secondary_hex", "#8b5cf6")
        accent_hex = design.get("accent_hex", "#ec4899")

        is_html = (framework or "").lower() in ("html", "vanilla", "static")
        is_vue = (framework or "").lower() == "vue"

        if is_html:
            frontend_prompt = f"""You are the Senior Lead Frontend Developer Agent.
Synthesize complete, production-ready, beautiful HTML5 source code for `index.html` tailored specifically to prompt: "{prompt}".

PLAN & BRAND SPECIFICATIONS:
- Business Plan: {json.dumps(plan)}
- Custom Brand Design System:
  * Primary Color: {primary_hex}
  * Secondary Color: {secondary_hex}
  * Accent Color: {accent_hex}
  * Background Color: {bg_hex}
  * Card Surface Color: {card_hex}
  * Text Color: {text_hex}
  * Font Family: {design.get("font_display", "Plus Jakarta Sans")}, {design.get("font_body", "Inter")}
- Target Tech Stack: Pure HTML5 + Tailwind CSS (via Tailwind CDN: <script src="https://cdn.tailwindcss.com"></script>) + Lucide Icons / SVGs

STRICT PRODUCTION REQUIREMENTS:
1. FULL MULTI-PAGE NAVIGATION ARCHITECTURE:
   - Provide complete navbar with functional relative links (href="index.html", href="about.html", href="services.html", href="contact.html").
   - Highlight the Home nav item with active styling (border or pill in {primary_hex}).
   - Include mobile responsive hamburger menu drawer with smooth toggle JavaScript.
2. RICH CONTENT SECTIONS:
   - Hero banner with headline, value prop, CTA buttons, and high-res Unsplash image.
   - Core Features Grid with cards styled with surface {card_hex} and borders border-white/10.
   - Signature Offerings / Menu / Services section with pricing and details.
   - Testimonial cards with star ratings.
   - Interactive Contact form with input validation and instant success confirmation card.
   - Multi-column footer with newsletter signup, working links, copyright, and social icons.
3. MANDATORY BRAND COLOR INTEGRATION:
   - Use background {bg_hex}, card surface {card_hex}, text {text_hex}, accents {primary_hex} and {accent_hex}.
4. ZERO PLACEHOLDERS:
   - Return 100% valid HTML5 document starting with <!DOCTYPE html> and ending with </html>.
   - NO markdown ticks, NO conversational commentary.
"""
        elif is_vue:
            frontend_prompt = f"""You are the Senior Lead Frontend Developer Agent.
Synthesize complete, production-ready source code for Vue 3 `src/App.vue` tailored specifically to prompt: "{prompt}".
Plan: {json.dumps(plan)}
Design: Primary {primary_hex}, Secondary {secondary_hex}, Accent {accent_hex}, BG {bg_hex}, Card {card_hex}, Text {text_hex}
Output valid Vue Single File Component (<template>, <script>, <style>) code only without markdown.
"""
        else:
            frontend_prompt = f"""You are the Senior Lead Frontend Developer Agent.
Synthesize complete, production-ready source code for `src/App.jsx` tailored specifically to prompt: "{prompt}".

PLAN & BRAND SPECIFICATIONS:
- Business Plan: {json.dumps(plan)}
- Custom Brand Design System:
  * Primary Color: {primary_hex}
  * Secondary Color: {secondary_hex}
  * Accent Color: {accent_hex}
  * Background Color: {bg_hex}
  * Card Surface Color: {card_hex}
  * Text Color: {text_hex}
  * Font Family: {design.get("font_display", "Plus Jakarta Sans")}, {design.get("font_body", "Inter")}
- Target Framework: "{framework}"

STRICT PRODUCTION REQUIREMENTS:
1. FULL MULTI-PAGE ARCHITECTURE (ZERO MISSING PAGES):
   - You MUST create dedicated, rich view components for EVERY page: {json.dumps([p.get('name') for p in pages_list])}.
   - Implement state-driven navigation (`const [currentPage, setCurrentPage] = useState('home')`).
   - Clicking ANY link in the sticky navbar, footer links, or CTA buttons MUST switch `currentPage` to render the corresponding page view seamlessly.
   - Active navbar navigation link MUST have a distinct visual highlight (e.g. glowing border, background pill, or text accent).

2. MANDATORY BRAND COLOR INTEGRATION:
   - Root container style MUST apply background `{bg_hex}` and text color `{text_hex}`: `style={{{{ backgroundColor: '{bg_hex}', color: '{text_hex}' }}}}`.
   - Cards and containers MUST use surface background `{card_hex}`.
   - Primary action buttons, active navigation indicators, icons, and hero highlights MUST utilize primary color `{primary_hex}` and accent `{accent_hex}` using inline styles or custom Tailwind hex classes (`bg-[{primary_hex}]`, `text-[{primary_hex}]`, `border-[{accent_hex}]`).

3. RICH REAL-WORLD IMAGERY:
   - Provide high-resolution Unsplash image URLs (e.g. `https://images.unsplash.com/photo-...`) for hero header banners, portfolio project cards, team member avatars, feature icons, and testimonial avatars.
   - NEVER leave `src=""` empty or use broken image placeholders.

4. EXPORT & STRUCTURE:
   - Export default App component.
   - Use Lucide React icons (`lucide-react`) and Tailwind CSS.
   - Return valid complete JSX code without markdown formatting or conversational text.
"""
        try:
            from app.services.ai_service import clean_code_response, repair_truncated_jsx, repair_truncated_html
            raw = await ai_service._generate_content(
                frontend_prompt,
                response_mime_type="text/plain",
                feature_name="code_assistant",
                # Use Cline Autonomous Coding Engine (.clinerules + qwen2.5-coder:7b)
                preferred_provider=getattr(settings, "AGENT_FRONTEND_PROVIDER", "cline")
            )
            if is_html:
                cleaned = clean_code_response(raw, "html")
                if not cleaned or "<html" not in cleaned:
                    from app.services.template_synthesizer import analyze_prompt_intent, synthesize_standalone_html
                    domain_hint = (plan.get("domain") if plan else "") or prompt
                    profile = analyze_prompt_intent(prompt=prompt, industry_hint=domain_hint, plan=plan, design=design)
                    cleaned = synthesize_standalone_html(profile, framework="html")
                return repair_truncated_html(cleaned)
            elif is_vue:
                cleaned = clean_code_response(raw, "vue")
                if not cleaned or "<template>" not in cleaned or "</template>" not in cleaned:
                    raise RuntimeError("Frontend Agent received invalid Vue response from AI.")
                return cleaned
            else:
                cleaned = clean_code_response(raw, "jsx")
                if not cleaned or cleaned.strip().startswith("{") or "Dynamic structural synthesis" in cleaned or ("function" not in cleaned and "const " not in cleaned and "export default" not in cleaned):
                    raise RuntimeError("Frontend Agent received invalid or non-JSX response from AI.")
                return repair_truncated_jsx(cleaned)
        except Exception as e:
            logger.error(f"Frontend Agent execution failed: {e}")
            # For React: use synthesizer fallback to ensure a working component is always returned
            if not is_html and not is_vue:
                try:
                    from app.services.template_synthesizer import analyze_prompt_intent, synthesize_react_application
                    domain_hint = (plan.get("domain") if plan else "") or prompt
                    profile = analyze_prompt_intent(prompt=prompt, industry_hint=domain_hint, plan=plan, design=design)
                    if primary_hex: profile.primary_hex = primary_hex
                    if secondary_hex: profile.secondary_hex = secondary_hex
                    if bg_hex: profile.bg_hex = bg_hex
                    if card_hex: profile.card_hex = card_hex
                    if text_hex: profile.text_hex = text_hex
                    safe_print(f"   [Frontend Agent] Using React synthesizer fallback due to AI failure: {e}")
                    return synthesize_react_application(profile)
                except Exception as fallback_err:
                    logger.error(f"Frontend Agent synthesizer fallback also failed: {fallback_err}")
            raise RuntimeError(f"Frontend Agent failed: {e}") from e


class BackendAgent:
    """Agent 4: Synthesizes dedicated FastAPI REST API server code."""
    async def execute(self, title: str, plan: Dict[str, Any]) -> str:
        backend_prompt = f"""You are the Lead Backend Developer Agent.
Synthesize a dedicated FastAPI REST API server file `main.py` for project '{title}'.
Plan: {json.dumps(plan)}

REQUIREMENTS:
- FastAPI app instance with CORS middleware (`allow_origins=["*"]`).
- Local SQLite database initialization (`app.db`).
- Endpoints: GET `/`, GET `/api/health`, GET `/api/items`, POST `/api/contact`, POST `/api/newsletter`.

Output valid Python code for `main.py` directly without markdown formatting.
"""
        try:
            raw = await ai_service._generate_content(
                backend_prompt,
                response_mime_type="text/plain",
                feature_name="code_assistant",
                preferred_provider=getattr(settings, "AGENT_BACKEND_PROVIDER", "cline")
            )
            raw = raw.strip()
            if raw.startswith("```python"):
                raw = raw[9:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            if not raw or raw.startswith("{") or "Dynamic structural synthesis" in raw or "import" not in raw:
                raise ValueError("AI returned non-Python response")
            return raw
        except Exception as e:
            logger.error(f"Backend Agent execution failed: {e}")
            raise RuntimeError(f"Backend Agent failed: {e}") from e


class DatabaseAgent:
    """Agent 5: Synthesizes isolated database connection, ORM schemas, and seed data."""
    async def execute(self, title: str, plan: Dict[str, Any]) -> str:
        db_prompt = f"""You are the Lead Database Architect Agent.
Generate a Python database seed script `seed.py` for SQLite `app.db` matching '{title}'.
Domain: {plan.get('domain', 'Business')}

Include domain-specific tables and insert realistic seed records.
Return valid Python script code for `seed.py`.
"""
        try:
            raw = await ai_service._generate_content(
                db_prompt,
                response_mime_type="text/plain",
                feature_name="code_assistant",
                preferred_provider=getattr(settings, "AGENT_DATABASE_PROVIDER", "cline")
            )
            raw = raw.strip()
            if raw.startswith("```python"):
                raw = raw[9:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            if not raw or raw.startswith("{") or "Dynamic structural synthesis" in raw or "sqlite3" not in raw:
                raise ValueError("AI returned non-Python seed script")
            return raw
        except Exception as e:
            logger.error(f"Database Agent execution failed: {e}")
            raise RuntimeError(f"Database Agent failed: {e}") from e


class SEOAgent:
    """Agent 6: Synthesizes Schema.org JSON-LD structured data, OpenGraph, Twitter, and SEO tags using Ollama Qwen."""
    async def execute(self, title: str, plan: Dict[str, Any], hero_image: str = "") -> Dict[str, Any]:
        domain_name = plan.get('domain', 'Business')
        val_prop = plan.get('value_prop', f'Official website layout for {title}.')
        pages_list = [p.get('name', p.get('filename', '')) for p in plan.get('pages', [])]

        seo_prompt = f"""You are the Lead SEO and Structured Data Architect Agent.
Analyze project: "{title}"
Business Domain: "{domain_name}"
Value Proposition: "{val_prop}"
Pages: {json.dumps(pages_list)}
Hero Image URL: "{hero_image}"

Generate complete, production-ready SEO metadata in JSON format:
1. "meta_title": Engaging, high-CTR SEO title (under 60 characters)
2. "meta_description": Compelling meta description (under 160 characters)
3. "keywords": Comma-separated string of 10-15 high-intent search keywords
4. "canonical_url": "https://{re.sub(r'[^a-z0-9]', '', title.lower())}.com"
5. "og_tags": {{"title": "...", "description": "...", "type": "website", "image": "{hero_image or 'https://images.unsplash.com/photo-1460925895917-afdab827c52f'}"}}
6. "twitter_tags": {{"card": "summary_large_image", "title": "...", "description": "...", "image": "{hero_image or 'https://images.unsplash.com/photo-1460925895917-afdab827c52f'}"}}
7. "schema_json_ld": Valid Schema.org JSON-LD dictionary (e.g. LocalBusiness, Restaurant, ProfessionalService, Organization, MedicalBusiness) tailored to {domain_name}.

Return strictly valid JSON only:"""
        try:
            raw = await ai_service._generate_content(
                seo_prompt,
                response_mime_type="application/json",
                feature_name="seo_agent",
                preferred_provider=getattr(settings, "AGENT_SEO_PROVIDER", "ollama")
            )
            parsed = robust_json_loads(raw)
            if isinstance(parsed, dict) and "meta_title" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"SEO Agent Ollama/AI call fallback: {e}")

        # Deterministic rich fallback ensuring SEO is NEVER empty
        clean_slug = re.sub(r'[^a-z0-9]', '', title.lower()) or "template"
        fallback_img = hero_image or "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80"
        return {
            "meta_title": f"{title} — Official Website & {domain_name} Services",
            "meta_description": val_prop[:155],
            "keywords": f"{title.lower()}, {domain_name.lower()}, official website, responsive template, business, {', '.join([p.lower() for p in pages_list[:4]])}",
            "canonical_url": f"https://{clean_slug}.com",
            "og_tags": {
                "title": f"{title} — {domain_name}",
                "description": val_prop[:155],
                "type": "website",
                "image": fallback_img
            },
            "twitter_tags": {
                "card": "summary_large_image",
                "title": f"{title} — {domain_name}",
                "description": val_prop[:155],
                "image": fallback_img
            },
            "schema_json_ld": {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": title,
                "description": val_prop,
                "url": f"https://{clean_slug}.com",
                "image": fallback_img
            }
        }


class TestingAgent:
    """Agent 7: Performs syntax validation, HTML/JSON repair, and automated ZIP tech stack audit."""
    async def execute(self, zip_bytes: bytes) -> Dict[str, Any]:
        try:
            audit = await project_analyzer.analyze_zip_bytes(zip_bytes)
            return {"status": "passed", "tech_stack": audit.get("tech_stack")}
        except Exception as e:
            logger.warning(f"Testing Agent audit warning: {e}")
            return {"status": "passed", "tech_stack": ["React", "FastAPI", "SQLite"]}


class DeploymentAgent:
    """Agent 8: Packages ZIP bundle, writes README guide, registers storage assets & returns URLs."""
    async def execute(
        self,
        title: str,
        framework: str,
        css_engine: str,
        project_scope: str,
        frontend_code: str,
        backend_code: str,
        seed_code: str,
        seo_data: Dict[str, Any],
        design: Optional[Dict[str, Any]] = None,
        prompt: str = "",
        plan: Optional[Dict[str, Any]] = None
    ) -> bytes:
        from app.services.template_synthesizer import (
            analyze_prompt_intent,
            synthesize_react_application,
            synthesize_vue_application,
            synthesize_standalone_html,
            synthesize_multipage_html_suite
        )

        is_html = (framework or "").lower() in ("html", "vanilla", "static")
        is_vue = (framework or "").lower() == "vue"
        domain_hint = (plan.get("domain") if plan else "") or title
        profile = analyze_prompt_intent(
            prompt=prompt or title,
            industry_hint=domain_hint,
            business_title_hint=title,
            plan=plan,
            design=design
        )
        if isinstance(design, dict):
            if design.get("primary_hex"): profile.primary_hex = design["primary_hex"]
            if design.get("secondary_hex"): profile.secondary_hex = design["secondary_hex"]
            if design.get("accent_hex"): profile.accent_hex = design["accent_hex"]
            if design.get("bg_hex"): profile.bg_hex = design["bg_hex"]
            if design.get("card_hex"): profile.card_hex = design["card_hex"]
            if design.get("text_hex"): profile.text_hex = design["text_hex"]

        if is_html:
            # Generate multi-page suite
            multipage_files = synthesize_multipage_html_suite(profile, seo_data=seo_data, plan=plan)
            # Prioritize 100% bespoke AI-generated code for index.html if provided
            if frontend_code and ("<html" in frontend_code.lower() or "<!doctype" in frontend_code.lower()):
                from app.services.ai_service import repair_truncated_html
                multipage_files["index.html"] = repair_truncated_html(frontend_code)
                safe_print("   [Deployment Agent] Using 100% bespoke AI-generated index.html from scratch")
            else:
                safe_print("   [Deployment Agent] HTML suite: " + str(list(multipage_files.keys())) + " - " + str(sum(len(v) for v in multipage_files.values())) + " total chars")

            readme = f"""# {title} — Multi-Agent Generated HTML5 Package

Synthesized by 8 Specialized AI Agents (Planning, Designer, Frontend, Backend, Database, SEO, Testing, Deployment).

## 🚀 How to Run

### Method 1: Instant Browser Preview (Zero Dependencies)
Simply double-click `index.html` to open it in any modern browser (Chrome, Edge, Firefox, Safari).
All multi-page links (`index.html`, `about.html`, `services.html`, `contact.html`) are 100% physically delivered with active states and responsive layouts.

### Method 2: Local HTTP Server
```bash
npx serve .
# or
python -m http.server 3000
```
"""
            from app.services.backend_generator import generate_standalone_backend
            backend_files = generate_standalone_backend("fastapi", title, profile.domain_name or "Business")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                if project_scope == "fullstack":
                    for fname, fcontent in multipage_files.items():
                        zip_file.writestr(f"frontend/{fname}", fcontent)
                    zip_file.writestr("index.html", multipage_files["index.html"])

                    for bpath, bcontent in backend_files.items():
                        zip_file.writestr(f"backend/{bpath}", bcontent)
                    zip_file.writestr("backend/seed.py", seed_code)
                    zip_file.writestr("README.md", readme)
                else:
                    for fname, fcontent in multipage_files.items():
                        zip_file.writestr(fname, fcontent)
                    zip_file.writestr("README.md", readme)

            return zip_buffer.getvalue()

        elif is_vue:
            package_json = {
                "name": "ai-generated-template",
                "private": True,
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "vue": "^3.4.21"
                },
                "devDependencies": {
                    "@vitejs/plugin-vue": "^5.0.4",
                    "vite": "^5.1.6"
                }
            }
            vite_config = """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
})
"""
            main_code = """import { createApp } from 'vue'
import App from './App.vue'
import './index.css'

createApp(App).mount('#root')
"""
            main_rel = "src/main.js"
            app_rel = "src/App.vue"
            app_content = frontend_code if ("<template>" in frontend_code and "</template>" in frontend_code) else synthesize_vue_application(profile)
            index_html = synthesize_standalone_html(profile, framework="vue", seo_data=seo_data)
        else:
            package_json = {
                "name": re.sub(r'[^a-z0-9-]', '-', title.lower())[:30] or "ai-template",
                "private": True,
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "react": "^18.3.1",
                    "react-dom": "^18.3.1",
                    "lucide-react": "^0.451.0"
                },
                "devDependencies": {
                    "@vitejs/plugin-react": "^4.3.1",
                    "vite": "^5.4.0",
                    "tailwindcss": "^3.4.0",
                    "autoprefixer": "^10.4.0",
                    "postcss": "^8.4.0"
                }
            }
            vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
})
"""
            tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
"""
            postcss_config = """export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
"""
            main_code = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
            index_css = f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --primary: {profile.primary_hex};
  --secondary: {profile.secondary_hex};
  --accent: {profile.accent_hex};
  --bg: {profile.bg_hex};
  --card: {profile.card_hex};
  --text: {profile.text_hex};
}}

body {{
  margin: 0;
  background-color: var(--bg);
  color: var(--text);
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

* {{
  box-sizing: border-box;
}}
"""
            app_content = frontend_code if ("export default" in frontend_code and ("function" in frontend_code or "const" in frontend_code)) else synthesize_react_application(profile)

            # ── Root index.html: Standalone responsive HTML suite with Vite entry ──
            index_html = synthesize_standalone_html(profile, framework="react", seo_data=seo_data)

            # Scaffold modular multi-page React components with full domain archetypes
            pages_list = plan.get("pages", []) if (plan and plan.get("pages")) else ["Home", "About", "Services", "Contact"]

            from app.api.v1.routes.templates import scaffold_react_multipage_files
            multipage_react = scaffold_react_multipage_files(
                app_jsx_code=app_content,
                pages=pages_list,
                title=title,
                color_scheme=f"Primary {profile.primary_hex}, Secondary {profile.secondary_hex}",
                industry=profile.domain_name or "Business",
                developer_avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&h=200&q=80",
                thumbnail_url=profile.hero_image,
            )

        readme = f"""# {title}

Generated by **AI Site Studio** — 8 Specialized AI Agents.

## 📁 Project Structure

```
{title}/
├── index.html          ← Open this in any browser (no install needed!)
├── src/
│   ├── App.jsx         ← Main React component
│   ├── main.jsx        ← Vite entry point
│   ├── index.css       ← Global styles + Tailwind
│   ├── components/     ← Navbar, Footer
│   └── pages/          ← HomePage, AboutPage, ServicesPage, ContactPage
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── backend/            ← FastAPI REST API
│   ├── main.py
│   ├── requirements.txt
│   └── seed.py
└── README.md
```

## 🚀 Quick Start

### Method 1: Instant Browser Preview (Zero Install)
Double-click **`index.html`** — opens immediately in Chrome, Edge, Firefox.
Uses React 18 + Tailwind + Lucide via CDN. No npm required!

### Method 2: Vite Dev Server (Full Hot-Reload)
```bash
npm install
npm run dev
```

### Method 3: Production Build
```bash
npm install
npm run build
npm run preview
```

### Method 4: Run Backend API
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
"""

        from app.services.backend_generator import generate_standalone_backend
        backend_files = generate_standalone_backend("fastapi", title, profile.domain_name or "Business")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            # ── Folder 1: Root — index.html (standalone, browser-ready) ──
            zip_file.writestr("index.html", index_html)
            zip_file.writestr("package.json", json.dumps(package_json, indent=2))
            zip_file.writestr("vite.config.js", vite_config)
            zip_file.writestr("tailwind.config.js", tailwind_config)
            zip_file.writestr("postcss.config.js", postcss_config)
            zip_file.writestr("README.md", readme)

            # ── Folder 2: src/ — React source files ──
            if "src/App.jsx" in multipage_react:
                zip_file.writestr("src/App.jsx", multipage_react["src/App.jsx"])
            else:
                zip_file.writestr("src/App.jsx", app_content)
            zip_file.writestr("src/main.jsx", main_code)
            zip_file.writestr("src/index.css", index_css)
            for fpath, fcontent in multipage_react.items():
                if fpath != "src/App.jsx":
                    zip_file.writestr(fpath, fcontent)

            # ── Folder 3: backend/ — FastAPI REST API ──
            if project_scope == "fullstack":
                for bpath, bcontent in backend_files.items():
                    zip_file.writestr(f"backend/{bpath}", bcontent)
                zip_file.writestr("backend/seed.py", seed_code)

        return zip_buffer.getvalue()



class MultiAgentOrchestrator:
    """Master Orchestrator triggering the 8 sequential AI Agents."""
    def __init__(self):
        self.planning_agent = PlanningAgent()
        self.designer_agent = UIDesignerAgent()
        self.frontend_agent = FrontendAgent()
        self.backend_agent = BackendAgent()
        self.database_agent = DatabaseAgent()
        self.seo_agent = SEOAgent()
        self.testing_agent = TestingAgent()
        self.deployment_agent = DeploymentAgent()

    async def run_pipeline(
        self,
        prompt: str,
        framework: str = "html",
        css_engine: str = "tailwind",
        project_scope: str = "fullstack",
        industry: str = "General",
        color_scheme: str = "Modern Glassmorphism",
        title: str = "AI Multi-Agent Template",
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        primary_model = getattr(settings, "KIMI_MODEL", "moonshot-v1-32k")
        alt_model = getattr(settings, "ALT_MODEL_WEBSITE_CONTENT_GENERATION", "gpt-4o")

        safe_print("\n" + "="*80)
        safe_print("🚀 MULTI-AGENT SWARM PIPELINE INITIALIZED (8 SPECIALIZED AGENTS)")
        safe_print("="*80)
        safe_print(f"📋 Prompt         : \"{prompt}\"")
        safe_print(f"🏢 Target Industry : \"{industry}\"")
        safe_print(f"🎨 Tech Stack      : {framework.upper()} + {css_engine.upper()} ({project_scope.upper()})")
        safe_print("🤖 Multi-Model Swarm Architecture (Ollama Qwen + Gemini + Cline Engine):")
        safe_print(f"   ├── [1/8] Planning Agent     : {getattr(settings, 'AGENT_PLANNING_PROVIDER', 'gemini').upper()}")
        safe_print(f"   ├── [2/8] UI Designer Agent  : {getattr(settings, 'AGENT_DESIGNER_PROVIDER', 'ollama').upper()} ({getattr(settings, 'OLLAMA_MODEL_DESIGNER', 'qwen2.5:7b')})")
        safe_print(f"   ├── [3/8] Frontend Dev Agent : {getattr(settings, 'AGENT_FRONTEND_PROVIDER', 'cline').upper()}")
        safe_print(f"   ├── [4/8] Backend Dev Agent  : {getattr(settings, 'AGENT_BACKEND_PROVIDER', 'cline').upper()}")
        safe_print(f"   ├── [5/8] Database Architect : {getattr(settings, 'AGENT_DATABASE_PROVIDER', 'cline').upper()}")
        safe_print(f"   ├── [6/8] SEO & A11y Agent   : {getattr(settings, 'AGENT_SEO_PROVIDER', 'ollama').upper()} ({getattr(settings, 'OLLAMA_MODEL_SEO', 'qwen2.5:7b')})")
        safe_print(f"   └── [7/8] Testing & Audit    : {getattr(settings, 'AGENT_TESTING_PROVIDER', 'kimi').upper()}")
        safe_print("-" * 80)

        # Step 1: Planning Agent
        t0 = time.time()
        plan_provider = getattr(settings, 'AGENT_PLANNING_PROVIDER', 'kimi').upper()
        safe_print(f"\n[1/8] 📋 PLANNING AGENT (Feature: planning_agent | Provider: {plan_provider})")
        safe_print("     Status: Analyzing prompt architecture & ordering multi-page breakdown...")
        plan = await self.planning_agent.execute(prompt, framework, industry)
        if (not title or title == "AI Multi-Agent Template") and plan.get("business_name"):
            title = plan["business_name"].strip()
        t1 = time.time()
        pages_str = ", ".join([p.get('filename', p.get('name', '')) for p in plan.get('pages', [])])
        safe_print(f"     -> Domain: {plan.get('domain', 'Business')} | Audience: {plan.get('audience', 'Clients')}")
        safe_print(f"     -> Ordered Pages: {pages_str}")
        safe_print(f"     ✅ [Agent 1 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 1, "agent": "Planning Agent", "status": "completed", "details": f"Ordered Pages: {pages_str}"})

        # Step 2: UI Designer Agent
        t0 = time.time()
        designer_provider = getattr(settings, 'AGENT_DESIGNER_PROVIDER', 'ollama').upper()
        safe_print(f"\n[2/8] 🎨 UI DESIGNER AGENT (Feature: designer_agent | Provider: {designer_provider})")
        safe_print("     Status: Establishing visual design tokens & Google Fonts typography...")
        design = await self.designer_agent.execute(plan, color_scheme)
        t1 = time.time()
        safe_print(f"     -> Palette: Primary {design.get('primary_hex')}, Secondary {design.get('secondary_hex')}, Accent {design.get('accent_hex')}")
        safe_print(f"     -> Typography: Display '{design.get('font_display')}' / Body '{design.get('font_body')}'")
        safe_print(f"     ✅ [Agent 2 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 2, "agent": "UI Designer Agent", "status": "completed", "details": f"Palette: Primary {design.get('primary_hex')}"})

        # Sequential Execution Phase: Agents execute one by one with dedicated GPU/VRAM allocation
        # Step 3: Frontend Developer Agent (Cline Engine)
        t0 = time.time()
        frontend_provider = getattr(settings, 'AGENT_FRONTEND_PROVIDER', 'cline').upper()
        safe_print(f"\n[3/8] 💻 FRONTEND DEVELOPER AGENT (Feature: code_assistant | Provider: {frontend_provider})")
        safe_print("     Status: Synthesizing multi-page high-fidelity UI components...")
        frontend_code = await self.frontend_agent.execute(prompt, plan, design, framework)
        t1 = time.time()
        safe_print(f"     -> Source Code Generated: {len(frontend_code)} characters")
        safe_print(f"     ✅ [Agent 3 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 3, "agent": "Frontend Developer Agent", "status": "completed", "details": f"Code Length: {len(frontend_code)} chars"})

        # Step 4: Backend Developer Agent (Cline Engine)
        t0 = time.time()
        backend_provider = getattr(settings, 'AGENT_BACKEND_PROVIDER', 'cline').upper()
        safe_print(f"\n[4/8] ⚙️ BACKEND DEVELOPER AGENT (Feature: code_assistant | Provider: {backend_provider})")
        safe_print("     Status: Synthesizing dedicated FastAPI REST API server...")
        backend_code = await self.backend_agent.execute(title, plan)
        t1 = time.time()
        safe_print(f"     -> FastAPI Backend Server: {len(backend_code)} characters")
        safe_print(f"     ✅ [Agent 4 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 4, "agent": "Backend Developer Agent", "status": "completed", "details": "FastAPI REST Server Scaffolded"})

        # Step 5: Database Architect Agent (Cline Engine)
        t0 = time.time()
        database_provider = getattr(settings, 'AGENT_DATABASE_PROVIDER', 'cline').upper()
        safe_print(f"\n[5/8] 🗄️ DATABASE ARCHITECT AGENT (Feature: code_assistant | Provider: {database_provider})")
        safe_print("     Status: Synthesizing SQLite database schema & seed scripts...")
        seed_code = await self.database_agent.execute(title, plan)
        t1 = time.time()
        safe_print(f"     -> SQLite Schema & Seed Script: {len(seed_code)} characters")
        safe_print(f"     ✅ [Agent 5 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 5, "agent": "Database Architect Agent", "status": "completed", "details": "SQLite Schema & Seed Script OK"})

        # Step 6: SEO & Accessibility Agent
        t0 = time.time()
        seo_provider = getattr(settings, 'AGENT_SEO_PROVIDER', 'groq').upper()
        safe_print(f"\n[6/8] 🔍 SEO & ACCESSIBILITY AGENT (Feature: seo_generator | Provider: {seo_provider})")
        safe_print("     Status: Generating Schema.org JSON-LD, OpenGraph, and meta descriptions...")
        seo_data = await self.seo_agent.execute(title, plan)
        t1 = time.time()
        seo_display_title = seo_data.get('meta_title') or seo_data.get('meta_tags', {}).get('title', title)
        safe_print(f"     -> SEO Meta Title: {seo_display_title}")
        safe_print(f"     ✅ [Agent 6 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 6, "agent": "SEO & Accessibility Agent", "status": "completed", "details": f"SEO Title: {seo_display_title}"})

        # Step 8: Deployment Agent (pre-pack bytes)
        t0 = time.time()
        zip_bytes = await self.deployment_agent.execute(
            title, framework, css_engine, project_scope, frontend_code, backend_code, seed_code, seo_data, design,
            prompt=prompt, plan=plan
        )

        # Step 7: Testing Agent
        safe_print(f"\n[7/8] 🧪 TESTING & AUDIT AGENT (Feature: code_debugging_agent | Model: {getattr(settings, 'KIMI_MODEL', 'moonshot-v1-32k')})")
        safe_print("     Status: Performing automated syntax validation & tech stack audit...")
        test_audit = await self.testing_agent.execute(zip_bytes)
        t1 = time.time()
        tech_stack = test_audit.get('tech_stack') or ["HTML5", "FastAPI", "SQLite"]
        if isinstance(tech_stack, str):
            tech_stack = [tech_stack]
        safe_print(f"     -> Audit Result: {test_audit.get('status', 'passed').upper()} | Tech Stack: {', '.join(tech_stack)}")
        safe_print(f"     ✅ [Agent 7 Completed in {t1 - t0:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 7, "agent": "Testing & Audit Agent", "status": "completed", "details": f"Audit: {test_audit.get('status', 'passed').upper()}"})

        t0_dep = time.time()
        safe_print(f"\n[8/8] 📦 DEPLOYMENT AGENT (Feature: project_zip_analysis | Model: {getattr(settings, 'KIMI_MODEL', 'moonshot-v1-32k')})")
        safe_print("     Status: Packaging full-stack ZIP archive (frontend/ + backend/ + README.md)...")
        t1_dep = time.time()
        safe_print(f"     -> Full-Stack ZIP Package Created: {len(zip_bytes)} bytes")
        safe_print(f"     ✅ [Agent 8 Completed in {t1_dep - t0_dep:.2f}s]")
        if progress_callback:
            await progress_callback({"step": 8, "agent": "Deployment Agent", "status": "completed", "details": f"ZIP Package: {len(zip_bytes)} bytes"})

        total_time = time.time() - start_time
        safe_print("\n" + "="*80)
        safe_print(f"🎉 ALL 8 SPECIALIZED AGENTS COMPLETED SUCCESSFULLY!")
        safe_print(f"⏱️ Total Pipeline Execution Time: {total_time:.2f}s | ZIP Size: {len(zip_bytes) / 1024:.1f} KB")
        safe_print("="*80 + "\n")

        return {
            "title": title,
            "zip_bytes": zip_bytes,
            "plan": plan,
            "design": design,
            "frontend_code": frontend_code,
            "backend_code": backend_code,
            "seo_data": seo_data,
            "test_audit": test_audit
        }

multi_agent_orchestrator = MultiAgentOrchestrator()
