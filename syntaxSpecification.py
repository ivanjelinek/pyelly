#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# syntaxSpecification.py : 13dec2013 CPM
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
interpreting full syntax specification of phrase or grammar rule
"""

import ellyBits
import ellyChar
import grammarTable
import featureSpecification

def scan ( str ):

    """
    check for extent of syntax specification

    arguments:
        str  - string of chars to scan

    returns:
        char count > 0 on finding possible syntax specification, 0 otherwise
    """

    n = 0
    lm = len(str)
    while n < lm:
        c = str[n]
        if c == '.' or ellyChar.isLetterOrDigit(c): n += 1
        else: break
    if n == lm: return n
    c = str[n]
    if c == ' ': return n
    if c != '[': return 0
    k = featureSpecification.scan(str[n:])
    return n + k if k > 0 else 0

class SyntaxSpecification(object):

    """
    store encoded syntax category and features

    attributes:
        catg  - numerically encoded category (e.g. NOUN or VERB)
        synf  - syntactic features as EllyBits
    """

    def __init__ ( self , syms , spec ):

        """
        initialization from input string and symbol table

        arguments:
            self  -
            syms  - current symbol table
            spec  - input string
        """

        self.catg = -1    # values to set on an error
        self.synf = None  #

        if spec == None: return

        s = spec.lower()  # must be lower case for all lookups

        ln = len(s)
        n = 0
        while n < ln:
            c = s[n]
            if not ellyChar.isLetterOrDigit(c) and c != '.': break
            n += 1

        if n == 0: return # no acceptable category name found

        typs = s[:n]      # save category name
        catg = syms.getSyntaxTypeIndexNumber(typs)

        s = s[n:].strip() # feature part of syntax

        if len(s) == 0 or typs == '...': # ... category may have no features!
            synf = featureSpecification.FeatureSpecification(syms,None)
        else:                            # decode features
            synf = featureSpecification.FeatureSpecification(syms,s)

        if synf == None:
            print >> sys.stderr , 'no features for [' + s + ']'
            return

        self.catg = catg
        self.synf = synf

    def __str__ ( self ):

        """
        show SyntaxSpecification

        arguments:
            self

        returns:
            string representation
        """

        fs = '+....-....' if self.synf == None else str(self.synf)
        return 'type=' + str(self.catg) + ' ' + fs

if __name__ == '__main__':

    import sys
    import symbolTable

    stb = symbolTable.SymbolTable()
    stb.getSyntaxTypeIndexNumber('sent')
    stb.getSyntaxTypeIndexNumber('end')
    stb.getSyntaxTypeIndexNumber('unkn')
    stb.getSyntaxTypeIndexNumber('...')

#   note that ... is not allowed to have syntactic features specified

    spcl = sys.argv[1:] if len(sys.argv) > 1 else [ '...[.0,1]' ]
    for spc in spcl:
        n = scan(spc)
        sx = spc[:n]
        print n , 'chars in possible specification'
        ss = SyntaxSpecification(stb,sx)
        print 'syntax specification' , sx , '=' , ss