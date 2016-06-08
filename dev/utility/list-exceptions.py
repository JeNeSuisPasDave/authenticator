import builtins

for x in dir(builtins):
    if x.endswith('Error'): print(x)
