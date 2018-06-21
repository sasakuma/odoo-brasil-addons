# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

from odoo.addons.br_account.tests.test_base import TestBaseBr


class TestAccountInvoice(TestBaseBr):
    def setUp(self):
        super(TestAccountInvoice, self).setUp()

        self.partner_fis = self.env['res.partner'].create({
            'name': 'Nome Parceiro',
            'is_company': False,
            'property_account_receivable_id': self.receivable_account.id,
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Nome Empresa',
            'is_company': True,
            'property_account_receivable_id': self.receivable_account.id,
        })

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'update_posted': True,
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'quantity': 10.0,
                 'price_unit': self.default_product.list_price,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
             }
             ),
            (0, 0,
             {
                 'product_id': self.service.id,
                 'quantity': 10.0,
                 'price_unit': self.service.list_price,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'product_type': self.service.fiscal_type,
             }
             )
        ]

        payment_term = self.env.ref('account.account_payment_term_net')

        default_invoice = {
            'reference_type': "none",
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'payment_term_id': payment_term.id,
            'invoice_line_ids': invoice_line_data,
            'pre_invoice_date': '2017-07-01',
        }

        payment_lines = [(0, 0, {
                'value': 'percent',
                'value_amount': 33.3,
                'sequence': 8,
                'days': 0,
                'option': 'day_after_invoice_date',
            }), (0, 0, {
                'value': 'percent',
                'value_amount': 33.3,
                'sequence': 9,
                'days': 30,
                'option': 'day_after_invoice_date',
            }), (0, 0, {
                'value': 'balance',
                'value_amount': 0.0,
                'sequence': 10,
                'days': 60,
                'option': 'day_after_invoice_date',
            })]

        self.custom_payment_term = self.env['account.payment.term'].create({
            'name': '0/30/60',
            'note': '0/30/60',
            'line_ids': payment_lines,
        })

        incomplete_inv = {
            'name': 'Teste Fatura Incompleta',
            'partner_id': self.partner.id,
            'reference_type': "none",
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'pre_invoice_date': '2017-07-01',
        }

        self.invoices = self.env['account.invoice'].create(dict(
            list(default_invoice.items()),
            name='Teste Fatura Pessoa Fisica',
            partner_id=self.partner_fis.id,
        ))

        self.invoices |= self.env['account.invoice'].create(dict(
            list(default_invoice.items()),
            name='Teste Fatura Empresa',
            partner_id=self.partner.id,
        ))

        # Cria parcelas
        self.invoices.generate_parcel_entry(self.financial_operation,
                                            self.title_type)

        # Criamos faturas com dados ausentes para testar as excecoes
        # payment_term e falso
        self.incomplete_inv = self.env['account.invoice'].create(dict(
            list(incomplete_inv.items()),
            invoice_line_ids=invoice_line_data,
        ))

        # Fatura sem linhas
        self.incomplete_inv |= self.env['account.invoice'].create(dict(
            list(incomplete_inv.items()),
            payment_term_id=payment_term.id,
        ))

        # Fatura com state diferente de 'draft'
        self.incomplete_inv |= self.env['account.invoice'].create(dict(
            list(incomplete_inv.items()),
            state='open',
            invoice_line_ids=invoice_line_data,
            payment_term_id=payment_term.id,
        ))

    def test_action_invoice_cancel_paid_exception(self):

        for inv in self.invoices:

            # Forçamos o status da fatura apenas para fins de teste
            inv.state = 'cancel'

            with self.assertRaises(UserError):
                inv.action_invoice_cancel_paid()

    @mock.patch('odoo.addons.br_account.models.account_invoice.AccountInvoice.action_cancel')
    def test_action_invoice_cancel_paid_success(self, mk_action_cancel):

        for inv in self.invoices:
            inv.action_br_account_invoice_open()
            inv.action_invoice_cancel_paid()

        # Verificamos quantas vezes o metodo 'action_cancel' foi chamado.
        # Este metodo e responsavel por todo o processo de cancelamento
        # da fatura
        self.assertEqual(len(mk_action_cancel.mock_calls), len(self.invoices))

    def test_action_cancel_exception(self):

        for inv in self.invoices:

            # Confirmamos a fatura normalmente
            inv.action_br_account_invoice_open()

            # Forçamos o status de parcialmente pago
            # de modo a verificar se e possivel cancelar
            # account.move que nao foram pagas totalmente.
            for move in inv.move_ids:
                move.paid_status = 'partial'

            with self.assertRaises(UserError):
                inv.action_cancel()

    @mock.patch('odoo.fields.Date.today')
    def test_action_cancel_success(self, mk):

        # Realizamos o mock da data de cancelamento da fatura
        mk.return_value = '2017-09-04'

        for inv in self.invoices:

            # Confirmamos a fatura e verificamos se os
            # respectivos campos foram populados
            inv.action_br_account_invoice_open()

            self.assertNotEqual(inv.state, 'cancel')
            self.assertTrue(inv.move_id)
            self.assertTrue(inv.move_ids)

            # Salvamos os ids de cada
            moves = inv.move_ids

            # Cancelamos a fatura e verificamos se os campos
            # foram resetados
            self.assertTrue(inv.action_cancel())

            self.assertEqual(inv.state, 'cancel')
            self.assertFalse(inv.move_id)
            self.assertFalse(inv.move_ids)

            self.assertEqual(inv.cancel_invoice_date, '2017-09-04')

            # Verificamos se as account.move da fatura foram
            # realmente excluidas do banco
            self.assertFalse(moves.exists())

    def test_compute_total_values(self):

        for invoice in self.invoices:
            if invoice.partner_id == self.partner:
                invoice.payment_term_id = self.custom_payment_term.id
                invoice.invoice_line_ids = [(0, 0, {
                    'product_id': self.other_product.id,
                    'quantity': 1.0,
                    'price_unit': self.other_product.list_price,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    })]
                invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

                self.assertEqual(invoice.amount_total, 652.47)
                self.assertEqual(invoice.amount_total_signed, 652.47)
                self.assertEqual(invoice.amount_untaxed, 652.47)
                self.assertEqual(invoice.amount_tax, 0.0)
                self.assertEqual(invoice.total_tax, 0.0)
            else:
                self.assertEqual(invoice.amount_total, 650.0)
                self.assertEqual(invoice.amount_total_signed, 650.0)
                self.assertEqual(invoice.amount_untaxed, 650.0)
                self.assertEqual(invoice.amount_tax, 0.0)
                self.assertEqual(invoice.total_tax, 0.0)

            # Verifico as linhas recebiveis
            self.assertEqual(len(invoice.move_ids), 0)

            # Valido a fatura
            invoice.action_br_account_invoice_open()

            # Verifico as linhas recebiveis
            if invoice.partner_id == self.partner:
                self.assertEqual(len(invoice.move_ids), 3)
            else:
                self.assertEqual(len(invoice.move_ids), 1)
            self.assertEqual(all(move.account_type == 'receivable'
                for move in invoice.move_ids), True)
            self.assertEqual(all(move.amount == move.amount_residual
                for move in invoice.move_ids), True)
            self.assertEqual(len(invoice.parcel_ids), len(invoice.move_ids))

    def test_invoice_pis_cofins_taxes(self):

        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # PIS
            first_item.tax_pis_id = self.pis_500
            first_item._onchange_tax_pis_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.pis_base_calculo, 150.0)
            self.assertEqual(first_item.pis_valor, 7.5)
            self.assertEqual(first_item.pis_aliquota, 5.0)

            # COFINS
            first_item.tax_cofins_id = self.cofins_1500
            first_item._onchange_tax_cofins_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.cofins_base_calculo, 150.0)
            self.assertEqual(first_item.cofins_valor, 22.5)
            self.assertEqual(first_item.cofins_aliquota, 15.0)

            for item in invoice.invoice_line_ids:
                item.tax_pis_id = self.pis_500
                item._onchange_tax_pis_id()
                item._onchange_product_id()
                self.assertEqual(item.pis_base_calculo, item.price_total)
                self.assertEqual(item.pis_aliquota, 5.0)
                self.assertEqual(item.pis_valor, item.price_total * 0.05)

                item.tax_cofins_id = self.cofins_1500
                item._onchange_tax_cofins_id()
                item._onchange_product_id()
                self.assertEqual(item.cofins_base_calculo, item.price_total)
                self.assertEqual(item.cofins_aliquota, 15.0)
                self.assertEqual(item.cofins_valor, item.price_total * 0.15)

                self.assertEqual(len(item.invoice_line_tax_ids), 2)

            self.assertEqual(invoice.pis_base, 650.0)
            self.assertEqual(invoice.cofins_base, 650.0)
            self.assertEqual(invoice.pis_value, 32.5)
            self.assertEqual(invoice.cofins_value, 97.5)

            # Valido a fatura
            invoice.action_br_account_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEqual(invoice.pis_base, 650.0)
            self.assertEqual(invoice.cofins_base, 650.0)
            self.assertEqual(invoice.pis_value, 32.5)
            self.assertEqual(invoice.cofins_value, 97.5)

    def test_invoice_issqn_and_ii_taxes(self):

        for invoice in self.invoices:
            prod_item = invoice.invoice_line_ids[0]
            serv_item = invoice.invoice_line_ids[1]

            # II
            prod_item.tax_ii_id = self.ii_6000
            prod_item._onchange_tax_ii_id()
            self.assertEqual(prod_item.price_total, 150.0)
            self.assertEqual(prod_item.ii_base_calculo, 150.0)
            self.assertEqual(prod_item.ii_valor, 90.0)
            self.assertEqual(prod_item.ii_aliquota, 60.0)

            # ISSQN
            serv_item.tax_issqn_id = self.issqn_500
            serv_item._onchange_tax_issqn_id()
            self.assertEqual(serv_item.price_total, 500.0)
            self.assertEqual(serv_item.issqn_base_calculo, 500.0)
            self.assertEqual(serv_item.issqn_valor, 25.0)
            self.assertEqual(serv_item.issqn_aliquota, 5.0)

            # Totais
            self.assertEqual(invoice.issqn_base, 500.0)
            self.assertEqual(invoice.ii_value, 90.0)
            self.assertEqual(invoice.issqn_value, 25.0)

            # Valido a fatura
            invoice.action_br_account_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEqual(invoice.issqn_base, 500.0)
            self.assertEqual(invoice.ii_value, 90.0)
            self.assertEqual(invoice.issqn_value, 25.0)

    def test_invoice_icms_normal_tax(self):

        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # ICMS
            first_item.tax_icms_id = self.icms_1700
            first_item._onchange_tax_icms_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.icms_base_calculo, 150.0)
            self.assertEqual(first_item.icms_valor, 25.5)
            self.assertEqual(first_item.icms_aliquota, 17.0)

            for item in invoice.invoice_line_ids:
                item.tax_icms_id = self.icms_1700
                item._onchange_tax_icms_id()
                item._onchange_product_id()
                self.assertEqual(item.icms_base_calculo, item.price_total)
                self.assertEqual(
                    item.icms_valor, round(item.price_total * 0.17, 2))
                self.assertEqual(item.icms_aliquota, 17.0)

                self.assertEqual(len(item.invoice_line_tax_ids), 1)

            self.assertEqual(invoice.icms_base, 650.0)
            self.assertEqual(invoice.icms_value, 110.5)

            # Valido a fatura
            invoice.action_br_account_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEqual(invoice.icms_base, 650.0)
            self.assertEqual(invoice.icms_value, 110.5)

    def test_invoice_icms_reducao_base_tax(self):

        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # ICMS com Redução de base
            first_item.tax_icms_id = self.icms_1700
            first_item.icms_aliquota_reducao_base = 10.0
            first_item._onchange_tax_icms_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.icms_base_calculo, 135.0)
            self.assertEqual(first_item.icms_valor, 22.95)
            self.assertEqual(first_item.icms_aliquota, 17.0)

            for item in invoice.invoice_line_ids:
                item.tax_icms_id = self.icms_1700
                item.icms_aliquota_reducao_base = 10.0
                item._onchange_tax_icms_id()
                item._onchange_product_id()
                self.assertEqual(
                    item.icms_base_calculo, round(item.price_total * 0.9, 2))
                self.assertEqual(
                    item.icms_valor, round(item.price_total * 0.9 * 0.17, 2))
                self.assertEqual(item.icms_aliquota, 17.0)

                self.assertEqual(len(item.invoice_line_tax_ids), 1)

            self.assertEqual(invoice.icms_base, 585.0)
            self.assertEqual(invoice.icms_value, 99.45)

            # Valido a fatura
            invoice.action_br_account_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEqual(invoice.icms_base, 585.0)
            self.assertEqual(invoice.icms_value, 99.45)

    def test__compute_residual(self):

        for inv in self.invoices:

            # Valido a fatura
            inv.action_br_account_invoice_open()

            inv._compute_residual()

            # Como a fatura nao e de nenhum dos tipos a seguir
            # os valores abaixo serao positivos
            self.assertNotIn(inv.type, ['in_refund', 'out_refund'])
            self.assertEqual(inv.residual, inv.amount_total)
            self.assertEqual(inv.residual_company_signed, inv.amount_total)
            self.assertFalse(inv.reconciled)

    def test_generate_parcel_entry(self):

        for inv in self.invoices:

            self.assertEqual(len(inv.parcel_ids), 1)

            for parcel in inv.parcel_ids:
                self.assertEqual(parcel.date_maturity, '2017-07-31')
                self.assertEqual(parcel.old_date_maturity, '2017-07-31')
                self.assertEqual(parcel.name, '01')
                self.assertEqual(parcel.parceling_value, inv.amount_total)
                self.assertEqual(parcel.financial_operation_id.id,
                                 self.financial_operation.id)
                self.assertEqual(parcel.title_type_id.id, self.title_type.id)
                self.assertEqual(parcel.amount_days, 30)

        # Verificamos se as faturas incompletas lancam excecao
        for inv in self.incomplete_inv:
            with self.assertRaises(UserError):
                inv.action_open_periodic_entry_wizard()

    @mock.patch('odoo.fields.Date.context_today')
    def test_verify_new_maturity_parcel_date(self, mk_dt):

        mk_dt.return_value = '2017-07-02'

        for inv in self.invoices:

            for parcel in inv.parcel_ids:
                inv.pre_invoice_date = '2017-07-01'
                parcel.old_date_maturity = '2017-07-15'
                parcel.date_maturity = '2017-07-15'
                parcel.compute_amount_days()

                # Valido a fatura
                inv.action_br_account_invoice_open()

                # Verificamos se a data de vencimento das parcelas foram
                # atualizadas quando a fatura e confirmada
                self.assertEqual(parcel.date_maturity, '2017-07-16')
                self.assertEqual(parcel.old_date_maturity, '2017-07-15')

    def test_compare_total_parcel_value(self):

        for inv in self.invoices:
            self.assertTrue(inv.compare_total_parcel_value())

            # Mudamos o valor da fatura para disparar o erro
            inv.amount_total = '1000'

            self.assertTrue(inv.parcel_ids)
            self.assertFalse(inv.compare_total_parcel_value())

    def test_action_br_account_invoice_open_no_parcel(self):

        for inv in self.invoices:

            # Removemos a parcela de cada fatura
            inv.parcel_ids.unlink()

            # Verificamos quando nao existe nenhuma parcela
            self.assertFalse(inv.parcel_ids)

            with self.assertRaises(ValidationError):
                self.assertTrue(inv.action_br_account_invoice_open())

    def test_action_br_account_invoice_open_total_wrong(self):

        for inv in self.invoices:

            # Mudamos o valor da fatura para divergir do total
            # das parcelas
            inv.amount_total = '1000'

            with self.assertRaises(UserError):
                inv.action_br_account_invoice_open()

    def test_action_br_account_invoice_open(self):

        for inv in self.invoices:
            if inv.partner_id == self.partner:
                inv.payment_term_id = self.custom_payment_term.id
                inv.invoice_line_ids = [(0, 0,
                    {
                        'product_id': self.other_product.id,
                        'quantity': 1.0,
                        'price_unit': self.other_product.list_price,
                        'account_id': self.revenue_account.id,
                        'name': 'product test 5',
                    })]
                inv.generate_parcel_entry(self.financial_operation,
                                          self.title_type)
            # O valor total das parcelas deve ser igual ao valor total
            # da fatura
            self.assertTrue(inv.action_br_account_invoice_open())

            self.assertTrue(inv.move_ids)

            # Cada parcela deve criar uma account.move para a fatura
            self.assertEqual(len(inv.parcel_ids), len(inv.move_ids))

            # Verificamos se o backup do numero do pedido foi salvo
            self.assertEqual(inv.number_backup, inv.number)

            # Verificamos se os campos da account.move foram
            # preenchidos corretamente
            parcels = inv.parcel_ids.sorted(lambda r: r.date_maturity)
            moves = inv.move_ids.sorted(lambda r: r.date_maturity_current)
            for parcel, move in zip(parcels, moves):
                self.assertEqual(move.date_maturity_current,
                                 parcel.date_maturity)
                self.assertEqual(move.date_maturity_origin,
                                 parcel.date_maturity)
                self.assertEqual(move.financial_operation_id,
                                 parcel.financial_operation_id)
                self.assertEqual(move.title_type_id, parcel.title_type_id)
                self.assertEqual(move.parcel_id, parcel)

                self.assertEqual(move.company_id, inv.company_id)
                self.assertEqual(move.ref, inv.reference)
                self.assertEqual(move.journal_id, inv.journal_id)
                self.assertEqual(move.date, inv.date or inv.date_invoice)
                self.assertEqual(move.narration, inv.comment)
                self.assertEqual(move.invoice_id, inv)

                if move.partner_id == self.partner:
                    self.assertEqual(len(move.line_ids), 4)
                else:
                    self.assertEqual(len(move.line_ids), 3)

                self.assertEqual(parcel.abs_parceling_value, move.amount)
                self.assertEqual(parcel.abs_parceling_value,
                                 move.amount_origin)

                # Verificamos se os campos da account.move.line
                # foram preenchidos corretamente.
                for line in move.line_ids:
                    self.assertEqual(line.date_maturity, parcel.date_maturity)
                    self.assertEqual(line.amount_currency,
                                     parcel.amount_currency)
                    self.assertEqual(line.currency_id, parcel.currency_id)
                    self.assertEqual(line.invoice_id, inv)
                    self.assertEqual(line.partner_id, inv.partner_id)
                    self.assertEqual(line.company_id, inv.company_id)

                # Move Lines de credito
                debit_lines = move.line_ids.filtered(
                    lambda x: x.account_id.code_first_digit == '1')

                self.assertEqual(len(debit_lines), 1)
                if inv.partner_id != self.partner:
                    self.assertEqual(debit_lines[0].name, parcel.name)
                self.assertEqual(debit_lines[0].debit,
                                 parcel.abs_parceling_value)
                self.assertFalse(debit_lines[0].credit)

                # Remove as linhas que possuem 'debit' diferente de zero
                # Assim sobram as linhas com 'credit' diferente de zero
                credit_lines = move.line_ids - debit_lines

                # Cada account.move.line possui uma invoice.line como
                # geradora e uma invoice.line  pode gerar varias
                # account.move.line
                self.assertEqual(len(credit_lines), len(inv.invoice_line_ids))

                self.assertEqual(sum([line.credit for line in credit_lines]),
                                 parcel.abs_parceling_value)

                # Ordenamos os records para garantir que as comparacoes
                # estao na ordem correta.
                credit_lines = credit_lines.sorted(lambda r: r.id)
                invoice_lines = inv.invoice_line_ids.sorted(lambda r: r.id)
                for credit_lines, inv_line in zip(credit_lines, invoice_lines):                        
                    self.assertEqual(credit_lines.name, inv_line.name)
                    self.assertFalse(credit_lines.debit)
                    if inv.partner_id != self.partner:
                        self.assertEqual(credit_lines.credit,
                                        round(parcel.parceling_value * inv_line.percent_subtotal, 2))

            self.assertTrue(inv.move_id)
            self.assertTrue(inv.move_name)

    def test_action_open_periodic_entry_wizard(self):

        # O metodo deve receber apenas um record, caso contrário o retorno
        # sera comprometido. Aqui, verificamos se o metodo dispara excecao
        # quando o mesmo e invocado com mais de um record
        with self.assertRaises(ValueError):
            self.invoices.action_open_periodic_entry_wizard()

        for inv in self.invoices:
            action = inv.action_open_periodic_entry_wizard()

            # Verificamos se as chaves estao no dicionario.
            # Isso e feita a fim de detectar se alguma chave foi removida
            self.assertIn('type', action)
            self.assertIn('res_model', action)
            self.assertIn('view_type', action)
            self.assertIn('view_mode', action)
            self.assertIn('views', action)
            self.assertIn('target', action)
            self.assertIn('context', action)
            self.assertIn('default_payment_term_id', action['context'])
            self.assertIn('default_pre_invoice_date', action['context'])

            # Verificamos o valor das chaves
            self.assertEqual(action['type'], 'ir.actions.act_window')
            self.assertEqual(action['res_model'],
                             'br_account.invoice.parcel.wizard')
            self.assertEqual(action['view_type'], 'form')
            self.assertEqual(action['view_mode'], 'form')
            self.assertEqual(action['views'], [(False, 'form')])
            self.assertEqual(action['target'], 'new')

            self.assertEqual(action['context']['default_payment_term_id'],
                             inv.payment_term_id.id)

            self.assertEqual(action['context']['default_pre_invoice_date'],
                             inv.pre_invoice_date)

        # Verificamos se as faturas incompletas lancam excecao
        for inv in self.incomplete_inv:
            with self.assertRaises(UserError):
                inv.action_open_periodic_entry_wizard()

    def test__compute_percent_subtotal(self):

        for inv in self.invoices:
            for line in inv.invoice_line_ids:
                line._compute_percent_subtotal()
                self.assertEqual(line.percent_subtotal,
                                 round(line.price_subtotal / line.invoice_id.total_bruto, 6))
