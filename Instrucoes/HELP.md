# Manual do Operador - SuRI-EDU

## 1. Visão Geral E Segurança

O SuRI-EDU é um supervisório educacional para controlar seis servomotores de um braço Robix com Arduino Mega. Ele reúne Teach Pendant, editor da Linguagem Robix, painel de execução, comunicação serial e firmware de interpolação.

Repositório: https://github.com/Andrus227/SuRI-Edu

Use o braço fixado em uma base estável, mantenha sua área livre e conheça as limitações da parada por software antes de energizar os servos.

> **Atenção:** o firmware inicia os seis servos em 90 graus. Abrir a porta serial normalmente reinicia o Arduino e pode repetir esse movimento. Os pinos 8 a 13, a alimentação adequada dos servos, o terra comum e a compatibilidade mecânica da posição inicial devem ser conferidos antes da conexão.

## 2. Primeiros Passos

Execute os comandos a partir da raiz do repositório.

1. Instale Python 3.10 ou superior.
2. Execute `python -m venv .venv`.
3. Ative o ambiente conforme o terminal.

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Prompt de Comando:

```bat
.venv\Scripts\activate.bat
```

Git Bash:

```bash
source .venv/Scripts/activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

4. Execute `python -m pip install -r requirements.txt`.
5. Confira os pinos e grave `Servo/Servo.ino` no Arduino Mega pela Arduino IDE.
6. Com a área livre, execute `python main.py` e selecione a porta serial correta.

No Linux, Tk, `venv`, drivers USB e permissão de acesso à serial podem exigir configuração do sistema.

## 3. Conexão Serial E Modo Offline

- Selecione a porta no menu superior; use "Atualizar..." se necessário.
- A comunicação utiliza 115200 baud e o contrato de `Instrucoes/PROTOCOL.md`.
- Toda tentativa de conexão invalida os ângulos comandados conhecidos.
- O Monitor registra apenas quadros de movimento transmitidos com sucesso. STOP, ACK e erros aparecem em mensagens de status próprias.
- No modo offline, interface, editor e gravação de poses continuam disponíveis, mas não há movimento físico.

Uma transmissão que falha ou seja parcial não atualiza o estado comandado. Em uma pose com vários motores, somente os quadros enviados integralmente permanecem conhecidos.

O firmware atual aplica aceleração e desaceleração automaticamente a todo alvo recebido. Grave novamente `Servo/Servo.ino` para utilizar essa suavização; alterar apenas a aplicação Python não atualiza uma placa que ainda esteja com firmware antigo.

## 4. Teach Pendant

- Arraste os sliders ou use os botões `-10`, `-1`, `+1` e `+10`.
- `Tab` avança por Base, Ombro, Cotovelo, Pitch, Roll e Garra.
- `Shift+Tab` percorre a ordem inversa; a navegação é circular.
- Esquerda/direita alteram 1 grau; baixo/cima alteram 10 graus.
- O quadro azul indica o motor selecionado. Alterar foco não muda o ângulo.
- Com Tempo Real desativado, os ajustes apenas preparam a pose.
- Com Tempo Real ativo, o arraste transmite no máximo a cada 50 ms e o valor final é enviado ao soltar.
- "Enviar Pose" transmite somente motores desconhecidos ou diferentes do último comando bem-sucedido.
- "Salvar Ponto" guarda temporariamente a pose; "Exportar" gera código no Editor e limpa os pontos gravados.

O estado comandado é desconhecido na inicialização, em conexões e após STOP. Nessas situações, a pose seguinte tenta transmitir os seis motores. `MovePose` não é atômico: cada motor usa um quadro separado e uma falha ou parada pode deixar a pose parcialmente comandada.

Os controles aceitam de 0 a 180 graus. Essa é apenas a faixa do protocolo, não um limite mecânico seguro para todas as montagens.

Movimentos do Teach Pendant, inclusive atualizações em Tempo Real, enviam destinos. O Arduino calcula em segundo plano a velocidade, aceleração e frenagem de cada servo; a interface não precisa gerar degraus intermediários.

## 5. Editor, Arquivos E Exportação

- O Editor (F4) abre e salva arquivos `.txt` em UTF-8; todo salvamento usa "Salvar como".
- O Painel de Execução (F5) carrega o arquivo em modo somente leitura.
- Exportar não grava no disco: substitui o conteúdo atual do Editor.
- Não há salvamento automático, indicador de alterações ou confirmação ao abrir, exportar ou fechar com conteúdo não salvo.
- O nome exportado deve conter somente letras, números e `_`, sem espaços.

Os pontos capturados no Teach Pendant existem somente na memória até a exportação. O código gerado declara um método, acrescenta `Wait(1000)` após cada ponto, usa a primeira pose em `setup` e chama o método em um `loop` contínuo. Portanto, `F9` repetirá a sequência até STOP, troca de tela ou encerramento.

### Exemplos integrados

O ícone `🧪` ou `F6` abre a galeria. A prévia é somente leitura. Cada exemplo declara um método e o chama uma vez em `setup`; nenhum contém `loop`.

Métodos incorporados:

- `PosicaoNeutra`, `AbrirGarra`, `FecharGarra` e `CicloDaGarra` para operações básicas;
- `TestarJuntas`, `VarreduraDaBase` e `DemonstrarEspacoTrabalho` para conhecer os eixos;
- `PercorrerTresPontos`, `AcenarRobix` e `CoreografiaRobix` para movimentos coordenados;
- `InspecionarObjeto` e `PickAndPlace` para demonstrações de manipulação.

"Executar uma vez" ou `F9` inicia imediatamente o exemplo selecionado com seus ângulos originais. "Adicionar método ao Editor" acrescenta somente a declaração ao fim do código, sem apagar o conteúdo, criar uma chamada ou executar movimento. Para usá-la, chame o nome em `setup`, `loop` ou outro método. Uma declaração de mesmo nome não é duplicada e dependências entre métodos devem ser inseridas separadamente.

Os exemplos são fixos e não podem ser removidos. Seus ângulos são referências didáticas: revise limites mecânicos, orientação dos servos, ferramenta, objeto e obstáculos antes da execução direta.

Os métodos permanecem legíveis porque registram somente destinos. A suavização é global no firmware e não aparece como várias linhas intermediárias de `MoveTo` ou `MovePose`.

### Biblioteca pessoal de métodos

A aba "Métodos" do Editor também gerencia snippets pessoais. "Salvar métodos do código" extrai todas as declarações `metodo Nome:` do Editor e as mescla em `~/.suri_edu/metodos.json`. Um nome existente é atualizado, enquanto métodos salvos que não estão no Editor são preservados. A biblioteca não injeta métodos automaticamente na rotina: clique no item para inseri-lo antes de executar.

O botão `×` remove um método pessoal após confirmação, mas não remove a declaração do Editor aberto. Se o arquivo JSON estiver ausente, ilegível ou inválido, a aplicação inicia com a biblioteca pessoal vazia; os exemplos incorporados continuam disponíveis.

## 6. Linguagem Robix

Comandos suportados:

- `MoveTo(M, A)`: motor `M` de 1 a 6 e ângulo inteiro `A` de 0 a 180;
- `MovePose(B, O, C, P, R, G)`: seis ângulos inteiros de 0 a 180;
- `Wait(MS)`: espera por um inteiro não negativo de milissegundos.

Estrutura:

```text
metodo Inicio:
    MovePose(90, 90, 90, 90, 90, 90)

