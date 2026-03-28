import "./Footer.css";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <span className="footer-logo">
            <span className="footer-puzzle">🧩</span>
            <span className="footer-logo-jigsaw">Jigsaw</span>
            <span className="footer-logo-nights">Nights</span>
          </span>
          <p className="footer-tagline">Find your perfect stay, piece by piece.</p>
        </div>
        <div className="footer-copy">
          © {new Date().getFullYear()} Jigsaw Nights · All rights reserved
        </div>
      </div>
    </footer>
  );
}
