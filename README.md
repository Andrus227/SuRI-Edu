# SuRI-EDU: Sistema de Apoio Robótico Educacional

Projeto da disciplina de Robótica Industrial, orientada pelo Prof. Dr. Ronan Marcelo Martins, para controle didático de um braço Robix com Arduino Mega e uma aplicação desktop em Python.

## Funcionalidades

- Controle de seis servomotores pelo Teach Pendant;
- Modo em tempo real e preparação de poses offline;
- Gravação, edição e execução de rotinas na Linguagem Robix;
- Galeria com 12 métodos de exemplo para movimentos básicos, trajetórias e manipulação;
- Biblioteca pessoal de métodos persistente entre sessões;
- Comandos `MoveTo`, `MovePose` e `Wait`;
- Parada controlada pelo botão STOP ou, durante uma rotina, pela barra de espaço;
- Comunicação serial e interpolação não bloqueante no Arduino;
- Suavização global com aceleração e desaceleração automáticas no firmware;
- Manual integrado acessível por F1.

`MovePose` é uma operação lógica expandida em até seis quadros de movimento. São transmitidos os motores cujo estado comandado esteja desconhecido ou seja diferente do alvo. O estado torna-se desconhecido na inicialização, em toda tentativa de conexão e após um STOP.

## Estrutura

- `main.py`: inicialização da aplicação;
- `suri_edu/app.py`: telas, navegação e execução cancelável das rotinas;
- `suri_edu/motor_controller.py`: validação, transmissão e estado dos motores;
- `suri_edu/robix_language.py`: parser e geração de rotinas Robix;
- `suri_edu/routine_examples.py`: catálogo de métodos e rotinas de exemplo;
- `suri_edu/method_library.py`: persistência da biblioteca pessoal de métodos;
- `suri_edu/serial_manager.py`: conexão e enquadramento serial;
- `suri_edu/gui_components.py`: editor e componentes reutilizáveis;
- `suri_edu/help_content.py`: conteúdo da ajuda integrada;
- `Instrucoes/HELP.md`: Manual do Operador;
- `Instrucoes/PROTOCOL.md`: contrato entre supervisório e firmware;
- `Servo/Servo.ino`: firmware do Arduino Mega;
- `tests/`: testes unitários e de contrato.

## Requisitos

- Python 3.10 ou superior;
- Arduino IDE para gravar `Servo/Servo.ino`;
- Arduino Mega, braço Robix, fonte adequada aos servos e cabo USB;
- Windows, Linux ou macOS compatível com Tk e as dependências Python.

Em algumas distribuições Linux, pode ser necessário instalar Tk, suporte a ambientes virtuais e configurar a permissão da porta serial, por exemplo pelos pacotes `python3-tk` e `python3-venv` e pelo grupo `dialout`. Drivers USB também podem ser necessários conforme a placa.

## Instalação

Execute os comandos a partir da raiz do repositório.

1. Crie o ambiente virtual:

```bash
python -m venv .venv
```

2. Ative o ambiente conforme o terminal.

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

3. Instale as dependências de execução:

```bash
python -m pip install -r requirements.txt
```

Para desenvolver e testar, use `python -m pip install -r requirements-dev.txt`. Esse arquivo já inclui `requirements.txt`.

## Firmware E Conexão

1. Confira os pinos 8 a 13 definidos em `Servo/Servo.ino` e adapte-os à montagem.
2. Use alimentação dimensionada para os servos e terra comum com o Arduino. Não presuma que a alimentação USB seja adequada para seis servos.
3. Selecione Arduino Mega e a porta correta na Arduino IDE e grave o firmware.
4. Mantenha o braço fixado e sua área livre antes de conectar ou abrir a serial.
5. Execute `python main.py` e selecione a porta no topo da aplicação.

A aplicação e o firmware usam comunicação serial a 115200 baud.

