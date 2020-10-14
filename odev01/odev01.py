import sys

user_dict = {}

for i in range(int(sys.argv[1])):
    my_str = input('Sirasiyla ID, isim, soyisim ve yasinizi giriniz:')
    my_str = my_str.split(' ')
    if len(my_str) > 5:
        print('Gerekenden fazla veri girdiniz')
    if len(my_str) > 4:
        try:
            user_id = int(my_str[0])
        except:
            print("ID'niz sayi olmalidir")
        try:
            user_name = str(my_str[1]) +" "+str(my_str[2])
        except:
            print("İsminiz sadece harflerden olusmalidir.")
        try:
            user_surname = str(my_str[3])
        except:
            print("Soyadiniz sadece harflerden olusmalidir")
        try:
            user_age = int(my_str[4])
        except:
            print("Yasiniz sayi olmalidir.")
    else:
        try:
            user_id = int(my_str[0])
        except:
            print("ID'niz sayi olmalidir")
        try:
            user_name = str(my_str[1])
        except:
            print("İsminiz sadece harflerden olusmalidir.")
        try:
            user_surname = str(my_str[2])
        except:
            print("Soyadiniz sadece harflerden olusmalidir")
        try:
            user_age = int(my_str[3])
        except:
            print("Yasiniz sayi olmalidir.")

    if user_id in user_dict:
        print("Kullanici numarasi veritabaninda bulunmaktadır. Farklı numara giriniz.")
        continue

    user_tuple = (user_name, user_surname, user_age)
    user_dict.update({ user_id: user_tuple})

    sort_users = sorted(user_dict.items(), key= lambda x: x[0])
    for j in sort_users:
        print(j[0], j[1])