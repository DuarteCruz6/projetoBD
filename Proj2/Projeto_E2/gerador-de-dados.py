from datetime import date, timedelta, time, datetime
import time as t
import random

inicio = t.time()

MAX = 1000000
DATA_INICIO = date(2025, 1, 1)
DATAHORA_ATUAL = datetime(2025, 6, 17, 8, 0)
DATA_FIM = date(2025, 7, 31)

def insert(tabela: str) -> str:
    return f"INSERT INTO {tabela} VALUES\n"

def timestamp(datahora: datetime) -> str:
    return f"'{datahora.strftime('%Y-%m-%d %H:%M:%S')}'"

def boolean(boolean_value: bool) -> str:
    if boolean_value: return 'TRUE'
    else: return 'FALSE'

def aleatorioDistrNormal(minimo: int, maximo: int, mu: float|int = 0, sigma: float = 0):
    if mu == 0: mu = (minimo + maximo) / 2
    if sigma == 0: sigma = (maximo - minimo) / 4
    x = random.gauss(mu, sigma)
    valor = round(x)
    if valor > maximo: valor = maximo
    elif valor < minimo: valor = minimo
    return valor

def sqlListaParaStr(sql_lista: list[str]) -> str:
    sql_lista[-2] = f"{sql_lista[-1][:-1]};\n"
    return "".join(sql_lista)



class Aeroporto:
    sql_lista = [insert("aeroporto (codigo, nome, cidade, pais)")]

    def __init__(self, codigo: str, nome: str, cidade: str, pais: str, x: float, y: float):
        global DATA_INICIO
        self.codigo = codigo
        self.nome = nome
        self.cidade = cidade
        self.pais = pais

        self.x = x
        self.y = y
        self.ultima_partida = datetime.combine(DATA_INICIO, time(0, 0))
        Aeroporto.sql_lista += f"    ('{self.codigo}', '{self.nome}', '{self.cidade}', '{self.pais}'),\n"

    def tempoDeVoo(self, outro: 'Aeroporto'):
        x = outro.x - self.x
        y = outro.y - self.y
        distancia = (x ** 2 + y ** 2) ** 0.5 # Desprezando a curvatura da Terra...
        return int(distancia * 7.35)
    
    @staticmethod
    def SQL(): return sqlListaParaStr(Aeroporto.sql_lista)
    
    def __repr__(self) -> str:
        return f'Aeroporto({self.codigo}, {self.nome}, {self.cidade}, {self.pais})'



class Aviao:
    sql_lista = [insert("aviao (no_serie, modelo)")]
    ainda_nao_cumpriram = []
    rota_obrigatoria = ()

    def __init__(self, no_serie: int, modelo: str):
        self.no_serie = no_serie
        self.modelo = modelo

        self.assentos = self.gerarAssentos()
        self.ultimo_voo: Voo|None = None
        
        Aviao.ainda_nao_cumpriram.append(self)
        Aviao.sql_lista += f"    ('{self.no_serie}', '{self.modelo}'),\n"

    def gerarAssentos(self) -> tuple['Assento']:
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
                assentos.append(Assento(f"{fila}{letras[letra]}", prim_classe, self))

        return tuple(assentos)

    def obterAeroportoDePartida(self) -> Aeroporto:
        global AEROPORTOS, AEROPORTOS_NAO_USADOS
        if self.ultimo_voo is None: return obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS)
        return self.ultimo_voo.aero_chegada
    
    def numAssentos(self) -> int:
        return len(self.assentos)

    @staticmethod
    def definirRotaObrigatoria(aero1: Aeroporto, aero2: Aeroporto):
        Aviao.rota_obrigatoria = (aero1, aero2)
    
    @staticmethod
    def SQL(): return sqlListaParaStr(Aviao.sql_lista)
    
    def __repr__(self) -> str:
        return f'Aviao({self.no_serie}, {self.modelo})'



