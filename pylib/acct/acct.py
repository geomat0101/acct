#!/usr/bin/env python

"""
	this is the accounting package
	we'll start off with some basic definitions

	The Basic Accounting Equation
	Assets = Liabilities + Owners' Equity
	An org's assets are equal to its equities

	typical assets:
	cash, accounts receivable, equipment, land, buildings, inventory, investments

	equities: claims to assets (e.g. by owners, lenders)

	ownership claims to assets are called:
	owners' equity if unincorporated
	stockholders' equity if a corporation

	liabilities: claims of outside parties (banks, suppliers)

	balance sheet has assets on the left, liabilities / owners' equity on the right

	revenue and expenses impact owners' equity
	revenues increase it; expenses reduce it

	balances
	add up the debits and credits, subtract the smaller from the larger
	balance is referred to as debit or credit balance based on which side is larger
	Normal Balance Types
		Asset		Debit
		Liability	Credit
		Equity		Credit
		Revenue		Credit
		Expense		Debit

	Trial Balance
	a listing of all accounts with their debit and credit balances
	prepared at the end of an accounting period
	first step in developing financial statements
	it's "in balance" when sum of credit balances == sum of debit balances
	How to:
		Determine the balance of each account
		List all accounts, placing debit and credit balances in separate columns
		sum debits and credit balances separately
		compare the total of the debit and credit columns


	Adjustments

	Prepaids
	You may have noticed that prepaid expenses are listed as assets.  why does that make sense?
	This is because the bill hasn't actually come due yet, so no money has been spent yet!
	At the end of each accounting period, accruals and adjustments are made which
	reflect the actual expense during the period
	Example: 4800 for a 2-year insurance policy goes into a prepaid insurance asset account
	Each month the bill is 200, so for each monthly accounting period an adjustment
	is made which debits an insurance expense account and credits the prepaid insurance asset

	Inventory / Cost of Goods Sold
	What you bought during the accounting period is not necessarily your cost of goods,
	as you started with some inventory and ended up with some
	Beginning inventory + purchases - ending inventory = cost of goods
	If you end up with more inventory than you started with, then your adjustment will
	credit the inventory asset account and debit the cost of goods expense account

	Depreciation
	annual depreciation = (original cost - salvage value) / useful life expectancy
	to record the adjustment, you debit the depreciation expense account and credit the
	accumulated depreciation asset account
	accumulated depreciation is actually a contra-asset account, which is an asset account
	that normally has a credit balance and is used to offset specific asset accounts


	Accruals

	Payroll
	At the end of the month, employees may have worked some time for which they have not yet
	been paid.  GAAP says this needs to be reflected in the period where the expense is
	incurred.  The adjustment is a debit to the payroll expense account and a credit to the
	accrued payroll liability account. related expenses like FICA, unemployment taxes should
	be included as it is all money owed.

	Interest
	like payroll accruals, this is interest expenses for loans incurred during the period
	but not paid.  interest = remaining principal * rate * time
	time is length of accounting period / days in the year (assuming interest is APR)
	The adjustment is a debit to the interest expense account and a credit to the accrued
	interest liability account.


	Financial statements (post-adjustments)
	balance sheet: biz's assets and claims to its assets
	income statement: revenues and expenses for the current accounting period
	net income and losses are added/deducted from owners' equity prior to preparing the balance sheet
	the income statement is based on revenue and expense accounts
	those are then closed out to the owners' equity accounts (or retained earnings)
	the balance sheet is then based on the asset, liability, and equity accounts

	owners' equity withdrawls
	owners may withdraw funds for personal use
	use a temporary owners' equity account titled (Owner), Withdrawals
	this account is not an expense account and should not appear on the income statement
	it is closed to the owners' equity account at the end of the period

	dividends
	a corporation's board of directors may declare a dividend
	debit retained earnings and credit dividends payable (liability account)


	The accounting cycle

	Journalizing
	process of analyzing and classifying transactions
	most common is the general journal
	all adjustments and closing entries are recorded in the general journal

	Posting
	the recording of debits and credits from journals to the proper accounts
	most common and comprehensive is the general ledger, which consists of
	accounts for all assets, liabilities, equity, revenues, and expenses

	Trial Balance
	proves that debits equal credits
	conducted just prior to recording adjustments
	if the debits and credits are not equal, the reason must be determined
	and fixed before making any adjustments

	Adjustments
	inventory, prepaid expenses, depreciation, accruals
	after recording in the journal, they must be posted to the ledger accounts

	Adjusted Trial Balance
	checks that adjusting entries have been properly posted

	Financial Statements
	balance sheet and income statement
	prepared directly from either the adjusted trial balance or from the ledger accounts
	may also prepare other statements like cash flow, retained earnings, etc at this time

	Closing Temporary Proprietorship Accounts
	record and post the closing entries
	revenue, expense, and withdrawal accounts are closed with entries that clear them
	so that operating results and withdrawals of the following period can be recorded

	Post-Closing Trial Balance
	tests the equality of debit and credit accounts again
	only has asset, liability, and equity accounts since everything else has been closed
"""


