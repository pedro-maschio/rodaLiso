# -*- coding: utf-8 -*-
"""
@authors: Guilherme Silva, Gabriel Faustino and Pedro Maschio
"""

from player.parser import *
from r2a.ir2a import IR2A
from time import *
from base.whiteboard import *
from math import log


class R2ABola(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
       
        self.whiteboard = Whiteboard.get_instance()
        self.parsed_mpd = ''
        self.qi = []
        self.requestTime = 0
        self.throughputs = []
        self.gamma = 5
        self.QDMax = 0
        self.rNow = 0

    def handle_xml_request(self, msg):
        self.requestTime = perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        
        T = perf_counter() - self.requestTime
        self.throughputs.append(msg.get_bit_length() / T)

        self.send_up(msg)


    def handle_segment_size_request(self, msg):
        self.requestTime = perf_counter()

        t = min(msg.get_segment_id(), 596 - msg.get_segment_id()) 
        tLinha = max(t/2, 3*msg.get_segment_size()) 
        qDmax = min(self.whiteboard.get_max_buffer_size(), tLinha) 
        self.V = (qDmax - 1)/(log(self.qi[-1]/self.qi[0]) + self.gamma) 

        buffer = self.whiteboard.get_playback_buffer_size()

        if len(buffer) > 0:
            bufferSize = buffer[-1][1]
        else:
            bufferSize = 0

        prev, mLinha, idx = -math.inf, 0, 0
        for i in range(len(self.qi)):
            if (self.V*log(self.qi[i]/self.qi[0])  + self.V*self.gamma - bufferSize) / self.qi[i] >= prev:
                prev = (self.V*log(self.qi[i]/self.qi[0])  + self.V*self.gamma - bufferSize) / self.qi[i]
                idx = i 
            if self.qi[i] <= max(self.throughputs[-1], self.qi[0]):
                mLinha = i
        
        if idx >= self.rNow: 
            if mLinha >= idx:
                mLinha = idx
            elif mLinha < self.rNow:
                mLinha = self.rNow
            else:
                mLinha += 1

            idx = mLinha
        
        self.rNow = idx 
        msg.add_quality_id(self.qi[self.rNow])
    
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        T = perf_counter() - self.requestTime
        self.throughputs.append(msg.get_bit_length() / T)

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