class Assento:
    sql_lista = [insert("assento (lugar, no_serie, prim_classe)")]

    def __init__(self, lugar: str, primeira_classe: bool, aviao: 'Aviao'):
        self.lugar = lugar
        self.primeira_classe = primeira_classe
        self.aviao = aviao

        Assento.sql_lista += f"    ('{self.lugar}', '{aviao.no_serie}', '{self.primeira_classe}'),\n"

    @staticmethod
    def SQL(): return sqlListaParaStr(Assento.sql_lista)

    def __repr__(self) -> str:
        return f'Assento({self.lugar}, {self.primeira_classe})'



class Voo:
    sql_lista = [insert("voo (no_serie, hora_partida, hora_chegada, partida, chegada)")]
    id_counter = 1

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

        Voo.sql_lista += f"    ('{self.aviao.no_serie}', {timestamp(self.hora_partida)}, {timestamp(self.hora_chegada)}, '{self.aero_partida.codigo}', '{self.aero_chegada.codigo}'),\n"

    def definirPrecos(self) -> tuple[float, float]:
        tempo_voo = self.aero_partida.tempoDeVoo(self.aero_chegada) / 60
        return round(60 * tempo_voo), round(40 * tempo_voo, 2)
    
    def adicionarVenda(self, venda: 'Venda'):
        self.vendas.append(venda)

    @staticmethod
    def SQL(): return sqlListaParaStr(Voo.sql_lista)
    
    def __repr__(self) -> str:
        return f'Voo({self.id}, Aviao[{self.aviao.no_serie}], Partida: {self.hora_partida.day}/{self.hora_partida.month} {self.hora_partida.hour}:{self.hora_partida.minute}, Chegada: {self.hora_chegada.day}/{self.hora_chegada.month} {self.hora_chegada.hour}:{self.hora_chegada.minute}, AeroPartida[{self.aero_partida.codigo}], AeroChegada[{self.aero_chegada.codigo}], Preco-1-Classe: {self.preco_prim_classe}€, Preço-2-Classe: {self.preco_seg_classe}€)'



class Venda:
    sql_lista = [insert("venda (nif_cliente, balcao, hora)")]
    id_counter = 1
    nif = 1

    def __init__(self, balcao: Aeroporto, hora_partida_voo: datetime, voo: Voo):
        self.id_counter = Venda.id_counter
        self.nif = self.gerarNIF()
        self.balcao = balcao
        self.data_hora = self.gerarDataHoraDeCompra(hora_partida_voo)

        self.voo = voo
        self.bilhetes: list['Bilhete'] = []
        Venda.id_counter += 1

        Venda.sql_lista += f"    ('{self.nif}', '{self.balcao.codigo}', {timestamp(self.data_hora)}),\n"

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
        return datetimeAleatorio(datetime_min, datetime_max, max_atual=True)
    
    def adicionarBilhete(self, bilhete: 'Bilhete'):
        self.bilhetes.append(bilhete)

    def numBilhetes(self) -> int:
        return len(self.bilhetes)
    
    @staticmethod
    def SQL(): return sqlListaParaStr(Venda.sql_lista)

    def __repr__(self) -> str:
        return f'Venda({self.id_counter}, {self.nif}, {self.balcao}, {self.data_hora.day}/{self.data_hora.month} {self.data_hora.hour}:{self.data_hora.minute})'



class Bilhete:
    sql_lista = [insert("bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie)")]
    id_counter = 1

    def __init__(self, voo: Voo, nome: str, assento: Assento|None, venda: Venda, primeira_classe: bool):
        self.id = Bilhete.id_counter
        self.voo = voo
        self.nome = nome
        self.assento = assento
        self.venda = venda
        self.primeira_classe = primeira_classe
        Bilhete.id_counter += 1

        preco = voo.preco_prim_classe if self.primeira_classe else voo.preco_seg_classe
        Bilhete.sql_lista += f"    ({voo.id}, {venda.id_counter}, '{self.nome}', {preco}, {boolean(self.primeira_classe)}, {self.lugarOut()}, '{voo.aviao.no_serie}'),\n"

    @staticmethod
    def SQL(): return sqlListaParaStr(Bilhete.sql_lista)

    def lugarOut(self) -> str:
        if self.assento == None: return 'NULL'
        return f"'{self.assento.lugar}'"

    def __repr__(self) -> str:
        return f'Bilhete({self.id}, Voo[{self.voo.id}], {self.nome}, {self.assento.lugar if self.assento is not None else "NULL"})'



