#!/usr/bin/env python

# wsgi api

import collections
import os
import re

from decimal import Decimal as D

from sqldata import DBHandle, AccountData, QIFPattern, userDB, normalize_date
from acct import Xact
import qif


class api (object):
    """
    set of methods intended to be called via the wsgi interface
    """
    def __init__ (self, sessionId, username=None, password=None):

        self.userdb = userDB()
        self.dbfile = None
        self.sid = sessionId
        self.loggedIn = self.userAuth = False

        if self.userdb.authenticate(username, password):
            self.dbfile = '/home/mdg/src/acct/data.db.%s' % username
            self.sid = self.userdb.register_session(self.dbfile)
            self.userAuth = True
        else:
            self.dbfile = self.userdb.retrieve_session(self.sid)

        if not self.dbfile:
            self.dbfile = '/home/mdg/src/acct/data.db'
        else:
            self.loggedIn = True

        self.db = DBHandle(dbfile=self.dbfile)


    def change_password(self, username, password, newPassword):
        return self.userdb.change_password(username, password, newPassword)


    def get_acctlist (self):
        return self.db.get_acctlist()

    def get_xact_data (self, atype, name, create, xtype):
        return AccountData(self.db, atype, name, create=create).get_xact_data(xtype=xtype)

    def add_xact (self, debitAcctType, debitAcctName, creditAcctType, creditAcctName, amount, description, xactDate):
        xact = Xact(self.db)
        xact.add_debit(debitAcctName, debitAcctType, D(amount))
        xact.add_credit(creditAcctName, creditAcctType, D(amount))
        xact.save(description=description, date=xactDate)

    def add_acct (self, acctType, acctName):
        acctName = acctName.replace(' ', '_')
        AccountData(self.db, acctType, acctName, create=True)
        return True

    def add_qif_pattern (self, acctType, acctName, pattern, cptyAcctType, cptyAcctName):
        AccountData(self.db, acctType, acctName).add_qif_pattern(pattern, cptyAcctType, cptyAcctName)
        return True

    def del_qif_pattern (self, acctType, acctName, pattern, cptyAcctType, cptyAcctName):
        AccountData(self.db, acctType, acctName).del_qif_pattern(pattern, cptyAcctType, cptyAcctName)
        return True

    def get_qif_patterns (self):
        return QIFPattern(self.db).get_patterns()


    def get_qif_pending(self):
        return QIFPattern(self.db).get_pending()


    def create_instance(self, username, password):
        dbfile = '/home/mdg/src/acct/data/%s.db' % username
        if os.path.exists(dbfile):
            return False
        self.userdb.add_user(username, password)
        return True


    def applyQIFData(self, srcAcctType, srcAcctName, qifFile):
        q = qif.QIF(qifFile=qifFile)
        xacts = q.sections[0]
        pending_xacts = []
        for xact in xacts:
            record = (srcAcctType, srcAcctName, normalize_date(xact['date']), str(xact['amount']), xact['payee'])
            pending_xacts.append(record)
        AccountData(self.db, srcAcctType, srcAcctName).add_qif_pending(pending_xacts)


    def applyQIFPatterns(self):
        qp = QIFPattern(self.db)

        pending_xacts = qp.get_pending()

        compiled_patterns = collections.defaultdict(list)
        patterns = qp.get_patterns() # list of (atype, aname, patttern, cptyType, cptyName)
        for record in patterns:
            (srcType, srcName, pattern, cptyType, cptyName) = record
            compiled_patterns[':'.join((srcType, srcName))].append((re.compile(pattern), cptyType, cptyName))
        
        for xact in pending_xacts:

            (srcAcctType, srcAcctName, date, amount, description) = xact
            srcAcctFullName = ':'.join((srcAcctType, srcAcctName))

            cptyType = cptyName = None

            for record in compiled_patterns[srcAcctFullName]:
                pattern = record[0]
                if pattern.search(description):
                    cptyType = record[1]
                    cptyName = record[2]
                    break

            if not cptyName:
                # no match, leave it alone
                continue

            amount = D(amount)
            origDescription = description

            if srcAcctType in ['ASSET','LIABILITY'] and cptyType in ['ASSET','LIABILITY']:
                # rewrite description field so we can ID these as dupes in future imports
                cptyFullName = ':'.join((cptyType, cptyName))
                dfmt = "xfer from %s to %s"
                if amount > 0:
                    description = dfmt % (cptyFullName, srcAcctFullName)
                else:
                    description = dfmt % (srcAcctFullName, cptyFullName)

            if amount > 0:
                # asset debit
                self.add_xact(srcAcctType, srcAcctName, cptyType, cptyName, amount, description, date)
            else:
                # asset credit
                self.add_xact(cptyType, cptyName, srcAcctType, srcAcctName, abs(amount), description, date)

            qp.del_pending(srcAcctType, srcAcctName, date, str(amount), origDescription)

        return True

