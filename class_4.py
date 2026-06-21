import time

hour = int(time.strftime("%H"))
if 6 <= hour < 12:
    print("Good Morning")
elif 12 <= hour < 18:
    print("Good Afternoon")
elif 18 <= hour < 24:
    print("Good Evening")
else:    print("Good Night")

x  = "how are you Amal?"
z = "Hello"
y = x.replace("Amal", "Syamal")
# print(z,y)
# m = ",".join(z,y)
# print(m)
n = x.split()
print(n)
print(type(n))

# print(n[0]+n[1])
n.append(3)
print(n)
# a = ("a", "b", "c", "d")
# print(type(a))
d = [1, 2, 3, 4, "Amal, ", "Syamal",2, 2]
print(d.count(2))

d.reverse()
print(d)

e = [3, 7, 1, 5, 2]
e.sort()
print(e)