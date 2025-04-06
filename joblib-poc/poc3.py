import time
from joblib import Parallel, delayed
import math

def heavy_compute_task(i):
    return math.factorial(int(math.sqrt(i**3)))

def parallel_heavy_compute(start, end):
    return Parallel(n_jobs=-1)(delayed(heavy_compute_task)(i) for i in range(start, end))

t1 = time.time()

# Call the function with the desired range
r1 = parallel_heavy_compute(100, 1000)

t2 = time.time()

print(t2 - t1)