# -*- coding: utf-8 -*-
"""
@authors: Guilherme Silva, Gabriel Faustino and Pedro Maschio
"""

from player.parser import *
from r2a.ir2a import IR2A
from time import *
from base.whiteboard import *
from statistics import mean
from player import *

class R2AAdaptation(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
       
        self.whiteboard = Whiteboard.get_instance()
        self.parsed_mpd = ''
        self.qi = []
        self.requestTime = 0
        self.throughputs = []

        self.t = 0 
        self.fast = True 
        self.bufferInc = True
        self.rNow = -1
        self.tCurrent = 0
        self.bMin = 10
        self.bLow = 20
        self.a = (0.75, 0.33, 0.5, 0.75, 0.9)


    def handle_xml_request(self, msg):
        self.requestTime = perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        
        T = perf_counter() - self.requestTime
        self.throughputs.append(msg.get_bit_length() / T)

        self.send_up(msg)

    def movingAverage(self, s):

        ans = 0
        if(s <= 0): 
            ans = mean(self.throughputs[0:])
        else:
            ans = mean(self.throughputs[s:])
        return ans

    def handle_segment_size_request(self, msg):
        self.requestTime = perf_counter()
        
        deltaT = self.t - 10

        buffer = self.whiteboard.get_playback_buffer_size()

        if len(buffer) > 0:
            bufferSize = buffer[-1][1]
        else:
            bufferSize = 0
        
        i = 0
        while self.fast and i < len(self.whiteboard.get_playback_buffer_size()) - 1:
            if self.whiteboard.get_playback_buffer_size()[i][1] > self.whiteboard.get_playback_buffer_size()[i+1][1]:
                self.bufferInc = False
            i += 1
        
        if self.fast and self.rNow != len(self.qi)-1 and self.qi[self.rNow+1] <= self.a[0]*self.movingAverage(deltaT) and self.bufferInc:
            if bufferSize < self.bMin:
                if self.rNow < len(self.qi) - 1 and self.qi[self.rNow+1] <=  self.a[1]*self.movingAverage(deltaT):
                    self.rNow = self.rNow + 1
                elif bufferSize < self.bLow:
                    if self.rNow < len(self.qi) - 1 and self.qi[self.rNow+1] <= self.a[2]*self.movingAverage(deltaT):
                        self.rNow = self.rNow + 1
            else:
                if self.rNow < len(self.qi) - 1 and self.qi[self.rNow+1] <=  self.a[3]*self.movingAverage(deltaT):       
                    self.rNow = self.rNow + 1
        else:
            self.fast = False 
            
            if bufferSize < self.bMin:
                self.rNow = 0 
            elif bufferSize < self.bLow:
                if self.rNow != 0 and self.qi[self.rNow] >= self.movingAverage(0):
                    self.rNow = self.rNow - 1
            else:
                if self.rNow != 19 and self.qi[self.rNow + 1] < self.a[4]*self.movingAverage(deltaT):
                    self.rNow = self.rNow + 1


        msg.add_quality_id(self.qi[self.rNow])
        self.t += 1
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        T = perf_counter() - self.requestTime
        self.throughputs.append(msg.get_bit_length() / T)

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

