# Contrato de integração: LogBook Fafar e intranet

Status: proposta de contrato v1, ainda não implementada. Atualizado em 2026-11-11.

O transporte, as respostas e a consulta são especificados abaixo. Os campos
foram confirmados na mensagem 7 da transcrição
`conversa_registro_uso_equipamento.md` fornecida pelo usuário: Nome do Usuário, Matrícula
e “O que faz aqui?”, além do usuário do sistema e computador capturados
automaticamente. Os limites de tamanho abaixo são propostas de implementação;
o exemplo original não os especifica. O esquema verificável está em
[schemas/logbook-submission-v1.schema.json](schemas/logbook-submission-v1.schema.json).

## 1. Responsabilidade dos sistemas

- Desktop: captura, persistência SQLite local e fila persistente de envios.
- Intranet: armazenamento central de submissões e consulta autorizada.
- Uma submissão aceita é imutável nesta primeira versão. Não há edição,
  exclusão, restauração ou criação manual pela interface web.
- O protocolo de integração envia uma submissão JSON por requisição, em vez de
  importar o arquivo SQLite. Backup do arquivo, se necessário, é uma operação
  separada, sem endpoint previsto nesta versão.
- A intranet não é necessária para registrar localmente. Indisponibilidade de
  rede mantém a submissão pendente no desktop.

## 2. Autenticação de estações

Reutilizar `ServiceIdentity`, `ServiceCredential` e `Api::V1::BaseController` da
intranet, acrescentando o escopo `logbook_submissions:create` ao registro de
escopos permitidos. Cada estação recebe uma identidade de serviço estável e
credencial própria; a identidade determina a estação de origem no servidor.

- Transporte HTTPS com validação de certificado ativa, inclusive no Windows 7.
- Cabeçalho `Authorization: Bearer <token-da-estacao>` obrigatório.
- Rotação preserva a identidade da estação e a deduplicação dos seus envios.
- Revogação ou expiração impede novos envios; registros locais permanecem.
- Não distribuir um token compartilhado dentro do instalador. Provisionar a
  credencial da estação separadamente, com acesso local restrito.
- Token da estação autoriza somente criação por API; não autoriza consultar a
  intranet nem identifica a pessoa que respondeu ao formulário.
- Nome e matrícula são declarações da pessoa no formulário. Não representam
  login autenticado nem vínculo automático com um usuário da intranet.

## 3. Criação de submissão

`POST /api/v1/logbook_submissions`

Cabeçalhos obrigatórios:

```http
Authorization: Bearer <token-da-estacao>
Content-Type: application/json
Idempotency-Key: 7b695d42-9385-47c0-86cd-4e7737d750e1
```

Limite proposto: 1 MiB por corpo, alinhado à base da API existente. Verificar o
tamanho real do corpo, além de `Content-Length`. Objetos rejeitam propriedades
desconhecidas. Exemplo de registro completo, com valores fictícios:

```json
{
  "client_submission_id": "7b695d42-9385-47c0-86cd-4e7737d750e1",
  "form_key": "logbook",
  "form_version": 1,
  "completion_state": "complete",
  "recorded_at": "2026-11-11T15:00:00-03:00",
  "trigger": "manual",
  "client_version": "0.1.0",
  "client_context": {
    "os_username": "operador",
    "hostname": "LAB-PC-01"
  },
  "answers": {
    "name": "Maria de Exemplo",
    "registration_number": "00123456",
    "activity": "Consulta e registro dos resultados da análise."
  }
}
```

| Campo | Regra |
| --- | --- |
| `client_submission_id` | UUID v4 criado uma vez no desktop; igual ao `Idempotency-Key`. |
| `form_key` | Literal `logbook` nesta versão. |
| `form_version` | Inteiro positivo correspondente a um esquema registrado no servidor. |
| `completion_state` | `complete` ao registrar com validação; `partial` ao confirmar fechamento. |
| `recorded_at` | Instante de gravação local em RFC 3339 com fuso explícito; preservar mesmo em envio tardio. |
| `trigger` | `manual` ou `process_exit`. |
| `client_version` | Texto não vazio de até 50 caracteres. |
| `client_context` | Objeto com `os_username` e `hostname`, capturados no momento do registro local. |
| `answers` | Objeto com chaves, tipos, limites e obrigatoriedades definidos pela versão do formulário. |

Todos os campos do envelope são obrigatórios. Em `partial`, `answers` pode ser
vazio e perguntas podem estar ausentes ou ter `null` conforme o esquema. Tipos,
limites e opções de respostas presentes continuam sendo validados. Em
`complete`, o servidor também verifica todas as respostas obrigatórias.
Versão desconhecida recebe `422`; nunca presumir o esquema mais recente.

