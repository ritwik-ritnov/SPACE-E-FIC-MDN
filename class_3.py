a=int(input("enter year"))
b=a%4
c=a%100
d=a%400
if(b==0 & c!=0):
    print(a,"is a leap year")
elif(d==0 & c==0):
    print(a,"is a leap year")
else:
    print(a,"is not a leap year")
    
    
