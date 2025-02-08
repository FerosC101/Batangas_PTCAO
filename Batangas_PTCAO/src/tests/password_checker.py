import bcrypt

hashed_password = b"$2b$12$beUYqIixa29lAsJOJyv11.lVR3.atrovI3TBqe6.E21pEsxeuqlHO"
input_password = "1234".encode('utf-8')

if bcrypt.checkpw(input_password, hashed_password):
    print("✅ Password matches!")
else:
    print("❌ Incorrect password.")