import os
import sqldata
from decimal import Decimal as D

account_types = ['ASSET', 'EQUITY', 'EXPENSE', 'LIABILITY', 'REVENUE']

class Account (object):
	"""
	transactions are recorded in accounts

	Types and example groupings of accounts
	Asset
	  cash on hand (cash on hand / safe / registers / etc)
	  cash on deposit (cash in bank, separate account per bank account)
	  accounts receivable (cash due from guests)
	  allowance for doubtful accounts
	  notes receivable (promisory notes from employees)
	  inventory
	  marketable securities (short-term cash investments)
	  prepaid expenses (rent, licenses, insurance (all separate accounts))
	  investments (long-term stocks and bonds, generally reported at cost)
	  land
	  buildings
	  equipment
	  furniture
	  china/glassware/silver/linen (or could be expensed)
	  accumulated depreciation
	  deposits (e.g. utility deposits)
	Liability
	  accounts payable - trade (ordinary amounts due to suppliers, normal biz expenses)
	  accounts payable - other (equipment, non-standard expenses)
	  notes payable
	  taxes payable (one per type of tax)
	  deposits from guests for future events
	  accrued expenses (amts payable for expenses incurred at or near the end of an 
		  accounting period including accrued payroll, utilities, interest, rent)
	  dividends payable
	  long-term debt (debt not due for 12 months from the balance sheet date)
	Equity
	  Non-incorporated
		  (Name of Proprietor or Partner), Capital: owner's net worth in the restaurant
			  this is the initial investment less withdrawls and operating losses plus profits
	  Corporations
		  capital stock (one per type of stock issued)
		  paid-in capital in excess of par (proceeds from sale of capital stock in excess of the par value)
		  retained earnings

	Revenue accounts
	  food, beverage, other, interest income, dividend income

	Expense accounts
	  food cost, uniforms, supplies, laundry, decor, rent, utilites, depreciation (non-accumulated), etc

	Revenue and expense accounts are really temporary owners' equity accounts
	they are closed out each period to the permanent owners' equity accounts
	"""

	def __init__ (self, db, name=None, atype=None, create=False):
		"""
		>>> a = Account()
		Traceback (most recent call last):
		ValueError: missing required argument (name, atype)
		>>> a = Account("test")
		Traceback (most recent call last):
		ValueError: missing required argument (name, atype)
		>>> a = Account("test", "test")
		Traceback (most recent call last):
		ValueError: invalid account type
		>>> a = Account("test", "asset")
		Traceback (most recent call last):
		ValueError: Account does not exist and create is False
		>>> a = Account("test", "asset", create=True)
		>>> a.name
		'test'
		>>> a.atype
		'ASSET'
		"""
		self.db = db
		# check args
		if None in [name, atype]:
			raise ValueError("missing required argument (name, atype)")
		atype = atype.upper()
		if atype not in account_types:
			raise ValueError("invalid account type")

		# set instance vars
		name = name.replace(' ', '_')
		self.name = name
		self.atype = atype

		self.data = sqldata.AccountData(self.db, atype, name, create)

		(self.total_debits, self.debits)   = self.data.get_xact_data(xtype='debit')
		(self.total_credits, self.credits) = self.data.get_xact_data(xtype='credit')

		self._recompute_balance()


	def _recompute_balance (self):
		"""
		should be called any time the value of total_debits or total_credits changes
		"""
		self.debit_balance  = ""
		self.credit_balance = ""

		credit = D(self.total_credits)
		debit  = D(self.total_debits)

		if debit > credit:
			self.debit_balance = "%0.2f" % (debit - credit)
			if self.debit_balance == "0.00":
				self.debit_balance = ""
		elif credit > debit:
			self.credit_balance = "%0.2f" % (credit - debit)
			if self.credit_balance == "0.00":
				self.credit_balance = ""

	
	def _add_data (self, xtype=None, xid=None, amt=None, commit=False):
		"""
		adds transaction data to debit or credit file
		commit is deprecated as transactionality is now handled by the dbdata module
		"""
		if None in [xtype, xid, amt]:
			raise ValueError("missing required argument (xtype, xid, amt)")
		
		if xtype not in ["debit", "credit"]:
			raise ValueError("xtype must be one of: debit, credit")

		if type(xid) != type(0):
			# must be int
			raise ValueError("xid must be an integer")

		if type(amt) != type(D(0)):
			amt = D(amt)

		# input validated, add the data to existing
		if xtype == 'debit':
			self.debits += [(xid, amt)]
			self.total_debits = D(self.total_debits) + amt
		elif xtype == 'credit':
			self.credits += [(xid, amt)]
			self.total_credits = D(self.total_credits) + amt
		self._recompute_balance()


	def add_debit (self, xid=None, amt=None, commit=False):
		"""
		debit the account
		"""
		if None in [xid, amt]:
			raise ValueError("missing required argument (xid, amt)")

		self._add_data(xtype="debit", xid=xid, amt=amt, commit=commit)


	def add_credit (self, xid=None, amt=None, commit=False):
		"""
		credit the account
		"""
		if None in [xid, amt]:
			raise ValueError("missing required argument (xid, amt)")

		self._add_data(xtype="credit", xid=xid, amt=amt, commit=commit)
	

