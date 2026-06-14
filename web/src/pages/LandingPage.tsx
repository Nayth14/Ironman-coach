import { Link } from "react-router-dom";
import { Logo } from "../components/Logo";
import { Button } from "../components/Button";
import { BRAND_NAME } from "../lib/config";

const TRUST_LOGOS = [
  "IRONMAN",
  "IRONMAN 70.3",
  "Challenge Family",
  "Subaru IRONMAN Canada",
  "IRONMAN World Championship",
];

const FEATURES = [
  {
    icon: "🧠",
    title: "Adaptive plans",
    desc: "AI adjusts your training each week based on your performance, fatigue, and life.",
  },
  {
    icon: "⏱️",
    title: "Race-day pacing",
    desc: "Get personalized pacing targets and strategy to perform your best on race day.",
  },
  {
    icon: "❤️",
    title: "Recovery tracking",
    desc: "Monitor fatigue, sleep, and readiness to train smarter and reduce injury risk.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg">
      <header className="flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <Logo />
        <Link
          to="/login"
          className="rounded-full bg-text text-white px-5 py-2 text-sm font-semibold"
        >
          Log in
        </Link>
      </header>

      <section className="max-w-7xl mx-auto px-8 py-12 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span className="inline-block rounded-full bg-primary/10 text-primary text-xs font-semibold px-3 py-1 mb-4">
            AI-built race plans
          </span>
          <h1 className="text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight mb-4">
            Your Ironman,
            <br />
            engineered.
          </h1>
          <p className="text-xl font-semibold mb-3">
            Personalized triathlon training that adapts every week.
          </p>
          <p className="text-text-muted mb-8 max-w-lg">
            Intelligent swim, bike, and run plans that adapt to your data, feedback,
            and performance — so you arrive ready on race day.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button to="/onboarding">Build my plan</Button>
            <Button variant="secondary" to="/onboarding?demo=beginner_first_im">
              See a sample week
            </Button>
          </div>
        </div>

        <div className="relative">
          <div className="bg-white rounded-2xl shadow-xl border border-border p-4 transform rotate-1">
            <div className="flex gap-3">
              <div className="w-12 bg-gray-50 rounded-lg p-2 space-y-3">
                {["🏠", "📅", "📊", "💪"].map((i) => (
                  <div key={i} className="text-center text-sm">{i}</div>
                ))}
              </div>
              <div className="flex-1 space-y-3">
                <div className="text-sm font-semibold">Week 12 · Jun 10 – Jun 16</div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <div className="text-xs text-text-muted">Training Load</div>
                  <div className="text-2xl font-bold">620 <span className="text-green-500 text-sm">+18%</span></div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-blue-50 rounded-lg p-2">🏊 11.2 km</div>
                  <div className="bg-green-50 rounded-lg p-2">🚴 312 km</div>
                  <div className="bg-orange-50 rounded-lg p-2">🏃 42.6 km</div>
                </div>
                <div className="text-xs space-y-1">
                  {["Mon Aerobic swim ✓", "Tue Threshold bike ✓", "Wed Easy run ✓"].map((r) => (
                    <div key={r} className="flex justify-between bg-gray-50 rounded px-2 py-1">
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-border bg-white py-8">
        <div className="max-w-7xl mx-auto px-8 text-center">
          <p className="text-sm text-text-muted mb-4">Trusted by athletes training for</p>
          <div className="flex flex-wrap justify-center gap-8 opacity-50 font-bold text-sm">
            {TRUST_LOGOS.map((l) => (
              <span key={l}>{l}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-8 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">
          Everything you need to reach the finish line
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-white rounded-2xl border border-border p-8 shadow-sm">
              <div className="text-3xl mb-4">{f.icon}</div>
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-text-muted text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border bg-white py-12">
        <div className="max-w-7xl mx-auto px-8 grid grid-cols-2 md:grid-cols-5 gap-8 text-sm">
          {[
            { title: "Product", links: ["Features", "Pricing", "Sample plan"] },
            { title: "Resources", links: ["Blog", "Help center", "Training guides"] },
            { title: "Company", links: ["About", "Careers", "Contact"] },
            { title: "Legal", links: ["Privacy", "Terms", "Cookie policy"] },
          ].map((col) => (
            <div key={col.title}>
              <h4 className="font-semibold mb-3">{col.title}</h4>
              <ul className="space-y-2 text-text-muted">
                {col.links.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          ))}
          <div>
            <h4 className="font-semibold mb-3">Follow us</h4>
            <div className="flex gap-3 text-text-muted">📷 🏃 ▶️ ✉️</div>
          </div>
        </div>
        <p className="text-center text-text-muted text-xs mt-8">
          © 2026 {BRAND_NAME}. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
