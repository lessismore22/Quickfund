import React from 'react';
import { Shield, Users, Award, Target, Heart, Lightbulb } from 'lucide-react';
import Card from '../components/UI/Card';

const About: React.FC = () => {
  const values = [
    {
      icon: Shield,
      title: 'Trust & Security',
      description: 'We protect your data with bank-level security and transparent practices.'
    },
    {
      icon: Users,
      title: 'Customer First',
      description: 'Every decision we make puts our customers\' needs and success first.'
    },
    {
      icon: Award,
      title: 'Excellence',
      description: 'We strive for excellence in everything we do, from technology to service.'
    },
    {
      icon: Target,
      title: 'Innovation',
      description: 'We continuously innovate to make lending faster, easier, and more accessible.'
    },
    {
      icon: Heart,
      title: 'Empathy',
      description: 'We understand that financial needs are personal and treat each customer with care.'
    },
    {
      icon: Lightbulb,
      title: 'Simplicity',
      description: 'We make complex financial processes simple and easy to understand.'
    }
  ];

  const team = [
    {
      name: 'Uche Chen',
      role: 'CEO & Co-Founder',
      bio: 'Former VP at Goldman Sachs with 15+ years in fintech innovation.'
    },
    {
      name: 'Sarah Michael',
      role: 'CTO & Co-Founder',
      bio: 'Ex-Google engineer passionate about democratizing financial services.'
    },
    {
      name: 'Emily Fagbo',
      role: 'Head of Risk',
      bio: 'PhD in Economics with expertise in credit risk modeling and machine learning.'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl lg:text-5xl font-bold mb-6">
              Democratizing Access to Credit
            </h1>
            <p className="text-xl text-primary-100 leading-relaxed">
              At QuickFund, we believe that everyone deserves access to fair, transparent, 
              and affordable credit. We're on a mission to revolutionize the lending industry 
              through technology and human-centered design.
            </p>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
                Our Mission
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                We're building the future of lending by combining cutting-edge technology 
                with responsible lending practices. Our platform makes it possible for 
                people to access credit when they need it most, without the traditional 
                barriers and lengthy processes.
              </p>
              <p className="text-lg text-gray-600">
                Since our founding in 2022, we've helped over 50,000 customers access 
                more than $50 million in funding, with industry-leading approval rates 
                and customer satisfaction scores.
              </p>
            </div>
            <div className="bg-primary-50 rounded-2xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">By the Numbers</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="text-3xl font-bold text-primary-600">50K+</div>
                  <div className="text-gray-600">Happy Customers</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary-600">$50M+</div>
                  <div className="text-gray-600">Loans Funded</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary-600">4.9★</div>
                  <div className="text-gray-600">Customer Rating</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary-600">5 Min</div>
                  <div className="text-gray-600">Avg Approval</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Our Values
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              These core values guide everything we do and shape how we serve our customers.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {values.map((value, index) => (
              <Card key={index} hover className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <value.icon className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{value.title}</h3>
                <p className="text-gray-600">{value.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Leadership Team
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Meet the experienced leaders driving QuickFund's mission forward.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {team.map((member, index) => (
              <Card key={index} hover className="text-center">
                <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4"></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-1">{member.name}</h3>
                <p className="text-primary-600 font-medium mb-3">{member.role}</p>
                <p className="text-gray-600 text-sm">{member.bio}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl p-8 text-white">
              <h3 className="text-2xl font-bold mb-4">Powered by AI</h3>
              <p className="text-primary-100 mb-6">
                Our proprietary machine learning algorithms analyze hundreds of data points 
                in real-time to make fair and accurate lending decisions in under 5 minutes.
              </p>
              <div className="space-y-3">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-300 rounded-full mr-3"></div>
                  <span>Advanced risk assessment</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-300 rounded-full mr-3"></div>
                  <span>Real-time fraud detection</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-300 rounded-full mr-3"></div>
                  <span>Personalized loan terms</span>
                </div>
              </div>
            </div>
            <div>
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
                Technology That Works for You
              </h2>
              <p className="text-lg text-gray-600 mb-6">
                We leverage the latest in financial technology to provide a seamless, 
                secure, and intelligent lending experience. Our platform is built on 
                enterprise-grade infrastructure with bank-level security.
              </p>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <Shield className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Bank-Level Security</h4>
                    <p className="text-gray-600">256-bit encryption and SOC 2 compliance</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <Lightbulb className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Smart Decisions</h4>
                    <p className="text-gray-600">AI-powered underwriting for fair outcomes</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <Target className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Always Improving</h4>
                    <p className="text-gray-600">Continuous learning and optimization</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;