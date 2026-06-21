# a = input("Enter a number: ")
# print(type(a))
# class X:
#     a = 1

# print(type(X))
# # print(X.a)
# a = "hey there how are you"
# b = len(a)
# print(len("hey there how are you"))
# print(type(b))

x = int(input("Enter Year: "))
if x%4 == 0 and x%100 != 0:
    print("Leap Year")
elif x%400 == 0 and x%100 == 0:
    print("Leap Year")
else:    print("Not a Leap Year")