> **Atenção:** ao iniciar, o firmware anexa os seis servos e solicita 90 graus. Abrir a porta serial normalmente reinicia o Arduino e pode repetir esse movimento. Confira a montagem antes de conectar.

Após gravar o firmware atual, todo alvo recebido pelo Arduino usa automaticamente um perfil de velocidade triangular ou trapezoidal, com aceleração e frenagem progressivas. Isso vale para `MoveTo`, `MovePose`, Teach Pendant, métodos pessoais e exemplos; não é necessário escrever ângulos intermediários no código Robix.

A suavização começa depois da inicialização. O movimento para 90 graus ao anexar os servos não pode partir de uma posição física conhecida porque esta versão não possui sensores. O STOP também interrompe o perfil imediatamente em vez de desacelerar, priorizando a parada solicitada.

Sem Arduino, a interface, o editor e a gravação de poses podem ser usados em modo offline. Tentativas de transmissão falham e não são registradas como estado comandado.

## Linguagem Robix

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

- `MoveTo(M, A)`: motor de 1 a 6 e ângulo de 0 a 180;
- `MovePose(B, O, C, P, R, G)`: seis ângulos de 0 a 180;
- `Wait(MS)`: espera em milissegundos;
- `setup`: executado uma vez;
- `loop`: repetido indefinidamente até uma parada controlada, troca de tela ou encerramento;
- `metodo Nome`: bloco reutilizável, chamado pelo nome sem parênteses.

Por compatibilidade com rotinas antigas, o reconhecimento de comandos é permissivo e localiza chamadas mesmo com texto antes ou depois delas. Para desativar uma linha, use `//`; apenas acrescentar outro texto pode não impedir o movimento.

Arquivos de rotina usam texto UTF-8 com extensão `.txt`. Consulte a gramática e o comportamento de erros no [Manual do Operador](Instrucoes/HELP.md).

## Exemplos Integrados

Abra a galeria pelo ícone `🧪` ou por `F6`. A prévia é somente leitura. Cada exemplo declara um método e o chama uma vez em `setup`; nenhum possui `loop`.

| Método | Finalidade |
|---|---|
| `PosicaoNeutra` | Centralizar os seis motores em 90 graus |
| `AbrirGarra` | Abrir a garra na referência didática |
| `FecharGarra` | Fechar a garra na referência didática |
| `CicloDaGarra` | Demonstrar dois ciclos de abertura e fechamento |
| `TestarJuntas` | Testar os seis motores individualmente |
| `VarreduraDaBase` | Percorrer esquerda, centro e direita com a base |
| `DemonstrarEspacoTrabalho` | Explorar uma sequência moderada de poses |
| `PercorrerTresPontos` | Demonstrar uma trajetória coordenada A-B-C |
| `AcenarRobix` | Produzir um gesto curto com punho e braço |
| `InspecionarObjeto` | Simular a rotação de um objeto na garra |
| `CoreografiaRobix` | Coordenar várias juntas em quatro poses |
| `PickAndPlace` | Demonstrar uma sequência de coleta e entrega |

"Executar uma vez" ou `F9` na galeria inicia imediatamente o código original do exemplo. Para adaptar os ângulos, use "Adicionar método ao Editor", edite a declaração e chame seu nome em `setup`, `loop` ou outro método. Inserir apenas acrescenta a declaração ao fim do código, não cria a chamada e não executa movimento. Uma declaração com o mesmo nome não é inserida novamente.

Os métodos mostram apenas poses e destinos relevantes. A aceleração, os passos físicos e a frenagem são calculados pelo firmware, portanto não aparecem como sequências artificiais de pequenos ângulos no Editor.

> **Segurança dos exemplos:** os valores são referências didáticas. Antes da execução direta, mantenha a área livre e confira orientação dos servos, limites mecânicos, ferramenta e obstáculos. A faixa de 0 a 180 graus do protocolo não é um envelope seguro da montagem.

### Biblioteca pessoal