setup:
    Inicio

loop:
    MoveTo(1, 120)
    Wait(1000)
    MoveTo(1, 60)
    Wait(1000)
```

- `setup` executa uma vez e um `loop` não vazio repete indefinidamente até STOP, troca de tela, nova rotina ou encerramento;
- `metodo Nome:` declara um bloco e `Nome` o chama sem parênteses;
- comandos e cabeçalhos não diferenciam maiúsculas de minúsculas;
- chamadas de métodos devem coincidir exatamente com o nome declarado;
- `//` inicia comentário e `;` no fim da linha é aceito;
- o corpo de cada bloco deve ter indentação maior que seu cabeçalho;
- comandos fora de um bloco são incorporados ao `setup`;
- recursão direta ou indireta aborta a execução;
- comandos desconhecidos e valores inválidos são registrados e a rotina segue para a próxima etapa.

Por compatibilidade com rotinas antigas, o parser procura `MoveTo`, `MovePose` e `Wait` dentro da linha, mesmo se houver texto antes ou depois da chamada. Portanto, não tente desativar um comando acrescentando texto: use `//`. Conteúdo depois dos dois-pontos de uma declaração de método também não faz parte do corpo.

As esperas e estimativas de movimento são agendadas sem `sleep` na interface. A aplicação estima a duração com o mesmo limite de velocidade e aceleração configurado no firmware, mais 100 ms para `MoveTo` ou 200 ms para `MovePose`. Movimentos curtos usam perfil triangular; movimentos longos atingem velocidade máxima e usam perfil trapezoidal. Estado anterior desconhecido é estimado como 180 graus. Falha total ou ausência de motores alterados usa atraso zero; em falha parcial de `MovePose`, apenas envios bem-sucedidos entram na estimativa. A rotina continua após falhas, portanto inclua `Wait` em loops para evitar novas tentativas em alta frequência. Esses tempos não são medição física nem confirmação do Arduino. Conexão e escrita serial ainda são síncronas e podem causar pequenas pausas.

## 7. Execução E Parada

