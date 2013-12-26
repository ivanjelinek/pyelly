#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# punctuationRecognizer.py : 29oct2013 CPM
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
builtin single-char punctuation recognition

provided as a convenience so that marks do not have to be listed in an internal
or external dictionary for every Elly grammar definition

multiple-char punctuation MUST be in an internal or external dictionary!
"""

import ellyBits
import featureSpecification

category = 'punc' # this must be used in Elly grammars for punctuation!

listing  = [ '.' , '?' , '!' , ',' , ':' , ';' , '\'' , '\"' ]

class PunctuationRecognizer(object):

    """
    recognizer to support parsing

    attributes:
        catg   - syntactic info for all recognized punctuation
        synf   -
        period - for stop syntactic flag
    """

    def __init__ ( self , syms ):

        """
        initialization

        arguments:
            self  -
            syms  - Elly symbol table
        """

        self.catg = syms.getSyntaxTypeIndexNumber(category)
        self.synf = ellyBits.EllyBits()  # zero bits for all features turned off

        p = featureSpecification.FeatureSpecification(syms,'[:period]')
        self.period = p.positive

    def match ( self , s ):

        """
        check whether list of chars corresponds to punctuation

        arguments:
            self  -
            s     - list of chars to check (usually an elly token root)

        returns:
            True if punctuation, False otherwise
        """

        if len(s) != 1:     # only single-char punctuation expected here!
            return False

        if s[0] in listing: # simple lookup
            return True
        else:
            return False

#
# unit test
#

if __name__ == '__main__':

    import symbolTable

    ps = '.?!ab,;:+cd$%&\'\"ef'

    syms = symbolTable.SymbolTable()
    punc = PunctuationRecognizer(syms)

    for p in ps:

        f = punc.match(p)
        print p , f