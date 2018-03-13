# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons.br_boleto.tests.test_common import TestBoleto


class TestBoletoSicoob(TestBoleto):

    def _return_payment_mode(self):
        super(TestBoletoSicoob, self)._return_payment_mode()

        sequencia = self.env['ir.sequence'].create({
            'name': "Nosso Número"
        })

        sicoob = self.env['res.bank'].search([('bic', '=', '756')])

        conta = self.env['res.partner.bank'].create({
            'acc_number': '12345',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '1234',  # 4 digitos
            'bra_number_dig': '0',
            'codigo_convenio': '123456-7',  # 7 digitos
            'bank_id': sicoob.id,
        })

        mode = self.env['payment.mode'].create({
            'name': 'Sicoob',
            'boleto_type': '9',
            'boleto_carteira': '1',
            'boleto_modalidade': '01',
            'nosso_numero_sequence': sequencia.id,
            'bank_account_id': conta.id
        })

        return mode.id

    def setUp(self):
        super(TestBoletoSicoob, self).setUp()

    # Não precisa fazer essa validação em outras classes
    def test_basic_validation(self):
        with self.assertRaises(UserError):
            self.invoices.action_br_account_invoice_open()

    def _update_main_company(self):
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'inscr_est': '219.882.606',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
        })

    def _update_partner_fisica(self):
        self.partner_fisica.write({
            'cnpj_cpf': '075.932.961-30',
            'district': 'Centro',
            'zip': '88032-050',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

    def test_validation_partner_and_company(self):
        error_partner = self.partner_fisica.validate()
        error_company = self.main_company.validate()
        
        # import ipdb; ipdb.set_trace()
        self.assertEqual(error_partner, _('Client: %s\nMissing Fields:'
                                           '\n-CNPJ/CPF \n-District\n-ZIP'
                                           '\n-City\n-Country\n-State\n\n\n')
                          % self.partner_fisica.name)

        self.assertEqual(error_company, _('Company: %s\n'
                                           'Missing Fields:\n-Legal Name'
                                           '\n-CNPJ/CPF \n-District\n-ZIP'
                                           '\n-City\n-Street\n-Number'
                                           '\n-State\n\n\n') %
                          self.main_company.name)

        self._update_main_company()
        self._update_partner_fisica()

        self.assertEqual(self.partner_fisica.validate(), '')
        self.assertEqual(self.main_company.validate(), '')

    # def test_raise_error_if_not_payment(self):
    #     self._update_main_company()
    #     self._update_partner_fisica()

    #     self.invoices.action_br_account_invoice_open()

    #     self.assertEqual(len(self.invoices.receivable_move_line_ids), 1)

    #     move = self.invoices.receivable_move_line_ids[0]
    #     vals = move.action_print_boleto()

    #     self.assertEqual(vals['report_name'], 'br_boleto.report.print')
    #     self.assertEqual(vals['report_type'], 'pdf')

    #     vals = self.invoices.action_register_boleto()

    #     self.assertEqual(vals['report_name'], 'br_boleto.report.print')
    #     self.assertEqual(vals['report_type'], 'pdf')

    #     move.action_register_boleto()
