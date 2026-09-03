import bcrypt

def generate_hash(password):
    # Generar un salt y el hash de la contraseña
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    print("--- Generador de Hashes para Zona Fit Evolution ---")
    password_to_hash = input("Ingresa la contraseña que deseas encriptar: ")
    hash_result = generate_hash(password_to_hash)
    print(f"\nTu contraseña encriptada es:\n{hash_result}")
    print("\nCopia este código y pégalo en tu archivo SQL o base de datos.")
