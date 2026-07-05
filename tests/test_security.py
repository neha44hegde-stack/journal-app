import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import JournalCipher, WrongPasswordError, generate_salt


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.salt = generate_salt()

    def test_encrypt_decrypt_round_trip(self):
        cipher = JournalCipher("correct-password", self.salt)
        plaintext = "Dear diary, today was interesting."
        encrypted = cipher.encrypt(plaintext)
        self.assertNotEqual(encrypted, plaintext)
        decrypted = cipher.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_wrong_password_raises(self):
        cipher = JournalCipher("correct-password", self.salt)
        encrypted = cipher.encrypt("secret text")

        wrong_cipher = JournalCipher("wrong-password", self.salt)
        with self.assertRaises(WrongPasswordError):
            wrong_cipher.decrypt(encrypted)

    def test_different_salts_produce_different_ciphertext(self):
        salt_a = generate_salt()
        salt_b = generate_salt()
        cipher_a = JournalCipher("same-password", salt_a)
        cipher_b = JournalCipher("same-password", salt_b)
        self.assertNotEqual(
            cipher_a.encrypt("hello"), cipher_b.encrypt("hello")
        )

    def test_salt_is_correct_length(self):
        self.assertEqual(len(generate_salt()), 16)


if __name__ == "__main__":
    unittest.main()