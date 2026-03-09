/**
 * GameRadar AI - Landing Page
 * Professional landing page for E-sports Talent Scouting Platform
 */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Navigation */}
      <nav className="fixed w-full bg-slate-900/80 backdrop-blur-sm z-50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg"></div>
              <span className="text-2xl font-bold text-white">GameRadar<span className="text-blue-400">AI</span></span>
            </div>
            <div className="hidden md:flex space-x-8">
              <a href="#features" className="text-slate-300 hover:text-white transition">Features</a>
              <a href="#how-it-works" className="text-slate-300 hover:text-white transition">How It Works</a>
              <a href="#pricing" className="text-slate-300 hover:text-white transition">Pricing</a>
              <a href="#contact" className="text-slate-300 hover:text-white transition">Contact</a>
            </div>
            <a href="#contact" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition">
              Get Started
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Discover Hidden E-Sports Talent
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
              Before Your Competitors Do
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-300 mb-10 max-w-3xl mx-auto">
            AI-powered transcultural scouting platform that finds emerging talent in Asia's gaming markets. 
            Real-time analytics, semantic search, and instant notifications.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="#contact" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition transform hover:scale-105">
              Start Free Trial
            </a>
            <a href="#how-it-works" className="bg-slate-700 hover:bg-slate-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition">
              See Demo
            </a>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-400">7</div>
              <div className="text-slate-400 mt-1">Asian Markets</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-400">AI</div>
              <div className="text-slate-400 mt-1">Powered Analysis</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-400">Real-time</div>
              <div className="text-slate-400 mt-1">Data Updates</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-orange-400">24/7</div>
              <div className="text-slate-400 mt-1">Monitoring</div>
            </div>
          </div>
        </div>
      </section>

      {/* Target Markets */}
      <section id="markets" className="py-20 px-4 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-4">Target Markets</h2>
          <p className="text-slate-300 text-center mb-12 text-lg">We specialize in untapped Asian gaming markets</p>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600 hover:border-blue-500 transition">
              <div className="text-4xl mb-4">🇰🇷🇨🇳🇯🇵</div>
              <h3 className="text-2xl font-bold text-white mb-3">East Asia</h3>
              <p className="text-slate-300">Korea, China, Japan - Premier leagues and emerging talent from gaming powerhouses</p>
            </div>
            
            <div className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600 hover:border-purple-500 transition">
              <div className="text-4xl mb-4">🇮🇳</div>
              <h3 className="text-2xl font-bold text-white mb-3">South Asia</h3>
              <p className="text-slate-300">India - Fast-growing market with 400M+ gamers and untapped potential</p>
            </div>
            
            <div className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600 hover:border-green-500 transition">
              <div className="text-4xl mb-4">🇻🇳🇹🇭</div>
              <h3 className="text-2xl font-bold text-white mb-3">Southeast Asia</h3>
              <p className="text-slate-300">Vietnam, Thailand - Rapidly expanding competitive gaming scenes</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-4">How It Works</h2>
          <p className="text-slate-300 text-center mb-16 text-lg">From data collection to talent discovery in 4 simple steps</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">1</div>
              <h3 className="text-xl font-bold text-white mb-3">Data Ingestion</h3>
              <p className="text-slate-300">Multi-source scraping from Liquipedia, OP.GG, regional platforms. Bronze layer validation.</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">2</div>
              <h3 className="text-xl font-bold text-white mb-3">AI Normalization</h3>
              <p className="text-slate-300">Automatic country detection, character handling, data enrichment. Silver layer processing.</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">3</div>
              <h3 className="text-xl font-bold text-white mb-3">Smart Scoring</h3>
              <p className="text-slate-300">GameRadar Score calculation: KDA, win rate, rank trajectory. Gold layer verification.</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">4</div>
              <h3 className="text-xl font-bold text-white mb-3">Talent Discovery</h3>
              <p className="text-slate-300">Semantic search, real-time alerts, dashboard analytics. TalentPing notifications.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section id="features" className="py-20 px-4 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-4">Why GameRadar AI?</h2>
          <p className="text-slate-300 text-center mb-16 text-lg">The competitive advantage you need</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-blue-600/20 to-blue-800/20 p-6 rounded-xl border border-blue-500/30">
              <div className="text-3xl mb-4">🎯</div>
              <h3 className="text-xl font-bold text-white mb-3">Transcultural Intelligence</h3>
              <p className="text-slate-300">Navigate Asian markets with automatic language detection, Unicode handling, and cultural context awareness.</p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-600/20 to-purple-800/20 p-6 rounded-xl border border-purple-500/30">
              <div className="text-3xl mb-4">⚡</div>
              <h3 className="text-xl font-bold text-white mb-3">Real-Time Monitoring</h3>
              <p className="text-slate-300">24/7 data pipeline with instant TalentPing notifications when high-potential players emerge.</p>
            </div>
            
            <div className="bg-gradient-to-br from-green-600/20 to-green-800/20 p-6 rounded-xl border border-green-500/30">
              <div className="text-3xl mb-4">🤖</div>
              <h3 className="text-xl font-bold text-white mb-3">AI-Powered Scoring</h3>
              <p className="text-slate-300">Proprietary GameRadar Score combines performance metrics, rank trajectory, and potential indicators.</p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-600/20 to-orange-800/20 p-6 rounded-xl border border-orange-500/30">
              <div className="text-3xl mb-4">🔍</div>
              <h3 className="text-xl font-bold text-white mb-3">Semantic Search</h3>
              <p className="text-slate-300">Natural language queries with vector embeddings. Find players by playstyle, not just stats.</p>
            </div>
            
            <div className="bg-gradient-to-br from-pink-600/20 to-pink-800/20 p-6 rounded-xl border border-pink-500/30">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-xl font-bold text-white mb-3">Elite Analyst View</h3>
              <p className="text-slate-300">Dense stats tables, champion pools, performance trends. Everything analysts need in one dashboard.</p>
            </div>
            
            <div className="bg-gradient-to-br from-indigo-600/20 to-indigo-800/20 p-6 rounded-xl border border-indigo-500/30">
              <div className="text-3xl mb-4">🌍</div>
              <h3 className="text-xl font-bold text-white mb-3">Multi-Language Support</h3>
              <p className="text-slate-300">7 languages: English, Hindi, Korean, Japanese, Thai, Vietnamese, Chinese. Native experience everywhere.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-4">Pricing Plans</h2>
          <p className="text-slate-300 text-center mb-16 text-lg">Choose the plan that fits your scouting needs</p>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Street Scout */}
            <div className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600 hover:border-blue-500 transition">
              <h3 className="text-2xl font-bold text-white mb-2">Street Scout</h3>
              <div className="text-4xl font-bold text-blue-400 mb-4">$99<span className="text-xl text-slate-400">/mo</span></div>
              <p className="text-slate-300 mb-6">Perfect for indie scouts and small organizations</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Access to 3 markets</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">50 searches/month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Basic analytics</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Email notifications</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Community support</span>
                </li>
              </ul>
              <a href="#contact" className="block w-full bg-slate-600 hover:bg-slate-500 text-white py-3 rounded-lg text-center font-semibold transition">
                Start Free Trial
              </a>
            </div>

            {/* Elite Analyst */}
            <div className="bg-gradient-to-br from-blue-600/30 to-purple-600/30 p-8 rounded-xl border-2 border-blue-500 transform scale-105 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                MOST POPULAR
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Elite Analyst</h3>
              <div className="text-4xl font-bold text-blue-400 mb-4">$299<span className="text-xl text-slate-400">/mo</span></div>
              <p className="text-slate-300 mb-6">For professional teams and organizations</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">All 7 markets</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Unlimited searches</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Advanced analytics + AI insights</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">TalentPing real-time alerts</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Priority support</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">API access</span>
                </li>
              </ul>
              <a href="#contact" className="block w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 rounded-lg text-center font-semibold transition">
                Start Free Trial
              </a>
            </div>

            {/* Organization */}
            <div className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600 hover:border-purple-500 transition">
              <h3 className="text-2xl font-bold text-white mb-2">Organization</h3>
              <div className="text-4xl font-bold text-purple-400 mb-4">Custom</div>
              <p className="text-slate-300 mb-6">Enterprise solutions for large organizations</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Everything in Elite</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Multi-team access</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Custom integrations</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">Dedicated account manager</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">White-label options</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-400 mr-2">✓</span>
                  <span className="text-slate-300">SLA guarantee</span>
                </li>
              </ul>
              <a href="#contact" className="block w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg text-center font-semibold transition">
                Contact Sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section id="contact" className="py-20 px-4 bg-slate-800/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-4xl font-bold text-white text-center mb-4">Get Started Today</h2>
          <p className="text-slate-300 text-center mb-12 text-lg">Start your 14-day free trial. No credit card required.</p>
          
          <form className="bg-slate-700/50 backdrop-blur p-8 rounded-xl border border-slate-600">
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <label htmlFor="firstName" className="block text-slate-300 mb-2 font-semibold">First Name *</label>
                <input
                  type="text"
                  id="firstName"
                  required
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
                  placeholder="John"
                />
              </div>
              <div>
                <label htmlFor="lastName" className="block text-slate-300 mb-2 font-semibold">Last Name *</label>
                <input
                  type="text"
                  id="lastName"
                  required
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
                  placeholder="Doe"
                />
              </div>
            </div>
            
            <div className="mb-6">
              <label htmlFor="email" className="block text-slate-300 mb-2 font-semibold">Work Email *</label>
              <input
                type="email"
                id="email"
                required
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
                placeholder="john@organization.com"
              />
            </div>
            
            <div className="mb-6">
              <label htmlFor="organization" className="block text-slate-300 mb-2 font-semibold">Organization *</label>
              <input
                type="text"
                id="organization"
                required
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
                placeholder="E-sports Team / Organization"
              />
            </div>
            
            <div className="mb-6">
              <label htmlFor="role" className="block text-slate-300 mb-2 font-semibold">Role *</label>
              <select
                id="role"
                required
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
              >
                <option value="">Select your role</option>
                <option value="scout">Talent Scout</option>
                <option value="analyst">Performance Analyst</option>
                <option value="coach">Coach / Manager</option>
                <option value="gm">General Manager</option>
                <option value="owner">Team Owner</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="mb-6">
              <label htmlFor="plan" className="block text-slate-300 mb-2 font-semibold">Interested Plan</label>
              <select
                id="plan"
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition"
              >
                <option value="">Select a plan</option>
                <option value="street-scout">Street Scout - $99/mo</option>
                <option value="elite-analyst">Elite Analyst - $299/mo</option>
                <option value="organization">Organization - Custom</option>
              </select>
            </div>
            
            <div className="mb-6">
              <label htmlFor="message" className="block text-slate-300 mb-2 font-semibold">Message</label>
              <textarea
                id="message"
                rows={4}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition resize-none"
                placeholder="Tell us about your scouting needs..."
              ></textarea>
            </div>
            
            <div className="mb-6">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  required
                  className="mt-1 mr-3"
                />
                <span className="text-slate-400 text-sm">
                  I agree to receive communications from GameRadar AI and accept the{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300">Privacy Policy</a> and{' '}
                  <a href="#" className="text-blue-400 hover:text-blue-300">Terms of Service</a>
                </span>
              </label>
            </div>
            
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-lg text-lg font-semibold transition transform hover:scale-105"
            >
              Start 14-Day Free Trial
            </button>
            
            <p className="text-slate-400 text-center mt-4 text-sm">
              No credit card required • Cancel anytime • Full access during trial
            </p>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg"></div>
                <span className="text-xl font-bold text-white">GameRadar<span className="text-blue-400">AI</span></span>
              </div>
              <p className="text-slate-400 text-sm">
                AI-powered transcultural e-sports talent scouting platform.
              </p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li><a href="#features" className="text-slate-400 hover:text-white transition text-sm">Features</a></li>
                <li><a href="#pricing" className="text-slate-400 hover:text-white transition text-sm">Pricing</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Roadmap</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">API Docs</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">About</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Blog</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Careers</a></li>
                <li><a href="#contact" className="text-slate-400 hover:text-white transition text-sm">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Privacy Policy</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Terms of Service</a></li>
                <li><a href="#" className="text-slate-400 hover:text-white transition text-sm">Cookie Policy</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-slate-400 text-sm mb-4 md:mb-0">
              © 2026 GameRadar AI. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a href="#" className="text-slate-400 hover:text-white transition">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"></path></svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z"></path><circle cx="4" cy="4" r="2"></circle></svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
