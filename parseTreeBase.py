#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# parseTreeBase.py : 03nov2014 CPM
# ------------------------------------------------------------------------------
# Copyright (c) 2013, Clinton Prentiss Mah
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
#   Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

"""
support for syntax analysis with preallocated, extensible arrays of data elements
"""

import ellyBits
import symbolTable
import conceptualHierarchy

NOMINAL = 256 # default starting allocation for phrases and goals

class ParseTreeBase(object):

    """
    data structures for implementing an Elly parse tree

    attributes:
        phrases - preallocated phrase nodes
        goals   - preallocated gaals
        phlim   - phrase allocation limit
        glim    - goal   allocation limit
        lastph  - last phrase allocated
    """

    class Phrase(object):

        """
        phrase node in a parse tree

        attributes:
            rule  - generating rule
            posn  - starting token position in sentence
            lftd  - descendant phrase
            rhtd  - descendant phrase
            typx  - syntax category
            usen  - usage flag for parser
            synf  - syntax features
            semf  - semantic features
            cncp  - semantic concept
            ctxc  - conceptual context
            llnk  - listing link
            alnk  - ambiguity link
            bias  - plausibility scoring for ambiguity ranking
            lens  - token length
            seqn  - sequence ID for debugging
            dump  - flag for tree dumping
        """

        def __init__ ( self ):
            """
            initialize node to defaults
            arguments:
                self
            """

            self.synf = ellyBits.EllyBits(symbolTable.FMAX)
            self.semf = ellyBits.EllyBits(symbolTable.FMAX)
            self.seqn = -1
            self.reset()

        def __unicode__ ( self ):
            """
            get information summary to support testing
            arguments:
                self
            returns:
                summary string
            """

            cn = '' if self.cncp == conceptualHierarchy.NOname else '/' + self.cncp

            return ( 'phrase ' + unicode(self.seqn) + ' @' + unicode(self.posn)
                     + ': type=' + unicode(self.typx) + ' [' + self.synf.hexadecimal() + '] :'
                     + unicode(self.bias) + cn + ' use=' + str(self.usen) )

        def __str__ ( self ):
            """
            get information summary to support testing
            arguments:
                self
            returns:
                summary string
            """

            return unicode(self).encode('utf8')

        def reset ( self ):
            """
            reintialize
            arguments:
                self
            """

            self.rule = None
            self.posn = -1
            self.lftd = None
            self.rhtd = None
            self.typx = -1
            self.usen = 0
            self.synf.clear()
            self.semf.clear()
            self.cncp = conceptualHierarchy.NOname
            self.ctxc = conceptualHierarchy.NOname
            self.llnk = None
            self.alnk = None
            self.bias = 0
            self.lens = 0
            self.dump = True

        def order ( self ):
            """
            bring most plausible phrase to front of ambiguity list
            arguments:
                self
            """

            if self.alnk == None:
                return
#*          print 'ordering ambiguities for phrase' , self
            best = None             # phrase with best bias so far
            bias = -10000           # its bias value
            phn = self
            while phn != None:
                if bias < phn.bias: # check bias against best far
                    bias = phn.bias # update best bias
                    best  = phn     # and associated phrase
                phn = phn.alnk

#           print 'best bias=' , bias

            if self != best:        # need to swap phrases to get best at start
                self.swap(best)

        def swap ( self , othr ):

            """
            exchange basic contents of two phrases

            arguments:
                self  -
                othr  - phrase to swap with
            """

#           print 'swap phrases'
#           print 'self=' , self
#           print 'othr=' , othr
            self.rule, othr.rule = othr.rule, self.rule
            self.lftd, othr.lftd = othr.lftd, self.lftd
            self.rhtd, othr.rhtd = othr.rhtd, self.rhtd
            self.bias, othr.bias = othr.bias, self.bias
            self.cncp, othr.cncp = othr.cncp, self.cncp
            self.ctxc, othr.ctxc = othr.ctxc, self.ctxc
            self.seqn, othr.seqn = othr.seqn, self.seqn
            if self.lftd == self:
                self.lftd = None
#           print 'result'
#           print 'self=' , self
#           print 'othr=' , othr

    class Goal(object):

        """
        goal for generating phrase to complete 2-branch rule

        attributes:
            cat   - syntax category
            lph   - phrase already found
            rul   - rule to be completed for phrase
            seq   - sequence ID for debugging
        """

        _sqn = 0

        def __init__ ( self ):
            """
            initialize attributes to defaults
            arguments:
                self
            """
            self.cat = 0
            self.lph = None
            self.rul = None
            self.seq = -1

        def __unicode__ ( self ):
            """
            get information summary to support testing
            arguments:
                self
            returns:
                summary string
            """

            n = self.rul.seqn
            return ( 'goal ' + unicode(self.seq) + ': type=' + unicode(self.cat)
                    + ' for [' + unicode(self.lph) + ']' + ' [rule= ' + str(n) + ']' )

        def __str__ ( self ):
            """
            get information summary to support testing
            arguments:
                self
            returns:
                summary string
            """

            return unicode(self).encode('utf8')

    def __init__ ( self ):

        """
        initialize attributes, including preallocated nodes for parsing

        arguments:
            self
        """

#       print "at ParseTreeBase.__init__()"
        self.phrases = [ ]
        self.goals   = [ ]
        for i in range(NOMINAL):        # preallocate phrases and goals
            phrase = self.Phrase()      # get phrase
            phrase.seqn = i             # assign ID
            self.phrases.append(phrase)
            goal = self.Goal()          # get goal
            goal.seq = i                # assign ID
            self.goals.append(goal)
        self.reset()
