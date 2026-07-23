from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoutineExample:
    key: str
    title: str
    description: str
    method_name: str
    method_code: str

    @property
    def code(self) -> str:
        return f"{self.method_code.rstrip()}\n\nsetup:\n    {self.method_name}\n"


ROUTINE_EXAMPLES = (
    RoutineExample(
        key="posicao_neutra",
        title="Posição neutra",
        description="Centraliza os seis motores em 90 graus.",
        method_name="PosicaoNeutra",
        method_code="""metodo PosicaoNeutra:
    // Centraliza todas as juntas
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="abrir_garra",
        title="Abrir garra",
        description="Move somente a garra para a abertura didática de 30 graus.",
        method_name="AbrirGarra",
        method_code="""metodo AbrirGarra:
    // Motor 6: garra aberta
    MoveTo(6, 30)
""",
    ),
    RoutineExample(
        key="fechar_garra",
        title="Fechar garra",
        description="Move somente a garra para o fechamento didático de 100 graus.",
        method_name="FecharGarra",
        method_code="""metodo FecharGarra:
    // Motor 6: garra fechada
    MoveTo(6, 100)
""",
    ),
    RoutineExample(
        key="ciclo_garra",
        title="Ciclo da garra",
        description="Demonstra duas sequências finitas de abertura e fechamento.",
        method_name="CicloDaGarra",
        method_code="""metodo CicloDaGarra:
    // Duas aberturas e fechamentos; termina com a garra aberta
    MoveTo(6, 30)
    Wait(500)
    MoveTo(6, 100)
    Wait(500)
    MoveTo(6, 30)
    Wait(500)
    MoveTo(6, 100)
    Wait(500)
    MoveTo(6, 30)
""",
    ),
    RoutineExample(
        key="teste_juntas",
        title="Teste das juntas",
        description="Testa cada motor separadamente ao redor da posição neutra.",
        method_name="TestarJuntas",
        method_code="""metodo TestarJuntas:
    // Pequena varredura individual dos seis motores
    MovePose(90, 90, 90, 90, 90, 90)
    Wait(500)
    MoveTo(1, 70)
    Wait(300)
    MoveTo(1, 110)
    Wait(300)
    MoveTo(1, 90)
    MoveTo(2, 70)
    Wait(300)
    MoveTo(2, 110)
    Wait(300)
    MoveTo(2, 90)
    MoveTo(3, 70)
    Wait(300)
    MoveTo(3, 110)
    Wait(300)
    MoveTo(3, 90)
    MoveTo(4, 70)
    Wait(300)
    MoveTo(4, 110)
    Wait(300)
    MoveTo(4, 90)
    MoveTo(5, 70)
    Wait(300)
    MoveTo(5, 110)
    Wait(300)
    MoveTo(5, 90)
    MoveTo(6, 70)
    Wait(300)
    MoveTo(6, 100)
    Wait(300)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="varredura_base",
        title="Varredura da base",
        description="Percorre esquerda, centro e direita usando apenas o motor da base.",
        method_name="VarreduraDaBase",
        method_code="""metodo VarreduraDaBase:
    // Mantém as demais juntas em 90 graus
    MovePose(90, 90, 90, 90, 90, 90)
    Wait(500)
    MoveTo(1, 50)
    Wait(500)
    MoveTo(1, 90)
    Wait(500)
    MoveTo(1, 130)
    Wait(500)
    MoveTo(1, 90)
""",
    ),
    RoutineExample(
        key="espaco_trabalho",
        title="Espaço de trabalho",
        description="Demonstra uma varredura moderada de base, braço, punho e garra.",
        method_name="DemonstrarEspacoTrabalho",
        method_code="""metodo DemonstrarEspacoTrabalho:
    // Varredura didática ao redor de 90 graus
    MovePose(90, 90, 90, 90, 90, 90)
    Wait(500)
    MovePose(50, 90, 90, 90, 90, 90)
    Wait(300)
    MovePose(130, 90, 90, 90, 90, 90)
    Wait(300)
    MovePose(90, 70, 90, 90, 90, 90)
    Wait(300)
    MovePose(90, 110, 70, 90, 90, 90)
    Wait(300)
    MovePose(90, 90, 110, 65, 90, 90)
    Wait(300)
    MovePose(90, 90, 90, 115, 45, 90)
    Wait(300)
    MovePose(90, 90, 90, 90, 135, 30)
    Wait(300)
    MovePose(90, 90, 90, 90, 90, 100)
    Wait(300)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="percurso_tres_pontos",
        title="Percurso de três pontos",
        description="Apresenta uma trajetória finita entre três poses coordenadas.",
        method_name="PercorrerTresPontos",
        method_code="""metodo PercorrerTresPontos:
    // Pontos didáticos A, B e C; adapte-os à montagem
    MovePose(60, 100, 80, 100, 90, 90)
    Wait(700)
    MovePose(90, 75, 105, 85, 90, 90)
    Wait(700)
    MovePose(120, 100, 80, 100, 90, 90)
    Wait(700)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="aceno_robix",
        title="Aceno do Robix",
        description="Faz uma saudação; o firmware suaviza automaticamente cada movimento.",
        method_name="AcenarRobix",
        method_code="""metodo AcenarRobix:
    // O perfil global suaviza os destinos sem passos intermediários
    MovePose(90, 90, 90, 90, 90, 90)
    MovePose(90, 80, 50, 70, 60, 90)
    MoveTo(5, 120)
    MoveTo(5, 60)
    MoveTo(5, 120)
    MoveTo(5, 60)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="inspecionar_objeto",
        title="Inspeção de objeto",
        description="Simula a apresentação e a rotação de um objeto preso pela garra.",
        method_name="InspecionarObjeto",
        method_code="""metodo InspecionarObjeto:
    // Posicione o objeto antes de executar e adapte o fechamento da garra
    MovePose(90, 105, 75, 105, 90, 100)
    Wait(600)
    MoveTo(5, 45)
    Wait(500)
    MoveTo(5, 135)
    Wait(500)
    MoveTo(5, 90)
    Wait(400)
    MovePose(90, 90, 90, 90, 90, 100)
""",
    ),
    RoutineExample(
        key="coreografia",
        title="Coreografia coordenada",
        description="Demonstra quatro poses com vários motores movimentando-se em conjunto.",
        method_name="CoreografiaRobix",
        method_code="""metodo CoreografiaRobix:
    // Sequência coordenada e finita ao redor da posição neutra
    MovePose(70, 80, 105, 75, 65, 90)
    Wait(500)
    MovePose(110, 100, 75, 105, 115, 90)
    Wait(500)
    MovePose(70, 105, 80, 100, 115, 90)
    Wait(500)
    MovePose(110, 75, 100, 80, 65, 90)
    Wait(500)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
    RoutineExample(
        key="pick_and_place",
        title="Pick-and-place",
        description="Exemplo completo para adaptar aos pontos reais de coleta e entrega.",
        method_name="PickAndPlace",
        method_code="""metodo PickAndPlace:
    // Ajuste os pontos conforme a montagem e os objetos utilizados
    MovePose(90, 90, 90, 90, 90, 90)
    Wait(500)
    MovePose(65, 110, 75, 110, 90, 30)
    Wait(500)
    MoveTo(6, 100)
    Wait(500)
    MovePose(65, 90, 90, 90, 90, 100)
    Wait(300)
    MovePose(115, 110, 75, 110, 90, 100)
    Wait(500)
    MoveTo(6, 30)
    Wait(500)
    MovePose(90, 90, 90, 90, 90, 90)
""",
    ),
)


def get_routine_example(key: str) -> RoutineExample | None:
    return next((example for example in ROUTINE_EXAMPLES if example.key == key), None)
