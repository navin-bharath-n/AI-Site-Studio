import Navbar from "@/components/layout/Navbar";
import "./Page.css";

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main className="about-main">
        <div className="about-container">
          <h1 className="about-title">
            About <span className="gradient-text">AI Site Studio</span>
          </h1>
          <p className="about-description">
            We are on a mission to democratize web design. AI Site Studio empowers creators, developers, and agencies to build stunning, professional websites in a fraction of the time using the power of artificial intelligence.
          </p>
          <div className="about-story-box">
            <h2 className="about-story-title">Our Story</h2>
            <p className="about-story-text">
              Founded in 2026, we recognized that the gap between a great idea and a live website was too wide. By combining a rich marketplace of curated templates with intelligent AI customization, we've created a platform where anyone can succeed online.
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
