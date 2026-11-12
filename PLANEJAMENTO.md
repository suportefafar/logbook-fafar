# LogBook Fafar

Um aplicativo desktop leve em Python construído para facilitar o registro de logs operacionais no Windows 7 e 10. Ele combina uma interface CRUD simples (Create e Read) com automações de sistema, como auto-inicialização e gatilhos baseados em encerramento de processos específicos.

## 🚀 Funcionalidades

- **Registro Rápido (CREATE):** Formulário “Registro de uso” com Nome, Matrícula e “O que faz aqui?”, além da captura automática do usuário do sistema e computador.
- **Visualização (READ):** Tabela em modo *Read-Only* para consulta rápida do histórico.
- **Automação por Gatilho:** A tela de registro abre automaticamente assim que um processo monitorado (ex: `programa_x.exe`) é encerrado pelo usuário.
- **Auto-run no Boot:** A tela de visualização é carregada automaticamente ao iniciar o Windows.
- **Sincronização com a Intranet:** Submissões são salvas localmente e enviadas em JSON por uma fila persistente, com idempotência para evitar duplicatas.
- **Consulta Web Restrita:** A intranet terá lista paginada, pesquisa e perfil das submissões, protegidos pela capacidade `read_logbook_submission`.
- **Salvamento Inteligente:** Se a janela de registro for fechada (pelo "X" ou Alt+F4), o sistema salva os dados preenchidos parcialmente, garantindo que nenhuma informação seja perdida.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.8
- **Interface Gráfica:** PyQt5 (ou Tkinter)
- **Banco de Dados:** SQLite3
- **Monitoramento de Processos:** `psutil`
- **Requisições HTTP:** `requests`

## ⚙️ Pré-requisitos

Certifique-se de ter o Python 3.8 instalado na sua máquina.

```bash
pip install -r requirements.txt
```

O projeto está em planejamento; o código e o arquivo `requirements.txt` ainda
não foram criados. Os alvos incluem Windows 7, Windows 10 e Debian/Ubuntu.

## Documentação

- [Requisitos do sistema](technical-requirements.md).
- [Proposta de contrato da API e consulta na intranet](api-contract.md).
