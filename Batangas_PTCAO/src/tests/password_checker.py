import bcrypt

hashed_password = b"$2b$12$yHvs1h6D4gK1IbZnNRQG2eMxqRvUNBX7O0jwF6AGF6CF6GqXG/vZK"
input_password = "juandelacruz".encode('utf-8')

if bcrypt.checkpw(input_password, hashed_password):
    print("✅ Password matches!")
else:
    print("❌ Incorrect password.")
