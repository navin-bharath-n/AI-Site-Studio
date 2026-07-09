import Navbar from "@/components/layout/Navbar";
import { Mail, MessageSquare, MapPin } from "lucide-react";
import "./Page.css";

export default function ContactPage() {
  return (
    <>
      <Navbar />
      <main className="contact-main">
        <div className="contact-container">
          <div className="contact-header">
            <h1 className="contact-title">
              Get in <span className="gradient-text">Touch</span>
            </h1>
            <p className="contact-subtitle">
              We're here to help you succeed. Reach out with any questions.
            </p>
          </div>

          <div className="contact-cards-grid">
            <div className="contact-card">
              <div className="contact-icon-wrapper primary">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <h3 className="contact-card-title">Email Us</h3>
                <p className="contact-card-desc">support@aisitestudio.com</p>
              </div>
            </div>

            <div className="contact-card">
              <div className="contact-icon-wrapper secondary">
                <MessageSquare className="w-6 h-6" />
              </div>
              <div>
                <h3 className="contact-card-title">Live Chat</h3>
                <p className="contact-card-desc">Available 9am - 5pm EST</p>
              </div>
            </div>

            <div className="contact-card">
              <div className="contact-icon-wrapper accent">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <h3 className="contact-card-title">Office</h3>
                <p className="contact-card-desc">San Francisco, CA</p>
              </div>
            </div>
          </div>
          
          <div className="contact-form-box">
            <h2 className="contact-form-title">Send a Message</h2>
            <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
              <div className="contact-form-row">
                <input type="text" placeholder="First Name" className="contact-input" />
                <input type="text" placeholder="Last Name" className="contact-input" />
              </div>
              <input type="email" placeholder="Email Address" className="contact-input" />
              <textarea placeholder="How can we help?" rows="4" className="contact-input contact-textarea"></textarea>
              <button className="contact-submit-btn">
                Send Message
              </button>
            </form>
          </div>
        </div>
      </main>
    </>
  );
}