### Perguntas do formulário v1

| Rótulo | Chave em `answers` | Campo no exemplo PowerShell | Tipo e limite proposto | Obrigatório em `complete` |
| --- | --- | --- | --- | --- |
| Nome do Usuário | `name` | `nomeUsuario` | Texto de uma linha, até 255 caracteres | Sim |
| Matrícula | `registration_number` | `matricula` | Texto de uma linha, até 100 caracteres | Sim |
| O que faz aqui? | `activity` | `oQueFazAqui` | Texto multilinha, até 5.000 caracteres | Sim |

A matrícula é texto: preservar zeros iniciais e permitir valores alfanuméricos,
sem impor unicidade ou formato numérico não especificado. A mesma pessoa pode
enviar várias submissões. Na interface, usar o título “Registro de uso”.

Remover espaços externos antes de gravar/enfileirar, preservando quebras internas
da atividade. Em `complete`, as três respostas devem conter caracteres além de
espaços. Nos campos de uma linha, rejeitar CR/LF. Em `partial`, aceitar respostas
ausentes, `null` ou texto vazio, inclusive `answers: {}`; os limites e tipos de
valores presentes continuam válidos. A interface deve aplicar os mesmos limites
para não gerar submissões que a API não possa aceitar.

O esquema registra estas três perguntas fixas; não prevê anexos nem perguntas
configuráveis nesta versão. Chaves desconhecidas em `answers` são rejeitadas.

### Metadados automáticos

| Chave em `client_context` | Origem no PowerShell | Regra |
| --- | --- | --- |
| `os_username` | `usuarioWindows`, de `$env:USERNAME` | Nome do usuário da sessão do sistema, até 255 caracteres, ou `null` se indisponível. |
| `hostname` | `computador`, de `$env:COMPUTERNAME` | Nome informado pelo sistema operacional, até 255 caracteres, ou `null` se indisponível. |

No Linux, obter os valores equivalentes pelas APIs do sistema. As duas chaves
são obrigatórias no objeto, mas indisponibilidade não deve impedir o registro:
usar `null`, sem fabricar valores. Texto presente é não vazio e sem CR/LF.
Esses metadados não são perguntas editáveis do formulário.

`hostname` é um relato do cliente e pode mudar; a estação confiável continua
sendo determinada pela identidade autenticada. Nenhum desses textos concede
permissões ou autentica a pessoa. O script original é uma referência de campos:
seu payload plano precisa ser adaptado a este envelope v1.

IDs internos, estação, identidade de serviço, instante de recebimento e dados
de auditoria são definidos pelo servidor; não são aceitos do cliente. Guardar
os instantes de captura e recebimento separadamente, pois a estação pode ficar
offline ou ter relógio incorreto.

### Confirmação

Criar a submissão, a auditoria e a confirmação de idempotência atomicamente.
Responder `201 Created` somente após persistência:

```json
{
  "request_id": "a83d7b29-c2ef-4df1-90b3-e94f5b540fdc",
  "data": {
    "id": "326b85cf-e82c-40ca-bf66-297b4ddf82c2",
    "client_submission_id": "7b695d42-9385-47c0-86cd-4e7737d750e1",
    "completion_state": "complete",
    "received_at": "2026-11-11T18:00:03Z"
  }
}
```

`id` é o UUID atribuído pela intranet. O cliente só marca como sincronizado após
receber uma confirmação válida com o mesmo `client_submission_id` e um ID
remoto. Resposta truncada ou inválida mantém o envio pendente.

### Idempotência

- Deduplicar pela identidade estável da estação e UUID da submissão, com índice
  único no banco. Não usar a credencial como chave, pois ela pode ser rotacionada.
- Mesmo UUID e mesmos bytes JSON: reproduzir o `201` e o corpo original,
  incluindo o `request_id` original, com `Idempotency-Replayed: true`.
- Mesmo UUID já aceito e corpo diferente: `409 idempotency_conflict`, sem alterar
  a submissão original. Calcular e guardar o SHA-256 dos bytes recebidos.
- Concorrência não pode criar duplicatas; se o processamento ainda não terminou,
  pode retornar `409 request_in_progress`, que permite nova tentativa.
- Manter UUID e digest enquanto a submissão existir, mesmo após expirar registros
  temporários de requisições, para impedir duplicação em restaurações do cliente.
