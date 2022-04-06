#!/usr/bin/env python

"""
crude qif file importer
expressions need to move into a db and have a ui built for them
needs to be restructured into a class, currently assumes specific filenames are present
needs unit tests
"""

import re
import acct
import qif

if __name__ == "__main__":
    already_done = []

    for source_account in ["Checking", "Savings"]:
        fname = "%s.qif" % source_account
        q=qif.QIF(filename=fname)

        xacts = q.sections[0]
        for xact in xacts:
            matched_account = None
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

            if not matched_account:
                raise ValueError("No Match: %s" % xact['payee'])

            (atype, aname) = matched_account.split(':', 1)

            if aname in already_done:
                continue

            amount = xact['amount']
                    
            x=acct.Xact()

            if amount > 0:
                # asset debit
                x.add_debit(source_account, "asset", amount)
                x.add_credit(aname, atype, amount)
            else:
                # asset credit
                amount = abs(amount)
                x.add_credit(source_account, "asset", amount)
                x.add_debit(aname, atype, amount)

    #        print("new %s xact: %s %s - %s" % (source_account, matched_account, amount, xact['payee']))
            x.save(create=True, date=xact['date'], description=xact['payee'])
        
        already_done.append(source_account)


map_payees = {
        'asset:Bullion':    {    'patterns': [    'Bullion Direct, Inc. Bill Payment',
                                                'BKOFAMERICA ATM 08/23 #000009325 DEPOSIT BROADWAY/WARREN NEW YORK NY',
                                                'BKOFAMERICA ATM 08/17 #000007950 DEPOSIT BROADWAY/WARREN NEW YORK NY',
                                            ],
                                'compiled': None,
                            },
        'expense:ATM':    {     'patterns':    ['WITHDRWL'],
                            'compiled': None
                        },
        'expense:Amex_Platinum':    {    'patterns': ['^AMERICAN EXPRESS DES:AM PMT ID:'],
                                        'compiled': None
                                    },
        'expense:BoA_Amex':    {    'patterns': [ 'Online Banking payment to CRD 1310' ],
                                'compiled': None
                            },
        'expense:Fees':    {    'patterns': [
                                    '^BANK OF AMERICA DES:TRIALCREDT'
                                ],
                            'compiled': None
                        },
        'revenue:Other_Income': {    'patterns': [    '^BKOFAMERICA ATM .* DEPOSIT',
                                                    'IRS DES:USATAXPYMT',
                                                    'NY STATE DES:TAX REFUND',
                                                    'Online Banking transfer from CHK 3050 .* TRIBBLE, MARCI',
                                                    'Online Banking transfer from SAV 8323 .* TRIBBLE, MARCI',
                                                    'Counter Credit',
                                                    'ORIGINS REAL EST DES:PAYMENT .* INDN:MATTHEW GEORGE',
                                                ],
                                    'compiled': None
                                },
        'revenue:Interest': {    'patterns': ['Interest Earned'],
                                'compiled': None
                            },
        'expense:Mortgage': {    'patterns': ['Bank of America DES:MORTGAGE'],
                                'compiled': None
                            },
        'expense:Discretionary': {    'patterns': [    '^CHECKCARD',
                                                    'Patrick George Bill Payment',
                                                ],
                                    'compiled': None
                                },
        'expense:Power': {    'patterns': ['^CON ED OF NY DES:INTELL CK ID:'],
                            'compiled': None
                        },
        'revenue:Salary': {    'patterns': [ 'GOLDMAN, SACHS & DES:PAYROLL' ],
                            'compiled': None
                        },
        'expense:Newton': {    'patterns': [    'Kirk Stansbury Bill Payment',
                                            'Origins Real Estate Bill Payment'
                                        ],
                            'compiled': None
                        },
        'asset:Savings': {    'patterns': [    'Online Banking transfer .* SAV 0488',
                                            'Online Banking transfer .* Sav 0488',
                                            'Online scheduled transfer .* Sav 0488',
                                        ],
                            'compiled': None
                        },
        'asset:Checking': {    'patterns':    [    'Online .* transfer .* CHK 8728' ],
                            'compiled': None
                        },
        'asset:PWM': {        'patterns': [ '^Check 60' ],
                            'compiled': None
                        },
        'expense:Rent': {    'patterns': [ 'Yon Kyong Yoo Bill Payment' ],
                            'compiled': None
                        },
        'expense:Phone': {    'patterns': [    'T-MOBILE Bill Payment',
                                            'T-Mobile Bill Payment'
                                        ],
                            'compiled': None
                        },
        'expense:Cable': {    'patterns': [    'TIME WARNER CABLE Bill Payment',
                                            'Time Warner Cable Bill Payment'
                                        ],
                            'compiled': None
                        },
    }


