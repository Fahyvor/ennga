import random
import string

def generate_email():
    users_alphabets = "".join(random.choices(string.ascii_lowercase, k=5))
    users_number = random.randint(00000, 99999)
    email_ = str(users_alphabets) + str(users_number)
    email = "deleted-user-" + email_ + "@ennga.com"
    return email