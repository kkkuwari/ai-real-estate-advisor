import "./globals.css";

export const metadata = {
  title: "AI Real Estate Investment Advisor",
  description: "Academic prototype for property investment analysis",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header className="site-header">
            <div className="brand">
              <div className="brand-row">
                <span className="brand-mark">AI</span>
                <h1>AI Real Estate Investment Advisor</h1>
              </div>
              <p>Investment analytics dashboard</p>
            </div>
            <nav>
              <a href="/">Home</a>
              <a href="/analyse">Analyse Property</a>
              <a href="/compare">Compare Properties</a>
              <a href="/analyses">Saved Analyses</a>
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
