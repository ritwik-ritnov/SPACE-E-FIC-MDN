'''a=str(input("any name:"))
for i in a:
    print(i)'''
#problem1
b=[20,50,30,20,22,100,50]
c=[]
for i in b:
    if(i>99):
        break
    elif(i%5!=0):
        continue
    c.append(i)
c.sort()
print(c)








