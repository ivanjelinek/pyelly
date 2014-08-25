#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# patternTable.py : 24aug2014 CPM
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
finite-state automaton (FSA) for inferring syntactic type of tokens
"""

import sys
import ellyBits
import ellyChar
import ellyWildcard
import ellyException
import syntaxSpecification

class Link(object):

    """
    for defining FSA transitions with Elly pattern matching

    attributes:
        patn  - Elly pattern to match
        nxts  - next state on match
        catg  - syntactic category
        synf  - syntactic features
    """

    def __init__ ( self , syms , dfls ):

        """
        initialization

        arguments:
            self  -
            syms  - Elly symbol table
            dfls  - definition elements in list

        exceptions:
            FormatFailure
        """

        if len(dfls) != 3:                            # must have 3 elements
            raise ellyException.FormatFailure
        else:
            self.patn = ellyWildcard.convert(dfls[0]) # encode wildcards in pattern
            self.catg = None                          # defaults
            self.synf = None                          #
            sss = dfls[1].lower()                     # cannot be Unicode!
#           print 'sss=' , sss
            if sss != '-':                            # allow for no category
                syx = syntaxSpecification.SyntaxSpecification(syms,sss)
                if syx != None:
                    self.catg = syx.catg              # syntactic category
                    self.synf = syx.synf.positive     # syntactic features

            try:
                n = int(dfls[2])                      # next state for link
            except:
                n = -1                                # unrecognizable string taken as -1

            if n < 0:                                 # final transition?
                pe = self.patn[-1]                    # if so, look at last pattern element
                if ( pe != ellyWildcard.cALL and      # final pattern must end with * or $
                     pe != ellyWildcard.cEND ):
                    self.patn += ellyWildcard.cEND    # default is $
                    print >> sys.stderr , '** default $ added to pattern' , dfls

            self.nxts = n                             # specify next state

    def __unicode__ ( self ):

        """
        string representation

        arguments:
            self

        returns:
            string for printing out link
        """

        if self.patn == None:
            return 'None!'
        else:
            cat = unicode(self.catg)
            fet = u'None' if self.synf == None else self.synf.hexadecimal()
            return ( ellyWildcard.deconvert(self.patn) + ' ' + cat + ' ' +
                     fet + ' next=' + unicode(self.nxts) )

class PatternTable(object):

    """
    FSA with Elly patterns to determine syntax types

    attributes:
        indx      - for FSA states and their links

        _errcount - running input error count
     """

    def __init__ ( self , syms=None , fsa=None ):

        """
        initialize

        arguments:
            self  -
            syms  - symbol table for syntax categories and features
            fsa   - EllyDefinitionReader for FSA patterns plus syntax specifications

        exceptions:
            TableFailure on error
        """

        self.indx = [ ]     # start empty
        self._errcount = 0  # no errors yet
        if fsa != None and syms != None:
            self.load(syms,fsa)

    def _err ( self , s='malformed FSA transition' , l='' ):

        """
        for error handling

        arguments:
            self  -
            s     - error message
            l     - problem line
        """

        self._errcount += 1
        print >> sys.stderr , '** pattern error:' , s
        if l != '':
            print >> sys.stderr , '** at [' , l , ']'

    def load ( self , syms , fsa ):

        """
        convert text input to get FSA with encoded syntax

        arguments:
            self  -
            syms  - symbol table for syntax categories and features
            fsa   - FSA link input from Elly definition reader

        exceptions:
            TableFailure on error
        """

        ins = [ 0 ]     # states with incoming links
        sss = [   ]     # starting states
        lss = [ 0 ]     # all defined states

        nm = 0                               # states producing matches
#       print 'FSA definition line count=' , fsa.linecount()
        while True: # read all input from ellyDefinitionReader
            l = fsa.readline()
#           print 'line=' , l
            if len(l) == 0: break            # EOF check
            ls = l.strip().split(' ')        # get link definition as list
#           print 'ls=' , ls
            sts = ls.pop(0)                  # starting state for FSA link
            if not ellyChar.isDigit(sts[0]): # starting state should be numerical
                self._err('bad input',l)
                continue
            stn = int(sts)                   # numerical starting state
            n = len(self.indx)
            
            if stn >= n:                     # make sure state index has enough slots allocated
                for i in range(stn - n + 1): #
                    self.indx.append([ ])    #
            try:
                lk = Link(syms,ls)           # allocate new link
            except:
                self._err('bad link',l)
                continue
#           print 'load lk=' , lk

            if lk.catg != None: nm += 1      # link has category for match
            if not stn in lss: lss.append(stn)
            if not stn in sss: sss.append(stn)
            if lk.nxts >= 0:                 # -1 is stop, not state
                if not lk.nxts in lss: lss.append(lk.nxts)
                if not lk.nxts in ins: ins.append(lk.nxts)

            self.indx[stn].append(lk)        # add to its slot in FSA state index
#           print '=' , self.indx[stn]

        if len(self.indx) == 0 and self._errcount == 0:
            return                           # in case of empty definition file

        if nm == 0:                          # FSA must have at least one match state
            self._err('no match states')
#       print 'ins=' , ins
#       print 'lss=' , lss

        ns = len(lss)                        # total number of states
        if len(ins) != ns:
            self._err('some states unreachable')
        if len(sss) != ns:
            self._err('some non-stop states are dead ends')
        if self._errcount > 0:
            print >> sys.stderr , 'pattern table generation FAILed'
            raise ellyException.TableFailure

    def bound ( self , segm ):

        """
        get maximum limit for matching
        (override this method if necessary)

        arguments:
            self  -
            segm  - text segment to match against

        returns:
            char count
        """

        lm = len(segm)   # limit can be up to total length of text for matching
        ll = 0
        while ll < lm:   # look for first space in text segment
            if segm[ll] == ' ': break
            ll += 1
#       print 'll=' , ll , ', lm=' , lm
        ll -= 1
        while ll > 0:    # exclude trailing non-alphanumeric from matching except for '.'
            c = segm[ll]
            if c == '.' or ellyChar.isLetterOrDigit(c): break
            ll -= 1
        return ll + 1

    def match ( self , segm , tree ):

        """
        compare text segment against FSA patterns 

        arguments:
            self  -
            segm  - segment to match against
            tree  - parse tree in which to put results

        returns:
            maximum text length matched by FSA
        """

#       print 'compare' , segm

        if len(self.indx) == 0: return 0  # no matches if FSA is empty

        ll = self.bound(segm)             # get limit for matching

        mtchs = None   # initialize best  match
        mtchl = 0      #            total match length

        ml = 0         # partial match length

        stk = [ ]      # for backup on failure

        state = 0      # initial state for FSA must always be this
        ls = self.indx[state]
        ix = 0
        sg = segm[:ll] # text subsegment for matching

        while True:             # run FSA for maximum match
#           print 'state=' , state
#           print 'count=' , mtchl , 'matched'
#           print 'links=' , len(ls)
            lns = len(ls)       # how many links from current automaton state
            if lns == 0: break  # if none, then done

            while ix < lns:     # iterate on links
                lk = ls[ix]     # get next one
                ix += 1         # and increment link index
#               print 'lk=' , lk, ', sg=' , sg
                bds = ellyWildcard.match(lk.patn,sg)
#               print 'bds=' , bds
                if bds == None: continue
                ml = bds[0]     # get match length, can ignore wildcard bindings
                if lk.catg != None:
#                   print 'match type=' , lk.catg
                    mtchs = [ lk.catg , lk.synf ]
                break           # accept first link path match
                
            else:               # failure to match on this path of links
#               print 'stk=' , len(stk)
                if len(stk) == 0 or mtchs != None: break
#               print 'backup=' , len(stk)
                r = stk.pop()   # back up to previous state
                state = r[0]
                ls = r[1]       # retry matching from there
                ix = r[2]
                sg = r[3]
                mtchl = r[4]
                continue

            mtchl += ml                                  # increment match length
            if lk.nxts < 0: break                        # check for successful FSA match
            stk.append([ state , ls , ix , sg , mtchl ]) # if not, save info for possible backup
            state = lk.nxts
            ls = self.indx[state]                        # move to next state
            ix = 0
            sg = sg[ml:]                                 # move up in text input
#           print 'sg=' , sg

        if mtchs == None:                                # check for unsuccessful match
            return 0                                     # if so, done
        elif tree.addLiteralPhrase(mtchs[0],mtchs[1]):   # otherwise make phrase in parse tree
            tree.lastph.lens = mtchl
            return mtchl
        else:
            return 0

    def dump ( self ):

        """
        show contents of pattern table

        arguments:
            self
        """

        for k in range(len(self.indx)):
            lks = self.indx[k]
            if lks == None or lks == [ ]:
                continue
            print '[state ' + str(k) + ']'
            for lk in lks:
                print u'  ' + unicode(lk)
        print ''
#
# unit test
#

if __name__ == '__main__':

    import symbolTable
    import ellyConfiguration
    import ellyDefinitionReader
    import dumpEllyGrammar
    import parseTest
    import os,stat

    mode = os.fstat(0).st_mode       # to check for redirection of stdin (=0)
    interact = not ( stat.S_ISFIFO(mode) or stat.S_ISREG(mode) )

    tre = parseTest.Tree()           # dummy parse tree for testing
    ctx = parseTest.Context()        # dummy interpretive context for testing
        
    base = ellyConfiguration.baseSource + '/'
    file = sys.argv[1] if len(sys.argv) > 1 else 'test' # which FSA definition to use
    inp = ellyDefinitionReader.EllyDefinitionReader(base + file + '.p.elly')

    print 'pattern test with' , '<' + file + '>'

    pat = None
    try:
        pat = PatternTable(ctx.syms,inp) # try to define FSA
    except ellyException.TableFailure:
        print 'no pattern table generated'
        sys.exit(1)

    print len(pat.indx) , 'pattern groups'

    print 'grammar syntax categories'
    dumpEllyGrammar.dumpCategories(ctx.syms)
    pat.dump()

    while True: # try FSA with test examples

        if interact: sys.stdout.write('> ')
        t = sys.stdin.readline().strip()
        if len(t) == 0: break
        print 't=' , '[' + t + ']'
        t = t.strip()
        n = pat.match(list(t),tre)
        print '    from <'+ t + '>' , n , 'chars matched' , '| leaving <' + t[n:] + '>'

    if interact: sys.stdout.write('\n')
