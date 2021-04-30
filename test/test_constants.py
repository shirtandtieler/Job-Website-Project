import unittest
from app.constants import AccountType


class MyTestCase(unittest.TestCase):
    def test_seeker_values(self):
        self.assertEqual(AccountType.value_of("candidate"), AccountType.SEEKER)
        self.assertEqual(AccountType.value_of("CANDID"), AccountType.SEEKER)
        self.assertEqual(AccountType.value_of("SEEKER"), AccountType.SEEKER)

    def test_company_values(self):
        self.assertEqual(AccountType.value_of("COMPANY"), AccountType.COMPANY)
        self.assertEqual(AccountType.value_of("employee"), AccountType.COMPANY)
        self.assertEqual(AccountType.value_of("EmPlOyE"), AccountType.COMPANY)

    def test_admin_values(self):
        self.assertEqual(AccountType.value_of("admin user"), AccountType.ADMIN)
        self.assertEqual(AccountType.value_of("ADMIN"), AccountType.ADMIN)
        self.assertEqual(AccountType.value_of("SUpeR user"), AccountType.ADMIN)


if __name__ == '__main__':
    unittest.main()
