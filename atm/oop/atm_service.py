from atm.oop.domain import ATMError


class ATMService:
    """
    Manages active accounts and ATM session states.
    """

    def __init__(self, accounts, pin = "1234"):
        self.__accounts = accounts
        self.__pin = str(pin)
        self.__session_active = False
        self.__failed_attempts = 0
        self.__max_attempts = 4
        
    # login
    def authenticate(self, pin):

        if self.__session_active:
            raise ATMError("ATM is already unlocked.")

        if self.__failed_attempts >= self.__max_attempts:
            raise ATMError("ATM access is locked.")

        if str(pin) != self.__pin:
            self.__failed_attempts += 1

            remaining = self.__max_attempts - self.__failed_attempts

            if remaining == 0:
                raise ATMError("PIN locked after three incorrect attempts.")

            raise ATMError(
                f"Incorrect PIN. {remaining} attempts remaining."
            )

        self.__session_active = True
        self.__failed_attempts = 0

        return True

    # logout
    def logout(self):
        if not self.__session_active:
            raise ATMError("ATM is already locked.")

        self.__session_active = False

    # get current account
    def get_accounts(self):
        if not self.__session_active:
            raise ATMError("Please unlock the ATM first.")

        return self.__accounts
    
    def reset_lock(self):
        if self.__session_active:
            raise ATMError("ATM is already unlocked.")
        
        self.__failed_attempts = 0

    # check if session is active
    @property
    def session_active(self):
        return self.__session_active
