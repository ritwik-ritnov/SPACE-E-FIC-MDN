x = "hey there how are you"
y = x.split()
print(y)
for i in y:
    print(i)
    if i == "how":
        break
    