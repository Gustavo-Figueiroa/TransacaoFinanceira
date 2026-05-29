# TransacaoFinanceira

Aplicação em Python para simular transações financeiras entre contas, com foco em consistência de saldos, concorrência e validação das regras de negócio.

## Objetivo

O projeto foi desenvolvido para atender a um case técnico de refatoração, correção de erros de compilação/lógica, aplicação de boas práticas de design e criação de testes unitários.

## Funcionalidades

- Cadastro inicial de contas em memória.
- Transferência entre contas com validação de saldo.
- Rejeição de transações inválidas.
- Processamento seguro em ambiente concorrente.
- Ordenação cronológica das transações.
- Prevenção de race conditions e deadlocks.

## Tecnologias utilizadas

- Python 3
- `decimal.Decimal`
- `threading.RLock`
- `dataclasses`
- `unittest`

## Estrutura do projeto

- `main.py`: contém as entidades, repositório, serviço de transações e execução principal.
- `test_main.py`: contém os testes unitários da solução.

## Regras de negócio implementadas

- O valor da transação deve ser maior que zero.
- A conta de origem e a conta de destino não podem ser iguais.
- A conta de origem e a conta de destino devem existir.
- A transferência só é realizada quando houver saldo suficiente.
- O saldo é atualizado de forma segura em cenários concorrentes.
- Quando duas contas precisam ser travadas ao mesmo tempo, a ordem de aquisição de lock evita deadlock.

## Decisões de implementação

- Foi utilizado `Decimal` para representar valores financeiros, evitando problemas de precisão.
- Cada conta possui seu próprio `RLock`, permitindo sincronização segura em múltiplas threads.
- As transações são ordenadas por data e hora antes do processamento para manter a linha do tempo correta.
- O repositório foi mantido em memória para simplificar o case e facilitar os testes.
- A lógica de negócio foi separada da estrutura de dados para melhorar organização e manutenção.

## Como executar

### Executar a aplicação

```bash
python main.py
```

### Executar os testes

```bash
python -m unittest test_transacao.py -v
```

## Cobertura dos testes

Os testes unitários validam os seguintes cenários:

- Criação de conta com saldo válido.
- Criação de conta com saldo zero.
- Rejeição de saldo inicial negativo.
- Existência de lock por conta.
- Parsing correto da data da transação.
- Ordenação cronológica das transações.
- Carregamento dos dados iniciais do repositório.
- Recuperação e sobrescrita de contas.
- Transferência com sucesso.
- Transferência com saldo exato.
- Cancelamento por saldo insuficiente.
- Rejeição de valor zero.
- Rejeição de valor negativo.
- Rejeição de conta inexistente.
- Cenário original completo com as transações do enunciado.
- Execução concorrente sem race condition.
- Execução bidirecional sem deadlock.

## Observações

A solução foi refatorada para melhorar legibilidade, responsabilidade única, segurança em concorrência e cobertura de testes.
