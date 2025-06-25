from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone


class MinLoanAmountValidator(BaseValidator):
    """Validate minimum loan amount"""
    
    def __init__(self, limit_value=1000):
        super().__init__(limit_value)
        self.message = f'Loan amount must be at least ${limit_value:,.2f}'
    
    def compare(self, a, b):
        return a < b


class MaxLoanAmountValidator(BaseValidator):
    """Validate maximum loan amount"""
    
    def __init__(self, limit_value=1000000):
        super().__init__(limit_value)
        self.message = f'Loan amount cannot exceed ${limit_value:,.2f}'
    
    def compare(self, a, b):
        return a > b


class InterestRateValidator(BaseValidator):
    """Validate interest rate range"""
    
    def __init__(self, min_rate=0.01, max_rate=30.0):
        self.min_rate = min_rate
        self.max_rate = max_rate
        super().__init__(max_rate)
        self.message = f'Interest rate must be between {min_rate}% and {max_rate}%'
    
    def __call__(self, value):
        if not (self.min_rate <= value <= self.max_rate):
            raise ValidationError(self.message, code='invalid_interest_rate')


class LoanTermValidator(BaseValidator):
    """Validate loan term in months"""
    
    def __init__(self, min_term=1, max_term=360):
        self.min_term = min_term
        self.max_term = max_term
        super().__init__(max_term)
        self.message = f'Loan term must be between {min_term} and {max_term} months'
    
    def __call__(self, value):
        if not (self.min_term <= value <= self.max_term):
            raise ValidationError(self.message, code='invalid_loan_term')


def validate_loan_purpose(value):
    """Validate loan purpose is not empty and meets minimum requirements"""
    if not value or len(value.strip()) < 10:
        raise ValidationError(
            'Loan purpose must be at least 10 characters long',
            code='invalid_purpose'
        )
    
    # Check for prohibited purposes
    prohibited_terms = [
        'gambling', 'casino', 'betting', 'illegal', 'drugs', 
        'weapons', 'speculation', 'cryptocurrency'
    ]
    
    if any(term in value.lower() for term in prohibited_terms):
        raise ValidationError(
            'Loan purpose contains prohibited terms',
            code='prohibited_purpose'
        )


def validate_monthly_income(value):
    """Validate monthly income is reasonable"""
    if value < Decimal('500'):
        raise ValidationError(
            'Monthly income must be at least $500',
            code='insufficient_income'
        )
    
    if value > Decimal('1000000'):
        raise ValidationError(
            'Monthly income seems unusually high, please verify',
            code='excessive_income'
        )


def validate_employment_duration(value):
    """Validate employment duration in months"""
    if value < 0:
        raise ValidationError(
            'Employment duration cannot be negative',
            code='negative_duration'
        )
    
    if value > 600:  # 50 years
        raise ValidationError(
            'Employment duration seems unusually long',
            code='excessive_duration'
        )


def validate_debt_to_income_ratio(monthly_income, existing_debt_payments, requested_payment):
    """Validate debt-to-income ratio"""
    total_debt_payments = existing_debt_payments + requested_payment
    dti_ratio = (total_debt_payments / monthly_income) * 100
    
    if dti_ratio > 43:  # Standard DTI limit
        raise ValidationError(
            f'Debt-to-income ratio ({dti_ratio:.1f}%) exceeds maximum allowed (43%)',
            code='excessive_dti'
        )
    
    return dti_ratio


class BankAccountValidator:
    """Validate bank account details"""
    
    def __init__(self, account_number, routing_number=None):
        self.account_number = account_number
        self.routing_number = routing_number
    
    def validate(self):
        errors = []
        
        # Validate account number
        if not self.account_number or not self.account_number.isdigit():
            errors.append('Account number must contain only digits')
        elif len(self.account_number) < 8 or len(self.account_number) > 17:
            errors.append('Account number must be between 8 and 17 digits')
        
        # Validate routing number if provided
        if self.routing_number:
            if not self.routing_number.isdigit() or len(self.routing_number) != 9:
                errors.append('Routing number must be exactly 9 digits')
        
        if errors:
            raise ValidationError(errors)
        
        return True


def validate_collateral_value(loan_amount, collateral_value, loan_type):
    """Validate collateral value against loan amount"""
    if loan_type in ['SECURED', 'AUTO', 'MORTGAGE']:
        if not collateral_value:
            raise ValidationError(
                'Collateral value is required for secured loans',
                code='missing_collateral'
            )
        
        # Loan-to-value ratio check
        ltv_ratio = (loan_amount / collateral_value) * 100
        max_ltv = {
            'AUTO': 85,
            'MORTGAGE': 80,
            'SECURED': 75
        }
        
        if ltv_ratio > max_ltv.get(loan_type, 75):
            raise ValidationError(
                f'Loan-to-value ratio ({ltv_ratio:.1f}%) exceeds maximum for {loan_type} loans ({max_ltv.get(loan_type, 75)}%)',
                code='excessive_ltv'
            )


def validate_credit_score_requirements(credit_score, loan_type, loan_amount):
    """Validate credit score requirements based on loan type and amount"""
    min_scores = {
        'PERSONAL': 600,
        'AUTO': 580,
        'MORTGAGE': 620,
        'BUSINESS': 650,
        'STUDENT': 550
    }
    
    min_required = min_scores.get(loan_type, 600)
    
    # Higher amounts require higher scores
    if loan_amount > 50000:
        min_required += 50
    elif loan_amount > 100000:
        min_required += 100
    
    if credit_score < min_required:
        raise ValidationError(
            f'Credit score ({credit_score}) is below minimum requirement ({min_required}) for {loan_type} loans',
            code='insufficient_credit_score'
        )