- Falhas transitórias com rollback não podem reservar permanentemente a chave
  nem tornar um `500` uma resposta definitiva reproduzida para sempre.
- O cliente persiste o corpo serializado na fila e reenvia os mesmos bytes,
  inclusive após reinício. Uma submissão enfileirada não é editada.

## 4. Erros e tentativas

Reutilizar o envelope da API da intranet:

```json
{
  "request_id": "a83d7b29-c2ef-4df1-90b3-e94f5b540fdc",
  "error": {
    "code": "validation_failed",
    "message": "Submission is invalid",
    "details": [{ "field": "form_version", "message": "is not supported" }]
  }
}
```

| HTTP | Código | Comportamento do desktop |
| --- | --- | --- |
| 400 | `invalid_request` | Reter localmente e sinalizar erro de contrato. |
| 401 | `unauthorized` | Reter e suspender tentativas automáticas até corrigir a credencial. |
| 403 | `forbidden` | Reter e sinalizar escopo/estação sem autorização. |
| 409 | `idempotency_conflict` | Reter e sinalizar conflito; não gerar outro UUID automaticamente. |
| 409 | `request_in_progress` | Repetir com a mesma chave e corpo. |
| 413 | `payload_too_large` | Reter e sinalizar limite excedido. |
| 422 | `validation_failed` | Reter e sinalizar versão/respostas inválidas. |
| 429 | `rate_limited` | Repetir respeitando `Retry-After`, quando presente. |
| 500/502/503/504 | `internal_error` quando gerado pela aplicação | Repetir com a mesma chave e corpo. |

Timeouts e falhas de rede também permitem repetição. Usar espera crescente com
limite e variação aleatória, limites de tempo de conexão/leitura e fila em disco.
O proxy pode devolver erros sem JSON: nunca interpretá-los como confirmação.
Falha TLS exige diagnóstico, sem desativar a validação do certificado.

Tentar enviar depois de cada gravação e ao iniciar o agente; fechar uma janela
também solicita uma tentativa. O agente independente das janelas processa a
fila. Desligamento abrupto é recuperado pela fila na próxima inicialização.

## 5. Consulta na intranet

Rotas de navegador propostas, com sessão autenticada:

- `GET /logbook_submissions?query=...&page=1`: lista de submissões.
- `GET /logbook_submissions/:id`: perfil da submissão.

Não oferecer formulário web de criação, nem rotas de edição/exclusão nesta fase.
Não criar API de leitura para o desktop: seu histórico continua sendo local.

### Lista

- Página intitulada “LogBook”, seguindo os componentes visuais da intranet.
- Um input `query`, botão “Pesquisar” e ação para limpar a pesquisa.
- Tabela com identificador, nome, matrícula, estação, situação
  (Completo/Parcial), data de registro, data de recebimento e botão “Ver”.
- Pesquisa literal, sem distinção entre maiúsculas/minúsculas, por UUID local
  ou remoto, código/nome da estação, chave do formulário, situação, nome,
  matrícula, atividade, usuário do sistema e nome do computador informado.
- `query` com até 255 caracteres, espaços externos removidos, parâmetros SQL
  vinculados e escape de curingas de `LIKE`.
- Paginação no servidor de 10 itens, conforme o padrão de listas existente;
  preservar `query` ao navegar e voltar à primeira página em nova pesquisa.
- Ordenar por recebimento decrescente e ID como desempate, evitando que relógios
  incorretos das estações determinem a ordem principal.
- Mostrar total, estado vazio e navegação Anterior/Próxima. Página inválida ou
  fora do intervalo é ajustada ao intervalo válido.

### Perfil

Exibir Nome, Matrícula e “O que faz aqui?”, além de usuário do sistema,
computador informado, estação autenticada, formulário/versão, situação, origem
da abertura e datas de registro/recebimento. Preservar os rótulos da versão
original e identificar ausências em submissões parciais. Renderizar respostas como texto
escapado, sem executar HTML recebido. Oferecer “Voltar” à lista preservando
pesquisa e página por parâmetros locais validados.

### Capacidade de leitura

Registrar `read_logbook_submission` (“Consultar submissões do LogBook”) em
`Capability::REGISTERED_KEYS` e `Capability::ASSIGNABLE_KEYS`, no catálogo de
seeds e em uma migração para instalações existentes.

- A mesma capacidade protege lista, perfil e item do menu via policy/scope.
- Exigir usuário ativo, não excluído e com a capacidade efetiva.
- Iniciar sem atribuições globais, setoriais ou a usuários comuns. O
  administrador concede acesso aos usuários selecionados pelo mecanismo
  existente de capacidades diretas; pacotes seguem o mecanismo existente.
