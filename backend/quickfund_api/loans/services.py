import logging
from decimal import Decimal
from django.utils import timezone
from .models import Loan, CreditAssessment


logger = logging.getLogger(__name__)

class CreditScoringService:
    def __init__(self, user, loan_application):
        self.user = user
        self.loan = loan_application
        self.base_score = 300

    def calculate_credit_score(self):
        """Calculate credit score based on various factors"""
        score = self.base_score
        
        # Income verification (30% weight)
        score += self._calculate_income_score() * 0.3
        
        # Loan history (25% weight)
        score += self._calculate_history_score() * 0.25
        
        # Debt-to-income ratio (20% weight)
        score += self._calculate_debt_ratio_score() * 0.2
        
        # Employment stability (15% weight)
        score += self._calculate_employment_score() * 0.15
        
        # Other factors (10% weight)
        score += self._calculate_other_factors_score() * 0.1
        
        return min(850, max(300, int(score)))

    def _calculate_income_score(self):
        """Calculate score based on income verification"""
        if not self.user.monthly_income:
            return 50
        
        monthly_income = self.user.monthly_income
        loan_amount = self.loan.amount
        
        # Income to loan ratio
        if monthly_income >= loan_amount * 3:
            return 200
        elif monthly_income >= loan_amount * 2:
            return 150
        elif monthly_income >= loan_amount:
            return 100
        return 50

    def _calculate_history_score(self):
        """Calculate score based on loan history"""
        previous_loans = Loan.objects.filter(user=self.user).exclude(id=self.loan.id)
        
        if not previous_loans.exists():
            return 100  # Neutral for new customers
        
        completed_loans = previous_loans.filter(status='completed').count()
        defaulted_loans = previous_loans.filter(status='defaulted').count()
        
        if defaulted_loans > 0:
            return 0
        elif completed_loans >= 3:
            return 200
        elif completed_loans >= 1:
            return 150
        return 100

    def _calculate_debt_ratio_score(self):
        """Calculate debt-to-income ratio score"""
        if not self.user.monthly_income:
            return 50
        
        active_loans = Loan.objects.filter(
            user=self.user,
            status__in=['active', 'disbursed']
        )
        
        total_monthly_payment = sum([
            loan.calculate_repayment_amount() / loan.tenure_days * 30
            for loan in active_loans
        ])
        
        debt_ratio = total_monthly_payment / self.user.monthly_income
        
        if debt_ratio <= 0.3:
            return 200
        elif debt_ratio <= 0.5:
            return 150
        elif debt_ratio <= 0.7:
            return 100
        return 50

    def _calculate_employment_score(self):
        """Calculate employment stability score"""
        if self.user.employment_status in ['employed', 'self_employed']:
            return 150
        elif self.user.employment_status == 'student':
            return 100
        return 50

    def _calculate_other_factors_score(self):
        """Calculate other factors score"""
        score = 100
        
        # BVN verification
        if self.user.bvn:
            score += 50
        
        # Account verification
        if self.user.is_verified:
            score += 50
        
        return score

    def get_loan_decision(self, credit_score):
        """Get loan decision based on credit score"""
        if credit_score >= 650:
            return 'approved', Decimal('1.0')  # Full amount
        elif credit_score >= 550:
            return 'approved', Decimal('0.7')  # 70% of requested amount
        elif credit_score >= 450:
            return 'approved', Decimal('0.5')  # 50% of requested amount
        return 'rejected', Decimal('0.0')


class LoanProcessingService:
    def process_loan_application(self, loan_id):
        """Process loan application with credit scoring"""
        try:
            loan = Loan.objects.get(id=loan_id)
            
            # Calculate credit score
            scorer = CreditScoringService(loan.user, loan)
            credit_score = scorer.calculate_credit_score()
            decision, approval_percentage = scorer.get_loan_decision(credit_score)
            
            # Update loan with credit score
            loan.credit_score = credit_score
            loan.save()
            
            # Create credit assessment
            assessment = CreditAssessment.objects.create(
                user=loan.user,
                loan=loan,
                risk_score=credit_score,
                decision=decision,
                approval_percentage=approval_percentage
            )
            
            # Auto-approve if score is high enough
            if decision == 'approved' and credit_score >= 650:
                loan.status = 'approved'
                loan.approved_amount = loan.amount * approval_percentage
                loan.save()
                
                # Send approval notification
                from quickfund_api.notifications.tasks import send_loan_approval_notification
                send_loan_approval_notification.delay(loan.id)
            
            logger.info(f"Loan {loan.id} processed with score {credit_score}")
            
        except Exception as e:
            logger.error(f"Error processing loan {loan_id}: {str(e)}")

    def process_loan_decision(self, loan, approved_by):
        """Process manual loan decision"""
        if loan.status == 'approved':
            # Calculate repayment details
            if not loan.approved_amount:
                loan.approved_amount = loan.amount
            
            loan.total_repayment = loan.calculate_repayment_amount()
            loan.balance = loan.total_repayment
            loan.due_date = timezone.now().date() + timezone.timedelta(days=loan.tenure_days)
            loan.save()
            # Send approval notification
            from quickfund_api.notifications.tasks import send_loan_approval_notification
            send_loan_approval_notification.delay(loan.id)
            
        elif loan.status == 'rejected':
            # Send rejection notification
            from quickfund_api.notifications.tasks import send_loan_rejection_notification
            send_loan_rejection_notification.delay(loan.id)