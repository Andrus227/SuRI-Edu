from __future__ import annotations

HELP_TOPICS: dict[str, str] = {
    "1. Visão Geral": (
        "O SuRI-EDU é um supervisório educacional para seis servomotores de um braço "
        "Robix com Arduino Mega.\n"
        "Repositório: https://github.com/Andrus227/SuRI-Edu\n"
        "Manual: Instrucoes/HELP.md | Protocolo: Instrucoes/PROTOCOL.md\n"
        "Use o robô fixado e com a área livre. A parada por software não substitui "
        "uma emergência física cabeada e independente."
    ),
    "2. Primeiros Passos": (
        "Requisito: Python 3.10 ou superior.\n"
        "1. Crie o ambiente: python -m venv .venv\n"
        "2. PowerShell: .\\.venv\\Scripts\\Activate.ps1\n"
        "   Prompt: .venv\\Scripts\\activate.bat\n"
        "   Git Bash: source .venv/Scripts/activate\n"
        "   Linux/macOS: source .venv/bin/activate\n"
        "3. Execute: python -m pip install -r requirements.txt\n"
        "4. Confira os pinos e grave a versão atual de Servo/Servo.ino.\n"
        "5. Com a área livre, execute: python main.py"
    ),
    "3. Conexão Serial": (
        "Selecione a porta do Arduino no topo e use Atualizar se necessário.\n"
        "O protocolo opera a 115200 baud; o Monitor registra movimentos enviados.\n"
        "Abrir a serial pode reiniciar o Arduino: os seis servos iniciam em 90 graus.\n"
        "Toda tentativa de conexão invalida o estado comandado anterior.\n"
        "Sem Arduino, editor e interface funcionam offline, sem movimento físico."
    ),
    "4. Teach Pendant (Sliders)": (
        "Tab avança pelos seis motores; Shift+Tab retorna e a ordem é circular.\n"
        "As setas ajustam o slider selecionado, identificado pelo quadro azul.\n"
        "Mudar o foco não altera o ângulo e o arraste pelo mouse continua disponível.\n"
        "Tempo Real transmite no máximo uma vez a cada 50 ms durante alterações e "
        "novamente ao soltar.\n"
        "Enviar Pose manda motores desconhecidos ou alterados; após conexão ou STOP, "
        "a próxima pose tenta enviar os seis. A faixa 0-180 não é limite mecânico."
    ),
    "5. Editor de Código": (
        "Comandos: MoveTo(M, A), MovePose(B, O, C, P, R, G) e Wait(MS).\n"
        "Motores: 1-6; ângulos: 0-180; esperas: inteiros não negativos.\n"
        "Blocos: setup (uma vez), loop (repetição) e metodo; use // para comentários.\n"
        "Métodos usam letras, números ou _ e são chamados sem parênteses.\n"
        "A aba Métodos insere exemplos e snippets pessoais; inserir não executa movimento.\n"
        "Salvar métodos do código mescla declarações em ~/.suri_edu/metodos.json.\n"
        "O parser localiza comandos mesmo com texto ao redor; use // para desativar linhas.\n"
        "Arquivos são .txt UTF-8 e todo salvamento usa Salvar como. Não há autosave nem "
        "confirmação ao fechar conteúdo não salvo."
    ),
    "6. Painel de Execução": (
        "Carregue uma rotina .txt no Painel (F5) e pressione F9 para iniciar.\n"
        "O Painel é somente leitura; abrir e salvar pertencem ao Editor.\n"
        "Trocar de tela cancela etapas locais pendentes e solicita STOP.\n"
        "MovePose usa até seis quadros e pode ser interrompido parcialmente.\n"
        "Carregar um arquivo não executa movimento; F9 inicia o conteúdo mostrado."
    ),
    "7. Exemplos": (
        "Use o ícone de laboratório ou F6 para abrir as rotinas de exemplo.\n"
        "Básicos: PosicaoNeutra, AbrirGarra, FecharGarra e CicloDaGarra.\n"
        "Eixos: TestarJuntas, VarreduraDaBase e DemonstrarEspacoTrabalho.\n"
        "Coordenados: PercorrerTresPontos, AcenarRobix e CoreografiaRobix.\n"
        "Manipulação: InspecionarObjeto e PickAndPlace.\n"
        "Cada exemplo declara um método e o chama uma vez no setup; nenhum possui loop.\n"
        "Os exemplos mostram somente os destinos; o firmware atual aplica aceleração e "
        "frenagem automaticamente, sem exigir passos intermediários no código.\n"
        "Executar uma vez/F9 movimenta imediatamente com o código original. Adicionar ao "
        "Editor insere só a declaração: edite-a e chame seu nome no setup ou loop.\n"
        "Métodos pessoais são mesclados em ~/.suri_edu/metodos.json; remover da biblioteca "
        "não altera o Editor e dependências não são inseridas automaticamente.\n"
        "Revise todos os ângulos: 0-180 é a faixa do protocolo, não um limite mecânico."
    ),
    "8. Atalhos e Parada": (
        "F1 Manual | F2 Menu | F3 Teach Pendant | F4 Editor | F5 Painel | "
        "F6 Exemplos | F9 Executar no Editor, Painel ou Exemplos.\n"
        "Trocar de tela, inclusive com F6, solicita STOP durante uma rotina.\n"
        "Durante uma rotina, Espaço e STOP cancelam etapas e tentam enviar <STOP,id>.\n"
        "O botão também atua fora da rotina; Espaço então mantém seu comportamento normal.\n"
        "O ACK é aguardado por 1 s. Após falha ou timeout, STOP permite nova tentativa.\n"
        "O Arduino congela alvos e mantém PWM, mas não mede posição ou torque físico.\n"
        "A serial é FIFO e não garante latência máxima para a parada. Nova rotina e "
        "fechamento não aguardam o ACK do STOP anterior."
    ),
    "9. Estado e Sincronização": (
        "Desejado: posição solicitada. Comandado: quadro aceito pela API serial.\n"
        "Confirmado exigiria telemetria ou sensor; atualmente permanece desconhecido.\n"
        "Não existe ACK de movimento ou medição física contínua.\n"
        "O ACK de STOP confirma processamento lógico, não posição, torque ou sustentação."
    ),
    "10. Troubleshooting": (
        "Nenhuma porta: verifique cabo, driver, alimentação e use Atualizar.\n"
        "Erro serial: confirme a porta, 115200 baud e o firmware.\n"
        "Sem ACK de STOP: não assuma que o controlador interrompeu o movimento.\n"
        "Sintaxe inválida: confira comandos, parâmetros, faixa e indentação.\n"
        "Biblioteca vazia: salve novamente; JSON ausente, ilegível ou inválido é ignorado.\n"
        "Movimento ao conectar: é a inicialização do firmware em 90 graus.\n"
        "Movimento ainda brusco: regrave o firmware atual e verifique fonte, carga, folgas, "
        "servo danificado e possíveis colisões."
    ),
    "11. Suporte e Próximos Passos": (
        "Planejado: ACK de movimento, telemetria, protocolo versionado e sensores.\n"
        "Também estão previstas visualização esquemática/3D e evolução visual da GUI.\n"
        "Ao relatar falhas, envie sistema, Python, passos, rotina e log.\n"
        "Contato: André Victor Lucio - andrelucio.ifmt@gmail.com"
    ),
}
