# LogBook Fafar

Um aplicativo desktop leve em Python construído para facilitar o registro de logs operacionais no Windows 7 e 10. Ele combina uma interface CRUD simples (Create e Read) com automações de sistema, como auto-inicialização e gatilhos baseados em encerramento de processos específicos.

## 🚀 Funcionalidades

- **Registro Rápido (CREATE):** Formulário simples para inserção de dados.
- **Visualização (READ):** Tabela em modo *Read-Only* para consulta rápida do histórico.
- **Automação por Gatilho:** A tela de registro abre automaticamente assim que um processo monitorado (ex: `programa_x.exe`) é encerrado pelo usuário.
- **Auto-run no Boot:** A tela de visualização é carregada automaticamente ao iniciar o Windows.
- **Backup Silencioso:** O banco de dados SQLite é enviado via POST para um servidor remoto em *background* sempre que o programa é fechado.
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