######################## Funções Gerais ########################


def obterAleatorio(opcoes: tuple, nao_usados: list, excluir=None):
    opcoes_list = list(opcoes)
    if excluir is not None: opcoes_list = [x for x in opcoes_list if x != excluir]
    if not nao_usados: return random.choice(tuple(opcoes_list))
    else:
        opcao = random.choice(tuple(nao_usados))
        nao_usados.remove(opcao)
        return opcao
    

def datetimeAleatorio(inicio: datetime, fim: datetime, max_atual: bool = False):
    global DATAHORA_ATUAL
    if not max_atual: delta = fim - inicio
    else: delta = min(DATAHORA_ATUAL, fim) - inicio
    segundos_totais = int(delta.total_seconds())
    if segundos_totais < 0: raise ValueError("Data de início posterior à de fim")
    segundos_aleatorios = random.randint(0, segundos_totais)
    return inicio + timedelta(seconds=segundos_aleatorios)
    

def obterAviao(data: date, excluir=None) -> Aviao:
    global AVIOES, AVIOES_NAO_USADOS, MAX

    avioes = list(AVIOES)
    if excluir is not None: avioes.remove(excluir)
    i = 0
    while i < MAX:
        aviao: Aviao = obterAleatorio(tuple(avioes), AVIOES_NAO_USADOS)
        if aviao.ultimo_voo is not None and (aviao.ultimo_voo.hora_chegada.date() > data \
        or aviao.ultimo_voo.hora_chegada.time() > time(23, 29)):
            i += 1
            continue
        return aviao
    raise ValueError("Nenhum avião disponível")


def obterAeroportoChegada(aero_partida: Aeroporto, data: date) -> Aeroporto:
    global AEROPORTOS, AEROPORTOS_NAO_USADOS, MAX
    i = 0
    while i < MAX:
        aero_chegada: Aeroporto = obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS, excluir=aero_partida)
        if aero_partida.cidade != aero_chegada.cidade and aero_chegada.ultima_partida.date() <= data:
            return aero_chegada
        i += 1

    raise ValueError("Não há aeroportos de chegada disponíveis")



######################## Voo ########################


def obterHorasVoo(data: date, aviao: Aviao, aero_partida: Aeroporto, aero_chegada: Aeroporto,
                  hora_partida_partida_chegada: set, hora_chegada_partida_chegada: set) -> tuple[datetime, datetime]:
    global MAX
    hora_maxima = datetime.combine(data, time(23, 59))
    hora_minima = max(datetime.combine(data, time(0, 0)), aero_chegada.ultima_partida)
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


def criarVooVolta(voo_ida: Voo) -> Voo:
    aero_partida = voo_ida.aero_chegada
    aero_chegada = voo_ida.aero_partida
    tempo_voo = aero_partida.tempoDeVoo(aero_chegada)
    hora_partida = voo_ida.hora_chegada + timedelta(minutes=aleatorioDistrNormal(30, 240))
    hora_chegada = hora_partida + timedelta(minutes=tempo_voo)
    return Voo(voo_ida.aviao, hora_partida, hora_chegada, aero_partida, aero_chegada)
    

