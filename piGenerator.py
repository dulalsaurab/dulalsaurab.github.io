
from math import factorial
from decimal import Decimal, getcontext



def check_prime():
    pass

def print_ulm_spiral(num):
    
    pass 




def piGenerator(x):
    # num is no of digits you want to generate PI for

    '''
    Algorithm: 
    1. get a 
    '''
  
    from decimal import Decimal, getcontext
    getcontext().prec=2000
    print sum(1/Decimal(16)**k * 
          (Decimal(4)/(8*k+1) - 
           Decimal(2)/(8*k+4) - 
           Decimal(1)/(8*k+5) -
           Decimal(1)/(8*k+6)) for k in range(100))


piGenerator(2)