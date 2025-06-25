import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calculator, FileText, CheckCircle, AlertCircle, User, DollarSign } from 'lucide-react';
import Card from '../../components/UI/Card';
import Input from '../../components/UI/Input';
import Button from '../../components/UI/Button';
import { LoanFormData } from '../../types';
import { useMutation } from '@tanstack/react-query';
import mockApiService from '../../services/mockApi';



  // API hooks
  const LoanApplication: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<LoanFormData>({
    amount: 50000,
    purpose: '',
    term: 12,
    monthlyIncome: 0,
    employmentType: '',
    creditHistory: '',
    collateral: '',
    guarantor: {
      name: '',
      phone: '',
      email: '',
      relationship: ''
    }
  });
  const [loanCalculation, setLoanCalculation] = useState<{ monthlyPayment?: number; interestRate?: number }>({});

  const { mutate: submitApplication, isPending: isSubmitting } = useMutation<unknown, unknown, LoanFormData>(
    (data: LoanFormData) => mockApiService.submitLoanApplication(data),
    {
      onSuccess: () => {
        navigate('/loans');
      },
      onError: (error: any) => {
        console.error('Application submission failed:', error);
      }
    }
  );

  const steps = [
    { number: 1, title: 'Loan Details', icon: Calculator },
    { number: 2, title: 'Personal Info', icon: User },
    { number: 3, title: 'Guarantor Info', icon: FileText },
    { number: 4, title: 'Review & Submit', icon: CheckCircle }
  ];

  const loanPurposes = [
    'Business Expansion',
    'Education',
    'Medical Emergency',
    'Home Improvement',
    'Debt Consolidation',
    'Equipment Purchase',
    'Working Capital',
    'Personal Emergency',
    'Other'
  ];

  const employmentTypes = [
    'Full-time Employee',
    'Part-time Employee',
    'Self-employed',
    'Business Owner',
    'Freelancer',
    'Contract Worker',
    'Unemployed',
    'Student',
    'Retired'
  ];

  const creditHistoryOptions = [
    'Excellent (No defaults)',
    'Good (Minor delays)',
    'Fair (Some defaults)',
    'Poor (Multiple defaults)',
    'No Credit History'
  ];

  const relationshipOptions = [
    'Family Member',
    'Friend',
    'Colleague',
    'Business Partner',
    'Neighbor',
    'Other'
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name.startsWith('guarantor.')) {
      const guarantorField = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        guarantor: {
          ...prev.guarantor!,
          [guarantorField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'amount' || name === 'term' || name === 'monthlyIncome' 
          ? Number(value) 
          : value
      }));
    }

    // Auto-calculate loan when amount or term changes
    if ((name === 'amount' || name === 'term') && formData.amount > 0 && formData.term > 0) {
      const amount = name === 'amount' ? Number(value) : formData.amount;
      const term = name === 'term' ? Number(value) : formData.term;
      calculateLoan({ amount, term });
    }
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return formData.amount > 0 && formData.purpose !== '' && formData.term > 0;
      case 2:
        return formData.monthlyIncome > 0 && formData.employmentType !== '' && formData.creditHistory !== '';
      case 3:
        return formData.guarantor?.name !== '' && formData.guarantor?.phone !== '' && 
               formData.guarantor?.email !== '' && formData.guarantor?.relationship !== '';
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (validateStep(currentStep) && currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (validateStep(currentStep)) {
      await submitApplication(formData);
    }
  };

  // Calculate loan details
  const calculateLoan = ({ amount, term }: { amount: number; term: number }) => {
    // Example calculation logic (replace with real logic as needed)
    // Let's assume a flat 2.5% monthly interest rate for demonstration
    const interestRate = 2.5;
    const monthlyInterest = interestRate / 100;
    const monthlyPayment = Math.round(
      (amount * monthlyInterest) / (1 - Math.pow(1 + monthlyInterest, -term))
    );
    setLoanCalculation({
      monthlyPayment,
      interestRate,
    });
  };

  React.useEffect(() => {
    if (formData.amount > 0 && formData.term > 0) {
      calculateLoan({ amount: formData.amount, term: formData.term });
    }
  }, [formData.amount, formData.term]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Apply for a Loan
          </h1>
          <p className="text-gray-600">
            Get instant approval in just a few minutes
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4 md:space-x-8">
            {steps.map((step) => (
              <div key={step.number} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= step.number
                    ? 'bg-primary-600 border-primary-600 text-white'
                    : 'border-gray-300 text-gray-400'
                }`}>
                  {currentStep > step.number ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}
                </div>
                <span className={`ml-2 text-sm font-medium hidden md:block ${
                  currentStep >= step.number ? 'text-primary-600' : 'text-gray-400'
                }`}>
                  {step.title}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form */}
          <div className="lg:col-span-2">
            <Card>
              {/* Step 1: Loan Details */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Loan Details</h2>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Loan Amount: ₦{formData.amount.toLocaleString()}
                    </label>
                    <input
                      type="range"
                      name="amount"
                      min="10000"
                      max="1000000"
                      step="10000"
                      value={formData.amount}
                      onChange={handleInputChange}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>₦10,000</span>
                      <span>₦1,000,000</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      What's this loan for?
                    </label>
                    <select
                      name="purpose"
                      value={formData.purpose}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select a purpose</option>
                      {loanPurposes.map(purpose => (
                        <option key={purpose} value={purpose}>{purpose}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Repayment Term: {formData.term} months
                    </label>
                    <input
                      type="range"
                      name="term"
                      min="3"
                      max="36"
                      step="1"
                      value={formData.term}
                      onChange={handleInputChange}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>3 months</span>
                      <span>36 months</span>
                    </div>
                  </div>

                  <Input
                    label="Collateral (Optional)"
                    name="collateral"
                    value={formData.collateral}
                    onChange={handleInputChange}
                    placeholder="Describe any collateral you can offer"
                    fullWidth
                  />
                </div>
              )}

              {/* Step 2: Personal Info */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Personal Information</h2>
                  
                  <Input
                    label="Monthly Income (₦)"
                    type="number"
                    name="monthlyIncome"
                    value={formData.monthlyIncome || ''}
                    onChange={handleInputChange}
                    placeholder="150000"
                    fullWidth
                    required
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Employment Type
                    </label>
                    <select
                      name="employmentType"
                      value={formData.employmentType}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select employment type</option>
                      {employmentTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Credit History
                    </label>
                    <select
                      name="creditHistory"
                      value={formData.creditHistory}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select credit history</option>
                      {creditHistoryOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Step 3: Guarantor Info */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Guarantor Information</h2>
                  <p className="text-sm text-gray-600">
                    Please provide details of someone who can guarantee your loan.
                  </p>
                  
                  <Input
                    label="Guarantor Full Name"
                    name="guarantor.name"
                    value={formData.guarantor?.name || ''}
                    onChange={handleInputChange}
                    placeholder="John Doe"
                    fullWidth
                    required
                  />

                  <Input
                    label="Guarantor Phone Number"
                    type="tel"
                    name="guarantor.phone"
                    value={formData.guarantor?.phone || ''}
                    onChange={handleInputChange}
                    placeholder="+234 801 234 5678"
                    fullWidth
                    required
                  />

                  <Input
                    label="Guarantor Email"
                    type="email"
                    name="guarantor.email"
                    value={formData.guarantor?.email || ''}
                    onChange={handleInputChange}
                    placeholder="guarantor@example.com"
                    fullWidth
                    required
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Relationship to Guarantor
                    </label>
                    <select
                      name="guarantor.relationship"
                      value={formData.guarantor?.relationship || ''}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select relationship</option>
                      {relationshipOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Step 4: Review */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Review Your Application</h2>
                  
                  <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-gray-600">Loan Amount:</span>
                        <span className="font-semibold ml-2">₦{formData.amount.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Purpose:</span>
                        <span className="font-semibold ml-2">{formData.purpose}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Term:</span>
                        <span className="font-semibold ml-2">{formData.term} months</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Monthly Income:</span>
                        <span className="font-semibold ml-2">₦{formData.monthlyIncome?.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Employment:</span>
                        <span className="font-semibold ml-2">{formData.employmentType}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Guarantor:</span>
                        <span className="font-semibold ml-2">{formData.guarantor?.name}</span>
                      </div>
                    </div>
                    
                    {loanCalculation && (
                      <div className="border-t pt-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Estimated Monthly Payment:</span>
                          <span className="font-bold text-lg text-primary-600">
                            ₦{loanCalculation.monthlyPayment?.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-gray-600">Interest Rate:</span>
                          <span className="font-semibold">{loanCalculation.interestRate}% APR</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <AlertCircle className="h-5 w-5 text-primary-600 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-primary-800">
                        <p className="font-medium mb-1">Important Information</p>
                        <p>
                          By submitting this application, you agree to our terms and conditions. 
                          Your guarantor will be contacted for verification.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8 pt-6 border-t">
                <Button
                  variant="outline"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                >
                  Previous
                </Button>
                
                {currentStep < 4 ? (
                  <Button 
                    onClick={nextStep}
                    disabled={!validateStep(currentStep)}
                  >
                    Next Step
                  </Button>
                ) : (
                  <Button
                    onClick={handleSubmit}
                    loading={isSubmitting}
                    disabled={!validateStep(currentStep)}
                  >
                    Submit Application
                  </Button>
                )}
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Loan Summary</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Amount:</span>
                  <span className="font-semibold">₦{formData.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Term:</span>
                  <span className="font-semibold">{formData.term} months</span>
                </div>
                {loanCalculation && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Interest Rate:</span>
                      <span className="font-semibold">{loanCalculation.interestRate}% APR</span>
                    </div>
                    <div className="flex justify-between border-t pt-3">
                      <span className="text-gray-600">Monthly Payment:</span>
                      <span className="font-bold text-primary-600">
                        ₦{loanCalculation.monthlyPayment?.toLocaleString()}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Why Choose Us?</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-success-500 mr-2" />
                  Instant approval decisions
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-success-500 mr-2" />
                  Competitive interest rates
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-success-500 mr-2" />
                  Flexible repayment terms
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-success-500 mr-2" />
                  Quick disbursement
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoanApplication;