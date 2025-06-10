from datetime import date, timedelta, time, datetime
import random

MAX = 100000

def aleatorioDistrNormal(minimo: int, maximo: int, mu: float|int = 0, sigma: float = 0):
    if mu == 0: mu = (minimo + maximo) / 2
    if sigma == 0: sigma = (maximo - minimo) / 4
    x = random.gauss(mu, sigma)
    valor = round(x)
    if valor > maximo: valor = maximo
    elif valor < minimo: valor = minimo
    return valor



class Aeroporto:
    def __init__(self, codigo: str, nome: str, cidade: str, pais: str, x: float, y: float):
        self.codigo = codigo
        self.nome = nome
        self.cidade = cidade
        self.pais = pais

        self.x = x
        self.y = y

    def tempoDeVoo(self, outro: 'Aeroporto'):
        x = outro.x - self.x
        y = outro.y - self.y
        distancia = (x ** 2 + y ** 2) ** 0.5 # Desprezando a curvatura da Terra...
        return int(distancia * 7.35)
    
    def __repr__(self) -> str:
        return f'Aeroporto({self.codigo}, {self.nome}, {self.cidade}, {self.pais})'



class Assento:
    def __init__(self, lugar: str, primeira_classe: bool):
        self.lugar = lugar
        self.primeira_classe = primeira_classe

    def __repr__(self) -> str:
        return f'Assento({self.lugar}, {self.primeira_classe})'



class Aviao:

    def __init__(self, no_serie: int, modelo: str):
        self.no_serie = no_serie
        self.modelo = modelo

        self.assentos = self.gerarAssentos()
        self.ultimo_voo: Voo|None = None

    def gerarAssentos(self) -> tuple[Assento]:
        assentos = []
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        num_filas = aleatorioDistrNormal(25, 50)
        num_assentos_por_fila = aleatorioDistrNormal(2, 4) * 2
        percentagem_prim_classe = aleatorioDistrNormal(8, 15) / 100
        num_filas_prim_classe = round(num_filas * percentagem_prim_classe)

        for fila in range(1, num_filas + 1):
            prim_classe = False
            if fila <= num_filas_prim_classe: prim_classe = True
            for letra in range(num_assentos_por_fila):
                assentos.append(Assento(f"{fila}{letras[letra]}", prim_classe))

        return tuple(assentos)

    def obterAeroportoDePartida(self) -> Aeroporto:
        global AEROPORTOS, AEROPORTOS_NAO_USADOS
        if self.ultimo_voo is None: return obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS)
        return self.ultimo_voo.aero_chegada
    
    def num_assentos(self) -> int:
        return len(self.assentos)
    
    def __repr__(self) -> str:
        return f'Aviao({self.no_serie}, {self.modelo})'



class Voo:
    id_counter = 0

    def __init__(self, aviao: Aviao, hora_partida: datetime, hora_chegada: datetime,
                 aero_partida: Aeroporto, aero_chegada: Aeroporto):
        self.id = Voo.id_counter
        self.aviao = aviao
        self.hora_partida = hora_partida
        self.hora_chegada = hora_chegada
        self.aero_partida = aero_partida
        self.aero_chegada = aero_chegada

        self.preco_prim_classe, self.preco_seg_classe = self.definirPrecos()
        self.vendas: list[Venda] = []
        Voo.id_counter += 1

    def definirPrecos(self) -> tuple[float, float]:
        base = aleatorioDistrNormal(1, 4)
        multiplicador = aleatorioDistrNormal(200, 400) / 100
        preco_seg_classe = base * self.aero_partida.tempoDeVoo(self.aero_chegada)
        return round(preco_seg_classe * multiplicador, 2), round(preco_seg_classe, 2)
    
    def num_vendas(self) -> int:
        return len(self.vendas)
    
    def __repr__(self) -> str:
        return f'Voo({self.id}, Aviao[{self.aviao.no_serie}], Partida: {self.hora_partida.day}/{self.hora_partida.month} {self.hora_partida.hour}:{self.hora_partida.minute}, Chegada: {self.hora_chegada.day}/{self.hora_chegada.month} {self.hora_chegada.hour}:{self.hora_chegada.minute}, AeroPartida[{self.aero_partida.codigo}], AeroChegada[{self.aero_chegada.codigo}], Preco-1-Classe: {self.preco_prim_classe}€, Preço-2-Classe: {self.preco_seg_classe}€)'



class Venda:
    codigo = 0
    nif = 1

    def __init__(self, balcao: Aeroporto, hora_partida_voo: datetime, voo: Voo):
        self.codigo = Venda.codigo
        self.nif = self.gerarNIF()
        self.balcao = balcao
        self.data_hora = self.gerarDataHoraDeCompra(hora_partida_voo)

        self.voo = voo
        self.bilhetes: list['Bilhete'] = []
        Venda.codigo += 1

    def gerarNIF(self):
        new_nif = ''
        nif_str = str(Venda.nif)
        num_zeros = 9 - len(nif_str)
        if num_zeros < 0: raise ValueError("Demasiados clientes!")
        for _ in range(num_zeros): new_nif += '0'
        new_nif += nif_str
        Venda.nif += 1
        return new_nif
    
    def gerarDataHoraDeCompra(self, hora_partida_voo: datetime):
        datetime_max = hora_partida_voo - timedelta(hours=12)
        datetime_min = hora_partida_voo - timedelta(hours=2200) # Aproximadamente 3 meses
        return datetimeAleatorio(datetime_min, datetime_max)
    
    def adicionarBilhete(self, bilhete: 'Bilhete'):
        self.bilhetes.append(bilhete)

    def __repr__(self) -> str:
        return f'Venda({self.codigo}, {self.nif}, {self.balcao}, {self.data_hora.day}/{self.data_hora.month} {self.data_hora.hour}:{self.data_hora.minute})'



class Bilhete:
    id_counter = 0

    def __init__(self, voo: Voo, nome: str, assento: Assento):
        self.id = Bilhete.id_counter
        self.voo = voo
        self.nome = nome
        self.assento = assento
        Bilhete.id_counter += 1

    def __repr__(self) -> str:
        return f'Bilhete({self.id}, Voo[{self.voo.id}], {self.nome}, {self.assento.lugar})'



######################## Funções Gerais ########################


def obterAleatorio(opcoes: tuple, nao_usados: list, excluir=None):
    opcoes_list = list(opcoes)
    if excluir is not None: opcoes_list = [x for x in opcoes_list if x != excluir]
    if not nao_usados: return random.choice(tuple(opcoes_list))
    else:
        opcao = random.choice(tuple(nao_usados))
        nao_usados.remove(opcao)
        return opcao
    

def datetimeAleatorio(inicio: datetime, fim: datetime):
    delta = fim - inicio
    segundos_totais = int(delta.total_seconds())
    segundos_aleatorios = random.randint(0, segundos_totais)
    return inicio + timedelta(seconds=segundos_aleatorios)
    

def obterAviao(data: date) -> Aviao:
    global AVIOES, AVIOES_NAO_USADOS, MAX
    i = 0
    while i < MAX:
        aviao: Aviao = obterAleatorio(AVIOES, AVIOES_NAO_USADOS)
        if aviao.ultimo_voo is not None and (aviao.ultimo_voo.hora_chegada.date() > data \
        or aviao.ultimo_voo.hora_chegada.time() > time(23, 30)):
            i += 1
            continue
        return aviao
    raise ValueError("Nenhum avião disponível")




######################## Voo ########################


def obterHorasVoo(data: date, aviao: Aviao, aero_partida: Aeroporto, aero_chegada: Aeroporto,
                  hora_partida_partida_chegada: set, hora_chegada_partida_chegada: set) -> tuple[datetime, datetime]:
    global MAX
    hora_maxima = datetime.combine(data, time(23, 59))
    hora_minima = datetime.combine(data, time(0, 0))
    if aviao.ultimo_voo is not None and aviao.ultimo_voo.hora_chegada.date() == data:
        hora_minima = aviao.ultimo_voo.hora_chegada + timedelta(minutes=30)

    i = 0
    while i < MAX:
        hora_partida = datetimeAleatorio(hora_minima, hora_maxima)
        tempo_voo = aero_partida.tempoDeVoo(aero_chegada)
        hora_chegada = hora_partida + timedelta(minutes=tempo_voo)

        if (hora_partida, aero_partida, aero_chegada) not in hora_partida_partida_chegada \
        and (hora_chegada, aero_partida, aero_chegada) not in hora_chegada_partida_chegada:
            hora_partida_partida_chegada.add((hora_partida, aero_partida, aero_chegada))
            hora_chegada_partida_chegada.add((hora_chegada, aero_partida, aero_chegada))
            return hora_partida, hora_chegada
        i += 1
        
    raise ValueError("Não há horas de partida e chegada disponíveis")
    

def gerarVoo(data: date, hora_partida_partida_chegada: set, hora_chegada_partida_chegada: set, voos_regresso: list[Voo]):    
    global AEROPORTOS, AVIOES, VOOS, AEROPORTOS_NAO_USADOS, AVIOES_NAO_USADOS # Para reduzir a quantidade de argumentos das funções
    garantir_regresso = True
    if not voos_regresso:
        aviao = obterAviao(data)
        aero_partida = aviao.obterAeroportoDePartida()
        aero_chegada = obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS, excluir=aero_partida)
    else:
        aviao = voos_regresso[-1].aviao
        if aviao.ultimo_voo is not None and (aviao.ultimo_voo.hora_chegada.date() > data \
        or aviao.ultimo_voo.hora_chegada.time() > time(23, 30)):
            aviao = obterAviao(data)
            aero_partida = aviao.obterAeroportoDePartida()
            aero_chegada = obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS, excluir=aero_partida)
        else:
            aero_partida = voos_regresso[-1].aero_chegada
            aero_chegada = voos_regresso[-1].aero_partida
            garantir_regresso = False
            voos_regresso.pop()

    hora_partida, hora_chegada = obterHorasVoo(data, aviao, aero_partida, aero_chegada,
                                               hora_partida_partida_chegada, hora_chegada_partida_chegada)
    voo = Voo(aviao, hora_partida, hora_chegada, aero_partida, aero_chegada)

    gerarVendas(voo)

    if garantir_regresso: voos_regresso.append(voo)
    aviao.ultimo_voo = voo
    VOOS.append(voo)



######################## Vendas ########################


def gerarVendas(voo: Voo):
    forcar_prim_classe = True
    forcar_sec_classe = True
    assentos_disponiveis = list(voo.aviao.assentos)
    bilhetes_por_vender = aleatorioDistrNormal(
                            minimo=round(voo.aviao.num_assentos() * 0.33),
                            maximo=voo.aviao.num_assentos(),
                            mu=round(voo.aviao.num_assentos() * 0.8) # Para que os aviões tendam a estar 80% cheios
                          )
    
    while bilhetes_por_vender > 0:
        venda = Venda(voo.aero_partida, voo.hora_partida, voo)
        bilhetes_por_vender, forcar_prim_classe, forcar_sec_classe = venderBilhetes(venda, bilhetes_por_vender,
                                                                                    assentos_disponiveis,
                                                                                    forcar_prim_classe,
                                                                                    forcar_sec_classe)




######################## Bilhetes ########################


def gerarNome(nomes_ja_gerados: list[str]) -> str:
    global NOMES, APELIDOS, MAX
    apelidos = list(APELIDOS)
    nome = f"{random.choice(NOMES)} "
    i = 0
    while i < MAX:
        quantidade_apelidos = aleatorioDistrNormal(1, 6, mu=2.5)
        for _ in range(quantidade_apelidos):
            apelido = random.choice(tuple(apelidos))
            nome += apelido
            nome += ' '
            apelidos.remove(apelido)

        nome = nome.rstrip(' ')
        if nome not in nomes_ja_gerados:
            nomes_ja_gerados.append(nome)
            return nome
        
        i += 1
    raise ValueError("Esgotaram-se os nomes")


