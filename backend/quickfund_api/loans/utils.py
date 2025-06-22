from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class LoanCalculator:
    """Utility class for loan calculations."""
    
    @staticmethod
    def calculate_monthly_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
        """
        Calculate monthly payment using the standard loan payment formula.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            term_months: Loan term in months
            
        Returns:
            Monthly payment amount
        """
        if annual_rate == 0:
            return principal / term_months
        
        monthly_rate = annual_rate / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                 ((1 + monthly_rate) ** term_months - 1)
        
        return Decimal(str(round(payment, 2)))
    
    @staticmethod
    def calculate_total_interest(principal: Decimal, monthly_payment: Decimal, term_months: int) -> Decimal:
        """Calculate total interest over the life of the loan."""
        total_paid = monthly_payment * term_months
        return total_paid - principal
    
    @staticmethod
    def generate_amortization_schedule(principal: Decimal, annual_rate: Decimal, term_months: int) -> List[Dict]:
        """
        Generate an amortization schedule for a loan.
        
        Returns:
            List of dictionaries containing payment details for each month
        """
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, term_months)
        monthly_rate = annual_rate / 12
        
        schedule = []
        remaining_balance = principal
        
        for month in range(1, term_months + 1):
            interest_payment = remaining_balance * monthly_rate
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            # Ensure final payment clears any remaining balance due to rounding
            if month == term_months and remaining_balance > 0:
                principal_payment += remaining_balance
                remaining_balance = Decimal('0.00')
            
            schedule.append({
                'month': month,
                'payment': monthly_payment,
                'principal': round(principal_payment, 2),
                'interest': round(interest_payment, 2),
                'balance': max(round(remaining_balance, 2), Decimal('0.00'))
            })
        
        return schedule


class CreditScoreCalculator:
    """Utility class for credit score and assessment calculations."""
    
    CREDIT_SCORE_RANGES = {
        'excellent': (750, 850),
        'good': (700, 749),
        'fair': (650, 699),
        'poor': (600, 649),
        'bad': (300, 599)
    }
    
    @staticmethod
    def get_credit_rating(score: int) -> str:
        """Get credit rating based on score."""
        for rating, (min_score, max_score) in CreditScoreCalculator.CREDIT_SCORE_RANGES.items():
            if min_score <= score <= max_score:
                return rating
        return 'unknown'
    
    @staticmethod
    def calculate_risk_factor(credit_score: int, debt_to_income: Decimal, employment_years: int) -> Decimal:
        """
        Calculate a risk factor based on various criteria.
        
        Args:
            credit_score: Credit score (300-850)
            debt_to_income: Debt-to-income ratio as decimal (e.g., 0.3 for 30%)
            employment_years: Years of employment
            
        Returns:
            Risk factor between 0.0 (lowest risk) and 1.0 (highest risk)
        """
        # Credit score component (0.5 weight)
        credit_risk = max(0, (750 - credit_score) / 450) * 0.5
        
        # Debt-to-income component (0.3 weight)
        dti_risk = min(1.0, float(debt_to_income) / 0.5) * 0.3
        
        # Employment component (0.2 weight)
        employment_risk = max(0, (5 - employment_years) / 5) * 0.2
        
        total_risk = credit_risk + dti_risk + employment_risk
        return Decimal(str(round(min(total_risk, 1.0), 3)))
    
    @staticmethod
    def suggest_interest_rate(credit_score: int, base_rate: Decimal = Decimal('0.05')) -> Decimal:
        """
        Suggest an interest rate based on credit score.
        
        Args:
            credit_score: Applicant's credit score
            base_rate: Base interest rate (default 5%)
            
        Returns:
            Suggested annual interest rate
        """
        rating = CreditScoreCalculator.get_credit_rating(credit_score)
        
        rate_adjustments = {
            'excellent': Decimal('0.00'),    # No adjustment
            'good': Decimal('0.01'),         # +1%
            'fair': Decimal('0.025'),        # +2.5%
            'poor': Decimal('0.05'),         # +5%
            'bad': Decimal('0.10'),          # +10%
            'unknown': Decimal('0.15')       # +15%
        }
        
        adjustment = rate_adjustments.get(rating, Decimal('0.15'))
        return base_rate + adjustment


class LoanStatusManager:
    """Utility class for managing loan statuses and transitions."""
    
    VALID_STATUSES = [
        'pending',
        'under_review',
        'approved',
        'rejected',
        'active',
        'completed',
        'defaulted',
        'cancelled'
    ]
    
    STATUS_TRANSITIONS = {
        'pending': ['under_review', 'cancelled'],
        'under_review': ['approved', 'rejected'],
        'approved': ['active', 'cancelled'],
        'rejected': [],
        'active': ['completed', 'defaulted'],
        'completed': [],
        'defaulted': [],
        'cancelled': []
    }
    
    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """Check if a status transition is valid."""
        return new_status in LoanStatusManager.STATUS_TRANSITIONS.get(current_status, [])
    
    @staticmethod
    def get_valid_transitions(current_status: str) -> List[str]:
        """Get list of valid status transitions from current status."""
        return LoanStatusManager.STATUS_TRANSITIONS.get(current_status, [])


class DateTimeUtils:
    """Utility functions for date and time operations."""
    
    @staticmethod
    def add_business_days(start_date: datetime, days: int) -> datetime:
        """Add business days to a date (excluding weekends)."""
        current_date = start_date
        days_added = 0
        
        while days_added < days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                days_added += 1
        
        return current_date
    
    @staticmethod
    def get_next_payment_date(start_date: datetime, payment_number: int) -> datetime:
        """Calculate the next payment date based on start date and payment number."""
        # Add months to the start date
        month = start_date.month + payment_number - 1
        year = start_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        
        try:
            return start_date.replace(year=year, month=month)
        except ValueError:
            # Handle cases like Jan 31 -> Feb 28/29
            if month == 2:
                # February edge case
                last_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                day = min(start_date.day, last_day)
            else:
                # Other months with fewer days
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                day = min(start_date.day, days_in_month[month - 1])
            
            return start_date.replace(year=year, month=month, day=day)


class ValidationUtils:
    """Utility functions for data validation."""
    
    @staticmethod
    def validate_loan_amount(amount: Decimal, min_amount: Decimal = Decimal('1000'), 
                           max_amount: Decimal = Decimal('1000000')) -> bool:
        """Validate loan amount is within acceptable range."""
        return min_amount <= amount <= max_amount
    
    @staticmethod
    def validate_credit_score(score: int) -> bool:
        """Validate credit score is within valid range."""
        return 300 <= score <= 850
    
    @staticmethod
    def validate_interest_rate(rate: Decimal) -> bool:
        """Validate interest rate is reasonable."""
        return Decimal('0.001') <= rate <= Decimal('0.50')  # 0.1% to 50%
    
    @staticmethod
    def validate_loan_term(term_months: int, min_months: int = 6, max_months: int = 360) -> bool:
        """Validate loan term is within acceptable range."""
        return min_months <= term_months <= max_months


# Constants that can be used across the loans app
DEFAULT_INTEREST_RATE = Decimal('0.05')  # 5%
MIN_LOAN_AMOUNT = Decimal('1000')
MAX_LOAN_AMOUNT = Decimal('1000000')
MIN_LOAN_TERM_MONTHS = 6
MAX_LOAN_TERM_MONTHS = 360  # 30 years
DEFAULT_PROCESSING_DAYS = 5