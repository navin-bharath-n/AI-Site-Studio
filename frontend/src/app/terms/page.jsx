import Navbar from "@/components/layout/Navbar";
import Link from "@/components/Link";
import "../privacy/PrivacyPage.css";

const LAST_UPDATED = "30 September 2026";

export default function TermsPage() {
  return (
    <>
      <Navbar />
      <main className="legal-page">
        <div className="legal-container">
          <header className="legal-header">
            <p className="legal-eyebrow">Legal</p>
            <h1 className="legal-title">Terms &amp; Conditions</h1>
            <p className="legal-updated">Last updated: {LAST_UPDATED}</p>
          </header>

          <div className="legal-body">
            <p>
              Please read these Terms &amp; Conditions ("Terms") carefully
              before using Site Studio. By accessing or using Site Studio you
              agree to be bound by these Terms. If you disagree with any part of
              the Terms, do not use the platform.
            </p>

            <h2>1. Definitions</h2>
            <ul>
              <li><strong>"Platform"</strong> — The Site Studio website and all associated tools.</li>
              <li><strong>"User"</strong> — Any person who accesses the Platform, with or without an account.</li>
              <li><strong>"Creator"</strong> — A User who uploads templates to the Platform.</li>
              <li><strong>"Template"</strong> — A website source-code package made available via the Platform.</li>
              <li><strong>"Content"</strong> — Any text, images, files, or data submitted by a User.</li>
            </ul>

            <h2>2. Eligibility</h2>
            <p>
              You must be at least 13 years old to use Site Studio. By using
              the Platform you confirm that you meet this requirement. If you
              are using the Platform on behalf of a company, you confirm you
              have authority to bind that company to these Terms.
            </p>

            <h2>3. Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your
              account credentials and for all activity that occurs under your
              account. Notify us immediately if you become aware of any
              unauthorised use of your account.
            </p>
            <p>
              We reserve the right to suspend or terminate accounts that violate
              these Terms without notice.
            </p>

            <h2>4. Template Licenses</h2>
            <h3>4.1 Templates You Download</h3>
            <p>
              Unless a Template's listing specifies a different license, you
              are granted a non-exclusive, worldwide, royalty-free license to
              use, modify, and deploy the Template for any personal or
              commercial project. You may not redistribute the Template as a
              standalone template product or list it on another marketplace
              without the Creator's written permission.
            </p>

            <h3>4.2 Templates You Upload (Creators)</h3>
            <p>
              By uploading a Template you confirm that you own or have the right
              to distribute all code, assets, and third-party libraries it
              contains. You grant Site Studio a non-exclusive license to display,
              preview, and distribute the Template to Users.
            </p>
            <p>
              You remain the owner of your Template. Site Studio does not claim
              intellectual property rights over your uploads.
            </p>

            <h2>5. Prohibited Conduct</h2>
            <p>You agree not to:</p>
            <ul>
              <li>Upload malicious code, malware, or scripts designed to harm Users.</li>
              <li>Upload content that infringes third-party intellectual property rights.</li>
              <li>Use the Platform to send spam or unsolicited communications.</li>
              <li>Attempt to gain unauthorised access to other accounts or platform infrastructure.</li>
              <li>Scrape, crawl, or systematically download Platform content without written permission.</li>
              <li>Impersonate another person or organisation.</li>
              <li>Use the Platform in any way that violates applicable laws or regulations.</li>
            </ul>

            <h2>6. Content Moderation</h2>
            <p>
              Uploaded Templates are subject to automated code analysis and
              manual review. We reserve the right to remove any Template or
              content that violates these Terms, is illegal, or that we deem
              harmful — at our sole discretion, with or without notice.
            </p>

            <h2>7. Payments and Refunds</h2>
            <p>
              Browsing and downloading templates is currently free. If paid
              plans or per-template purchases are introduced, pricing will be
              displayed clearly before any charge is made.
            </p>
            <p>
              Unless otherwise stated, all transactions are non-refundable once
              a download has been delivered. If you believe a refund is
              warranted due to a technical issue on our end, contact us within
              7 days of purchase.
            </p>

            <h2>8. Payouts to Creators</h2>
            <p>
              If Site Studio operates a revenue-share programme, payout terms
              (minimum balance, payment schedule, currency) will be documented
              separately in the Creator Agreement. We reserve the right to
              withhold payouts in cases of suspected fraud or policy violation
              pending investigation.
            </p>

            <h2>9. Disclaimer of Warranties</h2>
            <p>
              Site Studio is provided "as is" and "as available" without
              warranty of any kind. We do not warrant that the Platform will be
              uninterrupted, error-free, or that templates will be free of
              defects. Your use of the Platform and any downloaded templates is
              at your own risk.
            </p>

            <h2>10. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by applicable law, Site Studio
              and its operators shall not be liable for any indirect, incidental,
              special, consequential, or punitive damages arising from your use
              of the Platform or any Template, even if we have been advised of
              the possibility of such damages.
            </p>
            <p>
              Our total aggregate liability to you for any claims arising under
              these Terms shall not exceed the amount you paid to us (if any) in
              the 12 months preceding the claim.
            </p>

            <h2>11. Third-Party Links and Services</h2>
            <p>
              The Platform may link to third-party websites or integrate
              third-party services. We are not responsible for the content,
              privacy practices, or availability of those third-party services.
            </p>

            <h2>12. Changes to These Terms</h2>
            <p>
              We may update these Terms at any time. When we do, we will update
              the "Last updated" date. Continued use of the Platform after
              changes take effect constitutes your acceptance of the revised
              Terms. If changes are material, we will notify registered users by
              email.
            </p>

            <h2>13. Governing Law</h2>
            <p>
              These Terms are governed by and construed in accordance with the
              laws of the jurisdiction in which Site Studio is incorporated,
              without regard to conflict of law principles. Any disputes shall
              be subject to the exclusive jurisdiction of the courts of that
              jurisdiction.
            </p>

            <h2>14. Contact</h2>
            <p>
              If you have questions about these Terms, reach us through our{" "}
              <Link href="/contact" className="legal-link">contact page</Link>.
            </p>
          </div>

          <div className="legal-footer-nav">
            <Link href="/privacy" className="legal-link">Privacy Policy</Link>
            <span className="legal-footer-divider">·</span>
            <Link href="/" className="legal-link">Back to Home</Link>
          </div>
        </div>
      </main>
    </>
  );
}
