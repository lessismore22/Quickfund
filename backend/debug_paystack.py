import sys
import os
sys.path.append('/root/Quickfund/backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

try:
    from quickfund_api.payments.base import BasePaymentProvider
    from quickfund_api.payments.providers.paystack import PaystackProvider
    
    print("Base class abstract methods:")
    print([method for method in dir(BasePaymentProvider) if getattr(getattr(BasePaymentProvider, method), '__isabstractmethod__', False)])
    
    print("\nPaystackProvider methods:")
    print([method for method in dir(PaystackProvider) if not method.startswith('_')])
    
    print("\nTrying to instantiate PaystackProvider...")
    provider = PaystackProvider()
    print("SUCCESS: PaystackProvider instantiated successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e)}")
    
    # Check if it's still abstract
    if "abstract" in str(e).lower():
        print("\nChecking abstract methods...")
        try:
            from quickfund_api.payments.providers.paystack import PaystackProvider
            abstract_methods = getattr(PaystackProvider, '__abstractmethods__', set())
            print(f"Missing abstract methods: {abstract_methods}")
        except Exception as inner_e:
            print(f"Could not check abstract methods: {inner_e}")