- Preservar o bypass canônico do administrador bootstrap da intranet.
- Verificar autorização no servidor também no acesso direto por URL; ocultar
  o menu não é suficiente. A busca opera somente sobre o scope autorizado.
- A capacidade concede leitura de todas as submissões. Recortes por estação ou
  setor não fazem parte desta versão.
- Não incluir o recurso na pesquisa global sem aplicar a mesma autorização.

## 6. Persistência e implementação planejadas

Na intranet, criar `LogbookSubmission` com UUID, identidade estável da estação,
UUID local, envelope, respostas e contexto do cliente em JSONB, digest do corpo
e instante de recebimento.
Guardar a versão do formulário e preservar seus rótulos/tipos para leitura
histórica. Índices: unicidade estação/UUID local e ordenação recebimento/ID.

Seguir os padrões existentes: controller fino, serviço `Logbook::Ingestion`,
serviço de pesquisa `Logbook::SubmissionDirectory`, policy e scope próprios,
views `index`/`show`, auditoria e idempotência por `IntegrationRequest`. Não
registrar tokens ou respostas pessoais completas em logs operacionais.

No desktop, separar `completion_state` de sincronização (`pending`, `synced`,
`blocked`) e gravar submissão e item da fila na mesma transação SQLite.
Metadados técnicos podem ter `NOT NULL`; respostas obrigatórias condicionais
não devem impedir o salvamento parcial.

## 7. Critérios de aceite

1. Submissões completas e parciais chegam à intranet; parcial vazio é aceito.
2. Nome, matrícula e atividade são obrigatórios em registros completos;
   matrícula mantém zeros iniciais e aceita letras. Tipos, limites, CR/LF em
   campos de uma linha e versões desconhecidas retornam erros por campo.
3. Sem token, com token revogado e sem escopo, nenhum registro é criado.
4. Repetições após timeout, concorrência, reinício e rotação não duplicam dados.
5. Conflito de corpo não altera uma submissão aceita.
6. Falha transacional não deixa submissão parcial ou bloqueio permanente de retry.
7. Usuário sem capacidade não vê menu, lista, perfil ou resultados por outra rota.
8. Concessão/revogação da capacidade altera o acesso; bootstrap mantém seu padrão.
9. Pesquisa por respostas/metadados, paginação, ordenação e retorno do perfil
   preservam o contexto, sem expor dados a usuários sem capacidade.
10. Não existem ações web/API de atualização ou exclusão de submissões.
11. Fila sobrevive a rede indisponível e desligamento; instalação/atualização
    preserva banco, fila, UUIDs e identidade da estação.
12. Instalações limpas Windows 7/10 e Debian/Ubuntu enviam por HTTPS sem
    desabilitar a validação de certificados.

## 8. Origem dos campos e pendências operacionais

- Os três campos foram solicitados explicitamente pelo usuário na mensagem 7
  de `conversa_registro_uso_equipamento.md`; o script PowerShell confirma os
  tipos e a obrigatoriedade. Data/hora, usuário do sistema e computador são
  metadados automáticos. Os limites de tamanho são propostas deste contrato.
- URL por ambiente, provisionamento de estações/credenciais e responsáveis pela
  rotação, retenção e recuperação operacional.
- Lista inicial de usuários que receberão a capacidade (pode ser atribuída
  depois, sem impedir a implementação).

O script usa `notepad` como processo de exemplo e uma URL placeholder.
O nome real do processo monitorado e as URLs por ambiente ainda precisam ser
configurados. O exemplo não altera o requisito de salvar parcialmente ao
confirmar fechamento: a aplicação deve persistir localmente antes de tentar
enviar e informar “Salvo localmente; envio pendente” quando estiver offline.
Se a janela for fechada, o agente continua monitorando e enviando a fila.

## 9. Referências locais examinadas

Na intranet (`../intranet/`): `docs/api_v1_reference.md`,
`docs/domain/roles-permissions.md`, `app/controllers/api/v1/base_controller.rb`,
`app/controllers/api/v1/auditorium_reservations_controller.rb`,
`app/services/auditorium/ingestion.rb`, `app/models/service_identity.rb`,
`app/models/service_credential.rb`, `app/models/capability.rb`,
`app/models/user.rb`, `app/policies/place_policy.rb`,
`app/controllers/places_controller.rb` e `app/views/places/index.html.erb`.

Este documento não altera o contrato canônico nem implementa rotas na intranet.
Na implementação do módulo, atualizar também a documentação e os testes daquele
repositório.
