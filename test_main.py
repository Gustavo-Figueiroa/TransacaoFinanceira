import unittest
import threading
from decimal import Decimal
from datetime import datetime
from main import Account, AccountRepository, TransactionService, TransactionDto

# TESTES DE UNIDADE - TransacaoFinanceira

class TestAccount(unittest.TestCase):
    """Testes para a entidade Account."""

    def test_account_creation_valid(self):
        acc = Account(1, Decimal("100.00"))
        self.assertEqual(acc.account_id, 1)
        self.assertEqual(acc.balance, Decimal("100.00"))

    def test_account_creation_zero_balance(self):
        """Conta com saldo zero é válida."""
        acc = Account(2, Decimal("0"))
        self.assertEqual(acc.balance, Decimal("0"))

    def test_account_creation_negative_balance_raises(self):
        """Saldo inicial negativo deve lançar ValueError."""
        with self.assertRaises(ValueError):
            Account(3, Decimal("-1"))

    def test_account_has_lock(self):
        """Cada conta deve possuir um RLock para concorrência."""
        acc = Account(4, Decimal("50"))
        self.assertIsInstance(acc.lock, type(threading.RLock()))


class TestTransactionDto(unittest.TestCase):
    """Testes para o DTO de transação."""

    def test_parsed_datetime_correct(self):
        dto = TransactionDto(1, "09/09/2023 14:15:00", 1, 2, Decimal("100"))
        expected = datetime(2023, 9, 9, 14, 15, 0)
        self.assertEqual(dto.parsed_datetime, expected)

    def test_parsed_datetime_ordering(self):
        """Transações devem ser ordenadas corretamente por data/hora."""
        t1 = TransactionDto(1, "09/09/2023 14:15:00", 1, 2, Decimal("10"))
        t2 = TransactionDto(2, "09/09/2023 14:19:01", 2, 1, Decimal("10"))
        sorted_list = sorted([t2, t1], key=lambda x: x.parsed_datetime)
        self.assertEqual(sorted_list[0].correlation_id, 1)
        self.assertEqual(sorted_list[1].correlation_id, 2)


class TestAccountRepository(unittest.TestCase):
    """Testes para o repositório de contas."""

    def setUp(self):
        self.repo = AccountRepository()

    def test_seed_data_loaded(self):
        """Repositório deve ter contas pré-carregadas."""
        self.assertIsNotNone(self.repo.get_by_id(938485762))

    def test_get_by_id_existing(self):
        acc = self.repo.get_by_id(938485762)
        self.assertEqual(acc.balance, Decimal("180"))

    def test_get_by_id_nonexistent_returns_none(self):
        """Conta inexistente deve retornar None."""
        result = self.repo.get_by_id(9999999)
        self.assertIsNone(result)

    def test_save_and_retrieve(self):
        new_acc = Account(777, Decimal("250"))
        self.repo.save(new_acc)
        retrieved = self.repo.get_by_id(777)
        self.assertEqual(retrieved.balance, Decimal("250"))

    def test_save_overwrites_existing(self):
        """Salvar conta com mesmo ID deve sobrescrever."""
        acc_v1 = Account(888, Decimal("100"))
        acc_v2 = Account(888, Decimal("999"))
        self.repo.save(acc_v1)
        self.repo.save(acc_v2)
        self.assertEqual(self.repo.get_by_id(888).balance, Decimal("999"))


