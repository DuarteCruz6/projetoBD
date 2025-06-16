#!/usr/bin/python3
from config_stuff import *
from auxiliar_functions import *

@app.route("/", methods=("GET",))
@limiter.limit("1 per second")
def list_aeroports():
    """Show all the aeroports (name and city)"""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            aeroports = cur.execute(
                """
                SELECT nome, cidade, codigo
                FROM aeroporto
                """,
                {},
            ).fetchall()
            
    if not aeroports:
        return jsonify({"message": "Não foi encontrado nenhum aeroporto.", "status": "error"}), 404
    
    aeroport_list = [
        {
            "nome": aeroport[0],
            "cidade": aeroport[1],
            "codigo":aeroport[2]
        }
        for aeroport in aeroports
    ]

    return jsonify(aeroport_list), 200


@app.route("/voos/<partida>/", methods=("GET",))
@limiter.limit("1 per second")
def show_flights_12hour(partida):
    """Show every flight that leave the aeroport <partida> until 12h from the moment of search."""
    """flight = (no_serie, hora_partida, chegada)"""
    timeNow = datetime.datetime.now()
    timeEnd = timeNow + datetime.timedelta(hours=12)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            
            if not checkAeroport(cur,partida):
                return jsonify({"message": "Aeroporto não encontrado."}), 404
            
            flights = cur.execute(
                """
                SELECT no_serie, hora_partida, chegada, id
                FROM voo
                WHERE hora_partida >= %(timeNow)s 
                AND hora_partida <= %(timeEnd)s 
                AND partida = %(partida)s;
                """,
                {"partida": partida, "timeNow": timeNow, "timeEnd": timeEnd},
            ).fetchall()

    if not flights:
        return jsonify({"message": "Não foi encontrado nenhum voo."}), 200

    flight_list = [
        {
            "no_serie": flight[0],
            "hora_partida": flight[1].isoformat(),
            "chegada": flight[2],
            "voo_id":flight[3]
        }
        for flight in flights
    ]

    return jsonify(flight_list), 200



@app.route("/voos/<partida>/<chegada>/", methods=("GET",))
@limiter.limit("1 per second")
def show_3_flights_with_tickets(partida, chegada):
    """Shows the next 3 flights between <partida> and <chegada> that still have tickets available to purchase"""
    """flight = (no_serie, hora_partida)"""
    
    if partida == chegada:
        return jsonify({"message": "Foi selecionado o mesmo aeroporto na chegada e na partida.", "status": "error"}), 400
    
    timeNow = datetime.datetime.now()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            if not checkAeroport(cur,partida):
                return jsonify({"message": "Aeroporto de partida não encontrado."}), 404
            if not checkAeroport(cur,chegada):
                return jsonify({"message": "Aeroporto de chegada não encontrado."}), 404
            
            flights = cur.execute(
                """
                SELECT voo.no_serie, voo.hora_partida, voo.id
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
        return jsonify({"message": "Não foi encontrado nenhum voo com bilhetes disponíveis entre os aeroportos.", "status": "error"}), 404

    flight_list = [
        {
            "no_serie": flight[0],
            "hora_partida": flight[1].isoformat(),
            "voo_id":flight[2]
        }
        for flight in flights
    ]
    
    return jsonify(flight_list), 200

@app.route(
    "/compra/<int:voo_id>/",methods=("POST",),
)
@limiter.limit("1 per second")
def buyTickets(voo_id):
    """Buys one or more tickets for <voo> populating <venda> and <bilhete>."""
    """Receives as arguments nif_cliente, and a list of pairs (nome_passageiro, classe de bilhete)"""
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "Corpo do pedido em falta ou inválido", "status": "error"}), 400

    nif_cliente = data.get("nif_cliente")
    if not nif_cliente:
        return jsonify({"message": "Dados incompletos", "status": "error"}), 400
    
    try:
        test = int(nif_cliente)
        if len(str(test))!=9:
            return jsonify({"message": "Nif inválido."}), 400
    except:
        return jsonify({"message": "Nif inválido."}), 400
    
    
    pairs = data.get("pairs")
    if not pairs:
        return jsonify({"message": "Dados incompletos", "status": "error"}), 400
    
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2:
            return jsonify({"message": "Par inválido."}), 400
        
        if not isinstance(pair[0],str):
            return jsonify({"message": "O par tem de ter uma string como primeiro argumento."}), 400
        
        if not isinstance(pair[1],bool):
            return jsonify({"message": "O par tem de ter um bool como segundo argumento."}), 400

    try:
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:

                    #get flight
                    flight = getFlight(cur,voo_id)
                    if not flight:
                        return jsonify({"message": "Voo não encontrado."}), 404

                    if not verifyTicketsAvailability(cur,voo_id,pairs):
                        #there are no suficient tickets
                        return jsonify({"message": "Não há lugares suficientes."}), 409

                    tempo_voo = calculateTempoVoo(cur, voo_id)
                    if tempo_voo == 0:
                        return jsonify({"message": "Erro a calcular tempo de voo."}), 500

                    listTicketsId = createTickets(cur, voo_id, pairs, nif_cliente, tempo_voo)
                    if not listTicketsId:
                        return jsonify({"message": "Erro a criar bilhetes."}), 500

            
    except Exception as e:
        return jsonify({"message": f"Erro interno: {str(e)}"}), 500

    return jsonify({"message": "Bilhetes comprados com sucesso", "Ids": listTicketsId}), 201

@app.route(
    "/checkin/<int:bilhete_id>/",methods=("POST",),
)
@limiter.limit("1 per second")
def do_checkIn_ticket(bilhete_id):
    """Does a checkIn of a ticket, giving him the seat from the correspondent class"""

    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                        SELECT voo_id, prim_classe, lugar FROM bilhete
                        WHERE id = %(bilhete_id)s
                        LIMIT 1
                    """,
                    {
                        "bilhete_id":bilhete_id,
                    } 
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"message": "Bilhete não encontrado."}), 404 
                
                voo_id, prim_classe, lugar_atual = row
                
                if lugar_atual is not None:
                    return jsonify({"message": "Check-in já efetuado para este bilhete."}), 400
                
                no_serie = getNoSerie(cur,voo_id)
                if no_serie is None:
                    return jsonify({"message": "Erro ao atribuir no_serie."}), 500 


                lugar = getSeat(cur, voo_id, no_serie, prim_classe)
                if lugar is None:
                    return jsonify({"message": "Erro ao atribuir lugar."}), 500 
             

                cur.execute(
                    """
                        UPDATE bilhete
                        SET lugar = %(lugar)s, no_serie = %(no_serie)s
                        WHERE id = %(bilhete_id)s
                    """,
                    {
                        "lugar": lugar,
                        "bilhete_id": bilhete_id,
                        "no_serie":no_serie,
                    }
                )
                

    return jsonify({"message": "Check-in efetuado com sucesso.", "lugar": lugar}), 201


@app.route("/ping", methods=("GET",))
@limiter.exempt
def ping():
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
