#counts the total number of vowels and consonants in a given sentence, ignoring spaces
x=(input("any string"))
z=[]
Vowels=0
for i in x:
    z.append(i)
for i in z:
    if(i=="a"):
        Vowels+=1
    elif(i=="e"):
        Vowels+=1
    elif(i=="i"):
        Vowels+=1
    elif(i=="o"):
        Vowels+=1
    elif(i=="u"):
        Vowels+=1
f=x.replace(" ","")
y=len(f)

Consonants=y-Vowels
print("Consonants=",Consonants)
print("Vowels=",Vowels)



    
        
        
    