def gerarVoo(data: date, hora_partida_partida_chegada: set, hora_chegada_partida_chegada: set):    
    global AEROPORTOS, AVIOES, VOOS, AEROPORTOS_NAO_USADOS, AVIOES_NAO_USADOS # Para reduzir a quantidade de argumentos das funções

    aviao = obterAviao(data)
    aero_partida = aviao.obterAeroportoDePartida()
    aero_chegada = obterAeroportoChegada(aero_partida, data)

    hora_partida, hora_chegada = obterHorasVoo(data, aviao, aero_partida, aero_chegada,
                                               hora_partida_partida_chegada, hora_chegada_partida_chegada)
    
    voo_ida = Voo(aviao, hora_partida, hora_chegada, aero_partida, aero_chegada)
    gerarVendas(voo_ida)

    voo_volta = criarVooVolta(voo_ida)
    gerarVendas(voo_volta)

    # Para não permitir partidas entre o voo de ida e o de volta
    aero_chegada.ultima_partida = voo_volta.hora_partida

    aviao.ultimo_voo = voo_volta
    VOOS.append(voo_ida)
    VOOS.append(voo_volta)


def gerarVooRotaObrigatoria(aviao: Aviao, sentido: bool) -> tuple[bool, date]:
    global AEROPORTOS, AEROPORTOS_NAO_USADOS, VOOS
    i, j = 0, 1
    if sentido: i, j = 1, 0
    aero_partida = Aviao.rota_obrigatoria[i]
    aero_chegada = Aviao.rota_obrigatoria[j]

    hora_partida = aero_partida.ultima_partida
    if aviao.ultimo_voo is not None: hora_partida =  max(aviao.ultimo_voo.hora_chegada, hora_partida)
    hora_partida += timedelta(minutes=5)

    tempo_voo = aero_partida.tempoDeVoo(aero_chegada)
    hora_chegada = hora_partida + timedelta(minutes=tempo_voo)

    voo = Voo(aviao, hora_partida, hora_chegada, aero_partida, aero_chegada)

    VOOS.append(voo)

    aero_partida.ultima_partida = hora_partida

    # Para o avião voltar ao normal depois de fazer a rota obrigatória
    if aviao.ultimo_voo is None: aero = obterAleatorio(AEROPORTOS, AEROPORTOS_NAO_USADOS)
    else: aero = aviao.ultimo_voo.aero_chegada
    voo_falso = Voo(aviao, hora_partida, hora_chegada, aero_chegada, aero, )

    aero_chegada.ultima_partida = hora_partida
    aviao.ultimo_voo = voo_falso

    return not sentido, hora_chegada.date()


######################## Vendas ########################


def gerarVendas(voo: Voo):
    forcar_prim_classe = True
    forcar_sec_classe = True
    assentos_disponiveis = list(voo.aviao.assentos)
    bilhetes_por_vender = aleatorioDistrNormal(
                            minimo=round(voo.aviao.numAssentos() * 0.33),
                            maximo=voo.aviao.numAssentos(),
                            mu=round(voo.aviao.numAssentos() * 0.8) # Para que os aviões tendam a estar 80% cheios
                          )
    
    while bilhetes_por_vender > 0:
        venda = Venda(voo.aero_partida, voo.hora_partida, voo)
        bilhetes_por_vender, forcar_prim_classe, forcar_sec_classe = venderBilhetes(venda, bilhetes_por_vender,
                                                                                    assentos_disponiveis,
                                                                                    forcar_prim_classe,
                                                                                    forcar_sec_classe)
        voo.adicionarVenda(venda)




######################## Bilhetes ########################


def gerarNome(nomes_ja_gerados: list[str]) -> str:
    global NOMES, APELIDOS, MAX
    apelidos = list(APELIDOS)
    nome = f"{random.choice(NOMES)} "
    i = 0
    while i < MAX:
        quantidade_apelidos = aleatorioDistrNormal(1, 4, mu=2.5)
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


def atribuirAssento(venda: Venda, assentos_disponiveis: list[Assento],
                    forcar_prim_classe: bool, forcar_seg_classe: bool) -> tuple[Assento|None, bool, bool, bool]:
    global DATAHORA_ATUAL

    min_check_in_date = DATAHORA_ATUAL + timedelta(days=2)
    prim_classe = False
    checked_in = True

    if venda.voo.hora_partida > min_check_in_date or (venda.voo.hora_partida > DATAHORA_ATUAL and random.random() < 0.5):
        checked_in = False

    if forcar_prim_classe:
        prim_classe = True
        assento = assentos_disponiveis[0]
        forcar_prim_classe = False

    elif forcar_seg_classe:
        assento = assentos_disponiveis[-1]
        forcar_seg_classe = False

    else: assento = random.choice(tuple(assentos_disponiveis))
    assentos_disponiveis.remove(assento)
    if assento.primeira_classe: prim_classe = True
    if not checked_in: assento = None

    return assento, forcar_prim_classe, forcar_seg_classe, prim_classe


