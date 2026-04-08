import { GraduationCap, TrendingUp, Users, AlertTriangle, ArrowRight } from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <GraduationCap className="h-8 w-8 text-slate-700" />
              <span className="text-xl font-semibold text-slate-900">EWS</span>
            </div>
            <button
              onClick={onGetStarted}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-slate-900 mb-6">
              Early Warning System
            </h1>
            <p className="text-xl text-slate-600 mb-4 max-w-3xl mx-auto">
              AI-Powered Student Success Platform for Educational Institutions
            </p>
            <p className="text-lg text-slate-500 mb-10 max-w-2xl mx-auto">
              Identify at-risk students early, provide timely interventions, and improve retention rates
              through data-driven insights and predictive analytics.
            </p>
            <button
              onClick={onGetStarted}
              className="inline-flex items-center px-8 py-4 bg-slate-900 text-white text-lg font-medium rounded-lg hover:bg-slate-800 transition-colors shadow-lg hover:shadow-xl"
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          </div>

          <div className="mt-24 grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Predictive Analytics
              </h3>
              <p className="text-slate-600">
                Machine learning algorithms analyze academic, attendance, and behavioral data to predict student risk levels with high accuracy.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <AlertTriangle className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Real-Time Alerts
              </h3>
              <p className="text-slate-600">
                Get instant notifications when students exhibit warning signs such as declining grades, poor attendance, or behavioral changes.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="h-12 w-12 bg-amber-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="h-6 w-6 text-amber-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Intervention Management
              </h3>
              <p className="text-slate-600">
                Coordinate support services, track intervention outcomes, and measure the effectiveness of student support programs.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="h-12 w-12 bg-slate-100 rounded-lg flex items-center justify-center mb-4">
                <GraduationCap className="h-6 w-6 text-slate-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Comprehensive Reporting
              </h3>
              <p className="text-slate-600">
                Generate detailed reports on student performance, retention trends, and intervention effectiveness for institutional planning.
              </p>
            </div>
          </div>

          <div className="mt-24 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="grid md:grid-cols-2">
              <div className="p-12">
                <h2 className="text-3xl font-bold text-slate-900 mb-6">
                  How It Works
                </h2>
                <div className="space-y-6">
                  <div className="flex">
                    <div className="flex-shrink-0 h-8 w-8 bg-slate-900 text-white rounded-full flex items-center justify-center font-semibold">
                      1
                    </div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-slate-900 mb-1">Data Integration</h4>
                      <p className="text-slate-600">
                        Import student academic records, attendance data, and demographic information securely into the system.
                      </p>
                    </div>
                  </div>
                  <div className="flex">
                    <div className="flex-shrink-0 h-8 w-8 bg-slate-900 text-white rounded-full flex items-center justify-center font-semibold">
                      2
                    </div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-slate-900 mb-1">AI Analysis</h4>
                      <p className="text-slate-600">
                        Advanced algorithms process multiple data points to identify patterns and calculate individual risk scores.
                      </p>
                    </div>
                  </div>
                  <div className="flex">
                    <div className="flex-shrink-0 h-8 w-8 bg-slate-900 text-white rounded-full flex items-center justify-center font-semibold">
                      3
                    </div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-slate-900 mb-1">Early Intervention</h4>
                      <p className="text-slate-600">
                        Faculty and counselors receive alerts and can implement targeted support strategies before issues escalate.
                      </p>
                    </div>
                  </div>
                  <div className="flex">
                    <div className="flex-shrink-0 h-8 w-8 bg-slate-900 text-white rounded-full flex items-center justify-center font-semibold">
                      4
                    </div>
                    <div className="ml-4">
                      <h4 className="font-semibold text-slate-900 mb-1">Continuous Monitoring</h4>
                      <p className="text-slate-600">
                        Track intervention effectiveness and adjust support strategies based on real-time progress data.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-slate-100 to-slate-200 p-12 flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center h-32 w-32 bg-white rounded-full shadow-lg mb-6">
                    <GraduationCap className="h-16 w-16 text-slate-700" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-2">
                    Improve Student Outcomes
                  </h3>
                  <p className="text-slate-600 max-w-sm">
                    Evidence-based interventions powered by comprehensive data analysis and machine learning.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-24 bg-slate-900 rounded-2xl p-12 text-center text-white">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Transform Student Support?
            </h2>
            <p className="text-slate-300 text-lg mb-8 max-w-2xl mx-auto">
              Join educational institutions using data-driven insights to identify at-risk students
              and provide timely, effective interventions.
            </p>
            <button
              onClick={onGetStarted}
              className="inline-flex items-center px-8 py-4 bg-white text-slate-900 text-lg font-medium rounded-lg hover:bg-slate-100 transition-colors shadow-lg"
            >
              Access Platform
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-slate-500">
            <p>&copy; 2026 Early Warning System. Educational Institution Support Platform.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