class TestTransactionService(unittest.TestCase):
    """Testes para o serviço de transações."""

    def setUp(self):
        self.repo = AccountRepository()
        self.repo._accounts.clear()
        self.repo.save(Account(1, Decimal("100.00")))
        self.repo.save(Account(2, Decimal("50.00")))
        self.service = TransactionService(self.repo)

    def _make_tx(self, corr_id, origin, dest, amount):
        return TransactionDto(corr_id, "09/09/2023 14:00:00", origin, dest, amount)

    # Casos de sucesso
 
    def test_transfer_success_deducts_origin(self):
        """Transferência bem-sucedida deve debitar a origem."""
        self.service.transfer(self._make_tx(1, 1, 2, Decimal("40.00")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("60.00"))

    def test_transfer_success_credits_destination(self):
        """Transferência bem-sucedida deve creditar o destino."""
        self.service.transfer(self._make_tx(1, 1, 2, Decimal("40.00")))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("90.00"))

    def test_transfer_exact_balance(self):
        """Transferência com valor exatamente igual ao saldo deve ser efetivada."""
        self.service.transfer(self._make_tx(2, 1, 2, Decimal("100.00")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("0"))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("150.00"))

    # Casos de falha / cancelamento
    def test_transfer_insufficient_balance_does_not_deduct(self):
        """Saldo insuficiente não deve debitar a origem."""
        self.service.transfer(self._make_tx(3, 2, 1, Decimal("100.00")))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("50.00"))

    def test_transfer_insufficient_balance_does_not_credit(self):
        """Saldo insuficiente não deve creditar o destino."""
        self.service.transfer(self._make_tx(3, 2, 1, Decimal("100.00")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))

    def test_transfer_same_account_rejected(self):
        """Transferência para a mesma conta deve ser rejeitada sem alterar saldo."""
        self.service.transfer(self._make_tx(4, 1, 1, Decimal("10.00")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))

    def test_transfer_zero_amount_rejected(self):
        """Valor zero não deve ser processado."""
        self.service.transfer(self._make_tx(5, 1, 2, Decimal("0")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("50.00"))

    def test_transfer_negative_amount_rejected(self):
        """Valor negativo não deve ser processado."""
        self.service.transfer(self._make_tx(6, 1, 2, Decimal("-10")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))

    def test_transfer_origin_not_found(self):
        """Conta origem inexistente deve cancelar sem alterar contas existentes."""
        self.service.transfer(self._make_tx(7, 9999, 2, Decimal("10")))
        self.assertEqual(self.repo.get_by_id(2).balance, Decimal("50.00"))

    def test_transfer_destination_not_found(self):
        """Conta destino inexistente deve cancelar sem alterar contas existentes."""
        self.service.transfer(self._make_tx(8, 1, 9999, Decimal("10")))
        self.assertEqual(self.repo.get_by_id(1).balance, Decimal("100.00"))


    # Cenário da tarefa original (linha do tempo completa)
   
    def test_scenario_transaction_1_efetivada(self):
        """
        Transação 1: conta 938485762 (saldo 180) envia 150 para 2147483649.
        Esperado: efetivada. Origem fica com 30, destino com 150.
        """
        repo = AccountRepository()
        svc  = TransactionService(repo)
        tx = TransactionDto(1, "09/09/2023 14:15:00", 938485762, 2147483649, Decimal("150"))
        svc.transfer(tx)
        self.assertEqual(repo.get_by_id(938485762).balance,  Decimal("30"))
        self.assertEqual(repo.get_by_id(2147483649).balance, Decimal("150"))

    def test_scenario_transaction_2_efetivada_apos_tx1(self):
        """
        Transação 2 só tem saldo porque a transação 1 depositou 150 antes.
        Garante que a ordenação cronológica é respeitada.
        """
        repo = AccountRepository()
        svc  = TransactionService(repo)
        # Tx 1 primeiro (ordem cronológica)
        svc.transfer(TransactionDto(1, "09/09/2023 14:15:00", 938485762,  2147483649, Decimal("150")))
        svc.transfer(TransactionDto(2, "09/09/2023 14:15:05", 2147483649, 210385733,  Decimal("149")))
        self.assertEqual(repo.get_by_id(2147483649).balance, Decimal("1"))
        self.assertEqual(repo.get_by_id(210385733).balance,  Decimal("159"))

    def test_scenario_transaction_4_cancelada_saldo_insuficiente(self):
        """
        Transação 4: conta 675869708 (saldo 4900) tenta enviar 5300.
        Esperado: cancelada por falta de saldo.
        """
        repo = AccountRepository()
        svc  = TransactionService(repo)
        tx = TransactionDto(4, "09/09/2023 14:17:00", 675869708, 210385733, Decimal("5300"))
        svc.transfer(tx)
        self.assertEqual(repo.get_by_id(675869708).balance, Decimal("4900"))

    
    # Teste de concorrência (race condition)
    def test_concurrent_transfers_no_race_condition(self):
        """
        Dispara 100 threads tentando transferir R$1 da conta 1 para conta 2 simultaneamente.
        O saldo final deve ser consistente (sem valores negativos ou inconsistentes).
        """
        repo = AccountRepository()
        repo._accounts.clear()
        repo.save(Account(1, Decimal("100")))
        repo.save(Account(2, Decimal("0")))
        svc = TransactionService(repo)

        threads = [
            threading.Thread(
                target=svc.transfer,
                args=(TransactionDto(i, "09/09/2023 14:00:00", 1, 2, Decimal("1")),)
            )
            for i in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        balance_origin      = repo.get_by_id(1).balance
        balance_destination = repo.get_by_id(2).balance

        # Saldo nunca pode ser negativo
        self.assertGreaterEqual(balance_origin,      Decimal("0"))
        self.assertGreaterEqual(balance_destination, Decimal("0"))
        # Soma dos saldos deve ser conservada (sem dinheiro criado ou destruído)
        self.assertEqual(balance_origin + balance_destination, Decimal("100"))

    def test_concurrent_bidirectional_no_deadlock(self):
        """
        Transferências cruzadas simultâneas (1->2 e 2->1) não devem causar deadlock.
        """
        repo = AccountRepository()
        repo._accounts.clear()
        repo.save(Account(1, Decimal("500")))
        repo.save(Account(2, Decimal("500")))
        svc = TransactionService(repo)

        results = []

        def do_transfer(corr_id, orig, dest):
            svc.transfer(TransactionDto(corr_id, "09/09/2023 14:00:00", orig, dest, Decimal("100")))
            results.append(corr_id)

        threads = []
        for i in range(50):
            threads.append(threading.Thread(target=do_transfer, args=(i,      1, 2)))
            threads.append(threading.Thread(target=do_transfer, args=(i + 50, 2, 1)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todos os 100 transfers devem ter sido tentados (sem deadlock travando threads)
        self.assertEqual(len(results), 100)
        # Conservação do dinheiro
        total = repo.get_by_id(1).balance + repo.get_by_id(2).balance
        self.assertEqual(total, Decimal("1000"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
