# LogBook Fafar

Aplicação desktop em desenvolvimento para registrar o uso de equipamentos. O planejamento e o contrato proposto estão em [PLANEJAMENTO.md](PLANEJAMENTO.md), [technical-requirements.md](technical-requirements.md) e [api-contract.md](api-contract.md).

## Estado atual

Estão disponíveis formulário, histórico local, monitoramento de processo e sincronização periódica. A intranet inclui o endpoint de criação e as páginas de consulta; é necessário aplicar a migração e provisionar credenciais com o escopo `logbook_submissions:create`. A capacidade `read_logbook_submission` é criada pela migração e pode ser concedida a usuários na administração de permissões. A inicialização automática ainda não foi configurada.

## Executar para teste

Instale Python compatível, Tkinter e a dependência:

```bash
python -m pip install -r requirements.txt
```

No Debian/Ubuntu pode ser necessário instalar o pacote `python3-tk`. Para abrir o formulário e consultar registros locais:

```bash
python logbook.py form
python logbook.py history
```

Para monitorar um processo, execute em outro terminal, substituindo pelo nome exato do processo (por exemplo `notepad.exe` no Windows):

```bash
python logbook_agent.py --process notepad.exe
```

Quando o processo observado encerrar, a aplicação abre o formulário. Os dados ficam sob `LOCALAPPDATA`, `XDG_DATA_HOME` ou `~/.local/share/logbook-fafar/logbook.sqlite`. Para conectar à intranet, defina `LOGBOOK_API_URL` como `https://<intranet>/api/v1/logbook_submissions` e `LOGBOOK_API_TOKEN` como o token da estação com escopo `logbook_submissions:create`. O agente tenta envios pendentes a cada 30 segundos e preserva a fila se houver falha. A API exige HTTPS e a chave `Idempotency-Key` igual ao UUID da submissão.