def venderBilhetes(venda: Venda, bilhetes_por_vender: int, assentos_disponiveis: list[Assento],
                   forcar_prim_classe: bool, forcar_seg_classe: bool) -> tuple[int, bool, bool]:
    num_bilhetes = min(aleatorioDistrNormal(1, 5, mu=2), bilhetes_por_vender)
    nomes_ja_gerados = []
    for _ in range(num_bilhetes):
        nome = gerarNome(nomes_ja_gerados)

        if forcar_prim_classe:
            assento = assentos_disponiveis[0]
            forcar_prim_classe = False

        elif forcar_seg_classe:
            assento = assentos_disponiveis[-1]
            forcar_seg_classe = False

        else: assento = random.choice(tuple(assentos_disponiveis))
        
        bilhete = Bilhete(venda.voo, nome, assento)
        venda.adicionarBilhete(bilhete)
        assentos_disponiveis.remove(assento)
        bilhetes_por_vender -= 1

    return bilhetes_por_vender, forcar_prim_classe, forcar_seg_classe




######################## Gerar dados ########################


NOMES = (
    "Ana", "Beatriz", "Bruna", "Carla", "Catarina", "Cláudia", "Cristina", "Daniela", "Diana", "Eva",
    "Filipa", "Helena", "Inês", "Isabel", "Joana", "Leonor", "Liliana", "Lúcia", "Luísa", "Madalena",
    "Margarida", "Mariana", "Marta", "Matilde", "Patrícia", "Rita", "Rosa", "Sara", "Sofia", "Teresa",
    "Vera", "Vitória", "Alexandra", "Andreia", "Bárbara", "Camila", "Débora", "Ema", "Francisca", "Gabriela",
    "Afonso", "Alexandre", "André", "António", "Bruno", "Carlos", "Cláudio", "Daniel", "David", "Diogo",
    "Eduardo", "Fábio", "Fernando", "Francisco", "Gabriel", "Gonçalo", "Geraldo", "Guilherme", "Hugo", "Igor", "Isaac",
    "João", "Jorge", "José", "Leonardo", "Luís", "Manuel", "Marco", "Martim", "Mateus", "Miguel",
    "Nuno", "Paulo", "Pedro", "Rafael", "Ricardo", "Rodrigo", "Rui", "Salvador", "Samuel", "Tiago",
    "Tomás", "Vicente", "Vítor", "Xavier"
)



APELIDOS = (
    "Abreu", "Aguiar", "Albuquerque", "Almeida", "Alves", "Amaral", "Andrade", "Antunes", "Araujo",
    "Azevedo", "Barbosa", "Barros", "Bastos", "Batista", "Bento", "Bernardo", "Borges", "Braga", "Branco",
    "Brás", "Cabral", "Campos", "Cardoso", "Carneiro", "Carvalho", "Castro", "Coelho", "Conceição",
    "Correia", "Corte-Real", "Costa", "Couto", "Cruz", "Dias", "Domingues", "Duarte", "Esteves", "Faria",
    "Fernandes", "Figueiredo", "Figueira", "Filipe", "Fonseca", "Freitas", "Freire", "Frota", "Gomes",
    "Gonçalves", "Gouveia", "Graça", "Guimarães", "Henriques", "Inácio", "Jesus", "Jorge", "Lemos", "Leal",
    "Lima", "Lopes", "Lorena", "Machado", "Madeira", "Magalhães", "Maia", "Manso", "Marques", "Martins",
    "Matias", "Matos", "Medeiros", "Meireles", "Melo", "Mendes", "Mesquita", "Miranda", "Monteiro",
    "Morais", "Moreira", "Moura", "Neves", "Nogueira", "Nunes", "Oliveira", "Ourique", "Pacheco", "Pais",
    "Palmeira", "Paredes", "Parente", "Pereira", "Pimentel", "Pinheiro", "Pinto", "Pires", "Queirós",
    "Quintana", "Ramalho", "Ramos", "Rebelo", "Reis", "Ribeiro", "Rocha", "Rodrigues", "Sá", "Sacadura",
    "Sales", "Salvador", "Sampaio", "Saraiva", "Santos", "Sequeira", "Silva", "Simões", "Soares",
    "Sousa", "Tavares", "Teixeira", "Tomé", "Torres", "Valente", "Varela", "Vasconcelos", "Vaz", "Veloso",
    "Vieira", "Vilela", "Xavier"
)



