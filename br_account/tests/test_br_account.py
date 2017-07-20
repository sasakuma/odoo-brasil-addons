# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart, Multidados
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBrAccountInvoiceParcel(TransactionCase):

    def setUp(self):
        super(TestBrAccountInvoiceParcel, self).setUp()

        self.date_maturity = '2017-07-01'

        vals = {
            'date_maturity': self.date_maturity,
            'parceling_value': 1.0,
        }

        # Criamos a parcela
        self.parcel = self.env['br_account.invoice.parcel'].create(vals)

    def test_update_date_maturity(self):

        new_date = '2017-07-20'

        # Ficamos a data de vencimento da parcela
        self.parcel.pin_date = True

        # Tentamos realizar a atualização da data de vencimento
        self.parcel.update_date_maturity(new_date)

        # A data de vencimento tem de permanecer a mesma, uma vez que fixamos
        # a data de vencimento
        self.assertNotEqual(new_date, self.date_maturity)
        self.assertEqual(self.parcel.date_maturity, self.date_maturity)

        # Desafixamos a data de vencimento
        self.parcel.pin_date = False

        # Tentamos realizar a atualização da data de vencimento
        self.parcel.update_date_maturity(new_date)

        # A data de vencimento foi alterada para a data 'new_date',
        # uma vez que desafixamos a data de vencimento
        self.assertEqual(new_date, self.date_maturity)
        self.assertNotEqual(self.parcel.date_maturity, self.date_maturity)
