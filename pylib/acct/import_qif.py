#!/usr/bin/env python

"""
crude qif file importer
expressions need to move into a db and have a ui built for them
needs to be restructured into a class, currently assumes specific filenames are present
needs unit tests
"""

import acct
import config
import os
import qif
import re
import sys
from sqldata import DBHandle
from payeeMap import map_payees

if __name__ == "__main__":
    print("QIF import started with args: %s" % sys.argv)
    try:
        qifInput = sys.argv[1:]
    except IndexError:
        print("ERR: Must supply QIF input files as commandline arguments")
        sys.exit(1)
    already_done = []
    db = DBHandle(dbfile=os.path.join(config.DBDIR, 'data.db.mdgnew'))

    for fname in qifInput:
        source_account = fname.replace('.qif', '')
        q=qif.QIF(filename=fname)

        xacts = q.sections[0]
        for xact in xacts:
            matched_account = None
            if q.account_type != 'LIABILITY':
                for account in map_payees:
                    if not map_payees[account]['compiled']:
                        map_payees[account]['compiled'] = []
                        for pattern in map_payees[account]['patterns']:
                            map_payees[account]['compiled'].append(re.compile(pattern))
                    for pattern in map_payees[account]['compiled']:
                        if pattern.search(xact['payee']):
                            matched_account = account
                            break
                    if matched_account:
                        break

            amount = xact['amount']

            if not matched_account:
                if q.account_type == 'LIABILITY':
                    # normal balance type is inverted
                    if amount > 0:
                        matched_account = 'EXPENSE:Exp_-_Default'
                        if 'memo' in xact:
                            try:
                                matched_account = 'expense:%s' % xact['memo'].decode('ascii')
                            except UnicodeDecodeError:
                                pass
                    else:
                        matched_account = 'ASSET:Checking'
                else:
                    if amount > 0:
                        matched_account = 'REVENUE:Rev_-_Default'
                    else:
                        matched_account = 'EXPENSE:Exp_-_Default'

            (atype, aname) = matched_account.split(':', 1)

            if aname in already_done:
                continue

            x=acct.Xact(db)

            if q.account_type == 'LIABILITY':
                if amount > 0:
                    x.add_credit(source_account, q.account_type, amount)
                    x.add_debit(aname, atype, amount)
                else:
                    amount = abs(amount)    # no negative values
                    x.add_debit(source_account, q.account_type, amount)
                    x.add_credit(aname, atype, amount)
            else:
                if amount > 0:
                    # asset debit
                    x.add_debit(source_account, q.account_type, amount)
                    x.add_credit(aname, atype, amount)
                else:
                    # asset credit
                    amount = abs(amount)    # no negative values
                    x.add_credit(source_account, q.account_type, amount)
                    x.add_debit(aname, atype, amount)

            print("new %s (%s) xact: %s %s - %s" % (source_account, q.account_type, matched_account, amount, xact['payee']))
            x.save(create=True, date=xact['date'], description=xact['payee'])
        
        already_done.append(source_account)


