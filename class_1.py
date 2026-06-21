#Date - 26/04/2026 (Sunday)

# a5 = '20.0'
# srijit = "I'm a good boy."
# # print(a)
# # print(type(a5))
# # print(srijit)
# # print(type(srijit))
# print(a5+srijit)

# print(a5,srijit)
# print('hey there')

# a,b = 20.0,10
# c=a/b
# print(type(b))
# # print("your sum result is =",c)
# print(a/b)

a = float(input("Type Your First Number =")) #typecasting, from str to float
b = float(input("Type Your Second Number ="))
# print(type(a))
opr = int(input("Type of your operation ?")) #typecasting to int
# c = a+b
if opr==0:
    c=a+b
elif opr==1:
    c=a-b
elif opr==2:
    c=a*b
elif opr==3:
    c=a/b

print("Answere = ",c)