import unittest
from decimal import Decimal
from main import Account, AccountRepository, TransactionService, TransactionDto

class TestTransactionService(unittest.TestCase):

    def setUp(self):
        self.repo = AccountRepository()
        self.service = TransactionService(self.repo)
        self.repo._accounts.clear()
        self.repo.save(Account(1, Decimal("100.00")))
        self.repo.save(Account(2, Decimal("50.00")))

    def test_transfer_success(self):
        trans = TransactionDto(1, "09/09/2023 14:00:00", 1, 2, Decimal("40.00"))
        self.service.transfer(trans)
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("60.00"))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("90.00"))

    def test_transfer_insufficient_balance(self):
        trans = TransactionDto(2, "09/09/2023 14:00:00", 2, 1, Decimal("100.00"))
        self.service.transfer(trans)
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("50.00"))

    def test_prevent_same_account_transfer(self):
        """Garante que transferir para si mesmo não causa deadlock e é rejeitado"""
        trans = TransactionDto(3, "09/09/2023 14:00:00", 1, 1, Decimal("10.00"))
        self.service.transfer(trans)
        # O saldo deve continuar intacto
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))

if __name__ == '__main__':
    unittest.main()