# Documento de Requisitos de Sistema: LogBook Fafar

## 1. Visão Geral do Sistema
O sistema é uma aplicação desktop leve focada em registro e consulta de logs operacionais. Ele implementa apenas as operações de **Create (C)** e **Read (R)** de um CRUD tradicional. A aplicação possui fortes integrações com o sistema operacional (Windows) para automação de abertura baseada em gatilhos de inicialização e monitoramento de processos.

## 2. Pilha Tecnológica (Tech Stack)
* **Linguagem:** Python 3.8
* **Interface Gráfica (GUI):** Tkinter ou PyQt5 (PyQt5 é recomendado para melhor renderização da tabela de visualização).
* **Banco de Dados:** SQLite3 (Local).
* **Comunicação Externa:** Biblioteca `requests` (para o envio do backup via POST).
* **Integração com SO:** `psutil` (para monitorar "PROGRAMA X") e manipulação do Registro/Pasta de Inicialização do Windows.
* **Sistema Operacional:** Windows 7 e Windows 10.

---

## 3. Requisitos Funcionais (RF)

### Módulo CREATE (Formulário)
* **RF01 - Renderização do Formulário:** O sistema deve exibir uma janela com campos de entrada de dados (perguntas do LogBook) e botões de controle nativos do Windows na barra superior.
* **RF02 - Botão de Registro:** O formulário deve possuir um botão "Registrar".
* **RF03 - Validação de Frontend:** Ao clicar em "Registrar", o sistema deve validar se os campos obrigatórios foram preenchidos. Se não, deve exibir um alerta e impedir o salvamento. Se sim, salva os dados e fecha a janela.
* **RF04 - Salvamento Parcial (Interceptação de Fechamento):** Se o usuário tentar fechar a janela (pelo "X" ou `Alt+F4`), o sistema deve:
    1. Interceptar o evento de fechamento.
    2. Exibir um pop-up de confirmação de saída.
    3. Se confirmado: Ignorar a validação de campos obrigatórios, salvar no banco de dados os campos que estiverem preenchidos (mesmo que parcialmente ou vazios) e fechar o aplicativo.

### Módulo READ (Visualização)
* **RF05 - Tabela de Logs:** O sistema deve exibir uma janela contendo uma tabela ou DataGrid com todos os registros presentes no banco SQLite.
* **RF06 - Restrição de Acesso:** A tela deve ser estritamente *Read-Only*. Não deve haver botões ou atalhos para edição ou exclusão (Update/Delete não implementados).

### Módulo de BACKUP (Sincronização Remota)
* **RF07 - Gatilho de Backup:** O evento de encerramento do processo principal (seja fechando o CREATE ou o READ) deve disparar a rotina de backup silencioso no *background*.
* **RF08 - Envio POST:** O sistema deve empacotar o arquivo `.sqlite` atual e enviá-lo como *payload* em uma requisição HTTP POST para um endpoint remoto pré-configurado.

### Módulo de AUTOMAÇÃO (Gatilhos de Sistema)
* **RF09 - Auto-Run no Boot:** O módulo READ deve ser registrado no sistema operacional para inicializar automaticamente assim que o Windows concluir o processo de login do usuário.
* **RF10 - Monitoramento de Processo (Daemon):** O sistema deve possuir um script em *background* que monitore a execução de um processo específico (doravante chamado "PROGRAMA X").
* **RF11 - Gatilho pós-Programa X:** Assim que o daemon detectar que o "PROGRAMA X" foi encerrado, ele deve instanciar e exibir a janela do módulo CREATE na tela.

### Módulo LANÇADOR
* **RF12 - Atalhos Manuais:** O sistema deve prover executáveis/atalhos individuais ou um menu simples em bandeja de sistema (System Tray) para que o usuário possa invocar os módulos CREATE e READ manualmente a qualquer momento.

---

## 4. Requisitos Não-Funcionais (RNF)

* **RNF01 - Compatibilidade:** O código não deve usar APIs exclusivas do Windows 11; deve garantir retrocompatibilidade com o Windows 7 (ex: atenção ao usar bibliotecas modernas que descontinuaram suporte ao Win7).
* **RNF02 - Autonomia:** A verificação de obrigatoriedade dos campos não deve existir em nível de restrição do Banco de Dados (`NOT NULL`), garantindo que o salvamento parcial de encerramento (RF04) não lance exceções de SQL.

---

## 5. Casos de Uso / Jornada do Usuário (Para testes da IA)

A IA geradora deverá usar este fluxo para criar testes unitários ou garantir a lógica:
1. `Event: Win_Startup` ➔ `Action: Open READ`.
2. `Event: User_Close_READ` ➔ `Action: Trigger Backup POST` ➔ `End`.
3. `Event: Launch_ProgramaX` ➔ `Action: Background Monitor Active`.
4. `Event: Close_ProgramaX` ➔ `Action: Open CREATE`.
5. `Event: Fill_Data + Click_Registrar` ➔ `Action: Validate UI -> Save DB -> Trigger Backup POST -> End`.
6. `Event: Fill_Partial + Click_X(Close)` ➔ `Action: Ask Confirm -> Bypass Validation -> Save Partial DB -> Trigger Backup POST -> End`.
7. `Event: Manual_Click_Create_Shortcut` ➔ `Action: Open CREATE`.
8. `Event: Manual_Click_Read_Shortcut` ➔ `Action: Open READ`.