def venderBilhetes(venda: Venda, bilhetes_por_vender: int, assentos_disponiveis: list[Assento],
                   forcar_prim_classe: bool, forcar_seg_classe: bool) -> tuple[int, bool, bool]:
    num_bilhetes = min(aleatorioDistrNormal(1, 5, mu=2), bilhetes_por_vender)
    nomes_ja_gerados = []
    for _ in range(num_bilhetes):
        nome = gerarNome(nomes_ja_gerados)
        assento, forcar_prim_classe, forcar_seg_classe, prim_classe = atribuirAssento(venda, assentos_disponiveis,
                                                                                      forcar_prim_classe, forcar_seg_classe)
        bilhete = Bilhete(venda.voo, nome, assento, venda, prim_classe)
        venda.adicionarBilhete(bilhete)
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


print("A gerar os Aeroportos")

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

Aviao.definirRotaObrigatoria(AEROPORTOS[0], AEROPORTOS[6])


print("A gerar os Aviões")

modelos = ["Boeing 737", "Airbus A320", "Embraer E190", "Bombardier CRJ200",
           "Boeing 777", "Airbus A350", "McDonnell Douglas MD-80", "Concorde"]

AVIOES = tuple(Aviao(1000 + i, modelos[i % len(modelos)]) for i in range(64))



AEROPORTOS_NAO_USADOS = list(AEROPORTOS)
AVIOES_NAO_USADOS = list(AVIOES)



VOOS: list[Voo] = []

print("A gerar voos e respetivas vendas e bilhetes")

# Gerar voos, vendas e bilhetes
data = DATA_INICIO

hora_partida_partida_chegada = set()
hora_chegada_partida_chegada = set()
sentido = False
rota_obrigatoria_data = (DATAHORA_ATUAL - timedelta(days=90)).date()

while data <= DATA_FIM:

    if data == rota_obrigatoria_data:
        data += timedelta(days=1)
        while Aviao.ainda_nao_cumpriram:
            aviao = Aviao.ainda_nao_cumpriram[-1]
            sentido, data = gerarVooRotaObrigatoria(aviao, sentido)
            Aviao.ainda_nao_cumpriram.pop()
        
        data += timedelta(days=1)
        continue

    for _ in range(random.randint(3, 5)):
        gerarVoo(data, hora_partida_partida_chegada, hora_chegada_partida_chegada)
    data += timedelta(days=1)



# Verificar restrições
print("A verificar restrições")

if AVIOES_NAO_USADOS: raise ValueError("Há aviões não usados")
if AEROPORTOS_NAO_USADOS: raise ValueError("Há aeroportos não usados")

num_vendas = 0
num_bilhetes = 0
for voo in VOOS:
    for venda in voo.vendas:
        num_bilhetes += venda.numBilhetes()
        num_vendas += 1

if num_vendas < 10000: raise ValueError(f"Foram feitas poucas vendas: {num_vendas}")
if num_bilhetes < 30000: raise ValueError(f"Foram vendidos poucos bilhetes: {num_bilhetes}")


# Gera o ficheiro populate.sql

print("A escrever o populate.sql")
conteudo = "\n".join((Aeroporto.SQL(), Aviao.SQL(), Assento.SQL(), Voo.SQL(), Venda.SQL(), Bilhete.SQL()))


with open("populate.sql", "w") as file: file.write(conteudo)

print("Feito!")

tempo_decorrido = t.time() - inicio
print(f"Tempo de execução: {tempo_decorrido:.2f}s")