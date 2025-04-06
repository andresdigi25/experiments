import time 
from joblib import Parallel,delayed 
import math 

t1 = time.time() 

# 2 Core 
r1 = Parallel(n_jobs=-1)(delayed(math.factorial) (int(math.sqrt(i**3))) for i in range(100,1000)) 

t2 = time.time() 

print(t2-t1) 
