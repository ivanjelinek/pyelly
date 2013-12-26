#!/usr/bin/python
# PyElly - scripting tool for analyzing natural language
#
# generativeDefiner.py : 19nov2013 CPM
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
method to compile code for a generative semantic procedure and optionally
to display it
"""

import sys
import ellyBits
import grammarTable
import semanticCommand

_simple = {  # commands with no arguments
    "noop"       : semanticCommand.Gnoop ,
    "pass"       : semanticCommand.Gnoop ,
    "return"     : semanticCommand.Gretn ,
    "fail"       : semanticCommand.Gfail ,
    "left"       : semanticCommand.Gleft ,
    "right"      : semanticCommand.Grght ,
    "blank"      : semanticCommand.Gblnk ,
    "space"      : semanticCommand.Gblnk ,
    "linefeed"   : semanticCommand.Glnfd ,
    "split"      : semanticCommand.Gsplt ,
    "back"       : semanticCommand.Gback ,
    "obtain"     : semanticCommand.Gobtn ,
    "capitalize" : semanticCommand.Gcapt ,
    "trace"      : semanticCommand.Gtrce 
}

_dir = [ '<' , '>' ] # qualifier for semantic command

def convertDefinition ( stb , inp ):

    """
    convert definition from input stream into executable generative semantic logic

    arguments:
        stb   - symbol table
        inp   - EllyDefinitionReader for procedure definition

    returns:
        procedure body as a list of commands and data on success, None otherwise
    """

    ######## special methods for handling conditional blocks

    backl = [ ]  # back link stack
    store = [ ]  # to save procedure body

    def _elseBlock ( ):

        """
        handle an ELSE by closing a block and resolving a previous IF failure branch
        returns:
            True on success, False otherwise
        """

#       print "elseBlock" , len(backl)
        if len(backl) == 0: return False
        no = backl[-1]            # location of previous conditional branch
        br = store[no]            # save chaining link saved in location
        if br < 0: return False   # < 0 indicates previous WHILE, which cannot have ELSE
        store.append(semanticCommand.Gskip) # end execution of preceding block
        backl[-1] = len(store)    # update back link stack to next skip destination
        store.append(br)          # place holder for skip destination
        store[no] = len(store)    # previous conditional branch comes here
        return True

    def _ifTest ( negn , rs ):

        """
        add conditional test at start of block according to type of arguments
        arguments:
            negn - any negation
            rs   - argument string
        returns:
            True on success, False otherwise
        """

#       print "ifTest" , len(backl) , rs
        if len(rs) == 0: return False
        
        if rs[0] == '[': # testing semantic feature
            k = rs.find(']')
            if k < 0: return False
            fs = stb.getFeatureSet(rs[1:k].lower())
            if fs == None: return False
            test = ellyBits.join(fs[0],fs[1])
            store.extend([ semanticCommand.Gchkf+negn , test ])
        else:            # testing local variable
            ar = rs.split('=')
#           print 'ar=' , len(ar) , ar
            if len(ar) < 2: return Fail
            ls = ar[1].split(', ') # separator must be a comma followed by space!
            store.extend([ semanticCommand.Gchck+negn , ar[0].lower() , ls ])
        return True

    ########

    def _procParse ( line ):

        """
        parse a call to standalone procedure and write out code
        arguments:
            line  - text to parse; it should start with '(' and end with ')'
        returns:
            True on success, False otherwise
        """

        k = line.find(')')     # look for end of procedure name
        if k < 0: return False # error if not found
        store.extend( [ semanticCommand.Gproc , line[1:k].lower() ] )
        return True

    def _operParse ( line ):

        """
        parse regular semantic operation and arguments and then write out code
        arguments:
            line  - text to parse, should be already stripped
        returns:
            True on success, False otherwise
        """ 

        negn = 0                    # negation indicator for Gchck and Gchkf operations
        k = line.find(' ')          # check for anything after operation code
        if k < 0:                   # if not, line has no arguments
            op = line.lower()       # extract the operation
            rs = ''                 # rest of string
        else:
            op = line[:k].lower()   # otherwise, line has arguments
            rs = line[k+1:].strip() # rest of string
            if op != semanticCommand.Gappd and rs[0] == '~':
                rs = rs[1:]         # special where '~' means negation in check
                negn = 1            # remove '~' and set flag

#       print 'op=' , op , 'rs=' , rs

        if op in _simple:           # nothing more to do if operation is simple
#           print "simple operation"
            store.append(_simple[op])
            return True             #

        if op == 'merge':
            if len(rs) == 0:
                store.append(semanticCommand.Gmrge)
            else:
                c = rs[0]
                store.append(semanticCommand.Gchng)
                ar = rs[1:].split(c)
                if len(ar) < 2:
                    return False  # incomplete substitution
                else:
                    store.extend(ar[:2])
        elif op == 'end':
            if len(backl) == 0: return False
            no = backl.pop()
#           print 'END @' , no , store[no]
            nn = no
            while nn > 0:         # follow back links to identify type of block
                on = nn
                nn = store[nn]
            if nn < 0:            # handling WHILE?
                store.extend([ semanticCommand.Gskip , on-3 ])
            ln = len(store)       # end of block
            while True:
                on = store[no]    # fill in chained back links to resolve branches
                store[no] = ln    # all branches will now go to end of block
                if on <= 0: break
                no = on
#               print "back" , no , store[no]
        elif op == 'else':
            if not _elseBlock(): return False
        elif op == 'elif':
            if len(rs) == 0: return False
            if not _elseBlock(): return False
            if not _ifTest(negn,rs): return False
            on = backl[-1]
#           print "extend back link"
            backl[-1] = len(store)
            store.append(on)
        elif op == 'while' or op == 'if':
            if len(rs) == 0: return False
            wh = (op == 'while')                 # are we dealing with WHILE?
#           print 'negation=',negn
            if not _ifTest(negn,rs): return False
#           print "new back link"
            backl.append(len(store))             # back link to conditional branch destination
            store.append(-1 if wh else 0)        # put in place holder with flag
#           print 'code save'
        elif op == 'break' or op == 'breakif':
            k = len(backl) - 1
            while k >= 0:                        # find first enclosing WHILE block
                no = backl[k]
                while no > 0:                    # follow back links
                    no = store[no]
                if no < 0: break                 # stored -1 marks marks WHILE test
                k -= 1                           # stored  0 marks IF/ELIF, must continue
            else:
                return False                     # no enclosing WHILE block found
            if op == 'break':
                store.append(semanticCommand.Gskip)  # put in branch command for BREAK
            else:
                ar = rs.split('=')               # check can be on local variable only
                if len(ar) < 2:
                    return False
                v = ar[0]                        # variable name
                if v[0] == '~':                  # get any sense of check
                    op = semanticCommand.Gchck   # (note that sense of check reverses)
                    v = v[1:]
                else:
                    op = semanticCommand.Gnchk   #
                store.extend([ op , v , ar[1] ]) # put if conditional branch for BREAKIF
            on = len(store)                      # for updating back link
            store.append(backl[k])               # save old back link
            backl[k] = on                        # update back back link for branch
                
        elif op == 'var' or op == 'variable' or op == 'set':
            if len(rs) == 0: return False
            co = semanticCommand.Gset if op == 'set' else semanticCommand.Gvar
            ar = rs.split('=')
            if len(ar) < 2: ar.append('')
            store.extend([ co , ar[0].lower() , ar[1] ])
        elif op == 'insert':
            ar = _getargs(rs)
            if ar == None: return False
            wh = ar.pop(0)
            sc = semanticCommand.Ginsr if wh == '<' else semanticCommand.Ginsn
            store.extend([ sc , ar[0] ])
        elif op == 'peek':
            ar = _getargs(rs)
            wh = ar.pop(0)
            if ar == None: return False
            store.extend([ semanticCommand.Gpeek , ar[0] , (wh == '<') ])
        elif op == 'extract':
            ar = _getargs(rs)
            if ar == None: return False
            wh = ar.pop(0)
            sc = semanticCommand.Gextr if wh == '<' else semanticCommand.Gextl
            if len(ar) == 1: ar.append('1')
            store.extend([ sc , ar[0] , int(ar[1]) ])
        elif op == 'shift' or op == 'delete':
            if len(rs) == 0: return False
            co = semanticCommand.Gshft if op == 'shift' else semanticCommand.Gdele
            ar = rs.split(' ')
            nch = 11111 if ar[0] == 'all' else int(ar[0])
            if len(ar) > 1 and ar[1] == '>': nch = -nch
            store.extend([ co , nch ])
        elif op == 'find':
            if len(rs) == 0: return False
            ar = rs.split(' ')
            ss = ar.pop(0)
            while ss[-1] == '\\' and len(ar) > 0:
                ss = ss[:-1] + ' ' + ar.pop(0)
            store.extend([ semanticCommand.Gfnd , ss ])
        elif op == 'pick':
#           print 'rs=' , rs
            if len(rs) == 0: return Fail
            ar = rs.split(' ')
            if len(ar) < 2: return Fail
            chs = ar[1]
#           print 'chs=' , chs
            if chs[0] != '(' or chs[-1] != ')': return Fail
            dic = { }
            ch = chs[1:-1].split('#')    # strip off ( )
#           print 'ch=' , ch
            for p in ch:                 # get mappings
#               print 'p=' , p
                if p != '':
                    he = p.split('=')
                    if len(he) == 2:     # should be only one assignment
                        dic[he[0]] = he[1]
#           print 'dic=' , dic
            store.extend([ semanticCommand.Gpick , ar[0].lower() , dic ])
#           print 'store=' , store
        elif op == 'append':
            store.extend([ semanticCommand.Gappd , rs ] )
        elif op == 'get' or op == 'put':
            co = semanticCommand.Gget if op == 'get' else semanticCommand.Gput
            av = rs.lower().split(' ')
            if len(av) < 2:
                print >> sys.stderr, "**missing global variable!!"
                return False
            store.extend([ co , av[0] , av[1] ])
        elif op == 'assign':
            av = rs.split('=')
            if len(av) == 1 or len(av[1]) == 0:
                print sys.stderr, "**incomplete assignment!!"
                return False
            store.extend([ semanticCommand.Gassg , av[0].lower() , av[1] ]);
        else:
            print >> sys.stderr, "**bad operation: " + op
            return False

#       print 'success!'
        return True

#
#   main loop for conversion
#

    while True:
        line = inp.readline()
        if len(line) == 0: break
#       print '>>' , line
        k = line.find(' # ')         # look for comments
        if k > 0:
            line = line[:k].rstrip() # and remove them
        if line[0] == '(':
            if not _procParse(line): # interpret procedure call
                return None
        else:
            if not _operParse(line): # interpret semantic command
#               print 'failure!'
                return None

    return store if len(backl) == 0 else None

def _getargs ( rs ):

    """
    parse arguments for insert or extract or peek command

    arguments:
        self  -
        rs    - argument string for a command

    returns:
        argument list on success, None otherwise
    """

    ar = rs.split(' ')
    if len(ar) < 2: return None
    x = ar[0]
    if x in _dir:
        ar[1] = ar[1].lower()
        return ar
    elif ar[1] in _dir:
        ar[0] = ar[1]
        ar[1] = x.lower()
        return ar
    else:
        return None

#
# unit test
#

def showCode ( cod ):

    """
    show operations in compiled generative semantic procedure

    arguments:
        cod   - code to display
    """

    if cod == None:
       print 'No Code'
       return
    loc = 0
    while len(cod) > 0:
        l = semanticCommand.Glen[cod[0]]
        com = semanticCommand.Gopn[cod[0]]
        arg = cod[1:l] if l != 1 else ''
        cod = cod[l:]
        print '>{0:3d} {1} {2}'.format(loc,com,str(arg))
        loc += l

if __name__ == "__main__":

    import symbolTable
    import ellyDefinitionReader

    stb = symbolTable.SymbolTable()

    try:
        src = sys.argv[1] if len(sys.argv) > 1 else 'generativeDefinerTest.txt'
        inp = ellyDefinitionReader.EllyDefinitionReader(src)
    except IOError:
        print >> sys.stderr, "cannot read procedure definition"
        sys.exit(1)

    cod = convertDefinition(stb,inp)
    if cod == None:
        print >> sys.stderr, "conversion error"
        sys.exit(1)

    print len(cod) , 'code elements in procedure'
    showCode(cod)
