
import { useState } from "react";
import "./App.css";

const schemes = [
  {
    title: "PM Scholarship Scheme",
    category: "Education",
    description:
      "Financial assistance for eligible students pursuing higher education.",
    icon: "✳",
    tone: "peach",
    label: "FOR STUDENTS",
  },
  {
    title: "PM Awas Yojana",
    category: "Housing",
    description:
      "Housing support for eligible families seeking a secure home.",
    icon: "⌂",
    tone: "sage",
    label: "FOR FAMILIES",
  },
  {
    title: "PM-KISAN",
    category: "Agriculture",
    description:
      "Income support for eligible farmer families across India.",
    icon: "❋",
    tone: "yellow",
    label: "FOR FARMERS",
  },
];

function App() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [state, setState] = useState("");
  const [income, setIncome] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const filteredSchemes = schemes.filter((scheme) => {
    const matchesSearch = scheme.title
      .toLowerCase()
      .includes(search.toLowerCase());

    const matchesCategory =
      category === "All" || scheme.category === category;

    return matchesSearch && matchesCategory;
  });

  function handleSubmit(event) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <div className="app">
      <header className="navbar">
        <a className="brand" href="#home">
          <span className="brand-mark">S</span>
          Scheme<span>Match</span>
          <small>AI</small>
        </a>

        <nav>
          <a href="#home">Home</a>
          <a href="#schemes">Explore schemes</a>
          <a href="#eligibility">Eligibility</a>
        </nav>

        <a className="nav-cta" href="#eligibility">
          Get started <span>↗</span>
        </a>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-dot"></span>
              GOVERNMENT BENEFITS, MADE SIMPLE
            </div>

            <h1>
              The right support.
              <br />
              <em>Right when</em>
              <br />
              you need it.
            </h1>

            <p className="hero-description">
              Discover government schemes that match your profile.
              Understand why you may qualify, what you need, and
              where to apply — all in one place.
            </p>

            <div className="hero-actions">
              <a className="primary-btn" href="#eligibility">
                Check my eligibility <span>↗</span>
              </a>
              <a className="text-link" href="#schemes">
                Explore schemes <span>→</span>
              </a>
            </div>

            <div className="hero-footnote">
              <span>✳</span> Clear information. Smarter discovery.
            </div>
          </div>

          <div className="hero-art">
            <div className="art-sun"></div>
            <div className="art-circle art-circle-one"></div>
            <div className="art-circle art-circle-two"></div>

            <div className="art-caption">
              <span>YOUR NEXT STEP</span>
              <strong>Starts here.</strong>
            </div>

            <div className="art-card">
              <div className="art-card-top">
                <span className="art-card-icon">✳</span>
                <span className="art-card-label">SCHEME DISCOVERY</span>
              </div>

              <div className="art-card-number">01</div>
              <h2>Benefits<br />within reach.</h2>
              <p>
                A clearer path to opportunities designed
                to support you.
              </p>

              <div className="art-card-bottom">
                <span>Explore what fits</span>
                <span className="arrow-circle">↗</span>
              </div>
            </div>

            <div className="art-stamp">
              <span>MADE FOR</span>
              <strong>YOU</strong>
              <span>INDIA ✳</span>
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <div>
            <span className="trust-icon">✳</span>
            <p><strong>One platform</strong><small>Multiple schemes, one place</small></p>
          </div>
          <div>
            <span className="trust-icon">⌕</span>
            <p><strong>Smarter discovery</strong><small>Find schemes by your profile</small></p>
          </div>
          <div>
            <span className="trust-icon">✓</span>
            <p><strong>Clear explanations</strong><small>Understand the eligibility rules</small></p>
          </div>
        </section>

        <section className="schemes-section" id="schemes">
          <div className="section-topline">
            <span>01 / DISCOVER</span>
            <span>FIND YOUR OPPORTUNITY</span>
          </div>

          <div className="section-heading">
            <div>
              <p className="section-kicker">A WORLD OF SUPPORT</p>
              <h2>
                Opportunities
                <br />
                <em>worth knowing.</em>
              </h2>
            </div>
            <p className="section-intro">
              Explore a selection of government schemes.
              Search by name or filter by the area of support
              you are interested in.
            </p>
          </div>

          <div className="scheme-controls">
            <input
              type="text"
              placeholder="Search a scheme..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />

            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="All">All categories</option>
              <option value="Education">Education</option>
              <option value="Housing">Housing</option>
              <option value="Agriculture">Agriculture</option>
            </select>
          </div>

          <div className="schemes-grid">
            {filteredSchemes.length > 0 ? (
              filteredSchemes.map((scheme) => (
                <article className={`scheme-card ${scheme.tone}`} key={scheme.title}>
                  <div className="scheme-card-top">
                    <span className="scheme-icon">{scheme.icon}</span>
                    <span className="scheme-label">{scheme.label}</span>
                  </div>
                  <h3>{scheme.title}</h3>
                  <p>{scheme.description}</p>
                  <div className="scheme-card-bottom">
                    <span>{scheme.category}</span>
                    <a href="#eligibility" aria-label={`Check eligibility for ${scheme.title}`}>↗</a>
                  </div>
                </article>
              ))
            ) : (
              <p className="empty-result">
                No matching sample schemes found. Try another search.
              </p>
            )}
          </div>

          <p className="demo-note">
            Note: These are sample scheme entries for the current frontend prototype.
            Verify scheme details against official government sources before use.
          </p>
        </section>

        <section className="eligibility-section" id="eligibility">
          <div className="eligibility-intro">
            <div className="section-topline">
              <span>02 / YOUR PROFILE</span>
              <span>LET'S GET PERSONAL</span>
            </div>
            <p className="section-kicker">A BETTER PLACE TO BEGIN</p>
            <h2>
              Let's find what
              <br />
              <em>you may qualify for.</em>
            </h2>
            <p>
              Share a few basic details to begin exploring
              schemes that may fit your circumstances.
            </p>

            <div className="privacy-note">
              <span>◈</span>
              <div>
                <strong>Your details matter.</strong>
                <small>This is a frontend demonstration. No information is sent to a server yet.</small>
              </div>
            </div>
          </div>

          <div className="form-panel">
            <div className="form-heading">
              <span>YOUR DETAILS</span>
              <span>✳</span>
            </div>

            <form onSubmit={handleSubmit}>
              <label>
                Full name
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                    setSubmitted(false);
                  }}
                  required
                />
              </label>

              <div className="form-row">
                <label>
                  Age
                  <input
                    type="number"
                    placeholder="Your age"
                    min="1"
                    max="120"
                    value={age}
                    onChange={(event) => {
                      setAge(event.target.value);
                      setSubmitted(false);
                    }}
                    required
                  />
                </label>

                <label>
                  State
                  <select
                    value={state}
                    onChange={(event) => {
                      setState(event.target.value);
                      setSubmitted(false);
                    }}
                    required
                  >
                    <option value="">Select state</option>
                    <option>Rajasthan</option>
                    <option>Punjab</option>
                    <option>Haryana</option>
                    <option>Delhi</option>
                    <option>Uttar Pradesh</option>
                    <option>Other</option>
                  </select>
                </label>
              </div>

              <label>
                Annual family income
                <select
                  value={income}
                  onChange={(event) => {
                    setIncome(event.target.value);
                    setSubmitted(false);
                  }}
                  required
                >
                  <option value="">Select income range</option>
                  <option>Below ₹1 lakh</option>
                  <option>₹1 lakh – ₹2.5 lakh</option>
                  <option>₹2.5 lakh – ₹5 lakh</option>
                  <option>₹5 lakh – ₹8 lakh</option>
                  <option>Above ₹8 lakh</option>
                </select>
              </label>

              <button type="submit">
                Continue to discover schemes <span>→</span>
              </button>

              {submitted && (
                <p className="form-success" role="status">
                  Thanks, {name}. Your details have been entered in this demo.
                  Eligibility matching will be connected to the backend next.
                </p>
              )}
            </form>
          </div>
        </section>
      </main>

      <footer>
        <a className="brand footer-brand" href="#home">
          <span className="brand-mark">S</span>
          Scheme<span>Match</span><small>AI</small>
        </a>
        <p>Making public benefits easier to discover.</p>
        <span>SCHEMEMATCH AI · STUDENT PROJECT PROTOTYPE</span>
      </footer>
    </div>
  );
}

export default App;
