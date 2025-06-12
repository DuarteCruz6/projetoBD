#!/usr/bin/python3
import os
from logging.config import dictConfig
import datetime
import json

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

app = Flask(__name__)
app.config.from_prefixed_env()
log = app.logger
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=RATELIMIT_STORAGE_URI,
)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://proj:proj@postgres/proj")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={
        "autocommit": True,  # If True don’t start transactions automatically.
        "row_factory": namedtuple_row,
    },
    min_size=4,
    max_size=10,
    open=True,
    # check=ConnectionPool.check_connection,
    name="postgres_pool",
    timeout=5,
)


@app.route("/", methods=("GET",))
def aeroport_index():
    """Show all the aeroports (name and city)"""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            aeroports = cur.execute(
                """
                SELECT nome, cidade
                FROM aeroporto
                """,
                {},
            ).fetchall()
            
    if not aeroports:
        return jsonify({"message": "No aeroports found.", "status": "error"}), 404

    return jsonify(aeroports), 200


@app.route("/voos/<partida>/", methods=("GET",))
def show_flights_12hour(partida):
    """Show every flight that leave the aeroport <partida> until 12h from the moment of search."""
    """flight = (no_serie, hora_partida, chegada)"""
    timeNow = datetime.datetime.now()
    timeEnd = timeNow + datetime.timedelta(hours=12)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            flights = cur.execute(
                """
                SELECT no_serie, hora_partida, chegada
                FROM voo
                WHERE hora_partida >= %(timeNow)s 
                AND hora_partida <= %(timeEnd)s 
                AND partida = %(partida)s;
                """,
                {"partida": partida, "timeNow": timeNow, "timeEnd": timeEnd},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    if not flights:
        return jsonify({"message": "No flights found.", "status": "error"}), 404

    flight_list = [
        {
            "no_serie": flight[0],
            "hora_partida": flight[1].isoformat(),
            "chegada": flight[2]
        }
        for flight in flights
    ]

    return jsonify(flight_list), 200



@app.route("/voos/<partida>/<chegada>/", methods=("GET",))
def show_3_flights_with_tickets(partida, chegada):
    """Shows the next 3 flights between <partida> and <chegada> that still have tickets available to purchase"""
    """flight = (no_serie, hora_partida)"""
    
    if partida == chegada:
        return jsonify({"message": "Foi selecionado o mesmo aeroporto na chegada e na partida.", "status": "error"}), 404
    
    timeNow = datetime.datetime.now()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            flights = cur.execute(
                """
                SELECT voo.id, voo.no_serie, voo.hora_partida,
                    COALESCE(bilhete.bilhetes_emitidos, 0) AS bilhetes_emitidos,
                    COALESCE(assento.total_assentos, 0) AS total_assentos
                FROM voo
                JOIN aviao ON voo.no_serie = aviao.no_serie 
                
                LEFT JOIN (
                    SELECT voo_id, COUNT(*) AS bilhetes_emitidos
                    FROM bilhete
                    GROUP BY voo_id
                ) bilhete ON bilhete.voo_id = voo.id
                
                LEFT JOIN (
                    SELECT no_serie, COUNT(*) AS total_assentos
                    FROM assento
                    GROUP BY no_serie
                ) assento ON assento.no_serie = aviao.no_serie
                
                WHERE partida = %(partida)s
                AND chegada = %(chegada)s
                AND hora_partida > %(timeNow)s 
                
                AND COALESCE(bilhete.bilhetes_emitidos, 0) < COALESCE(assento.total_assentos, 0)
                
                ORDER BY voo.hora_partida ASC
                LIMIT 3;
                """,
                {"partida": partida, "chegada": chegada, "timeNow":timeNow },
            ).fetchall()

    if not flights:
        return jsonify({"message": "No flights found with tickets available between those two airports.", "status": "error"}), 404

    return jsonify(flights), 200

    
def checkClassTickets(cur, voo_id, numClassToBuy, prim_classe):
    #if first class, prim_classe = True; if second class, prim_classe = False
    #verifies how many class tickets have been sold
    cur.execute(
        """
            SELECT COUNT(*) FROM bilhete 
            WHERE voo_id = %(voo_id)s
            AND prim_classe = %(prim_classe)s
        """, 
        {"voo_id":voo_id,"prim_classe":prim_classe}
    )
    row = cur.fetchone()
    if not row:
        return False
    bilhetes_vendidos_classe = row[0]
    
    #verifies how many class seats there are on the plane
    cur.execute(
        """
            SELECT COUNT(*) FROM assento 
            WHERE no_serie = (
                SELECT no_serie FROM voo 
                WHERE id = %(voo_id)s
            )
            AND prim_classe = %(prim_classe)s
        """, 
        {"voo_id":voo_id,"prim_classe":prim_classe}
    )
    row = cur.fetchone()
    if not row:
        return False
    total_assentos_classe = row[0]
    
    if numClassToBuy+bilhetes_vendidos_classe<=total_assentos_classe:
        return True
    return False

def verifyTicketsAvailability(cur, voo_id, pairs):
    numFirstClassToBuy = 0
    numSecondClassToBuy = 0
    for pair in pairs:
        # pair = (nome_passageiro, classe de bilhete)
        if pair[1]:
            #the ticket is first class
            numFirstClassToBuy+=1
        else:
            #the ticket is second class
            numSecondClassToBuy+=1
            
    if not checkClassTickets(cur, voo_id, numFirstClassToBuy, True):
        #no availability for first class tickets
        return False
    
    if not checkClassTickets(cur, voo_id, numSecondClassToBuy, False):
        #no availability for second class tickets
        return False
    
    return True

def createVenda(cur, nif_cliente):
    #gets the last codigo_venda
    cur.execute(
        """
            SELECT codigo_reserva FROM venda
            ORDER BY codigo_reserva DESC
            LIMIT 1
        """
    )
    row = cur.fetchone()
    last_codigo_reserva = row[0] if row else 0
        
    #creates <venda>
    cur.execute(
        """
            INSERT INTO venda (codigo_reserva, nif_cliente, balcao, hora)
            VALUES (%(codigo_reserva)s, %(nif_cliente)s, %(balcao)s, %(hora)s)
            RETURNING codigo_reserva;
        """, 
        {
            "codigo_reserva":last_codigo_reserva+1, "nif_cliente":nif_cliente, 
            "balcao":None, "hora":datetime.datetime.now()
        }
    )
    
    return last_codigo_reserva+1
    
def createTickets(cur, voo_id, pairs, nif_cliente, tempo_voo):
    #gets the last ticketId for this flight
    cur.execute(
        """
            SELECT id FROM bilhete
            ORDER BY id DESC
            LIMIT 1
        """,
        {} 
    )
    row = cur.fetchone()
    if not row:
        return False
    last_bilhete_id = row[0] if row else 0
    offSet = 1
    
    cur.execute(
        """
            SELECT no_serie FROM voo
            WHERE id = %(voo_id)s
            LIMIT 1
        """,
        {
            "voo_id":voo_id,
        } 
    )
    row = cur.fetchone()
    if not row:
        return False
    no_serie = row[0]
    
    codigo_reserva = createVenda(cur, nif_cliente)
    listTicketsIds = []
    for pair in pairs:
        print(pair)
        # pair = (nome_passageiro, classe de bilhete)
        #creates <bilhete>
        nome_passageiro = pair[0]
        prim_classe = pair[1]
        if prim_classe:
            preco = 60 * tempo_voo
        else:
            preco = 40 * tempo_voo
            
        cur.execute(
            """
                INSERT INTO bilhete (id, voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie)
                VALUES (
                    %(id)s,%(voo_id)s,%(codigo_reserva)s,%(nome_passegeiro)s,%(preco)s,
                        %(prim_classe)s,%(lugar)s,%(no_serie)s
                )
            """,
            {
                "id":last_bilhete_id+offSet, "voo_id":voo_id, "codigo_reserva":codigo_reserva, 
                "nome_passegeiro":nome_passageiro, "preco":preco, "prim_classe":prim_classe,
                "lugar": None,"no_serie":no_serie,
            }
        )
        listTicketsIds.append(last_bilhete_id+offSet)
        offSet+=1
    return listTicketsIds
        
        
def calculateTempoVoo(cur, voo_id):
    cur.execute(
        """
            SELECT hora_partida, hora_chegada FROM voo
            WHERE id = %(voo_id)s
            LIMIT 1
        """,
        {
            "voo_id":voo_id,
        } 
    )
    
    row = cur.fetchone()
    if row:
        partida, chegada = row
        #today = datetime.datetime.today()
        #partida_dt = datetime.datetime.combine(today, partida)
        #chegada_dt = datetime.datetime.combine(today, chegada)
        #tempo_voo = (chegada_dt - partida_dt).seconds / 3600  # em horas
        tempo_voo = (chegada - partida).total_seconds() / 3600
        return tempo_voo
    else:
        return 0

def getFlight(cur, voo_id):
    cur.execute(
        """
            SELECT * FROM voo
            WHERE id = %(voo_id)s
            LIMIT 1
        """,
        {
            "voo_id":voo_id,
        } 
    )
    row = cur.fetchone()
    if not row:
        return None
    return row

@app.route(
    "/compra/<int:voo_id>/",methods=("POST",),
)
def buyTickets(voo_id):
    """Buys one or more tickets for <voo> populating <venda> and <bilhete>."""
    """Receives as arguments nif_cliente, and a list of pairs (nome_passageiro, classe de bilhete)"""

    nif_cliente = request.args.get("nif_cliente")
    
    try:
        int(nif_cliente)
    except:
        return jsonify({"message": "Nif inválido."}), 400
    
    if len(nif_cliente)!=9:
        return jsonify({"message": "Nif inválido."}), 400
    
    pairs_jsonList = request.args.get("pairs")
    
    if not nif_cliente or not pairs_jsonList:
        return jsonify({"message": "Dados incompletos", "status": "error"}), 400
    
    try:
        pairs = json.loads(pairs_jsonList)
    except json.JSONDecodeError:
        return jsonify({"message": "Formato inválido para pairs", "status": "error"}), 400
    
    for pair in pairs:
        if not len(pair)==2:
            return jsonify({"message": "Dados inválidos."}), 400
        
        if not isinstance(pair[0],str):
            return jsonify({"message": "Dados inválidos."}), 400
        
        if not isinstance(pair[1],bool):
            return jsonify({"message": "Dados inválidos."}), 400

    conn = None
    try:
        with pool.connection() as conn:
            conn.autocommit = False #desliga commits automaticos para caso haja um erro a meio
            with conn.cursor() as cur:
                
                #get flight
                flight = getFlight(cur,voo_id)
                if not flight:
                    return jsonify({"message": "Voo não encontrado."}), 400
                 
                if not verifyTicketsAvailability(cur,voo_id,pairs):
                    #there are no suficient tickets
                    return jsonify({"message": "Não há lugares suficientes."}), 400
                
                tempo_voo = calculateTempoVoo(cur, voo_id)
                if tempo_voo == 0:
                    return jsonify({"message": "Erro a calcular tempo de voo."}), 400
                
                listTicketsId = createTickets(cur, voo_id, pairs, nif_cliente, tempo_voo)
                if not listTicketsId:
                    return jsonify({"message": "Erro a criar bilhetes."}), 400
                
            conn.commit()
            
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return jsonify({"message": f"Erro interno: {str(e)}"}), 500

    return jsonify({"message": f"Bilhetes comprados com sucesso com Ids: {listTicketsId}"}), 200

def getSeat(cur,voo_id,no_serie,prim_classe):
    cur.execute(
        """
        SELECT assento.lugar
        FROM assento
        WHERE assento.no_serie = %(no_serie)s
        AND assento.prim_classe = %(prim_classe)s
        AND NOT EXISTS (
            SELECT 1
            FROM bilhete
            WHERE bilhete.no_serie = assento.no_serie 
            AND bilhete.lugar = assento.lugar
            AND bilhete.voo_id = %(voo_id)s
        )
        LIMIT 1
        FOR UPDATE
        """,
        {"no_serie": no_serie, "prim_classe": prim_classe, "voo_id": voo_id}
    )
    row = cur.fetchone()
    return row[0] if row else None

@app.route(
    "/checkin/<int:bilhete_id>/",methods=("POST",),
)
def do_checkIn_ticket(bilhete_id):
    """Does a checkIn of a ticket, giving him the seat from the correspondent class"""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT voo_id, no_serie, prim_classe, lugar FROM bilhete
                    WHERE id = %(bilhete_id)s
                    LIMIT 1
                """,
                {
                    "bilhete_id":bilhete_id,
                } 
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"message": "Bilhete não encontrado."}), 400 
            
            voo_id, no_serie, prim_classe, lugar_atual = row
            if lugar_atual is not None:
                return jsonify({"message": "Check-in já efetuado para este bilhete."}), 400
            
            lugar = getSeat(cur, voo_id, no_serie, prim_classe)
            
            if lugar is None:
                return jsonify({"message": "Erro ao atribuir lugar."}), 400 
            
            cur.execute(
                """
                    UPDATE bilhete
                    SET lugar = %(lugar)s
                    WHERE id = %(bilhete_id)s
                """,
                {
                    "lugar": lugar,
                    "bilhete_id": bilhete_id,
                }
            )
            conn.commit() #para garantir que fica guardado na base de dados


    return jsonify({"lugar": lugar}), 200


@app.route("/ping", methods=("GET",))
@limiter.exempt
def ping():
    log.debug("ping!")
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