A aba "Métodos" do Editor reúne exemplos incorporados e métodos pessoais. "Salvar métodos do código" extrai todas as declarações `metodo Nome:` presentes no Editor e as mescla em `~/.suri_edu/metodos.json`.

- Um nome já salvo é atualizado; outros métodos da biblioteca são preservados.
- Métodos pessoais precisam ser inseridos no código antes da execução.
- Dependências chamadas por um método devem ser inseridas separadamente.
- O botão `×` remove o item da biblioteca após confirmação, mas não altera o Editor aberto.
- Os exemplos incorporados são fixos, não dependem do JSON e não podem ser removidos.

## Arquivos E Persistência

O Editor abre e salva `.txt` em UTF-8. Cada salvamento abre uma janela "Salvar como"; não há arquivo atual associado, salvamento automático, indicador de alterações ou confirmação ao abrir, exportar ou fechar com conteúdo não salvo.

Os pontos capturados no Teach Pendant permanecem somente na memória até "Exportar". A exportação substitui o conteúdo do Editor, acrescenta `Wait(1000)` após cada ponto e gera um `loop` que repete continuamente o método até STOP, troca de tela ou encerramento.

## Operação Segura

Durante uma rotina, espaço e STOP cancelam os callbacks e comandos locais ainda não executados. O botão STOP também pode ser usado fora de uma rotina para interromper uma interpolação manual. A aplicação invalida o estado comandado, tenta escrever `<STOP,id>` e, se a escrita for completa, aguarda por até 1 segundo o `<ACK,STOP,id>` correspondente.

O firmware congela os alvos na última etapa interpolada, mantém os servos anexados e continua solicitando o último PWM. Isso não mede nem garante posição, torque físico ou capacidade de sustentação. O transporte serial é FIFO: bytes anteriores permanecem à frente do STOP, portanto não há garantia de latência máxima.

A suavização reduz mudanças bruscas de velocidade, mas não detecta colisões, carga excessiva, folga, travamento ou limites mecânicos. Ela não transforma uma pose válida no protocolo em uma pose fisicamente segura.

Trocar de tela durante uma rotina solicita STOP. Iniciar outra rotina ou fechar a aplicação durante uma execução envia STOP de forma best-effort, mas esses fluxos não aguardam a confirmação antes de continuar ou encerrar.

No Editor, Painel e Exemplos, `F9` inicia imediatamente o código da tela atual. Nas demais telas apenas registra um aviso. Abrir ou inserir código não movimenta o robô por si só.

> **Limitação de segurança:** a parada depende do computador, aplicação, cabo, porta serial, firmware e alimentação. Ela não substitui uma parada de emergência física, cabeada e independente do software.

## Estado Dos Motores

- **Desejado:** ângulo solicitado pelo operador ou pela rotina;
- **Comandado:** ângulo cujo quadro inteiro foi aceito pela API serial;
- **Confirmado:** ângulo informado por telemetria ou sensor.

Não há ACK de movimento nem sensor de posição nesta versão. O estado confirmado permanece desconhecido e a posição física não deve ser inferida dos sliders.

## Testes E Qualidade

```bash
python -m pytest --cov=. --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
```

## Limitações E Próximos Passos

- Definir limites mecânicos por junta e prevenção de colisões;
- Adicionar ACK de movimento e telemetria contínua;
- Versionar o protocolo, adicionar heartbeat e recuperação automática;
- Integrar sensores para posição física confiável;
- Criar visualização esquemática ou 3D;
- Distinguir visualmente posições desejada, comandada e confirmada.

## Documentação

- Manual completo: [`Instrucoes/HELP.md`](Instrucoes/HELP.md)
- Protocolo serial: [`Instrucoes/PROTOCOL.md`](Instrucoes/PROTOCOL.md)
- Repositório: https://github.com/Andrus227/SuRI-Edu

## Contato E Autoria

André Victor Lucio, `andrelucio.ifmt@gmail.com`

Andrus227 e equipe da disciplina de Robótica Industrial.
