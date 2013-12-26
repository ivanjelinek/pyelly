#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# ellyDefinition.py : 20dec2013 CPM
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
language definition tables that can be pickled for quicker PyElly startup
"""

import sys
import os.path
import symbolTable
import macroTable
import grammarTable
import patternTable
import vocabularyTable
import morphologyAnalyzer
import inflectionStemmerEN
import conceptualHierarchy
import ellyDefinitionReader
import ellyConfiguration

class EllyDefinition(object):

    """
    superclass for managing Elly definitions

    attributes:
        errors - accumulated errors needed by inpT() method
    """

    def __init__ ( self ):

        """
        initialization

        arguments:
            self
        """

        self.errors = [ ]

    def inpT ( self , system , part ):

        """
        inherited method to compose table input

        arguments:
            self   -
            system - which set of table definitions?
            part   - which table to read in?

        returns:
            EllyDefinitionReader on success, None otherwise
        """

        base = ellyConfiguration.baseSource
        suf  = '.' + part + '.elly'
        file = base + system + suf
        if not os.path.exists(file):
            file = base + ellyConfiguration.defaultSystem + suf
        print >> sys.stderr , 'reading' , file ,
        rdr = ellyDefinitionReader.EllyDefinitionReader(file)
        if rdr.error != None:
            self.errors.append(rdr.error)
            print >> sys.stderr , ': failed'
            return None
        else:
            print >> sys.stderr , ': succeeded'
            return rdr

class Rules(EllyDefinition):

    """
    Elly language rule definitions

    attributes:
        stb    - symbols
        mtb    - macro substitution rules
        gtb    - grammar rules
        ptb    - pattern for syntactic types
        hry    - conceptual hierarchy
        man    - morphology analyzer
    """

    def __init__ ( self , system ):

        """
        load all definitions from text files

        arguments:
            self     -
            system   - which set of table definitions
        """

        super(Rules,self).__init__()

        self.stb = symbolTable.SymbolTable()  # new empty table to fill in

        self.mtb = macroTable.MacroTable(self.inpT(system,'m'))
        self.gtb = grammarTable.GrammarTable(self.stb,self.inpT(system,'g'))
        self.ptb = patternTable.PatternTable(self.stb,self.inpT(system,'p'))

        self.hry = conceptualHierarchy.ConceptualHierarchy(self.inpT(system,'h'))

        sa = self.inpT(system,'stl')
        pa = self.inpT(system,'ptl')
        self.man = morphologyAnalyzer.MorphologyAnalyzer(sa,pa)

class Vocabulary(EllyDefinition):

    """
    Elly vocabulary definition

    attributes:
        vtb    - vocabulary table maintained externally
    """

    def __init__ ( self , system , create=False , syms=None , stem=None ):

        """
        load vocabulary definitions from text file

        arguments:
            self    -
            system  - which database
            create  - whether to create
            syms    - Elly symbols defined for vocabulary
        """

#       print 'set vocabulary'
        super(Vocabulary,self).__init__()

        if ellyConfiguration.language == 'EN':
            stem = inflectionStemmerEN.InflectionStemmerEN()
        else:
            stem = None
        if create:
#           print 'compiling' , system , 'vocabulary'
            dT = self.inpT(system,'v')
#           dT.dump()
            if not vocabularyTable.compile(system,syms,dT,stem):
                print >> sys.stderr , 'vocabulary compilation failed'
                self.vtb = None
                return

        self.vtb = vocabularyTable.VocabularyTable(system,stem)

#
# unit test
#

if __name__ == '__main__':

    import sys
    import symbolTable

    sym = symbolTable.SymbolTable()
    nam = sys.argv[1] if len(sys.argv) > 1 else 'test'
    print 'system=' , nam
    print "------------ rules"
    rul = Rules(nam)
#   print dir(rul)
    print rul.stb
    print rul.mtb
    print rul.gtb
    print rul.ptb
    print rul.hry
    print rul.man
    for e in rul.errors:
        print "    " , e
    print "------------ internal dictionary"
    print rul.gtb.dctn.keys()
    print "------------ external vocabulary"
    voc = Vocabulary(nam,True,sym)
    if voc.vtb == None:
        sys.exit(1)
    print voc.vtb.dbs.keys()
    for e in voc.errors:
        print "    " , e