class Xact (object):
	"""
	all transactions affect the basic accounting equation
	there are 9 enumerated types of accounting transactions
		Increase one asset and decrease another asset
			buy equipment: Dr. Equipment, Cr. Cash
		Increase an asset and increase a liability
			borrow cash from the bank: Dr. Cash, Cr. Notes payable
		Increase an asset and increase an owners' equity account
			owner invests in the biz: Dr. Cash, Cr. Owner capital
		Increase one liability and decrease another liability
			a note is made in exchange for an account payable: Dr. Accounts payable, Cr. Notes payable
		Decrease a liability and decrease an asset
			pay a supplier: Dr. Accounts payable, Cr. Cash
		Increase a liability and decrease an owners' equity account
			dividends declared: Dr. Retained earnings and Cr. Dividends payable
		Decrease an asset and decrease an owners' equity account
			owner withdraws cash: Dr. Owner capital and Cr. Cash
		Decrease a liability and increase an owners' equity account
			long-term debt owed to the owner is converted to equity: Dr. Long-term debt, Cr. Owner capital
		Increase an owners' equity account and decrease another owners' equity account
			preferred stock converted to common stock: Dr. preferred, Cr. common

	PROHIBITED TRANSACTIONS are those that ONLY:
		increase an asset and decrease a liability
		decrease an asset and increase a liability
		increase a liability and increase an owners' equity account
		decrease a liability and decrease an owners' equity account
		decrease an asset and increase an owners' equity account
		increase an asset and decrease an owners' equity account

	how to determine entries in recording a transaction
		determine which accounts are affected
		determine whether to debit or credit the accounts
		determine the amounts to be recorded
	
	debits are entries made on the left side of a T account
	credits are entries made on the right side of a T account
	either of these can be an increase or decrease to the account depending on type

	debit/credit (Dr./Cr.) account relationships:
	   ASSETS     LIABILITIES    EQUITY     REVENUES     EXPENSES
	   -------    -----------    -------    ---------    ---------
	    + | -        - | +        - | +       - | +        + | -
	   Dr.|Cr.     Dr. | Cr.     Dr.|Cr.    Dr. | Cr.    Dr. | Cr.

	in a transaction, sum(debits) == sum(credits)

	The six classes of prohibited transactions cannot occur as long as debits
	and credits are balanced with each other.


	IMPLEMENTATION NOTES

	Get a new xact instance and call add_[credit|debit] as appropriate
	to build up the intended effect on the underlying accounts.

	For example, if you buy something for 10k with 7500/2500 loan/cash,
	you debit that asset for 10k, credit the cash account for 2500, and credit
	the loan's liability account for 7500.

	Once all the credits and debits have been entered, you call the save
	method. The transaction will be validated, and it will be passed to the
	various debit/credit methods for the underlying accounts twice.  The first
	time, the commit flag is False, so if there are any issues trying to add
	the data to the account, an appropriate exception will be raised.  If that
	completes ok then the commit flag is turned on and the data is sent again
	for actual storage.
	"""

	def __init__ (self, db, xid=None, closing=False):
		"""
		create a blank transaction
		FIXME: needs locking to guarantee xid uniqueness (fcntl.flock?)
		>>> x=Xact()
		>>> x.total_credits
		Decimal('0')
		>>> x.total_debits
		Decimal('0')
		>>> x.add_debit("cash", "asset", D('5000.00'))
		>>> x.save()
		Traceback (most recent call last):
		ValueError: XACT INVALID: credits/debits must equal each other (0.00/5000.00)
		>>> x.add_credit("capital", "equity", D('5000.00'))
		>>> x.total_credits
		Decimal('5000.00')
		>>> x.total_debits
		Decimal('5000.00')
		>>> x.save()
		Traceback (most recent call last):
		ValueError: Account does not exist and create is False
		>>> x.save(create=True)
		"""
		self.db = db

		self.closing = closing
		self.credits = []
		self.debits  = []
		self.total_credits = D(0)
		self.total_debits  = D(0)
		self.date = None
		self.description = ""
		self.data = sqldata.XactData(self.db)

		self.readonly = False
		if xid is not None:
			# retrieving a prior transaction
			self.readonly = True
			self.data.load_xid_data(xid, self)	# horrible calling convention

		# needs basic xact auditing details, e.g. who/when
	

	def add_credit (self, acctname, atype, amt):
		self.credits += [(acctname, atype, amt)]
		self.total_credits += amt
	

	def add_debit (self, acctname, atype, amt):
		self.debits += [(acctname, atype, amt)]
		self.total_debits += amt
	

	def save (self, create=False, date=None, description=""):
		"""
		Called when ready to actually store the data built up in this transaction
		instance in the data files for the associated accounts.  Xact validation
		occurs here.

		The create flag will create new accounts if they do not exist already
		"""
		if self.readonly:
			raise ValueError("ERROR: TRYING TO MODIFY READONLY TRANSACTION")

		if "%0.2f" % self.total_credits != "%0.2f" % self.total_debits:
			raise ValueError("XACT INVALID: credits/debits must equal each other (%0.2f/%0.2f)" % (self.total_credits, self.total_debits))

		# use a bogus xid for the pre-commit test
		xid = -1
		for (name, atype, amt) in self.credits:
			a = Account(self.db, name=name, atype=atype, create=create)
			a.add_credit(xid=xid, amt=amt, commit=False)
		for (name, atype, amt) in self.debits:
			a = Account(self.db, name=name, atype=atype, create=create)
			a.add_debit(xid=xid, amt=amt, commit=False)

		self.data.save(create, date, description, self)		# Horrible calling convention again


if __name__ == '__main__':
	import doctest
	# clean up prior test data
	if os.path.exists("testdata.db"):
		os.unlink("testdata.db")
	# don't pollute prod data
	sqldata.db = sqldata.DBHandle(dbfile='testdata.db')
	doctest.testmod()

