from database.distributore_DAO import DistributoreDAO
from database.prezzo_DAO import PrezzoDAO
import copy

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()           # carico i distributori

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1     # valore "sentinella", non ho ancora trovato una soluzione completa


    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()


    # Fz per prendere il prezzo medio del carburante in un determinato mese, per ogni distributore
    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        risultato = []    # lista di tuple (nome_distributore, media)

        # Scorro tutti i distributori
        for d in self._distributori:
            prezzi = PrezzoDAO.get_prezzi(d.id)   # li prendo con la fz nel DAO dei prezzi (con l'id del distributore)

            if prezzi is not None:
                somma_prezzi=0.0
                count=0

                for p in prezzi:
                    # Estraggo il mese dalla data (p è un oggetto prezzo_DTO con una data) (data è str 'AAAA-MM-GG')
                    data_str = str(p.data)
                    mese_corrente = int(data_str.split("-")[1])

                    if mese_corrente == mese:       # Se il mese corrisponde a quello selezionato dall'utente
                        somma_prezzi += p.prezzo_litro        # sommo i prezzi
                        count += 1

                # Se ho trovato dei prezzi per quel mese, calcolo la media
                if count > 0:
                    media = somma_prezzi / count
                    risultato.append((d.nome, media))
        return risultato



    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)


    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        # Prova tutte le combinazioni di rifornimento nei 7 giorni (sceglie tra A e B) e somma i costi. Al giorno 8,
        #          confronta il totale corrente con il record migliore e salva la sequenza che costa meno.
        # La soluzione parziale è una lista temporanea in cui l'indice è il giorno e i valori la scelta migliore tra i distributori

        if giorno > 7:      # Condizione di termine: ho controllato i primi 7 giorni
            # Se non ho ancora aggiornato il costo ottimo, o quello corrente è minore del costo ottimo attuale
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                self.__sequenza_ottima = copy.deepcopy(sequenza_parziale)  # salvo una copia indipendente della lista
            return

        for d in self._distributori:
            id_distributore = d.id

            # Calcolo del costo parziale per la scelta corrente
            # l prezzo è nel dizionario, con chiave id_distributore e indice (giorno - 1)
            prezzo_litro = prezzi_settimana[id_distributore][giorno - 1]
            costo_rifornimento = prezzo_litro * 100    # rifornisco di 100 litri

            costo_spostamento = 0    # costo di spostamento, se non è il 1 giorno o ha cambiato distributore
            if ultimo_distributore is not None and id_distributore != ultimo_distributore:   # se prima ero in un altro distributore
                costo_spostamento = 5

            nuovo_costo = costo_corrente + costo_rifornimento + costo_spostamento

            # Aggiungo il distributore alla sequenza parziale (è una lista con i distributori preferibili)
            sequenza_parziale.append(id_distributore)

            # Se non ho trovato ancora la soluzione completa (cioè costo_ottimo=-1), oppure quando la combinazione che
            #     stiamo costruendo non ha ancora superato il costo ottimale, allora ricorro con il giorno successivo
            if self.__costo_ottimo == -1 or nuovo_costo < self.__costo_ottimo:
                self.__ricorsione(sequenza_parziale, giorno + 1, id_distributore, nuovo_costo, prezzi_settimana)

            sequenza_parziale.pop()    #backtracking, per controllare l'altro distributore







#   Fz che restituisce un dizionario del tipo: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}, usa
    #   il metodo get_prezzi() implementato in Distributore
    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        prezzi_settimana = {}

        for d in self._distributori:         # per ogni distributore prendo i tutti i prezzi
            tutti_prezzi = d.get_prezzi()
            prezzi_7_giorni = []         # voglio estrarre solo quelli dei primi 7 giorni

            if tutti_prezzi is not None:
                for p in tutti_prezzi:
                    # estraggo il mese e il giorno dalla data ('AAAA-MM-GG')
                    parti_data = str(p.data).split("-")
                    mese_corrente = int(parti_data[1])
                    giorno_corrente = int(parti_data[2])

                    if mese_corrente == mese and 1 <= giorno_corrente <= 7:   # se mese selezionato e giorno tra 1 e 7
                        prezzi_7_giorni.append(p.prezzo_litro)

            prezzi_settimana[d.id] = prezzi_7_giorni   # associo al dizionario
        return prezzi_settimana