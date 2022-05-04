#!/usr/bin/env python


"""
Quicken Interchange Format (QIF) parser - 4-digit year format

spec from http://en.wikipedia.org/wiki/Quicken_Interchange_Format
"""

import os, datetime
from decimal import Decimal

class QIF (object):
    
    map_header_types = {
            'Cash':     {'description': 'Cash Flow: Cash Account',        'account_type': 'EXPENSE'},
            'Bank':     {'description': 'Cash Flow: Checking Account',    'account_type': 'ASSET'},
            'CCard':     {'description': 'Cash Flow: Credit Card Account', 'account_type': 'LIABILITY'},
            'Invst':     {'description': 'Investing: Investment Account',  'account_type': 'ASSET'},
            'Oth A':     {'description': 'Property & Debt: Asset',         'account_type': 'ASSET'},
            'Oth L':     {'description': 'Property & Debt: Liability',     'account_type': 'LIABILITY'},
            'Cat':         {'description': 'Category list',                  'account_type': None },
            'Class':     {'description': 'Class list',                     'account_type': None },
            'Memorized':{'description': 'Memorized transaction list',     'account_type': None },
        }
    
    def __init__ (self, filename=None, qifFile=None):
        """
        filename needs to be a QIF 4-digit format file
        """

        if not qifFile and (not filename or not os.path.exists(filename)):
            raise ValueError("need valid filename")

        self.sections    = []
        curr_section     = None
        header_type_name = None
        header_type      = None
        curr_record      = None

        def _new_record ():
            record = {
                    'date':            None,
                    'amount':        None,
                    'cleared':        False,
                    'reconciled':    False
                }
            return(record)

        def _validate (record):
            if None in [record['date'], record['amount']]:
                raise ValueError("Record validation failure")

        if qifFile:
            f = qifFile
        else:
            f = open(filename)
        for line in [l.strip() for l in f.readlines()]:
            if line.startswith("!Type:"):
                # new section
                if curr_section:
                    self.sections.append(curr_section)
                curr_section = []
                curr_record = _new_record()
                header_type_name = line.split(':')[1]
                header_type = self.map_header_types[header_type_name]
                continue

            if not header_type:
                raise ValueError("invalid file: no header")

# i don't really understand this yet... T and N are also detail codes, so commented out for now
# maybe N or T but only if preceded by an !Account line or something?
#            if line[0] in ['!', 'N', 'T']:
#                # !Account, NAccount Name, TAccount Type
#                # Account list or which account follows
#                # Internal Quicken Information
#                raise ValueError("unimplemented: %s" % line)

            if line[0] == 'D':
                # Date. Leading zeroes on month and day can be skipped. Year can be either 4 digits or 2 digits or '6 (=2006).
                # D08/03/2011
                (month, day, year) = line[1:].split('/')
                curr_record['date'] = datetime.date(month=int(month), day=int(day), year=int(year))

            elif line[0] == 'T':
                # Amount of the item. For payments, a leading minus sign is required. For deposits, either no sign or a leading
                # plus sign is accepted. Do not include currency symbols. Comma separators between thousands are allowed.
                # T-1,234.50
                curr_record['amount'] = Decimal(line[1:].replace(',', ''))

            elif line[0] == 'M':
                # Memo-any text you want to record about the item.
                # Mgasoline for my car
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'C':
                # Cleared status. Values are blank (not cleared), "*" or "c" (cleared) and "X" or "R" (reconciled).
                # CR
                if line == 'C':
                    continue
                if line[1] in ['*', 'c']:
                    curr_record['cleared'] = True
                elif line[1] in ['X', 'R']:
                    curr_record['cleared'] = True
                    curr_record['reconciled'] = True

            elif line[0] == 'N':
                if header_type_name in ['Bank', 'Splits']:
                    # Number of the check. Can also be "Deposit", "Transfer", "Print", "ATM", "EFT".
                    # N1001
                    curr_record['check_number'] = int(line[1:])
                elif header_type_name == 'Invst':
                    # Investment Action (Buy, Sell, etc.).
                    # NBuy
                    raise ValueError("unimplemented: %s" % line)
                else:
                    raise ValueError("wrong header type for Detail Item: %s" % line)

            elif line[0] == 'P':
                if header_type_name not in ['Bank', 'Invst']:
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Payee. Or a description for deposits, transfers, etc.
                # PStandard Oil, Inc.
                curr_record['payee'] = line[1:]

            elif line[0] == 'A':
                if header_type_name not in ['Bank', 'Splits']:
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Address of Payee. Up to 5 address lines are allowed. A 6th address line is a message that prints
                # on the check. 1st line is normally the same as the Payee line-the name of the Payee.
                # A101 Main St.
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'L':
                if header_type_name not in ['Bank', 'Splits']:
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Category or Transfer and (optionally) Class. The literal values are those defined in the Quicken Category list.
                # SubCategories can be indicated by a colon (":") followed by the subcategory literal. If the Quicken file uses Classes,
                # this can be indicated by a slash ("/") followed by the class literal. For Investments, MiscIncX or MiscExpX actions,
                # Category/class or transfer/class.
                # LFuel:car
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'F':
                if header_type_name != 'Bank':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Flag this transaction as a reimbursable business expense.
                # F???
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'S':
                if header_type_name != 'Splits':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Split category. Same format as L (Categorization) field.
                # Sgas from Esso
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'E':
                if header_type_name != 'Splits':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Split memo-any text to go with this split item.
                # Ework trips
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == '$':
                if header_type_name != 'Splits':
                    # Amount for this split of the item. Same format as T field.
                    # $1,000.50
                    raise ValueError("unimplemented: %s" % line)
                elif header_type_name != 'Invst':
                    # Amount transferred, if cash is moved between accounts
                    # $25,000.00
                    raise ValueError("unimplemented: %s" % line)
                else:
                    raise ValueError("wrong header type for Detail Item: %s" % line)

            elif line[0] == '%':
                if header_type_name != 'Splits':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Percent. Optional-used if splits are done by percentage.
                # %50
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'Y':
                if header_type_name != 'Invst':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Security name.
                # YIDS Federal Income
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'I':
                if header_type_name != 'Invst':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Price.
                # I5.125
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'Q':
                if header_type_name != 'Invst':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Quantity of shares (or split ratio, if Action is StkSplit).
                # Q4,896.201
                raise ValueError("unimplemented: %s" % line)

            elif line[0] == 'O':
                if header_type_name != 'Invst':
                    raise ValueError("wrong header type for Detail Item: %s" % line)

                # Commission cost (generally found in stock trades)
                # O14.95
                raise ValueError("unimplemented: %s" % line)

            elif line == '^':
                # End of Record
                _validate(curr_record) # will raise
                curr_section.append(curr_record)
                curr_record = _new_record()

            else:
                # unknown
                raise ValueError("unimplemented: %s" % line)


        if curr_section:
            self.sections.append(curr_section)

        f.close()

