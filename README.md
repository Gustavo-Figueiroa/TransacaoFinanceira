# Resolução do Case - Transação Financeira

Esta é a solução do desafio técnico refatorada de C# para **Python**, aplicando boas práticas de arquitetura e corrigindo falhas críticas de concorrência.

## 🛠️ Correções e Melhorias Realizadas

1. **Correção de Concorrência (Race Condition):** O código original sofria com problemas de concorrência devido ao uso de threads paralelas sem sincronização. Foi implementado o uso de `threading.RLock()` por conta para garantir a atomicidade das operações.
2. **Prevenção de Deadlocks:** Implementada a ordenação de locks por ID numérico. Sempre o menor ID de conta é bloqueado primeiro, evitando deadlocks em transferências cruzadas simultâneas.
3. **Consistência Cronológica:** As transações agora são ordenadas estritamente por data e hora (`datetime`) antes do processamento, evitando que uma transação futura seja processada antes de um depósito prévio.
4. **Tipagem Segura:** Utilização de tipos numéricos de alta precisão (`Decimal`) para evitar problemas de arredondamento comuns com ponto flutuante em sistemas financeiros.
5. **Arquitetura SOLID:** Divisão clara de responsabilidades entre Entidades (Domain), Repositórios (Data Access) e Serviços (Business Logic).

## 🚀 Como Executar

### Executar a aplicação principal:
```bash
python main.py