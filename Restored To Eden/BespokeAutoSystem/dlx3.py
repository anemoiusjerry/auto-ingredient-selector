import functools
from PySide2.QtCore import QObject, Signal, Slot
"""
Python implementation of Donald Knuths DLX3 algorithm
By Hayden Goodwin 2020

The following program is an implementation of Donald Knuths DLX3 algorithm.
DLX3 is an extension of DLX1 and DLX 2 where the min an max amount of times an
item is covered can be specified. It also includes the 'colour' of a node
which allows only nodes with like colours to cover the same item.

DLX3 by Knuth:
https://www-cs-faculty.stanford.edu/~knuth/programs/dlx3.w

It is recommended to have a look at the original source as it is very
well documnted. NOTE: The original is written in cweb.
"""

class Node:
    def __init__(self, up, down, item, colour):
        self.up = up
        self.down = down
        self.itm = item
        self.colour = colour

class Item:
    def __init__(self, name, prev, next, bound, slack, order):
        self.name = name
        self.prev = prev
        self.next = next
        self.bound = bound
        self.slack = slack
        self.order = order


class DLX(QObject):

    PRIMARY = 0
    SECONDARY = 1
    INFTY = 100000000
    MAX_LEVEL = 500
    MAX_COUNT = 10**10

    sols = Signal(int)

    def __init__(self, cols, rows):
        QObject.__init__(self)
        # NOTE!! All secondary items must be at the end of the rows list !!
        # columns is a list of item info where each item is in the form of a tuple
        # each item info should be formatted: (name, order,lower bound, upper bound)
        # name is a string
        # order is a 0 or 1. 0 denotes Primary, 1 denotes Secondary
        # lower bound and upper bound are integers which specify the range of
        # nodes allowed to cover an item.
        # NOTE: only primary items have bounds

        # cols is a list of options (or rows)
        # each option should be formatted: ( "rowname",[(item, colour), ... ,(item,colour)])
        # rowname can be pretty much anything, usually its the name of the row
        # colours can be any positive integer value (including 0) that isnt 100.
        # if no colour is being used, it should be specified as None.
        # NOTE: only secondary items have colours

        self.stop = True # When this value is set to False, the program will halt
        self.updates = 0
        self.cleansings = 0

        self.itms = [Item(None,0,0,0,0,0)] # initialise items with a header item
        self.nodes = [Node(0,0,0,0)] # initialise nodes with the node corresponding to the header item
        self.rownames = []
        self.rowid = [None] * (len(cols)+1)
        self.second = 0 # Location where the first secondary item is

        # creating the linked list of items
        cur = 1
        prev = 0
        self.root = 0 # the first item in the linked list of items
        for (name, type, low_bound, up_bound) in cols:
            slack = up_bound - low_bound
            if type == DLX.PRIMARY: # only primary items are linked
                self.itms.append(Item(name, prev, self.root ,up_bound, slack, type)) # adding an item
                self.itms[prev].next = cur # ammending the previous items next pointer
                self.itms[self.root].prev = cur # ammending the first items prev pointer
                prev = cur
                self.second = cur + 1
            else:
                self.itms.append(Item(name, cur, cur, up_bound, slack, type)) # secondary items point to thier own location
            self.nodes.append(Node(cur, cur, 0, 0)) # creating the header nodes
            cur += 1


        # creating the linked node list
        nnindex = len(self.nodes) # Index where the new nodes will be placed
        i = 0
        j = 0
        prev = 0
        for row, rowname in rows:
            self.rownames.append(rowname)
            if not self.onlySec(row):
                self.rowid.append(j)
                self.nodes.append(Node(prev, nnindex+len(row), -i,0)) #Creating spacer node
                nnindex += 1
                prev = nnindex
                for (item, colour) in row:
                    item += 1
                    self.rowid.append(j)
                    if self.itms[item].order == DLX.SECONDARY and colour == 0:
                        colour = 100 # Give all secondary nodes with a colour 0 a non zero value
                    elif colour == None:
                        colour = 0
                    self.nodes[item].itm += 1 # increasing the length of the linked list that is stored to reflect the newly added node
                    r = self.nodes[item].up # the bottom node in the list
                    self.nodes.append(Node(r, item, item, colour)) # creating new node
                    self.nodes[item].colour = len(self.nodes) - 1 # storing the new last node in the linked list
                    self.nodes[r].down = nnindex # ammending the previous nodes' down pointer
                    self.nodes[item].up = nnindex # ammending the header nodes' up pointer
                    nnindex += 1 # increase the new node index
                i+=1
            j+=1
        self.nodes.append(Node(prev, 0,-i,0))

        self.partialsolution = []
        self.solutions = []

        self.last_itm = len(self.itms)
        self.last_node = len(self.nodes) - 1

        # other variables used while dancing
        self.level = 0
        self.nodect = 0
        self.score = 0
        self.scor = []
        self.first_tweak = []
        self.choice = []
        self.best_s = 0
        self.best_l = 0
        self.best_itm = 0
        self.count = 0
        self.maxl = 0

    def onlySec(self,row):
        for (itm , _) in row:
            if not self.itms[itm + 1].order:
                return False
        return True

    def cover(self, c, deact):
        if deact:
            l = self.itms[c].prev
            r = self.itms[c].next
            self.itms[l].next = r
            self.itms[r].prev = l

        self.updates += 1

        rr = self.nodes[c].down
        while rr >= self.last_itm:

            nn = rr + 1
            while nn != rr:
                if self.nodes[nn].colour >= 0:
                    uu = self.nodes[nn].up
                    dd = self.nodes[nn].down
                    cc = self.nodes[nn].itm

                    if cc <= 0:
                        nn = uu
                        continue

                    self.nodes[uu].down = dd
                    self.nodes[dd].up = uu
                    self.updates += 1
                    self.nodes[cc].itm -= 1
                nn += 1
            rr = self.nodes[rr].down

    def uncover(self, c, react):
        rr = self.nodes[c].down
        while rr >= self.last_itm:
            nn = rr + 1
            while nn != rr:
                if self.nodes[nn].colour >= 0:
                    uu = self.nodes[nn].up
                    dd = self.nodes[nn].down
                    cc = self.nodes[nn].itm

                    if cc <= 0:
                        nn = uu
                        continue

                    self.nodes[uu].down = nn
                    self.nodes[dd].up = nn
                    self.nodes[cc].itm += 1
                nn += 1

            rr = self.nodes[rr].down

        if react:
            l = self.itms[c].prev
            r = self.itms[c].next
            self.itms[l].next = c
            self.itms[r].prev = c

    def purify(self, p):
        cc = self.nodes[p].itm
        x = self.nodes[p].colour
        self.nodes[cc].colour = x
        self.cleansings += 1

        rr = self.nodes[cc].down
        while rr >= self.last_itm:
            if self.nodes[rr].colour != x:
                nn = rr + 1
                while nn != rr:
                    uu = self.nodes[nn].up
                    dd = self.nodes[nn].down
                    cc = self.nodes[nn].itm

                    if cc <= 0:
                        nn = uu
                        continue

                    if self.nodes[nn].colour >= 0:
                        self.nodes[uu].down = dd
                        self.nodes[dd].up = uu
                        self.updates += 1
                        self.nodes[cc].itm -= 1
                    nn += 1
            elif rr != p:
                self.cleansings += 1
                self.nodes[rr].colour = -1

            rr = self.nodes[rr].down

    def unpurify(self, p):
        cc = self.nodes[p].itm
        x = self.nodes[p].colour

        rr= self.nodes[cc].up
        while rr >= self.last_itm:
            if self.nodes[rr].colour < 0:
                self.nodes[rr].colour = x
            elif rr != p:
                nn = rr - 1
                while nn != rr:
                    uu = self.nodes[nn].up
                    dd = self.nodes[nn].down
                    cc = self.nodes[nn].itm

                    if cc <= 0:
                        nn = dd
                        continue

                    if self.nodes[nn].colour >= 0:
                        self.nodes[uu].down = nn
                        self.nodes[dd].up = nn
                        self.nodes[cc].itm += 1
                    nn -= 1
            rr = self.nodes[rr].up

    def tweak(self, n, block):
        if block:
            nn = n + 1
        else:
            nn = n

        while 1:
            if self.nodes[nn].colour >= 0:
                uu = self.nodes[nn].up
                dd = self.nodes[nn].down
                cc = self.nodes[nn].itm

                if cc <= 0:
                    nn = uu
                    continue

                self.nodes[uu].down = dd
                self.nodes[dd].up = uu
                self.updates += 1
                self.nodes[cc].itm -= 1
            if nn == n:
                break
            nn += 1

    def untweak(self, c, x, unblock):
        z = self.nodes[c].down
        self.nodes[c].down = x

        rr = x
        k = 0
        qq = c
        while rr != z:
            self.nodes[rr].up = qq
            k += 1
            if unblock:
                nn = rr + 1
                while nn != rr:
                    if self.nodes[nn].colour >= 0:
                        uu = self.nodes[nn].up
                        dd = self.nodes[nn].down
                        cc = self.nodes[nn].itm

                        if cc <= 0:
                            nn = uu
                            continue

                        self.nodes[uu].down = nn
                        self.nodes[dd].up = nn
                        self.nodes[cc].itm += 1
                    nn += 1
            qq = rr
            rr = self.nodes[rr].down
        self.nodes[rr].up = qq
        self.nodes[c].itm += k

        if not unblock:
            self.uncover(c,0)

    def forward(self):
        self.score = DLX.INFTY

        k = self.itms[self.root].next
        while k != self.root:

            s = self.itms[k].slack
            if s > self.itms[k].bound:
                s = self.itms[k].bound

            t= self.nodes[k].itm + s - self.itms[k].bound + 1
            if t <= self.score:
                if (t < self.score) or (s < self.best_s) or (s == self.best_s and self.nodes[k].itm > self.best_l):
                    self.score = t
                    self.best_itm = k
                    self.best_s = s
                    self.best_l = self.nodes[k].itm
            k = self.itms[k].next

        if self.score < DLX.INFTY:
            a =1


        if self.score <= 0:
            return self.backdown
        if self.score == DLX.INFTY:
            #print("level: ", self.level)
            self.count += 1
            self.partialsolution = []
            for i in range(self.level):
                pp = self.choice[i]
                cc = pp if pp < self.last_itm else self.nodes[pp].itm

                #self.record_option(pp)

                if not(pp < self.last_itm or pp >= self.last_node or self.nodes[pp].itm <= 0):
                    self.partialsolution.append(self.rownames[self.rowid[pp]])

            self.solutions.append(self.partialsolution)

            if len(self.solutions) % 5000 == 0:
                self.solsFound(len(self.solutions))

            if self.count > DLX.MAX_COUNT:
                return None
            return self.backdown

        try:
            self.scor[self.level] = self.score
        except:
            self.scor.append(self.score)

        try:
            self.first_tweak[self.level] = 0
        except:
            self.first_tweak.append(0)

        try:
            self.choice[self.level] = self.nodes[self.best_itm].down
        except:
            self.choice.append(self.nodes[self.best_itm].down)

        self.cur_node = self.nodes[self.best_itm].down

        self.itms[self.best_itm].bound -= 1
        if self.itms[self.best_itm].bound == 0 and self.itms[self.best_itm].slack == 0:
            self.cover(self.best_itm,1)
        else:
            self.first_tweak[self.level] = self.cur_node
            if self.itms[self.best_itm].bound == 0:
                self.cover(self.best_itm,1)

        return self.advance

    def advance(self):
        if (self.itms[self.best_itm].bound == 0) and (self.itms[self.best_itm].slack==0):
            if self.cur_node == self.best_itm:
                return self.backup

        elif self.nodes[self.best_itm].itm <= (self.itms[self.best_itm].bound - self.itms[self.best_itm].slack):
            return self.backup

        elif self.cur_node != self.best_itm:
            self.tweak(self.cur_node, self.itms[self.best_itm].bound)
        elif self.itms[self.best_itm].bound != 0:
            # deactivate best item
            p = self.itms[self.best_itm].prev
            q = self.itms[self.best_itm].next
            self.itms[p].next = q
            self.itms[q].prev = p

        if self.cur_node > self.last_itm:
            pp = self.cur_node + 1
            while pp != self.cur_node:
                cc = self.nodes[pp].itm
                if cc <= 0:
                    pp = self.nodes[pp].up
                else:
                    if cc < self.second:
                        self.itms[cc].bound -= 1
                        if self.itms[cc].bound == 0:
                            self.cover(cc,1)
                    else:
                        if not self.nodes[pp].colour:
                            self.cover(cc,1)
                        elif self.nodes[pp].colour > 0:
                            self.purify(pp)
                    pp += 1

        self.level += 1
        if self.level > self.maxl:
            if self.level >= DLX.MAX_LEVEL:
                return None #there are too many levels, quit the function and return solutions
            self.maxl = self.level
        return self.forward

    def backup(self):
        if(self.itms[self.best_itm].bound == 0) and (self.itms[self.best_itm].slack == 0):
            self.uncover(self.best_itm,1)
        else:
            self.untweak(self.best_itm, self.first_tweak[self.level], self.itms[self.best_itm].bound)
        self.itms[self.best_itm].bound += 1
        return self.backdown

    def backdown(self):

        if self.level == 0:
            return None
        self.level -= 1
        self.cur_node = self.choice[self.level]
        self.best_itm = self.nodes[self.cur_node].itm
        self.score = self.scor[self.level]

        if self.cur_node < self.last_itm:
            self.best_itm = self.cur_node
            p = self.itms[self.best_itm].prev
            q = self.itms[self.best_itm].next
            self.itms[p].next= self.best_itm
            self.itms[q].prev= self.best_itm
            return self.backup

        pp = self.cur_node - 1
        while pp != self.cur_node:
            cc= self.nodes[pp].itm
            if cc <= 0:
                pp = self.nodes[pp].down
            else:
                if cc < self.second:
                    if self.itms[cc].bound == 0:
                        self.uncover(cc,1)
                    self.itms[cc].bound += 1
                else:
                    if not self.nodes[pp].colour:
                        self.uncover(cc,1)
                    elif self.nodes[pp].colour > 0:
                        self.unpurify(pp)
                pp -= 1
        self.choice[self.level] = self.nodes[self.cur_node].down;
        self.cur_node = self.nodes[self.cur_node].down

        return self.advance

    def dance(self):
        """
        Starts the dancing links program and returns a list of solutions found.
        """
        def tramampoline(func):
            @functools.wraps(func)
            def g(*args):
                h = func
                while (h is not None) and self.stop:
                    h = h(*args)
                return args
            return g()

        tramampoline(self.forward)

        if self.stop:
            return self.solutions
        else:
            return None

    def solsFound(self, i):
        self.sols.emit(i)

    @Slot()
    def stop_(self):
        self.stop = False
