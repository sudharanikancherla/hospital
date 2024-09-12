import random
def genotp():
    otp=''
    Syb=[chr(i) for i in range(ord('#'),ord('@')+1)]
    Caps=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    Sma=[chr(i) for i in range(ord('a'),ord('z')+1)]
    for i in range(0,2):
        otp=otp+random.choice(Syb)
        otp=otp+random.choice(Caps)
        otp=otp+random.choice(Sma)
    print(otp)
    return(otp)
print(genotp())