#       print "leaving ParseTreeBase.__init__()"

    def reset ( self ):

        """
        reset parse tree for new input

        arguments:
            self
        """

#       print "ParseTreeBase.reset()"
        self.phlim = 0
        self.glim  = 0
        self.lastph = None
        n = 0
        for ph in self.phrases:
            ph.seqn = n
            n += 1

    def makePhrase ( self , po , ru ):

        """
        allocate a phrase node for a sentence position with a syntax rule

        arguments:
            po   - position
            ru   - rule (can be extending or splitting)

        returns:
            new phrase node
        """

        if self.phlim >= len(self.phrases):    # do we have to allocate more phrases?
            phrase = self.Phrase()             # if so, allocate more
            phrase.seqn = self.phlim
            self.phrases.append(phrase)
        self.lastph = self.phrases[self.phlim] # get next available phrase
        self.lastph.reset()                    # 
        self.lastph.posn = po                  # parse position
        self.lastph.rule = ru                  # grammar rule defining phrase
        self.lastph.typx = ru.styp             #
        self.lastph.synf.combine(ru.sfet)
        self.phlim += 1
#*      print 'make' , self.lastph
        return self.lastph
    
    def makeGoal ( self , ru , ph ):

        """
        allocate a goal node for a phrase and a splitting syntax rule

        arguments:
            self  -
            ru    - splitting rule
            ph    - phrase

        returns:
            goal node if successful
        """

        if self.glim >= len(self.goals):
            goal = self.Goal()
            goal.seq = self.glim
            self.goals.append(goal)
        g = self.goals[self.glim]
        g.cat = ru.rtyp
        g.lph = ph
        g.rul = ru
        self.glim += 1
        return g

#
# unit test
#

import sys
import ellyToken

if __name__ == '__main__':

    class M(object):  # dummy derivability matrix
        """ dummy class for testing
        """
        def __init__ ( self ):
            """ initialization
            """
            self.xxx = 0
        def derivable (self,n,gbs):
            """ dummy method
            """
            self.xxx += 1
            return gbs.test(n)

    class R(object):  # dummy grammar rule class
        """ dummy class for testing
        """
        def __init__ (self,n):
            """ initialization
            """
            self.styp = n
            self.sfet = ellyBits.EllyBits()

    class G(object):  # dummy grammar table class
        """ dummy class for testing
        """
        def __init__ (self):
            """ initialization
            """
            self.START = 0
            self.END   = 1
            self.UNKN  = 2
            self.XXX   = 3
            self.NUM   = 4
            self.PUNC  = 5
            self.splits = [ [ ] , [ ] , [ ] , [ ] , [ ] , [ ] ] # must define this!
            self.dctn = { 'abc' : [ R(self.START) ] , 'xyz' : [ R(self.UNKN) ] }
            self.mat  = M()

    class S(object):  # dummy symbol table class
        """ dummy class for testing
        """
        def __init__ ( self ):
            """ initialization
            """
            self.xxx = 6
        def getSyntaxTypeCount(self):
            """ dummy method
            """
            return self.xxx  # for START, END, UNKN, XXX, NUM, PUNC

    print "allocating"
    sym = S()
    grm = G()
    tree = ParseTreeBottomUp(sym,grm,None)
    print "allocated"

    print tree
    print dir(tree)

    fbbs = ellyBits.EllyBits(symbolTable.FMAX)
    gbbs = ellyBits.EllyBits(symbolTable.NMAX)
    gbbs.complement()    # all goal bits turned on

    tree.gbits[0] = gbbs # set all goals in first position

    print '----'
    sgm = 'abc'          # test example in dictionary
    sta = tree.createPhrasesFromDictionary(sgm,False)
    print sgm , ':' , sta , ', phlim=' , tree.phlim , 'lastph=' , tree.lastph 

    print '----'
    sgm = 'abcd'         # test example not in dictionary
    sta = tree.createPhrasesFromDictionary(sgm,False)
    print sgm , ':' , sta,', phlim=' , tree.phlim , 'lastph=' , tree.lastph 

    print '----'
    sgm = 'xyz'          # test example in dictionary
    sta = tree.createPhrasesFromDictionary(sgm,False)
    print sgm , ':' , sta , ', phlim=' , tree.phlim , 'lastph=' , tree.lastph 

    print '----'
    sgm = 'pqr'          # test example not in dictionary
    sta = tree.createUnknownPhrase(ellyToken.EllyToken(sgm))
    print sgm , ':' , sta , ', phlim=' , tree.phlim , 'lastph=' , tree.lastph 

    print '----'
    sgm = '.'            # test example not in dictionary
    tree.gbits[0].clear()
    sta = tree.addLiteralPhrase(tree.gtb.PUNC,fbbs)
    print sgm , ':' , sta , ', phlim=' , tree.phlim , 'lastph=' , tree.lastph 
    tree.gbits[0].set(tree.gtb.PUNC)
    sta = tree.addLiteralPhrase(tree.gtb.PUNC,fbbs)
    print sgm , ':' , sta , ', phlim=' , tree.phlim , 'lastph=' , tree.lastph 

    print ''
    print 'ambiguities:'
    for a in tree.ambig:
        while a != None:
            print '' , a
            a = a.alnk
        print ''

    print '----'
    for rno in range(10,15):
        phrs = tree.makePhrase(0,R(rno))
        tree.enqueue(phrs)
    print '----'
    print 'dequeue phrase=' , tree.dequeue()
    print 'dequeue phrase=' , tree.dequeue()