AEROPORTOS = (
    Aeroporto("LHR", "Heathrow Airport", "Londres", "Reino Unido", 51.4700, -0.4543),
    Aeroporto("LGW", "Gatwick Airport", "Londres", "Reino Unido", 51.1537, -0.1821),
    Aeroporto("CDG", "Charles de Gaulle Airport", "Paris", "França", 49.0097, 2.5479),
    Aeroporto("ORY", "Orly Airport", "Paris", "França", 48.7262, 2.3652),
    Aeroporto("AMS", "Schiphol Airport", "Amesterdão", "Países Baixos", 52.3105, 4.7683),
    Aeroporto("FRA", "Frankfurt Airport", "Frankfurt", "Alemanha", 50.0379, 8.5622),
    Aeroporto("MUC", "Munich Airport", "Munique", "Alemanha", 48.3538, 11.7861),
    Aeroporto("MAD", "Adolfo Suárez Madrid–Barajas Airport", "Madrid", "Espanha", 40.4983, -3.5676),
    Aeroporto("BCN", "Barcelona–El Prat Airport", "Barcelona", "Espanha", 41.2974, 2.0833),
    Aeroporto("LIS", "Humberto Delgado Airport", "Lisboa", "Portugal", 38.7742, -9.1342),
    Aeroporto("OPO", "Francisco Sá Carneiro Airport", "Porto", "Portugal", 41.2422, -8.6781),
    Aeroporto("MXP", "Milan Malpensa Airport", "Milão", "Itália", 45.6306, 8.7281),
    Aeroporto("LIN", "Linate Airport", "Milão", "Itália", 45.4451, 9.2767),
    Aeroporto("ATH", "Athens International Airport", "Atenas", "Grécia", 37.9364, 23.9445),
    Aeroporto("CPH", "Copenhagen Airport", "Copenhaga", "Dinamarca", 55.6181, 12.6561),
    Aeroporto("OSL", "Oslo Gardermoen Airport", "Oslo", "Noruega", 60.1976, 11.1004),
    Aeroporto("ARN", "Stockholm Arlanda Airport", "Estocolmo", "Suécia", 59.6519, 17.9186),
    Aeroporto("BRU", "Brussels Airport", "Bruxelas", "Bélgica", 50.9014, 4.4844),
    Aeroporto("VIE", "Vienna International Airport", "Viena", "Áustria", 48.1103, 16.5697),
    Aeroporto("DUB", "Dublin Airport", "Dublin", "Irlanda", 53.4213, -6.2701)
)



AVIOES = (
    Aviao(no_serie=1000, modelo="Boeing 737"),
    Aviao(no_serie=1001, modelo="Airbus A320"),
    Aviao(no_serie=1002, modelo="Embraer E190"),
    Aviao(no_serie=1003, modelo="Bombardier CRJ200"),
    Aviao(no_serie=1004, modelo="Boeing 777"),
    Aviao(no_serie=1005, modelo="Airbus A350"),
    Aviao(no_serie=1006, modelo="McDonnell Douglas MD-80"),
    Aviao(no_serie=1007, modelo="Concorde"),
    Aviao(no_serie=1008, modelo="Boeing 737"),
    Aviao(no_serie=1009, modelo="Airbus A320"),
    Aviao(no_serie=1010, modelo="Embraer E190"),
    Aviao(no_serie=1011, modelo="Bombardier CRJ200"),
    Aviao(no_serie=1012, modelo="Boeing 777"),
    Aviao(no_serie=1013, modelo="Airbus A350"),
    Aviao(no_serie=1014, modelo="McDonnell Douglas MD-80"),
    Aviao(no_serie=1015, modelo="Concorde")
)



AEROPORTOS_NAO_USADOS = list(AEROPORTOS)
AVIOES_NAO_USADOS = list(AVIOES)



VOOS = []


# Gerar voos, vendas e bilhetes
data = date(2025, 1, 1)
data_fim = date(2025, 7, 31)

hora_partida_partida_chegada = set()
hora_chegada_partida_chegada = set()

voos_regresso = []

while data <= data_fim:
    for _ in range(aleatorioDistrNormal(5, 10)):
        gerarVoo(data, hora_partida_partida_chegada, hora_chegada_partida_chegada, voos_regresso)
    data += timedelta(days=1)