'''x = int(input("Enrter:"))
y = 0
for i in range(1, x+1):
  y=y+i
print(y)'''
'''for i in range(-10,0):
    print(i)
    if(i==-1):
        print("done")
x = int(input("Enrter:"))
for i in range(1,11):
    y=i*x
    print(y)'''
'''a= int(input("Enrter:"))
for i in range (1,a+1):
    b=i**3
    print("current number-",i," cube is-",b)'''
c = [12, 75, 150, 180, 145, 525, 50]
for i in c:
    
    if(i%5!=0):
        continue
    elif(i%5==0 and i>150):
        continue
    print(i)
    if(i>500):
        break
numbers = [12, 75, 150, 180, 145, 525, 50]

for item in numbers:
    # Condition 3: Stop the loop if number > 500
    if item > 500:
        break
    
    # Condition 2: Skip the number if > 150
    if item > 150:
        continue
    
    # Condition 1: Print if divisible by 5
    if item % 5 == 0:
        print(item)
    
        
        


    




        

