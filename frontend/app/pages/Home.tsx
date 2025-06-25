import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Shield, Zap, DollarSign, CheckCircle, Star, Users } from 'lucide-react';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';

const Home: React.FC = () => {
  const features = [
    {
      icon: Zap,
      title: 'Instant Approval',
      description: 'Get your loan approved in under 5 minutes with our advanced scoring system.'
    },
    {
      icon: Shield,
      title: 'Secure & Safe',
      description: 'Bank-level security with 256-bit encryption to protect your personal information.'
    },
    {
      icon: DollarSign,
      title: 'Competitive Rates',
      description: 'Low interest rates starting from 5.99% APR with transparent pricing.'
    }
  ];

  const benefits = [
    'No hidden fees or prepayment penalties',
    'Flexible repayment terms (3-36 months)',
    'Loan amounts from $500 to $10,000',
    'Same-day funding available',
    'Build your credit with on-time payments',
    '24/7 customer support'
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      text: 'QuickFund helped me cover unexpected medical expenses. The process was so simple and fast!',
      rating: 5
    },
    {
      name: 'Michael Chi',
      text: 'Great rates and excellent customer service. I got my loan approved within minutes.',
      rating: 5
    },
    {
      name: 'Emily Rabiu',
      text: 'Finally, a lending platform that treats customers with respect. Highly recommended!',
      rating: 5
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <div className="max-w-3xl">
            <h1 className="text-4xl lg:text-6xl font-bold leading-tight mb-6 animate-fade-in">
              Fast & Secure
              <span className="block text-yellow-300">Micro-Lending</span>
            </h1>
            <p className="text-xl lg:text-2xl text-primary-100 mb-8 leading-relaxed animate-slide-up">
              Get the funds you need in minutes, not days. Apply for personal loans 
              up to $10,000 with instant approval and competitive rates.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 animate-slide-up">
              <Link to="/apply">
                <Button size="lg" className="bg-white text-primary-600 hover:bg-gray-50 shadow-lg hover:shadow-xl">
                  Apply Now
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/about">
                <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-primary-600">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white to-transparent"></div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Why Choose QuickFund?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We make borrowing simple, transparent, and fast with cutting-edge technology 
              and customer-first approach.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
                Simple, Transparent Lending
              </h2>
              <p className="text-lg text-gray-600 mb-8">
                We believe in fair and honest lending practices. No surprises, 
                no hidden fees, just straightforward terms you can understand.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-success-500 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white">
                <h3 className="text-2xl font-bold mb-4">Loan Calculator</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Loan Amount:</span>
                    <span className="font-semibold">$5,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Interest Rate:</span>
                    <span className="font-semibold">7.99% APR</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Term:</span>
                    <span className="font-semibold">24 months</span>
                  </div>
                  <hr className="border-primary-400" />
                  <div className="flex justify-between text-lg font-bold">
                    <span>Monthly Payment:</span>
                    <span>$228</span>
                  </div>
                </div>
                <Link to="/apply">
                  <Button className="w-full mt-6 bg-white text-primary-600 hover:bg-gray-50">
                    Get Your Rate
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              What Our Customers Say
            </h2>
            <p className="text-xl text-gray-600">
              Join thousands of satisfied customers who trust QuickFund
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index}>
                <div className="flex mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-gray-600 mb-4 italic">"{testimonial.text}"</p>
                <p className="font-semibold text-gray-900">{testimonial.name}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-primary-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">50K+</div>
              <div className="text-primary-200">Loans Funded</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">$50M+</div>
              <div className="text-primary-200">Total Funded</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">4.9★</div>
              <div className="text-primary-200">Customer Rating</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">5 Min</div>
              <div className="text-primary-200">Avg Approval Time</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Apply for your loan today and get the funds you need tomorrow.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/apply">
              <Button size="lg" icon={ArrowRight} iconPosition="right">
                Apply for Loan
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="outline" size="lg" icon={Users} iconPosition="left">
                Create Account
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;