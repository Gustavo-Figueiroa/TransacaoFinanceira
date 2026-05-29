import threading
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

# ==========================================
# 1. ENTIDADES (Domain)
# ==========================================
class Account:
    def __init__(self, account_id: int, initial_balance: Decimal):
        if initial_balance < Decimal("0"):
            raise ValueError("Saldo inicial não pode ser negativo.")
        self.account_id = account_id
        self.balance = initial_balance
        # RLock evita deadlock se a mesma thread tentar re-adquirir o lock
        self.lock = threading.RLock()

    def __repr__(self):
        return f"Account(id={self.account_id}, balance={self.balance})"


@dataclass
class TransactionDto:
    correlation_id: int
    datetime_str: str
    origin_account_id: int
    destination_account_id: int
    amount: Decimal

    @property
    def parsed_datetime(self) -> datetime:
        """Converte a string de data para objeto datetime para ordenação cronológica."""
        return datetime.strptime(self.datetime_str, "%d/%m/%Y %H:%M:%S")


# ==========================================
# 2. REPOSITÓRIO (Data Access)
# ==========================================
class AccountRepository:
    def __init__(self):
        self._accounts: Dict[int, Account] = {}
        self._seed_data()

    def _seed_data(self):
        contas_iniciais = [
            (938485762,  Decimal("180")),
            (347586970,  Decimal("1200")),
            (2147483649, Decimal("0")),
            (675869708,  Decimal("4900")),
            (238596054,  Decimal("478")),
            (573659065,  Decimal("787")),
            (210385733,  Decimal("10")),
            (674038564,  Decimal("400")),
            (563856300,  Decimal("1200")),
        ]
        for acc_id, balance in contas_iniciais:
            self.save(Account(acc_id, balance))

    def get_by_id(self, account_id: int) -> Optional[Account]:
        return self._accounts.get(account_id)

    def save(self, account: Account):
        self._accounts[account.account_id] = account


# ==========================================
# 3. SERVIÇO (Business Logic)
# ==========================================
class TransactionService:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def transfer(self, transaction: TransactionDto):
        # Validação: valor deve ser positivo
        if transaction.amount <= Decimal("0"):
            print(f"Transacao numero {transaction.correlation_id} rejeitada: Valor da transação deve ser positivo.")
            return

        # Validação: conta origem e destino não podem ser iguais
        if transaction.origin_account_id == transaction.destination_account_id:
            print(f"Transacao numero {transaction.correlation_id} rejeitada: Conta de origem e destino são iguais.")
            return

        origin      = self.repository.get_by_id(transaction.origin_account_id)
        destination = self.repository.get_by_id(transaction.destination_account_id)

        if origin is None or destination is None:
            print(f"Transacao numero {transaction.correlation_id} falhou: Conta não encontrada.")
            return

        # Deadlock Prevention: sempre adquire locks em ordem crescente de ID
        first_lock, second_lock = (
            (origin.lock, destination.lock)
            if origin.account_id < destination.account_id
            else (destination.lock, origin.lock)
        )

        with first_lock:
            with second_lock:
                if origin.balance < transaction.amount:
                    print(
                        f"Transacao numero {transaction.correlation_id} "
                        f"foi cancelada por falta de saldo"
                    )
                else:
                    origin.balance      -= transaction.amount
                    destination.balance += transaction.amount
                    print(
                        f"Transacao numero {transaction.correlation_id} foi efetivada com sucesso! "
                        f"Novos saldos: Conta Origem: {origin.balance} | "
                        f"Conta Destino: {destination.balance}"
                    )


# ==========================================
# 4. EXECUÇÃO PRINCIPAL
# ==========================================
def main():
    transactions_data = [
        {"correlation_id": 1, "datetime_str": "09/09/2023 14:15:00", "origin_account_id": 938485762,  "destination_account_id": 2147483649, "amount": Decimal("150")},
        {"correlation_id": 2, "datetime_str": "09/09/2023 14:15:05", "origin_account_id": 2147483649, "destination_account_id": 210385733,  "amount": Decimal("149")},
        {"correlation_id": 3, "datetime_str": "09/09/2023 14:15:29", "origin_account_id": 347586970,  "destination_account_id": 238596054,  "amount": Decimal("1100")},
        {"correlation_id": 4, "datetime_str": "09/09/2023 14:17:00", "origin_account_id": 675869708,  "destination_account_id": 210385733,  "amount": Decimal("5300")},
        {"correlation_id": 5, "datetime_str": "09/09/2023 14:18:00", "origin_account_id": 238596054,  "destination_account_id": 674038564,  "amount": Decimal("1489")},
        {"correlation_id": 6, "datetime_str": "09/09/2023 14:18:20", "origin_account_id": 573659065,  "destination_account_id": 563856300,  "amount": Decimal("49")},
        {"correlation_id": 7, "datetime_str": "09/09/2023 14:19:00", "origin_account_id": 938485762,  "destination_account_id": 2147483649, "amount": Decimal("44")},
        {"correlation_id": 8, "datetime_str": "09/09/2023 14:19:01", "origin_account_id": 573659065,  "destination_account_id": 675869708,  "amount": Decimal("150")},
    ]

    transactions = [TransactionDto(**t) for t in transactions_data]

    # Ordenação cronológica garante consistência da linha do tempo
    transactions.sort(key=lambda x: x.parsed_datetime)

    repository = AccountRepository()
    service    = TransactionService(repository)

    for t in transactions:
        service.transfer(t)


if __name__ == "__main__":
    main()