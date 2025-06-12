import datetime

def checkAeroport(cur,codigo):
    cur.execute(
        """
            SELECT * FROM aeroporto 
            WHERE codigo = %(codigo)s
        """, 
        {"codigo":codigo}
    )
    row = cur.fetchone()
    if not row:
        return False
    return True

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
    #verifies if the client can buy the tickets
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
    #creates <venda>
    cur.execute(
        """
            INSERT INTO venda (nif_cliente, balcao, hora)
            VALUES (%(nif_cliente)s, %(balcao)s, %(hora)s)
            RETURNING codigo_reserva;
        """, 
        {
            "nif_cliente":nif_cliente,"balcao":None, "hora":datetime.datetime.now()
        }
    )
    codigo_reserva = cur.fetchone()[0]
    return codigo_reserva
    
def createTickets(cur, voo_id, pairs, nif_cliente, tempo_voo):
    #creates <bilhete>
    codigo_reserva = createVenda(cur, nif_cliente)
    listTicketsIds = []
    for pair in pairs:
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
                INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe)
                VALUES (
                    %(voo_id)s,%(codigo_reserva)s,%(nome_passegeiro)s,
                    %(preco)s,%(prim_classe)s
                )
                RETURNING id
            """,
            {
                "voo_id":voo_id, "codigo_reserva":codigo_reserva,"nome_passegeiro":nome_passageiro, 
                "preco":preco, "prim_classe":prim_classe,
            }
        )
        idBilhete = cur.fetchone()[0] 
        listTicketsIds.append(idBilhete)
    return listTicketsIds
        
        
def calculateTempoVoo(cur, voo_id):
    #calculates the time of the flight
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
        tempo_voo = (chegada - partida).total_seconds() / 3600
        return tempo_voo
    else:
        return 0

def getFlight(cur, voo_id):
    #returns the flight
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

def getSeat(cur,voo_id,no_serie,prim_classe):
    #returns the first seat available from the corresponding class
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

def getNoSerie(cur,voo_id):
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
        return None
    return row[0]