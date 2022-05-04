#!/usr/bin/env python

# data access api for sql based account, xact store (to replace the filedata prototype)
# sqlite initially, maybe postgres later

import base64
import datetime
import os

from decimal import Decimal as D

import sqlite3


def strToDate ( strDate=None ):
    """
    converts 'MM/DD/YYYY' to a datetime.date
    """
    if strDate is None:
        raise ValueError("strDate required")
    
    vals = [ int(v) for v in strDate.split('/') ]
    (month, day, year) = vals
    return datetime.date(year, month, day)


def normalize_date (date):
    """
    convert one of the several date formats i'm confusing myself with into an entirely new one
    in hopes to standardize on something...
    """
    if type(date) == type(datetime.date.today()):
        return(date.strftime('%Y%m%d'))
    elif '-' in date:
        (year, month, day) = [int(_) for _ in date.split('-')]
    elif '/' in date:
        (month, day, year) = [int(_) for _ in date.split('/')]
    elif len(date) == 8 and date.startswith('20'):
        # looks good already
        return date
    else:
        raise ValueError("yet another date format: %s" % date)

    return('%d%02d%02d' % (year, month, day))


class userDB (object):

    dbfile = '/home/mdg/src/acct/data.db.users'

    def __init__(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.cursor = self.conn.cursor()


    def add_user(self, username, password):
        self.cursor.execute("insert into users (username, password) values (?,?)", (username, password))
        self.conn.commit()


    def authenticate(self, username, password):
        self.cursor.execute("select * from users where username=? and password=?", (username, password))
        row = self.cursor.fetchone()
        if row is None:
            return False
        return True


    def change_password(self, username, password, newPassword):
        self.cursor.execute("update users set password=? where username=? and password=?", (newPassword, username, password))
        self.conn.commit()
        return self.authenticate(username, newPassword)


    def register_session(self, dbfile):
        sid = base64.b64encode(os.urandom(16))
        while True:
            self.cursor.execute("select * from sessions where sessionId=?", (sid,))
            row = self.cursor.fetchone()
            if not row:
                # unique
                break
            sid = base64.b64encode(os.urandom(16))

        self.cursor.execute("delete from sessions where dbfile=?", (dbfile,))
        self.cursor.execute("insert into sessions (sessionId, dbfile) values (?,?)", (sid, dbfile))
        self.conn.commit()

        return sid


    def retrieve_session(self, sessionId):
        self.cursor.execute("select dbfile from sessions where sessionId=?", (sessionId,))
        row = self.cursor.fetchone()
        if row and row[0]:
            return row[0]


class DBHandle (object):
    """
    class to manage database connection properties and query execution
    ideally this could be replaced with another db backend without too much difficulty
    """

    dbfile = None

    def __init__ (self, dbfile='data.db'):

        self.dbfile = dbfile

        create_new = False
        if not os.path.exists(dbfile):
            create_new = True

        self.conn   = sqlite3.connect(dbfile)
        self.cursor = self.conn.cursor()

        if create_new:
            self.apply_schema()

        self.cursor.execute("select max(id) from accounts")
        row = self.cursor.fetchone()
        if row is None or row[0] is None:
            acctid = 0
        else:
            acctid = row[0]

        self.cursor.execute("select max(id) from xacts")
        row = self.cursor.fetchone()
        if row is None or row[0] is None:
            xactid = 0
        else:
            xactid = row[0]

        self.next_acctid = acctid + 1
        self.next_xactid = xactid + 1
    

    def apply_schema (self):

        # Create tables
        self.cursor.execute( """ create table accounts ( id int unique not null, name text not null, atype text not null) """ )
        self.cursor.execute( """ create table xacts ( id int unique not null, date text, description text ) """ )
        self.cursor.execute( """ create table account_debits ( acctid int not null, xid int not null, amount text not null) """ )
        self.cursor.execute( """ create table account_credits ( acctid int not null, xid int not null, amount text not null) """ )
        self.cursor.execute( """ CREATE TABLE closing_entries ( xid int not null ) """ )
        self.cursor.execute( """ CREATE TABLE qif_import ( end_date text, source_account text ) """ )
        self.cursor.execute( """ CREATE TABLE qif_patterns (acctid int not null, pattern text not null, rewrite text, cpty_acctid int not null) """ )
        self.cursor.execute( """ CREATE TABLE qif_pending (srcType text, srcName text, date text, amount text, description text) """ )
        self.cursor.execute( """ CREATE VIEW v_credits as select x.id, x.date, ac.acctid, a.atype, a.name, ac.amount, x.description from xacts x, accounts a, account_credits ac where x.id = ac.xid and a.id = ac.acctid """ )
        self.cursor.execute( """ CREATE VIEW v_debits  as select x.id, x.date, ad.acctid, a.atype, a.name, ad.amount, x.description from xacts x, accounts a, account_debits  ad where x.id = ad.xid and a.id = ad.acctid """ )
        self.cursor.execute( """ CREATE VIEW v_periods as select ce.xid, x.date from closing_entries ce, xacts x where ce.xid = x.id """ )

        # Save (commit) the changes
        self.conn.commit()
    

    def get_acctlist (self):
        self.cursor.execute( "select atype, name from accounts order by atype, name" )
        return(self.cursor.fetchall())
    

class QIFPattern (object):
    def __init__ (self, db):
        self.db = db
    
    def get_patterns (self, srcAcctType=None, srcAcctName=None):
        if srcAcctType and srcAcctName:
            self.db.cursor.execute( "select p.pattern, aa.atype, aa.name from accounts a, accounts aa, qif_patterns p where a.id = p.acctid and aa.id = p.cpty_acctid and a.atype=? and a.name=? order by a.atype, a.name, aa.atype, aa.name", (srcAcctType, srcAcctName) )
        else:
            self.db.cursor.execute( "select a.atype, a.name, p.pattern, aa.atype, aa.name from accounts a, accounts aa, qif_patterns p where a.id = p.acctid and aa.id = p.cpty_acctid order by a.atype, a.name, aa.atype, aa.name" )
        return(self.db.cursor.fetchall())


    def get_pending(self):
        self.db.cursor.execute( "select srcType, srcName, date, amount, description from qif_pending order by srcType, srcName, date" )
        return(self.db.cursor.fetchall())


    def del_pending(self, srcType, srcName, date, amount, description):
        self.db.cursor.execute("delete from qif_pending where srcType=? and srcName=? and date=? and amount=? and description=?", (srcType, srcName, date, amount, description))
        self.db.conn.commit()


class AccountData (object):

    def __init__ (self, db, atype, name, create=False):
        """
        check that the specified account exists
        create a stub for the account if it doesn't exist and create is True
        """
        self.db = db

        atype = atype.upper()

        acctid = self.account_exists(atype, name)

        if not acctid:
            if create:
                acctid = self.account_add(atype, name)
            else:
                raise ValueError("Account does not exist and create is False")

        self.atype  = atype
        self.name   = name
        self.acctid = acctid
    

    def account_exists (self, atype, name):
        """
        returns acctid or None
        """
        self.db.cursor.execute( "select id from accounts where atype=? and name=?", (atype, name) )
        row = self.db.cursor.fetchone()
        if row is not None:
            return row[0]
        return None
    

    def account_add (self, atype, name):
        acctid = self.db.next_acctid
        self.db.next_acctid += 1

        self.db.cursor.execute( "insert into accounts (id, name, atype) values (?, ?, ?)", (acctid, name, atype) )
        self.db.conn.commit()

        return acctid


    def get_xact_data (self, xtype=None):
        """
        xtype must be either 'debit' or 'credit'
        returns a tuple (total, data)
        total is the sum of the amounts
        data is a list of tuples (int(xid), D(amt), text(date), text(description))
        date text format is MM/DD/YYYY
        """
        if xtype == 'debit':
            tablename = 'v_debits'
            othername = 'v_credits'
        elif xtype == 'credit':
            tablename = 'v_credits'
            othername = 'v_debits'
        else:
            raise ValueError("xtype must be one of: debit, credit")

        self.db.cursor.execute("select v.id, v.amount, v.date, v.description,  a.name from %s v, %s o, accounts a where v.acctid=? and v.id = o.id and o.acctid = a.id order by v.date desc, v.id desc" % (tablename, othername), (self.acctid,) )

        data = self.db.cursor.fetchall()

        total = D(0)
        new_data = []
        for row in data:
            total += D(row[1])
            new_row = (row[0:1] + (row[1],) + row[2:])
            new_data.append(new_row)

        return(str(total), new_data)
    

    def add_qif_pattern (self, pattern, cpty_type, cpty_name, rewrite=''):
        """
        add a regex for this account into the qif_patterns
        table which maps records matching those patterns
        to the given counterparty account type/name
        """
        cpty_acctid = self.account_exists(cpty_type, cpty_name)

        if not cpty_acctid:
            return

        self.db.cursor.execute( """ insert into qif_patterns (acctid, pattern, rewrite, cpty_acctid) values (?, ?, ?, ?) """, (self.acctid, pattern, rewrite, cpty_acctid) )
        self.db.conn.commit()


    def del_qif_pattern (self, pattern, cpty_type, cpty_name):
        """
        remove a qif pattern
        """
        cpty_acctid = self.account_exists(cpty_type, cpty_name)

        if not cpty_acctid:
            return

        self.db.cursor.execute( """ delete from qif_patterns where acctid = ? and pattern = ? and cpty_acctid = ? """, (self.acctid, pattern, cpty_acctid) )
        self.db.conn.commit()


    def add_qif_pending(self, xacts):
        """
        xacts is a list of tuples suitable for passing as a parameter set to executemany()
        """
        self.db.cursor.executemany( """ INSERT into qif_pending (srcType, srcName, date, amount, description) values (?,?,?,?,?) """, xacts )
        self.db.conn.commit()


class XactData (object):

    def __init__ (self, db):
        self.db = db


    def load_xid_data (self, xid, xact):
        """
        loading xid credit/debit info from db
        called if xid was passed into the xact constructor
        xact is the actual xact instance
        """

        self.db.cursor.execute("""
                select
                    a.atype,
                    a.name,
                    x.amount
                from
                    accounts a,
                    account_credits x
                where
                    x.acctid = a.id
                    and xid=?
                order by atype, name
            """, (xid,) )

        for (atype, name, amt) in self.db.cursor:
            xact.add_credit(name, atype, D(amt))

        self.db.cursor.execute("""
                select
                    a.atype,
                    a.name,
                    x.amount
                from
                    accounts a,
                    account_debits x
                where
                    x.acctid = a.id
                    and xid=?
                order by atype, name
            """, (xid,) )

        for (atype, name, amt) in self.db.cursor:
            xact.add_debit(name, atype, D(amt))

        self.db.cursor.execute("select date, description from xacts where id=?", (xid,) )
        row = self.db.cursor.fetchone()
        if row is not None:
            (xact.date, xact.description) = row[:2]


    def add_xact_data (self, xtype=None, xid=None, amt=None):
        """
        adds transaction data to debit or credit file
        """
        if xtype not in ["debit", "credit"]:
            raise ValueError("xtype must be one of: debit, credit")

        if None in [xid, amt]:
            raise ValueError("xid, amt are both required")

        tablename = "account_%ss" % xtype

        self.db.cursor.execute("insert into ? (acctid, xid, amount) values (?, ?, ?)", (tablename, self.acctid, xid, str(amt)) )
        self.db.conn.commit()


    def save (self, create=False, date=None, description="", xact=None):
        """
        Called when ready to actually store the data built up in this transaction
        instance in the data files for the associated accounts.  Xact validation
        occurs here.

        The create flag will cause new accounts to be created if they do not exist already

        xact is the Xact instance (it passes self)
        """
        if not xact:
            raise ValueError("xact required")

        if not date:
            date = datetime.date.today()

        # don't allow the addition of new xacts prior to the date of the last close
        # to do so requires restating financial data for all periods closed after this new xact date
        self.db.cursor.execute( """ select date from v_periods order by xid desc limit 1 """ )
        row = self.db.cursor.fetchone()
        if row is not None:
            last_close = strToDate(row[0])
            dt_date = strToDate(date)
            if dt_date <= last_close:
                raise ValueError("Cannot add new transactions to an accounting period which has already been closed")

        xid = self.db.next_xactid
        self.db.next_xactid += 1

        date = normalize_date(date)

        try:
            self.db.cursor.execute("insert into xacts (id, date, description) values (?, ?, ?)", (xid, date, description) )

            for (name, atype, amt) in xact.debits:
                a = AccountData(self.db, atype, name, create)
                self.db.cursor.execute("insert into account_debits (acctid, xid, amount) values (?, ?, ?)", (a.acctid, xid, str(amt)) )

            for (name, atype, amt) in xact.credits:
                a = AccountData(self.db, atype, name, create)
                self.db.cursor.execute("insert into account_credits (acctid, xid, amount) values (?, ?, ?)", (a.acctid, xid, str(amt)) )

            if xact.closing:
                self.db.cursor.execute( "insert into closing_entries (xid) values (?)", (xid,) )
        except:
            self.db.conn.rollback()
            raise

        self.db.conn.commit()

