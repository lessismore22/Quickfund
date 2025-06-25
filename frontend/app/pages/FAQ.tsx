import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Search, MessageCircle } from 'lucide-react';
import Card from '../components/UI/Card';
import Input from '../components/UI/Input';
import Button from '../components/UI/Button';

const FAQ: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedItems, setExpandedItems] = useState<number[]>([]);

  const faqCategories = [
    {
      title: 'Getting Started',
      faqs: [
        {
          question: 'How do I apply for a loan?',
          answer: 'Applying is simple! Just click "Apply Now" on our homepage, fill out the quick application form with your basic information, and you\'ll get an instant decision. The entire process takes less than 5 minutes.'
        },
        {
          question: 'What information do I need to apply?',
          answer: 'You\'ll need your Social Security number, employment information, monthly income, and a valid email address and phone number. We may also ask for additional documentation for verification.'
        },
        {
          question: 'How quickly will I get my money?',
          answer: 'Once approved, funds are typically deposited into your bank account within 1 business day. Some customers receive funds the same day if approved before 2 PM EST on weekdays.'
        }
      ]
    },
    {
      title: 'Loan Details',
      faqs: [
        {
          question: 'What loan amounts do you offer?',
          answer: 'We offer personal loans from $500 to $10,000. The exact amount you qualify for depends on your income, credit history, and other factors determined during the application process.'
        },
        {
          question: 'What are your interest rates?',
          answer: 'Our interest rates range from 5.99% to 35.99% APR, depending on your creditworthiness. Most of our customers receive rates between 7.99% and 24.99% APR. You\'ll see your exact rate during the application process.'
        },
        {
          question: 'What repayment terms do you offer?',
          answer: 'We offer flexible repayment terms from 3 to 36 months. You can choose the term that works best for your budget, and there are no prepayment penalties if you want to pay off your loan early.'
        }
      ]
    },
    {
      title: 'Eligibility',
      faqs: [
        {
          question: 'What are the requirements to get a loan?',
          answer: 'To qualify, you must be at least 18 years old, have a valid Social Security number, have a steady source of income, and have an active checking account. We also perform a credit check as part of our approval process.'
        },
        {
          question: 'Do you check credit scores?',
          answer: 'Yes, we perform a soft credit check during the application process, which won\'t affect your credit score. If you decide to accept a loan offer, we\'ll perform a hard credit check, which may temporarily lower your credit score by a few points.'
        },
        {
          question: 'Can I apply if I have bad credit?',
          answer: 'Yes! We consider applications from people with all types of credit histories. While credit score is a factor, we also look at your income, employment history, and other factors to make our lending decision.'
        }
      ]
    },
    {
      title: 'Repayment',
      faqs: [
        {
          question: 'How do I make payments?',
          answer: 'You can make payments through your online account, our mobile app, or by setting up automatic payments from your bank account. We also accept payments by phone or mail if needed.'
        },
        {
          question: 'What happens if I miss a payment?',
          answer: 'If you miss a payment, we\'ll contact you to help resolve the situation. Late fees may apply, and missed payments can affect your credit score. We encourage you to contact us immediately if you\'re having trouble making payments.'
        },
        {
          question: 'Can I pay off my loan early?',
          answer: 'Absolutely! You can pay off your loan early at any time without penalty. This can save you money on interest charges. You can make extra payments or pay off the full balance through your online account.'
        }
      ]
    }
  ];

  const toggleExpanded = (categoryIndex: number, faqIndex: number) => {
    const itemId = categoryIndex * 1000 + faqIndex;
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isExpanded = (categoryIndex: number, faqIndex: number) => {
    const itemId = categoryIndex * 1000 + faqIndex;
    return expandedItems.includes(itemId);
  };

  const filteredCategories = faqCategories.map(category => ({
    ...category,
    faqs: category.faqs.filter(faq =>
      faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(category => category.faqs.length > 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl lg:text-5xl font-bold mb-6">
            Frequently Asked Questions
          </h1>
          <p className="text-xl text-primary-100 mb-8">
            Find answers to common questions about our loans and services
          </p>
          <div className="max-w-lg mx-auto">
            <Input
              placeholder="Search for answers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              fullWidth
              className="bg-white"
            />
          </div>
        </div>
      </section>

      {/* FAQ Content */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {filteredCategories.length === 0 ? (
            <Card className="text-center py-12">
              <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No results found
              </h3>
              <p className="text-gray-600">
                Try adjusting your search terms or browse all categories below.
              </p>
            </Card>
          ) : (
            <div className="space-y-8">
              {filteredCategories.map((category, categoryIndex) => (
                <div key={categoryIndex}>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    {category.title}
                  </h2>
                  <div className="space-y-4">
                    {category.faqs.map((faq, faqIndex) => (
                      <Card key={faqIndex} padding="none" className="overflow-hidden">
                        <button
                          onClick={() => toggleExpanded(categoryIndex, faqIndex)}
                          className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors focus:outline-none focus:bg-gray-50"
                        >
                          <div className="flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-gray-900 pr-4">
                              {faq.question}
                            </h3>
                            {isExpanded(categoryIndex, faqIndex) ? (
                              <ChevronUp className="h-5 w-5 text-gray-500 flex-shrink-0" />
                            ) : (
                              <ChevronDown className="h-5 w-5 text-gray-500 flex-shrink-0" />
                            )}
                          </div>
                        </button>
                        {isExpanded(categoryIndex, faqIndex) && (
                          <div className="px-6 pb-4">
                            <p className="text-gray-600 leading-relaxed">
                              {faq.answer}
                            </p>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-16 bg-primary-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <MessageCircle className="h-12 w-12 text-primary-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Still have questions?
          </h2>
          <p className="text-gray-600 mb-6">
            Our customer support team is here to help you 24/7.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary">
              Chat with Support
            </Button>
            <Button variant="outline">
              Call 1-800-QUICK-FUND
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default FAQ;