import time 
import math 
  
t1 = time.time() 
  
# Normal 
r = [math.factorial(int(math.sqrt(i**3))) for i in range(100,1000)] 
  
t2 = time.time() 
  
print(t2-t1) 
