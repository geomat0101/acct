#!/usr/bin/python -i

from acct import *
import sqldata
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import pango
import numpy as np

from matplotlib.figure import Figure
from matplotlib.axes import Subplot
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import matplotlib.pyplot as plt


type_display = {}
for atype in ['ASSET', 'EXPENSE']:
	type_display[atype] = {}
	type_display[atype]['debit']  = '+'
	type_display[atype]['credit'] = '-'
for atype in ['EQUITY', 'LIABILITY', 'REVENUE']:
	type_display[atype] = {}
	type_display[atype]['debit']  = '-'
	type_display[atype]['credit'] = '+'


class acctui (object):

	ui = gtk.glade.XML("acctui.glade")
	win = ui.get_widget("window1")

	# account tab widgets
	tv_acctlist = ui.get_widget("treeview1")
	tv_acctlist_select_id = None
	tv_a_debits = ui.get_widget("treeview2")
	tv_a_debits_select_id = None
	tv_a_credits  = ui.get_widget("treeview3")
	tv_a_credits_select_id = None

	accounts = {}

	# transaction tab widgets
	cal_xactdate = ui.get_widget("calendar1")
	ck_create    = ui.get_widget("checkbutton1")
	btn_execute  = ui.get_widget("button3")
	btn_cancel   = ui.get_widget("button4")
	txt_desc     = ui.get_widget("entry3")
	txt_xid		 = ui.get_widget("entry5")
	btn_find     = ui.get_widget("button5")
	btn_back     = ui.get_widget("button6")
	btn_fwd      = ui.get_widget("button7")
	# advanced
	cb_d_atype   = ui.get_widget("combobox1")
	cbe_d_name   = ui.get_widget("comboboxentry1")
	txt_d_amt    = ui.get_widget("entry1")
	btn_d_ok     = ui.get_widget("button1")
	tv_x_debits  = ui.get_widget("treeview4")
	tv_x_debits_select_id = None
	cb_c_atype   = ui.get_widget("combobox2")
	cbe_c_name   = ui.get_widget("comboboxentry2")
	txt_c_amt    = ui.get_widget("entry2")
	btn_c_ok     = ui.get_widget("button2")
	tv_x_credits = ui.get_widget("treeview5")
	tv_x_credits_select_id = None
	# simple
	cb_ds_atype = ui.get_widget("combobox4")
	cbe_ds_name = ui.get_widget("comboboxentry3")
	cb_cs_atype = ui.get_widget("combobox5")
	cbe_cs_name = ui.get_widget("comboboxentry4")
	txt_s_amt   = ui.get_widget("entry4")

	# income statement tab
	tv_is_x = ui.get_widget("treeview6")
	tv_is_r = ui.get_widget("treeview7")
	btn_prep_close = ui.get_widget("button8")

	# balance sheet tab
	tv_bs_a = ui.get_widget("treeview8")
	tv_bs_l = ui.get_widget("treeview9")

	# docs tab
	cb_doc_topic = ui.get_widget("combobox3")
	txt_doc      = ui.get_widget("textview1")
	font_desc = pango.FontDescription("monospace normal 10")
	txt_doc.modify_font(font_desc)


	def __init__ (self):
		self.db = sqldata.db = DBHandle('data.db')

		# add columns for treeviews
		self.tv_acctlist.append_column(gtk.TreeViewColumn('Type', gtk.CellRendererText(), text=0))
		self.tv_acctlist.append_column(gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1))
		self.tv_acctlist.append_column(gtk.TreeViewColumn('Debit Balance', gtk.CellRendererText(), text=2))
		self.tv_acctlist.append_column(gtk.TreeViewColumn('Credit Balance', gtk.CellRendererText(), text=3))

		self.tv_a_debits.append_column(gtk.TreeViewColumn('Date', gtk.CellRendererText(), text=0))
		self.tv_a_debits.append_column(gtk.TreeViewColumn('Amt', gtk.CellRendererText(), text=1))
		self.tv_a_debits.append_column(gtk.TreeViewColumn('From', gtk.CellRendererText(), text=2))
		self.tv_a_debits.append_column(gtk.TreeViewColumn('Description', gtk.CellRendererText(), text=3))
		self.tv_a_debits.append_column(gtk.TreeViewColumn('XID', gtk.CellRendererText(), text=4))

		self.tv_a_credits.append_column(gtk.TreeViewColumn('Date', gtk.CellRendererText(), text=0))
		self.tv_a_credits.append_column(gtk.TreeViewColumn('Amt', gtk.CellRendererText(), text=1))
		self.tv_a_credits.append_column(gtk.TreeViewColumn('To', gtk.CellRendererText(), text=2))
		self.tv_a_credits.append_column(gtk.TreeViewColumn('Description', gtk.CellRendererText(), text=3))
		self.tv_a_credits.append_column(gtk.TreeViewColumn('XID', gtk.CellRendererText(), text=4))

		self.tv_x_debits.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_x_debits.append_column(gtk.TreeViewColumn('Type', gtk.CellRendererText(), text=1))
		self.tv_x_debits.append_column(gtk.TreeViewColumn('Amount', gtk.CellRendererText(), text=2))

		self.tv_x_credits.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_x_credits.append_column(gtk.TreeViewColumn('Type', gtk.CellRendererText(), text=1))
		self.tv_x_credits.append_column(gtk.TreeViewColumn('Amount', gtk.CellRendererText(), text=2))

		self.tv_is_x.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_is_x.append_column(gtk.TreeViewColumn('Balance', gtk.CellRendererText(), text=1))

		self.tv_is_r.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_is_r.append_column(gtk.TreeViewColumn('Balance', gtk.CellRendererText(), text=1))

		self.tv_bs_a.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_bs_a.append_column(gtk.TreeViewColumn('Balance', gtk.CellRendererText(), text=1))

		self.tv_bs_l.append_column(gtk.TreeViewColumn('Account', gtk.CellRendererText(), text=0))
		self.tv_bs_l.append_column(gtk.TreeViewColumn('Balance', gtk.CellRendererText(), text=1))
		
		# accounts
		font_desc = pango.FontDescription("bold 16")
		self.ui.get_widget("label8").modify_font(font_desc)
		font_desc = pango.FontDescription("monospace")
		self.ui.get_widget("label9").modify_font(font_desc)

		self.load_acctlist()

		# transactions
		self.xact_reset()

		for cb in [self.cb_d_atype, self.cb_ds_atype]:
			d_atype_liststore = gtk.ListStore(str)
			cb.set_model(d_atype_liststore)
			cb.set_model(d_atype_liststore)
			cell = gtk.CellRendererText()
			cb.pack_start(cell, True)
			cb.add_attribute(cell, 'text', 0)
			cb.append_text('ASSET (+)')
			cb.append_text('LIABILITY (-)')
			cb.append_text('EQUITY (-)')
			cb.append_text('REVENUE (-)')
			cb.append_text('EXPENSE (+)')

			cb.connect("changed", self.d_atype_changed)
		self.btn_d_ok.connect("clicked", self.d_ok_clicked)

		for cb in [self.cb_c_atype, self.cb_cs_atype]:
			c_atype_liststore = gtk.ListStore(str)
			cb.set_model(c_atype_liststore)
			cell = gtk.CellRendererText()
			cb.pack_start(cell, True)
			cb.add_attribute(cell, 'text', 0)
			cb.append_text('ASSET (-)')
			cb.append_text('LIABILITY (+)')
			cb.append_text('EQUITY (+)')
			cb.append_text('REVENUE (+)')
			cb.append_text('EXPENSE (-)')

			cb.connect("changed", self.c_atype_changed)
		self.btn_c_ok.connect("clicked", self.c_ok_clicked)

		self.btn_execute.connect("clicked", self.btn_execute_clicked)
		self.btn_cancel.connect("clicked", self.xact_reset)

		self.btn_find.connect("clicked", self.show_xact)
		self.btn_back.connect("clicked", self.show_xact)
		self.btn_fwd.connect("clicked", self.show_xact)
	
		# income statement
		self.load_income_statement()
		self.btn_prep_close.connect("clicked", self.prepare_closing_xact)

		# balance sheet
		self.load_balance_sheet()

		# docs
		self.cb_doc_topic.connect("changed", self.load_doc_topic)

		# charts
		self.box_chart = self.ui.get_widget("vbox140")
		self.cb_chart = self.ui.get_widget("combobox6")
		self.cb_chart.connect("changed", self.new_chart)
		self.chart_canvas = None

	
	def new_chart (self, widget=None):
		self.chart_canvas = self.plant_chart(atype=self.cb_chart.get_active_text(), can=self.chart_canvas)


	def plant_chart (self, figure=None, box=None, can=None, atype=None):
		""" 
		stick the new chart where it belongs
		removes the previous one if needed
		defaults to chart tab plot if box (vbox/hbox) not supplied
		returns the canvas object, caller needs to supply this for subsequent calls
		e.g.
			c = plant_chart(can=None)
			c = plant_chart(can=c)
		"""
		if box is None:
			box = self.box_chart

		if can is not None:
			can.parent.remove(can)

		figure = plt.figure()
		ax = figure.add_subplot(111)

		debits  = []
		credits = []
		labels  = []
		if not atype:
			atype = 'EXPENSE'
		else:
			atype = atype.upper()

		if atype not in self.accounts:
			return

		accts = self.accounts[atype]
		for acctname in accts:
			acct = accts[acctname]
			if acct.total_debits == '':
				debits.append(D(0))
			else:
				debits.append(D(acct.total_debits))

			if acct.total_credits == '':
				credits.append(D(0))
			else:
				credits.append(D(acct.total_credits))

			labels.append(acctname)
				
		ind = np.arange(len(debits))
		width = 0.35
		if atype in ['LIABILITY', 'ASSET']:
			debit_color  = 'g'
			credit_color = 'r'
		else:
			debit_color  = 'r'
			credit_color = 'g'
		r1 = ax.bar(ind, debits, width, color=debit_color)
		r2 = ax.bar(ind+width, credits, width, color=credit_color)
		plt.xticks(ind+width, labels)

		can = FigureCanvas(figure)
		box.pack_start(can, True, True)
		can.show()
		return can 


	def load_doc_topic (self, widget=None):
		topic = self.cb_doc_topic.get_active_text()
		buf = gtk.TextBuffer()
		if topic == 'General':
			from acct import __doc__ as moddoc
			buf.set_text(moddoc)
		if topic == 'Accounts':
			buf.set_text(Account.__doc__)
		if topic == 'Transactions':
			buf.set_text(Xact.__doc__)

		self.txt_doc.set_buffer(buf)
		

	def load_income_statement (self):
		x_list = gtk.ListStore(str, str)
		x_total = D(0)
		if 'EXPENSE' in self.accounts:
			for a in sorted(self.accounts['EXPENSE'].keys()):
				curracct = self.accounts['EXPENSE'][a]
				if curracct.debit_balance != "":
					# normal
					x_total += D(curracct.debit_balance)
					x_list.append([a, curracct.debit_balance])
				elif curracct.credit_balance != "":
					# abnormal
					x_total -= D(curracct.credit_balance)
					x_list.append([a, "(%s)" % curracct.credit_balance])

		self.tv_is_x.set_model(x_list)

		r_list = gtk.ListStore(str, str)
		r_total = D(0)
		if 'REVENUE' in self.accounts:
			for a in sorted(self.accounts['REVENUE'].keys()):
				curracct = self.accounts['REVENUE'][a]
				if curracct.credit_balance != "":
					# normal
					r_total += D(curracct.credit_balance)
					r_list.append([a, curracct.credit_balance])
				elif curracct.debit_balance != "":
					# abnormal
					r_total -= D(curracct.debit_balance)
					r_list.append([a, "(%s)" % curracct.debit_balance])

		self.tv_is_r.set_model(r_list)

		self.net_income = r_total - x_total
		self.ui.get_widget("label21").set_text("\nTotal Revenue:\t%0.2f\nTotal Expenses:\t%0.2f\nNet Income:\t\t%0.2f\n\n" % (r_total, x_total, self.net_income))
	

	def prepare_closing_xact (self, widget=None):
		"""
		This creates a transaction which closes all expense and revenue accounts out to
		an equity account named 'Owners_Equity'.
		"""
		self.xact_reset(closing=True)
		x_total = D(0)
		if 'EXPENSE' in self.accounts:
			for a in sorted(self.accounts['EXPENSE'].keys()):
				curracct = self.accounts['EXPENSE'][a]
				if curracct.debit_balance != "":
					# normal
					x_total += D(curracct.debit_balance)
					self._xact_add_credit('EXPENSE', a, curracct.debit_balance)
				elif curracct.credit_balance != "":
					# abnormal
					x_total -= D(curracct.credit_balance)
					self._xact_add_debit('EXPENSE', a, curracct.credit_balance)

		if x_total > 0:
			self._xact_add_debit('EQUITY', 'Owners_Equity', x_total)
		elif x_total < 0:
			self._xact_add_credit('EQUITY', 'Owners_Equity', (x_total * -1))
		
		r_total = D(0)
		if 'REVENUE' in self.accounts:
			for a in sorted(self.accounts['REVENUE'].keys()):
				curracct = self.accounts['REVENUE'][a]
				if curracct.credit_balance != "":
					# normal
					r_total += D(curracct.credit_balance)
					self._xact_add_debit('REVENUE', a, curracct.credit_balance)
				elif curracct.debit_balance != "":
					# abnormal
					r_total -= D(curracct.debit_balance)
					self._xact_add_credit('REVENUE', a, curracct.debit_balance)

		if r_total > 0:
			self._xact_add_credit('EQUITY', 'Owners_Equity', r_total)
		elif r_total < 0:
			self._xact_add_debit('EQUITY', 'Owners_Equity', (r_total * -1))
	
		self.ui.get_widget("notebook1").set_current_page(1)
		self.ui.get_widget("notebook2").set_current_page(1)
		self.txt_desc.set_text("Closing Accounts to Owners Capital")


	def load_balance_sheet (self):
		a_list = gtk.ListStore(str, str)
		a_total = D(0)
		if 'ASSET' in self.accounts:
			for a in sorted(self.accounts['ASSET'].keys()):
				curracct = self.accounts['ASSET'][a]
				if curracct.debit_balance != "":
					# normal
					a_total += D(curracct.debit_balance)
					a_list.append([a, curracct.debit_balance])
				elif curracct.credit_balance != "":
					# abnormal
					a_total -= D(curracct.credit_balance)
					a_list.append([a, "(%s)" % curracct.credit_balance])

		self.tv_bs_a.set_model(a_list)

		l_list = gtk.ListStore(str, str)
		l_total = D(0)

		def _l_append_record (a, l_list, l_total, credit_balance="", debit_balance=""):
			if credit_balance != "":
				# normal
				l_total += D(credit_balance)
				l_list.append([a, credit_balance])
			elif debit_balance != "":
				# abnormal
				l_total -= D(debit_balance)
				l_list.append([a, "(%s)" % debit_balance])
			return(l_total)

		for atype in ['LIABILITY', 'EQUITY']:
			if atype in self.accounts:
				for a in sorted(self.accounts[atype].keys()):
					curracct = self.accounts[atype][a]
					l_total = _l_append_record(a, l_list, l_total, credit_balance=curracct.credit_balance, debit_balance=curracct.debit_balance)

		if self.net_income > 0:
			l_total = _l_append_record('current_net_income', l_list, l_total, credit_balance="%0.2f" % self.net_income)
		elif self.net_income < 0:
			l_total = _l_append_record('current_net_income', l_list, l_total, debit_balance="%0.2f" % (self.net_income*-1))

		self.tv_bs_l.set_model(l_list)

		self.ui.get_widget("label27").set_text("\nTotal Assets:\t\t%0.2f\nTotal Liabilities:\t%0.2f\n\n" % (a_total, l_total))
	

	def load_acctlist (self):
		defined_acct_types = []

		total_debits  = D(0)
		total_credits = D(0)

		accts = sqldata.db.get_acctlist()

		acctlist = gtk.ListStore(str, str, str, str)

		for (t, a) in accts:
			if t not in self.accounts:
				self.accounts[t] = {}
			curracct = Account(self.db, a, t)
			self.accounts[t][a] = curracct
			acctlist.append([t, a, curracct.debit_balance, curracct.credit_balance])
			if curracct.debit_balance != "":
				total_debits  += D(curracct.debit_balance)
			if curracct.credit_balance != "":
				total_credits += D(curracct.credit_balance)
		
		if self.tv_acctlist_select_id is not None:
			self.tv_acctlist_select.disconnect(self.tv_acctlist_select_id)
		self.tv_acctlist.set_model(acctlist)
		self.tv_acctlist_select = self.tv_acctlist.get_selection()
		self.tv_acctlist_select.set_mode(gtk.SELECTION_SINGLE)
		self.tv_acctlist_select_id = self.tv_acctlist_select.connect("changed", self.show_account)

		self.ui.get_widget("label33").set_text("\nTrial Balance:\nDebit  Balance Total:\t%0.2f\nCredit Balance Total:\t%0.2f\n\n" % (total_debits, total_credits))


	def xact_reset (self, widget=None, closing=False):
		self.xact = Xact(self.db, closing=closing)	# current transaction

		self.tv_x_debits_liststore  = gtk.ListStore(str, str, str)
		if self.tv_x_debits_select_id is not None:
			self.tv_x_debits_select.disconnect(self.tv_x_debits_select_id)
		self.tv_x_debits.set_model(self.tv_x_debits_liststore)
		self.tv_x_debits_select = self.tv_x_debits.get_selection()
		self.tv_x_debits_select.set_mode(gtk.SELECTION_SINGLE)
		self.tv_x_debits_select_id = self.tv_x_debits_select.connect("changed", self.xact_show_account)

		self.tv_x_credits_liststore = gtk.ListStore(str, str, str)
		if self.tv_x_credits_select_id is not None:
			self.tv_x_credits_select.disconnect(self.tv_x_credits_select_id)
		self.tv_x_credits.set_model(self.tv_x_credits_liststore)
		self.tv_x_credits_select = self.tv_x_credits.get_selection()
		self.tv_x_credits_select.set_mode(gtk.SELECTION_SINGLE)
		self.tv_x_credits_select_id = self.tv_x_credits_select.connect("changed", self.xact_show_account)

		self.ui.get_widget("label11").set_text("Total: 0.00")
		self.ui.get_widget("label13").set_text("Total: 0.00")

		self.txt_xid.set_text("")
		self.txt_desc.set_text("")
		self.txt_s_amt.set_text("")


	def btn_execute_clicked (self, widget=None):
		active_page = self.ui.get_widget('notebook2').get_current_page()
		if active_page == 0:
			# simple mode execute
			amt  = self.txt_s_amt.get_text()
			if not amt:
				return
			self.xact_reset()
			# debit
			selected = self.cb_ds_atype.get_active_text()
			if selected is None:
				return
			atype = selected.split(' ')[0]
			name = self.cbe_ds_name.get_active_text()
			name = name.replace(' ', '_')
			self.xact.add_debit(name, atype, D(amt))
			# credit
			selected = self.cb_cs_atype.get_active_text()
			if selected is None:
				return
			atype = selected.split(' ')[0]
			name = self.cbe_cs_name.get_active_text()
			name = name.replace(' ', '_')
			self.xact.add_credit(name, atype, D(amt))

		(year, month, day) = self.cal_xactdate.get_date()
		month += 1	# month is 0-11
		date = "%d/%d/%d" % (month, day, year)
		self.xact.save(create=self.ck_create.get_active(), date=date, description=self.txt_desc.get_text())
		self.xact_reset()
		self.load_acctlist()
		self.load_income_statement()
		self.load_balance_sheet()

		if active_page == 0:
			self.d_atype_changed(widget=self.cb_ds_atype)
			self.c_atype_changed(widget=self.cb_cs_atype)
		else:
			self.d_atype_changed(widget=self.cb_d_atype)
			self.c_atype_changed(widget=self.cb_c_atype)


	def d_atype_changed (self, widget=None):
		selected = widget.get_active_text()
		if selected is None:
			return
		atype = selected.split(' ')[0]
		liststore = gtk.ListStore(str)
		if atype in self.accounts:
			for a in sorted(self.accounts[atype].keys()):
				iter = liststore.append()
				liststore.set(iter, 0, a)
		else:
			# clear it
			liststore.set(liststore.append(), 0, "")

		cb_map = {}
		cb_map['combobox1'] = self.cbe_d_name
		cb_map['combobox4'] = self.cbe_ds_name

		cbe = cb_map[widget.get_name()]

		cbe.set_model(liststore)
		cbe.set_text_column(0)
		cbe.set_active(0)
	

	def _xact_add_debit (self, atype, name, amt):
		self.xact.add_debit(name, atype, D(amt))
		self.ui.get_widget("label11").set_text("Total: %0.2f" % self.xact.total_debits)
		self.tv_x_debits_liststore.append([name, atype, amt])
		self.tv_x_debits.set_model(self.tv_x_debits_liststore)
	

	def d_ok_clicked (self, widget=None):
		selected = self.cb_d_atype.get_active_text()
		if selected is None:
			return
		atype = selected.split(' ')[0]
		name = self.cbe_d_name.get_active_text()
		name = name.replace(' ', '_')
		amt  = self.txt_d_amt.get_text()
		self._xact_add_debit(atype, name, amt)


	def c_atype_changed (self, widget=None):
		selected = widget.get_active_text()
		if selected is None:
			return
		atype = selected.split(' ')[0]
		liststore = gtk.ListStore(str)
		if atype in self.accounts:
			for a in sorted(self.accounts[atype].keys()):
				iter = liststore.append()
				liststore.set(iter, 0, a)
		else:
			# clear it
			liststore.set(liststore.append(), 0, "")

		cb_map = {}
		cb_map['combobox2'] = self.cbe_c_name
		cb_map['combobox5'] = self.cbe_cs_name

		cbe = cb_map[widget.get_name()]

		cbe.set_model(liststore)
		cbe.set_text_column(0)
		cbe.set_active(0)
	

	def _xact_add_credit (self, atype, name, amt):
		self.xact.add_credit(name, atype, D(amt))
		self.ui.get_widget("label13").set_text("Total: %0.2f" % self.xact.total_credits)
		self.tv_x_credits_liststore.append([name, atype, amt])
		self.tv_x_credits.set_model(self.tv_x_credits_liststore)


	def c_ok_clicked (self, widget=None):
		selected = self.cb_c_atype.get_active_text()
		if selected is None:
			return
		atype = selected.split(' ')[0]
		name = self.cbe_c_name.get_active_text()
		name = name.replace(' ', '_')
		amt  = self.txt_c_amt.get_text()
		self._xact_add_credit(atype, name, amt)
	

	def xact_show_account (self, widget=None):
		"""
		called to show an account when someone clicks on a debit or credit item in the xact tab
		"""
		(model, t_iter) = widget.get_selected()
		name  = model.get_value(t_iter, 0)
		atype = model.get_value(t_iter, 1)
		self.tv_acctlist_select.unselect_all()
		self.show_account(atype=atype, name=name)


	def show_account (self, widget=None, atype=None, name=None):
		"""
		called when user selects an account from the account list
		"""
		if atype is None:
			# accounts list selection
			(model, t_iter) = self.tv_acctlist_select.get_selected()

			if t_iter is None:
				# unselect occurred
				return

			atype = model.get_value(t_iter, 0)
			name  = model.get_value(t_iter, 1)

		self.ui.get_widget("notebook1").set_current_page(0)

		a = self.accounts[atype][name]

		debits  = a.debits
		credits = a.credits

		if self.ui.get_widget("notebook3").get_current_page() == 0:
			# combined view
			pass
		else:
			# split view
			list_debits = gtk.ListStore(str, str, str, str, str)
			for (xid, amt) in [d[:2] for d in debits]:
				x = Xact(self.db, xid=xid)
				if len(x.credits) == 1:
					acct_from = "%s:%s" % (x.credits[0][1], x.credits[0][0])
				else:
					acct_from = "Multiple"

				if x.date is not None:
					date = x.date
				else:
					date = ""
				list_debits.append([date, amt, acct_from, x.description, xid])
			if self.tv_a_debits_select_id is not None:
				self.tv_a_debits_select.disconnect(self.tv_a_debits_select_id)
			self.tv_a_debits.set_model(list_debits)
			self.tv_a_debits_select = self.tv_a_debits.get_selection()
			self.tv_a_debits_select.set_mode(gtk.SELECTION_SINGLE)
			self.tv_a_debits_select_id = self.tv_a_debits_select.connect("changed", self.show_xact)

			list_credits = gtk.ListStore(str, str, str, str, str)
			for (xid, amt) in [c[:2] for c in credits]:
				x = Xact(self.db, xid=xid)
				if len(x.debits) == 1:
					acct_to = "%s:%s" % (x.debits[0][1], x.debits[0][0])
				else:
					acct_to = "Multiple"

				if x.date is not None:
					date = x.date
				else:
					date = ""
				list_credits.append([date, amt, acct_to, x.description, xid])
			if self.tv_a_credits_select_id is not None:
				self.tv_a_credits_select.disconnect(self.tv_a_credits_select_id)
			self.tv_a_credits.set_model(list_credits)
			self.tv_a_credits_select = self.tv_a_credits.get_selection()
			self.tv_a_credits_select.set_mode(gtk.SELECTION_SINGLE)
			self.tv_a_credits_select_id = self.tv_a_credits_select.connect("changed", self.show_xact)

			self.ui.get_widget("label4").set_text("DEBITS (%s)" % type_display[atype]['debit'])
			self.ui.get_widget("label5").set_text("CREDITS (%s)" % type_display[atype]['credit'])
			self.ui.get_widget("label7").set_text("Type: %s" % atype)
			self.ui.get_widget("label8").set_text("%s" % name)
			self.ui.get_widget("label9").set_text("Debits : %15.2f\nCredits: %15.2f" % (a.total_debits, a.total_credits))
	

	def show_xact (self, widget=None, xid=None):
		"""
		display a stored transaction
		"""
		if widget is not None:
			if type(widget) == type(gtk.TreeSelection()):
				# clicked on a xact record in the accounts tab
				(model, t_iter) = widget.get_selected()
				xid = model.get_value(t_iter, 4)
			else:
				# buttons
				wname = widget.get_name()
				try:
					xid = int(self.txt_xid.get_text())
				except ValueError:
					xid = 0
				if wname == 'button5':
					# find
					pass
				elif wname == 'button6':
					# back
					if xid > 1:
						xid -= 1
				elif wname == 'button7':
					# forward
					xid += 1

		self.xact_reset()
		self.ui.get_widget("notebook1").set_current_page(1)
		self.ui.get_widget("notebook2").set_current_page(1)
		self.txt_xid.set_text(str(xid))
		self.xact = Xact(self.db, xid=xid)
		self.txt_desc.set_text(self.xact.description)
		if self.xact.date:
			if '-' in self.xact.date:
				(year, month, day) = self.xact.date.split('-')
			elif '/' in self.xact.date:
				(month, day, year) = self.xact.date.split('/')
			elif len(self.xact.date) == 8:
				year = self.xact.date[0:4]
				month = self.xact.date[4:6]
				day = self.xact.date[6:8]
			else:
				raise ValueError("unexpected date format: %s" % self.xact.date)

			month = int(month) - 1
			self.cal_xactdate.select_month(month, int(year))
			self.cal_xactdate.select_day(int(day))

		total_debits = D(0)
		for (name, atype, amt) in self.xact.debits:
			total_debits += D(amt)
			self.tv_x_debits_liststore.append([name, atype, amt])

		total_credits = D(0)
		for (name, atype, amt) in self.xact.credits:
			total_credits += D(amt)
			self.tv_x_credits_liststore.append([name, atype, amt])

		self.ui.get_widget("label11").set_text("Total: %0.2f" % total_debits)
		self.ui.get_widget("label13").set_text("Total: %0.2f" % total_credits)


if __name__ == "__main__":
	a = acctui()
	a.win.show()
