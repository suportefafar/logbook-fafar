# Documento de Requisitos de Sistema: LogBook Fafar

## 1. Visão Geral do Sistema
O sistema é uma aplicação desktop leve focada em registro e consulta de logs operacionais. Ele implementa apenas as operações de **Create (C)** e **Read (R)** de um CRUD tradicional. A aplicação possui fortes integrações com o sistema operacional (Windows) para automação de abertura baseada em gatilhos de inicialização e monitoramento de processos.

A intranet (`../intranet/`) será o sistema de armazenamento central das
submissões, com consulta web restrita. O SQLite permanece como persistência
local e suporte a funcionamento offline. O contrato proposto está em
[api-contract.md](api-contract.md), com os campos confirmados na mensagem 7 da
transcrição `conversa_registro_uso_equipamento.md` e no exemplo PowerShell.

## 2. Pilha Tecnológica (Tech Stack)
* **Linguagem:** Python 3.8
* **Interface Gráfica (GUI):** Tkinter ou PyQt5 (PyQt5 é recomendado para melhor renderização da tabela de visualização).
* **Banco de Dados:** SQLite3 (Local).
* **Comunicação Externa:** Biblioteca `requests` (para envio de submissões JSON via HTTPS).
* **Integração com SO:** `psutil` (para monitorar "PROGRAMA X") e manipulação do Registro/Pasta de Inicialização do Windows.
* **Sistema Operacional:** Windows 7, Windows 10 e Debian/Ubuntu (versões mínimas de Linux a definir).

---

## 3. Requisitos Funcionais (RF)

### Módulo CREATE (Formulário)
* **RF01 - Renderização do Formulário:** Exibir a janela “Registro de uso”, com Nome (texto de uma linha), Matrícula (texto de uma linha) e “O que faz aqui?” (texto multilinha), além dos controles nativos da janela. Os três campos são obrigatórios ao registrar normalmente. Matrícula deve preservar zeros iniciais e permitir letras; não é única por submissão. Limites propostos: 255, 100 e 5.000 caracteres, respectivamente, conforme o contrato da API.
* **RF02 - Botão de Registro:** O formulário deve possuir um botão "Registrar".
* **RF03 - Validação de Frontend:** Ao clicar em "Registrar", o sistema deve validar se os campos obrigatórios foram preenchidos. Se não, deve exibir um alerta e impedir o salvamento. Se sim, salva os dados e fecha a janela.
* **RF04 - Salvamento Parcial (Interceptação de Fechamento):** Se o usuário tentar fechar a janela (pelo "X" ou `Alt+F4`), o sistema deve:
    1. Interceptar o evento de fechamento.
    2. Exibir um pop-up de confirmação de saída.
    3. Se confirmado: Ignorar a obrigatoriedade das respostas, salvar os campos preenchidos (mesmo que parcialmente ou vazios), marcar a submissão como parcial e fechar a janela. O agente permanece ativo.
* **RF17 - Contexto Automático:** Capturar usuário da sessão do sistema operacional e nome do computador ao gravar a submissão. No Windows, equivalem a `USERNAME` e `COMPUTERNAME`; no Linux, usar as APIs equivalentes. Armazenar `null` se indisponíveis. Esses dados não autenticam a pessoa nem substituem a identidade da estação determinada pela credencial da API.

### Módulo READ (Visualização)
* **RF05 - Tabela de Logs:** O sistema deve exibir uma janela contendo uma tabela ou DataGrid com todos os registros presentes no banco SQLite.
* **RF06 - Restrição de Acesso:** A tela deve ser estritamente *Read-Only*. Não deve haver botões ou atalhos para edição ou exclusão (Update/Delete não implementados).

### Módulo de SINCRONIZAÇÃO (Intranet)
* **RF07 - Gatilho de Sincronização:** Após cada gravação local, na inicialização do agente e ao fechar CREATE ou READ, solicitar o envio das submissões pendentes. O agente continua independente das janelas; a fila persistente recupera tentativas interrompidas.
* **RF08 - Envio POST:** Enviar cada submissão em JSON para `POST /api/v1/logbook_submissions`, com credencial por estação, UUID estável e idempotência. Só marcar como sincronizada após confirmação válida. Não enviar o arquivo SQLite como protocolo de ingestão. Backup do arquivo é uma necessidade separada, ainda não especificada.

