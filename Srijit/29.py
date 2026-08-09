def factorial(num):
    b=1
    for i in range (1,num+1):
        c=b*i
        b=c
    print(c)
factorial(5)
