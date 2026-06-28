a=0

while a<50:
    a+=1
    print(a)
rows = 5
n=8
i = 1

while i <= rows:
    print(" "*n+"* " * i)
    i += 1
    n=n-2
rows = 5
i = 1

while i <= rows:
    j = 1
    while j <= i:
        print("*", end=" ")
        j += 1
    print()  # Moves to the next line
    
    i += 1
# Shortcut for a Right-Angled Triangle
rows = 5
i = 1

while i <= rows:
    print("* " * i)
    i += 1



    

