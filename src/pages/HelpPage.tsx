import { HelpCircle, BookOpen, Mail, MessageCircle } from 'lucide-react';

export default function HelpPage() {
  const faqs = [
    {
      question: 'How is risk level calculated?',
      answer:
        'Risk levels are calculated using machine learning algorithms that analyze multiple factors including academic performance (GPA, course grades), attendance patterns, behavioral indicators, and historical data from similar student profiles. The system provides a risk score from 0-100 and categorizes students as low, medium, or high risk.',
    },
    {
      question: 'What should I do when I receive a high-risk alert?',
      answer:
        'When you receive a high-risk alert, review the student profile to understand the contributing factors. Contact the student to discuss their challenges, and create an intervention plan. Document all interactions and outcomes in the system to track progress.',
    },
    {
      question: 'How often is student data updated?',
      answer:
        'Student data is updated in real-time as new information is uploaded. Risk assessments are recalculated daily based on the latest available data to ensure timely identification of at-risk students.',
    },
    {
      question: 'Can I export reports for institutional review?',
      answer:
        'Yes, all reports can be exported in PDF, CSV, and Excel formats. Navigate to the Reports section, select the desired report, and click the Export button to download in your preferred format.',
    },
    {
      question: 'How do I upload new student data?',
      answer:
        'Go to the Data Upload section and either drag and drop your files or click to browse. Supported formats include CSV and Excel. Download our templates to ensure your data is properly formatted for import.',
    },
    {
      question: 'What is the difference between faculty and administrator roles?',
      answer:
        'Faculty members can view students assigned to them and create interventions. Administrators have full system access including data management, system-wide reports, and can manage all students across departments.',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Help & Support</h1>
        <p className="text-slate-600 mt-1">
          Get answers to common questions and learn how to use the Early Warning System
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <div className="inline-flex items-center justify-center h-12 w-12 bg-blue-100 rounded-lg mb-4">
            <BookOpen className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Documentation</h3>
          <p className="text-sm text-slate-600 mb-4">
            Comprehensive guides and tutorials
          </p>
          <button className="px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
            View Docs
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <div className="inline-flex items-center justify-center h-12 w-12 bg-green-100 rounded-lg mb-4">
            <MessageCircle className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Live Chat</h3>
          <p className="text-sm text-slate-600 mb-4">Chat with our support team</p>
          <button className="px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
            Start Chat
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <div className="inline-flex items-center justify-center h-12 w-12 bg-amber-100 rounded-lg mb-4">
            <Mail className="h-6 w-6 text-amber-600" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Email Support</h3>
          <p className="text-sm text-slate-600 mb-4">Get help via email</p>
          <button className="px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors text-sm">
            Contact Us
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center">
          <HelpCircle className="h-5 w-5 mr-2 text-slate-600" />
          Frequently Asked Questions
        </h2>
        <div className="space-y-6">
          {faqs.map((faq, index) => (
            <div key={index} className="pb-6 border-b border-slate-200 last:border-0 last:pb-0">
              <h3 className="font-semibold text-slate-900 mb-2">{faq.question}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{faq.answer}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 text-white">
        <h2 className="text-xl font-bold mb-4">Need More Help?</h2>
        <p className="text-slate-300 mb-6">
          Our support team is available Monday through Friday, 8:00 AM to 6:00 PM EST to assist you
          with any questions or technical issues.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400 mb-1">Email</p>
            <p className="font-medium">support@earlywarning.edu</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Phone</p>
            <p className="font-medium">1-800-EWS-HELP</p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 rounded-xl border border-blue-100 p-6">
        <h3 className="font-semibold text-slate-900 mb-2">Training Resources</h3>
        <p className="text-slate-600 text-sm mb-4">
          Access video tutorials, webinars, and training materials to help your team get the most
          out of the Early Warning System.
        </p>
        <button className="px-6 py-2 bg-white text-slate-900 font-medium rounded-lg hover:bg-slate-50 transition-colors border border-slate-200">
          View Training Materials
        </button>
      </div>
    </div>
  );
}
