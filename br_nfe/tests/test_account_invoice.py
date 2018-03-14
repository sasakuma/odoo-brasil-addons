# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountInvoice(TransactionCase):
    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestAccountInvoice, self).setUp()

        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'currency_id': self.currency_real.id,
            'tipo_ambiente': '2',
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(
                open(os.path.join(self.caminho, 'teste.pfx'), 'rb').read()),
        })

        self.main_company.inscr_est = '219.882.606'

        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id,
        })

        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id,
        })

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123',
        })

        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0,
        })

        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0,
        })

        self.st_product = self.env['product.product'].create({
            'name': 'Product for ICMS ST',
            'default_code': '15',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 25.0,
        })

        partner_obj = self.env['res.partner']

        default_partner = {
            'name': 'Nome Parceiro',
            'legal_name': 'Razão Social',
            'zip': '88037-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'phone': '(48) 9801-6226',
            'property_account_receivable_id': self.receivable_account.id,
        }

        # Incializa parceiro fisico
        self.partner_fisica = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '545.770.154-98',
            'company_type': 'person',
            'is_company': False,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

        # Inicializa parceiro juridico
        self.partner_juridica = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '05.075.837/0001-13',
            'company_type': 'company',
            'is_company': True,
            'inscr_est': '433.992.727',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

        # Inicializa parceiro fisico internacional
        self.partner_fisica_inter = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '793.493.171-92',
            'company_type': 'person',
            'is_company': False,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_rs').id,
            'city_id': self.env.ref('br_base.city_4304606').id,
        })

        # Inicializa parceiro juridico internacional
        self.partner_juridica_inter = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '08.326.476/0001-29',
            'company_type': 'company',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_rs').id,
            'city_id': self.env.ref('br_base.city_4300406').id,
        })

        # Inicializa parceiro juridico de SP
        self.partner_juridica_sp = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '37.484.824/0001-94',
            'company_type': 'company',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sp').id,
            'city_id': self.env.ref('br_base.city_3501608').id,
        })

        # Inicializa parceiro exterior
        self.partner_exterior = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '12345670',
            'company_type': 'company',
            'is_company': True,
            'country_id': self.env.ref('base.us').id,
        })

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda',
            'natureza_operacao': 'Venda',
        })

        self.fpos_consumo = self.env['account.fiscal.position'].create({
            'name': 'Venda Consumo',
            'ind_final': '1',
        })

        invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
                 'cfop_id': self.env.ref(
                     'br_data_account_product.cfop_5101').id,
                 'icms_cst_normal': '40',
                 'icms_csosn_simples': '102',
                 'ipi_cst': '50',
                 'pis_cst': '01',
                 'cofins_cst': '01',
             }
             ),
        ]

        self.title_type = self.env.ref('br_account.account_title_type_2')
        self.financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        fiscal_document = self.env.ref('br_data_account.fiscal_document_55')
        payment_term = self.env.ref('account.account_payment_term_net')

        serie = self.env['br_account.document.serie'].search(
            [('fiscal_document_id', '=', fiscal_document.id)])

        default_invoice = {
            'name': "Teste Validação",
            'reference_type': "none",
            'fiscal_document_id': fiscal_document.id,
            'document_serie_id': serie.id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data,
            'payment_term_id': payment_term.id,
        }

        self.invoices = self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_fisica.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_juridica.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_juridica.id,
            'fiscal_position_id': self.fpos_consumo.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_fisica_inter.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_juridica_inter.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_juridica_sp.id,
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_exterior.id,
        })

        self.invoices.generate_parcel_entry(self.financial_operation,
                                            self.title_type)

    def test_action_print_danfe(self):

        # Antes de confirmar a fatura
        with self.assertRaises(UserError):
            self.invoices.action_print_danfe()

        # Confirmando a fatura deve gerar um documento eletrônico
        self.env['account.invoice.confirm'].with_context(
            active_ids=self.invoices.ids).invoice_confirm()

        invoice_electronics = self.env['invoice.electronic'].search(
            [('invoice_id', 'in', self.invoices.ids)])

        # Forçamos o status do doc. eletronico apenas para fins de teste
        for electronic_invoice in invoice_electronics:
            electronic_invoice.state = 'done'

        # Tentamos gerar o danfe
        danfe = self.invoices.action_print_danfe()

        # Comparamos os valores
        self.assertEqual(danfe['report_name'],
                         'br_nfe.main_template_br_nfe_danfe')

        self.assertEqual(danfe['report_type'], 'qweb-pdf')
        self.assertEqual(danfe['type'], 'ir.actions.report')

        self.assertListEqual(danfe['context']['active_ids'],
                             invoice_electronics.ids)
