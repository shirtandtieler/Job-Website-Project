
class AccountType:
    SEEKER, COMPANY, ADMIN = "Seeker", "Company", "Admin"

    @staticmethod
    def value_of(type_name: str):
        """ Expands a guessed name to the actual one """
        guess = type_name.lower()
        actual = None
        if guess[0] == "s" or guess.startswith("cand"):  # seeker / candidate
            actual = AccountType.SEEKER
        elif guess[0] == "c" or guess.startswith("emp"):  # company / employee
            actual = AccountType.COMPANY
        elif guess[0] == "a" or guess.startswith("super"):  # admin / superuser
            actual = AccountType.ADMIN
        return actual
