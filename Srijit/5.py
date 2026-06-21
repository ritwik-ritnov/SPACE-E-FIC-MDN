y=int(input("year"))
x=y%4
z=y%400
if(x==0):
    print(y,"is a leep year")
elif(z==0):
    print(y,"is a leap year.")
else:
    print(y,"is not a leep year")

    

