# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBrAccountInvoiceParcel(TransactionCase):

    def setUp(self):
        super(TestBrAccountInvoiceParcel, self).setUp()

        # Data de vencimento para ser usada como referencia
        self.date_maturity = '2017-07-15'
        self.pre_invoice_date = '2017-07-1'

        # Criamos os atributos da invoice a qual a parcela pertence
        revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.env.ref('base.main_company').id
        })

        receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.env.ref('base.main_company').id
        })

        journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': revenue_account.id,
            'default_credit_account_id': revenue_account.id,
        })

        partner = self.env['res.partner'].create({
            'name': 'Nome Parceiro',
            'is_company': False,
            'property_account_receivable_id': receivable_account.id,
        })

        values = {
            'name': 'Fatura de Teste',
            'partner_id': partner.id,
            'journal_id': journalrec.id,
            'account_id': receivable_account.id,
            'pre_invoice_date': self.pre_invoice_date,
        }

        # Criamos a fatura na qual a parcela pertence
        invoice = self.env['account.invoice'].create(values)

        values = {
            'date_maturity': self.date_maturity,
            'parceling_value': 1.0,
            'invoice_id': invoice.id,
        }

        # Criamos a parcela
        self.parcel = self.env['br_account.invoice.parcel'].create(values)

    def test_check_old_date_maturity(self):
        # Verificamos se old_date_maturity recebe o valor de 'date_maturity'
        # quando a parcela e criada.
        self.assertEqual(self.parcel.date_maturity,
                         self.parcel.old_date_maturity)

        # Verificamos a diferenca entre pre_invoice_date e old_date_maturity
        self.assertEqual(self.parcel.amount_days, 14)

    def test_compute_abs_parceling_value(self):
        self.parcel.parceling_value = -2

        self.parcel.compute_abs_parceling_value()

        # Verificamos se 'abs_parceling_value' esta com o valor positivo da
        # parcela
        self.assertEqual(self.parcel.abs_parceling_value,
                         abs(self.parcel.parceling_value))

    def test_compute_amount_days(self):

        # Verificamos se o metodo calcula a quantidade correta de dias
        self.parcel.amount_days = 0
        self.parcel.compute_amount_days()
        self.parcel.old_date_maturity = '2017-07-20'

        # Calculamos a quantidade de dias
        self.parcel.compute_amount_days()

        # Verificamos a diferenca entre pre_invoice_date e old_date_maturity
        self.assertEqual(self.parcel.amount_days, 19)

    def test_onchange_date_maturity(self):

        # verificamos a integridade das datas de vencimento
        self.assertEqual(self.parcel.date_maturity,
                         self.parcel.old_date_maturity)
        self.assertEqual(self.parcel.invoice_id.state, 'draft')
        self.parcel.date_maturity = '2017-07-20'
        self.parcel.onchange_date_maturity()

        # date_maturity sera igual a old_date_maturity
        self.assertEqual(self.parcel.date_maturity,
                         self.parcel.old_date_maturity)

        # Quando a fatura nao esta como 'draft', a data old_maturity nao se
        # altera
        self.parcel.invoice_id.state = 'open'
        self.parcel.date_maturity = '2017-07-21'
        self.parcel.onchange_date_maturity()
        self.assertNotEqual(self.parcel.date_maturity,
                            self.parcel.old_date_maturity)

    def test_update_date_maturity(self):

        # Data base no qual sera calculada a nova data de vencimento
        new_base_date = '2017-07-20'

        # Ficamos a data de vencimento da parcela
        self.parcel.pin_date = True

        # Tentamos realizar a atualização da data de vencimento
        self.parcel.update_date_maturity(new_base_date)

        # A data de vencimento tem de permanecer a mesma, uma vez que
        # fixamos a data de vencimento
        self.assertNotEqual(new_base_date, self.parcel.date_maturity)
        self.assertEqual(self.date_maturity, self.parcel.date_maturity)
        self.assertEqual(self.date_maturity, self.parcel.old_date_maturity)

        # Desafixamos a data de vencimento
        self.parcel.pin_date = False

        # Tentamos realizar a atualização da data de vencimento
        self.parcel.update_date_maturity(new_base_date)

        # A data de vencimento foi alterada com base na nova data fornecida
        # e no numero de dias
        self.assertEqual(self.parcel.amount_days, 14)
        self.assertEqual(self.parcel.date_maturity, '2017-08-03')
        self.assertEqual(self.date_maturity, self.parcel.old_date_maturity)
