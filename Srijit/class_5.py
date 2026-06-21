import time
h = int(time.strftime("%H"))
if 6 <= h <12:
    print("Good Morning")
elif 12 <= h <18:
    print("Good Evening")
elif 18 <= h <5:
    print("Good Night")
p=[3,7,6,8,5,4,4,7,3,890,2]
print(p)
print(type(p))
p.sort()
print(p)
p.remove(4)
print(p)
print(p[0])
x="how are you"
print(x.split())
p.append(3)
print(p)
p.pop(6)
print(p)
p.remove(7)
print(p)




