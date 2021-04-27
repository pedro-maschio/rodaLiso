# -*- coding: utf-8 -*-
"""
@author: André Luiz Bittencourt - 14/0130225

"""

from player.parser import *
from r2a.ir2a import IR2A
import time
import math
from base.whiteboard import *
from statistics import mean
from player import *


class R2AImplementado(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []
        self.momento_resposta = 0
        self.momento_requisicao = 0
        self.taxas_transferencia = [1] # o primeiro segmento terá sempre a menor qualidade possivel e por isso não é contabilizado 
        self.limite_taxa_bits = []
        self.delta = 0.1
        self.mu = 0.05

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def calcular_taxa_media(self, segmento):
        if segmento == 0 or segmento == 1:
            return self.taxas_transferencia[segmento]
        
        return (1-self.delta)*self.calcular_taxa_media(segmento-2) + self.delta*self.taxas_transferencia[segmento-1]

    def atualizar_delta(self, segmento, taxa_transferencia_media):
        taxa_transferencia_normalizada = abs(self.taxas_transferencia[segmento] - taxa_transferencia_media) / taxa_transferencia_media
        k = 21
        p0 = 0.2
        self.delta = 1 / (1 + math.exp(-k*(taxa_transferencia_normalizada-p0)))

    def handle_segment_size_request(self, msg):
        # time to define the segment quality choose to make the request

        numero_segmento = msg.segment_id - 1
        
        taxa_transferencia_media = self.calcular_taxa_media(numero_segmento)
        self.atualizar_delta(numero_segmento, taxa_transferencia_media)

        limite_taxa_bits = (1 - self.mu) * taxa_transferencia_media

        qualidade = 0
        for i in range(len(self.qi)):
            if self.qi[i] <= limite_taxa_bits:
                qualidade = i

        msg.add_quality_id(self.qi[qualidade])

        self.momento_requisicao = time.perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.momento_resposta = time.perf_counter()
        momento_diferenca = self.momento_resposta - self.momento_requisicao
        taxa_atual = msg.get_bit_length() / momento_diferenca

        self.taxas_transferencia.append(taxa_atual) 

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass