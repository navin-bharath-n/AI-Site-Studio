import Navbar from "@/components/layout/Navbar";
import Link from "@/components/Link";
import "./PrivacyPage.css";

const LAST_UPDATED = "30 September 2026";

export default function PrivacyPolicyPage() {
  return (
    <>
      <Navbar />
      <main className="legal-page">
        <div className="legal-container">
          <header className="legal-header">
            <p className="legal-eyebrow">Legal</p>
            <h1 className="legal-title">Privacy Policy</h1>
            <p className="legal-updated">Last updated: {LAST_UPDATED}</p>
          </header>

          <div className="legal-body">
            <p>
              Site Studio ("we", "us", or "our") operates the website available
              at this domain. This Privacy Policy explains what personal data we
              collect, why we collect it, and how we use it when you use the
              Site Studio platform.
            </p>

            <h2>1. Information We Collect</h2>
            <h3>1.1 Account Information</h3>
            <p>
              When you register for an account, we collect your email address,
              a display name, and an encrypted password. If you sign in via a
              third-party OAuth provider (e.g., Google), we receive only the
              profile information that provider makes available — typically your
              name and email address.
            </p>

            <h3>1.2 Usage Data</h3>
            <p>
              We record which templates you view, preview, or download, along
              with timestamps and your IP address. This data is used to improve
              the platform's search relevance and to debug technical issues. We
              do not sell usage data to third parties.
            </p>

            <h3>1.3 Uploaded Content</h3>
            <p>
              If you upload template files as a creator, those files are stored
              on our servers. We may inspect uploaded files automatically as
              part of the code-quality auditing process described in our Terms
              & Conditions.
            </p>

            <h3>1.4 Payment Information</h3>
            <p>
              Payments are processed by a third-party payment provider. We do
              not store your full card number, CVV, or bank account details on
              our servers. We retain only a transaction reference and the amount
              for bookkeeping purposes.
            </p>

            <h2>2. How We Use Your Information</h2>
            <ul>
              <li>To operate and improve the Site Studio platform.</li>
              <li>To authenticate you when you sign in.</li>
              <li>To send transactional emails (e.g., purchase receipts, password reset).</li>
              <li>To detect and prevent fraud or abuse.</li>
              <li>To comply with legal obligations.</li>
            </ul>
            <p>
              We do not use your data to train external AI models, nor do we
              share it with advertisers.
            </p>

            <h2>3. Cookies and Local Storage</h2>
            <p>
              We use session cookies and browser local storage to keep you
              signed in between visits and to remember your preferences (e.g.,
              selected currency). We do not use third-party advertising cookies.
            </p>

            <h2>4. Data Sharing</h2>
            <p>
              We share your data only with service providers that operate
              infrastructure on our behalf (hosting, email delivery, payment
              processing). These providers are contractually obligated to
              process your data only for the purposes we specify.
            </p>
            <p>
              We may disclose your data if required by law, court order, or
              government authority.
            </p>

            <h2>5. Data Retention</h2>
            <p>
              Account data is retained for as long as your account is active.
              If you delete your account, we will erase your personal data
              within 30 days, except where we are legally required to retain
              records (e.g., financial transaction history for accounting
              purposes, which is kept for 7 years).
            </p>

            <h2>6. Your Rights</h2>
            <p>
              Depending on your jurisdiction, you may have the right to:
            </p>
            <ul>
              <li>Access the personal data we hold about you.</li>
              <li>Correct inaccurate data.</li>
              <li>Request deletion of your data ("right to erasure").</li>
              <li>Object to or restrict certain processing activities.</li>
              <li>Export your data in a machine-readable format.</li>
            </ul>
            <p>
              To exercise any of these rights, contact us at the address below.
              We will respond within 30 days.
            </p>

            <h2>7. Security</h2>
            <p>
              We use industry-standard practices to protect your data: HTTPS for
              all data in transit, hashed passwords, and access controls that
              restrict data access to authorised personnel only. No system is
              completely secure; we cannot guarantee absolute security.
            </p>

            <h2>8. Children's Privacy</h2>
            <p>
              Site Studio is not directed at children under the age of 13. We do
              not knowingly collect personal data from children. If you believe
              a child has provided us with personal data, contact us and we will
              delete it.
            </p>

            <h2>9. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. When we do,
              we will update the "Last updated" date at the top of this page. If
              changes are material, we will notify registered users by email.
            </p>

            <h2>10. Contact</h2>
            <p>
              For privacy-related questions or requests, contact us through our{" "}
              <Link href="/contact" className="legal-link">contact page</Link>.
            </p>
          </div>

          <div className="legal-footer-nav">
            <Link href="/terms" className="legal-link">Terms &amp; Conditions</Link>
            <span className="legal-footer-divider">·</span>
            <Link href="/" className="legal-link">Back to Home</Link>
          </div>
        </div>
      </main>
    </>
  );
}