### Módulo de AUTOMAÇÃO (Gatilhos de Sistema)
* **RF09 - Auto-Run no Boot:** O módulo READ deve ser registrado no sistema operacional para inicializar automaticamente assim que o Windows concluir o processo de login do usuário.
* **RF10 - Monitoramento de Processo (Daemon):** O sistema deve possuir um script em *background* que monitore a execução de um processo específico (doravante chamado "PROGRAMA X").
* **RF11 - Gatilho pós-Programa X:** Assim que o daemon detectar que o "PROGRAMA X" foi encerrado, ele deve instanciar e exibir a janela do módulo CREATE na tela.

### Módulo LANÇADOR
* **RF12 - Atalhos Manuais:** O sistema deve prover executáveis/atalhos individuais ou um menu simples em bandeja de sistema (System Tray) para que o usuário possa invocar os módulos CREATE e READ manualmente a qualquer momento.

### Módulo WEB (Intranet)
* **RF13 - Listagem:** Disponibilizar tabela com nome, matrícula, estação, situação e datas, pesquisa por input `query`, botão de pesquisa, paginação no servidor e botão "Ver" por linha. A pesquisa inclui nome, matrícula, atividade e metadados definidos no contrato.
* **RF14 - Perfil:** Exibir Nome, Matrícula e “O que faz aqui?”, usuário do sistema, computador informado, estação autenticada e demais metadados da submissão. Preservar a versão original do formulário e identificar registros parciais.
* **RF15 - Autorização:** Exigir `read_logbook_submission` para lista, perfil e menu. Iniciar sem concessões globais/setoriais; atribuir aos usuários selecionados pelo mecanismo existente da intranet, preservando o bypass do administrador bootstrap. Aplicar autorização no servidor em todo acesso direto.
* **RF16 - Escopo Inicial Web:** Disponibilizar apenas consulta. Criação ocorre pela API do desktop; edição e exclusão não são implementadas nesta fase.

---

## 4. Requisitos Não-Funcionais (RNF)

* **RNF01 - Compatibilidade:** O código não deve usar APIs exclusivas do Windows 11; deve garantir retrocompatibilidade com o Windows 7 (ex: atenção ao usar bibliotecas modernas que descontinuaram suporte ao Win7).
* **RNF02 - Autonomia:** A obrigatoriedade condicional das respostas não deve impedir o salvamento parcial no banco (RF04). Metadados técnicos podem ter restrições `NOT NULL`. A interface e a API validam as respostas obrigatórias de registros completos conforme a versão do formulário.
* **RNF03 - Recuperação:** Gravar submissão e fila local na mesma transação. Falhas de rede e reenvios não podem perder ou duplicar submissões; submissões aceitas na intranet são imutáveis nesta fase.

---

## 5. Casos de Uso / Jornada do Usuário (Para testes da IA)

A IA geradora deverá usar este fluxo para criar testes unitários ou garantir a lógica:
1. `Event: Win_Startup` ➔ `Action: Open READ`.
2. `Event: User_Close_READ` ➔ `Action: Request Pending Sync` ➔ `Close Window; Agent Remains Active`.
3. `Event: Launch_ProgramaX` ➔ `Action: Background Monitor Active`.
4. `Event: Close_ProgramaX` ➔ `Action: Open CREATE`.
5. `Event: Fill_Data + Click_Registrar` ➔ `Action: Validate UI -> Save DB + Outbox Atomically -> Request Sync -> Close Window`.
6. `Event: Fill_Partial + Click_X(Close)` ➔ `Action: Ask Confirm -> Bypass Required Answers -> Save Partial DB + Outbox Atomically -> Request Sync -> Close Window`.
7. `Event: Manual_Click_Create_Shortcut` ➔ `Action: Open CREATE`.
8. `Event: Manual_Click_Read_Shortcut` ➔ `Action: Open READ`.
9. `Event: Offline_Save + Agent_Restart` ➔ `Action: Recover Pending Sync -> Retry Same UUID and Body -> No Duplicate`.
10. `Event: Authorized_Web_User` ➔ `Action: Search -> Paginate -> View Submission`.
11. `Event: Unauthorized_Web_User` ➔ `Action: Deny List and Direct Profile Access`.