F9 inicia o código quando o Editor, o Painel ou Exemplos está visível. Trocar de tela com F2 a F6 ou pelos botões de navegação durante uma rotina solicita a mesma parada controlada do STOP. Abrir a ajuda com F1 não troca de tela nem para a rotina.

Durante uma rotina, espaço ou STOP:

1. cancelam o callback pendente e impedem as próximas etapas locais;
2. invalidam o estado comandado;
3. tentam escrever `<STOP,id>` diretamente;
4. aguardam até 1 segundo pelo `<ACK,STOP,id>` correspondente se a escrita for completa.

O botão STOP também envia a solicitação fora de uma rotina, por exemplo para interromper uma interpolação iniciada manualmente. Sem rotina ativa, a barra de espaço mantém seu comportamento normal. Pedidos repetidos são combinados enquanto o STOP está pendente; após falha ou timeout, o botão permite uma nova tentativa com outro ID.

Estados apresentados:

- `requested`: parada solicitada localmente;
- `command_sent`: quadro STOP escrito integralmente;
- `controller_interrupted`: ACK correspondente recebido;
- `send_failed`: STOP não foi escrito integralmente;
- `no_confirmation`: ACK não chegou em 1 segundo.

Iniciar outra rotina durante uma execução envia STOP, mas não espera seu ACK antes da nova rotina. Fechar a aplicação durante uma execução também tenta enviar STOP e encerra sem aguardar confirmação.

O firmware congela os alvos na última etapa interpolada, mantém os servos anexados e continua solicitando o último PWM. Isso não garante torque físico, posição ou sustentação. O transporte serial é FIFO, portanto bytes já enviados permanecem antes do STOP e não há garantia de latência máxima.

O perfil suave vale para movimentos comandados depois da inicialização. Ao anexar os servos, o firmware ainda solicita 90 graus sem conhecer a posição física inicial. O STOP zera a velocidade imediatamente, sem rampa de desaceleração, para não prolongar intencionalmente o movimento após uma parada solicitada.

> **Limitação de segurança:** STOP e espaço dependem do computador, aplicação, cabo, porta serial, firmware e alimentação. Eles não substituem uma parada de emergência física, cabeada e independente do software.

## 8. Atalhos

- F1: abrir ajuda;
- F2: Menu;
- F3: Teach Pendant;
- F4: Editor;
- F5: Painel de Execução;
- F6: Exemplos;
- F9: iniciar o código no Editor, Painel ou Exemplos; nas outras telas, registrar aviso;
- Espaço: parada controlada durante rotina ativa;
- Tab e Shift+Tab: navegar entre motores no Teach Pendant;
- Setas: ajustar o motor selecionado.

## 9. Estado E Sincronização

- **Desejado:** posição solicitada pela interface ou rotina;
- **Comandado:** quadro de movimento escrito integralmente na serial;
- **Confirmado:** posição informada por telemetria ou sensor.

O modelo publica snapshots com horário, origem, conexão, rotina, parada e falhas. Não há ACK de movimento nem sensor nesta versão, portanto o estado confirmado permanece desconhecido e a posição física não deve ser inferida dos sliders.

## 10. Solução De Problemas

**Nenhuma porta:** verifique cabo, driver, alimentação, permissão do sistema e use "Atualizar...".

**Movimento ao conectar:** é a inicialização prevista em 90 graus após o reset da placa.

**Movimento ainda brusco:** confirme que o firmware atual foi gravado, reduza carga e folgas mecânicas e revise alimentação. A suavização não compensa fonte inadequada, servo danificado ou colisão.

**Erro serial:** confirme a porta, 115200 baud e o firmware correto.

**Parada sem confirmação:** a rotina local foi cancelada, mas não houve ACK correspondente. Não assuma que o controlador parou; use a parada física se houver risco.

**Sintaxe não reconhecida:** confira comando, parâmetros, faixa e indentação. A rotina pode continuar nas linhas seguintes.

**Recursão detectada:** remova a chamada direta ou indireta do método para ele mesmo.

**Biblioteca pessoal vazia:** confirme `~/.suri_edu/metodos.json`. Um arquivo ausente, ilegível ou inválido é ignorado; salve novamente os métodos pelo Editor.

## 11. Evoluções Planejadas E Suporte

1. Limites mecânicos por junta e prevenção de colisão;
2. ACK de movimento, telemetria e sensores;
3. protocolo versionado, heartbeat e recuperação de conexão;
4. visualização esquemática ou 3D;
5. distinção visual entre estado desejado, comandado e confirmado;
6. histórico de divergências e melhorias de acessibilidade visual.

Ao relatar um problema, informe sistema operacional, versão do Python, passos, rotina `.txt` e trechos do log.

Contato: André Victor Lucio, `andrelucio.ifmt@gmail.com`
