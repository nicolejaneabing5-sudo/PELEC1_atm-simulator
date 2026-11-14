from atm.oop.domain import ATMError

class ATMService:
    """
    Manages active accounts and handles session states (authentication, 
    current user tracking, and session logout).
    """
    def __init__(self, accounts_dict: dict):
        self.accounts = accounts_dict
        self.current_account_number = None

    def authenticate(self, account_number: str, pin: str) -> bool:
        """
        Validates account existence and PIN, then establishes the active session state.
        """
        if account_number not in self.accounts:
            raise ATMError("Account not found.")
        
        account = self.accounts[account_number]
        
        # Verify PIN via domain model method or attribute
        if hasattr(account, 'verify_pin'):
            if not account.verify_pin(pin):
                raise ATMError("Invalid PIN.")
        elif getattr(account, 'pin', None) != pin:
            raise ATMError("Invalid PIN.")

        # Set active session state
        self.current_account_number = account_number
        return True

    def logout(self) -> None:
        """Clears the active session state."""
        self.current_account_number = None

    def get_current_account(self):
        """Returns the account object for the currently active session."""
        if self.current_account_number and self.current_account_number in self.accounts:
            return self.accounts[self.current_account_number]
        return None