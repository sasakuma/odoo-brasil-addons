# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestBrSaleOrder(TransactionCase):
    def setUp(self):
        super(TestBrSaleOrder, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
            'company_id': self.main_company.id,
        })

        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })

        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0,
            'property_account_income_id': self.revenue_account.id,
        })

        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0,
            'property_account_income_id': self.revenue_account.id,
        })

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

        self.partner_fisica = self.env['res.partner'].create({
            **default_partner,
            'cnpj_cpf': '545.770.154-98',
            'company_type': 'person',
            'is_company': False,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id
        })

        self.partner_juridica = self.env['res.partner'].create({
            **default_partner,
            'cnpj_cpf': '05.075.837/0001-13',
            'company_type': 'company',
            'is_company': True,
            'inscr_est': '433.992.727',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

        self.tax_model = self.env['account.tax']
        self.pis = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'domain': 'pis',
            'amount': 5,
            'sequence': 1,
            'price_include': True,
        })

        self.cofins = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'domain': 'cofins',
            'amount': 15,
            'sequence': 2,
            'price_include': True,
        })

        self.ipi = self.tax_model.create({
            'name': "IPI",
            'amount_type': 'percent',
            'domain': 'ipi',
            'amount': 7,
            'sequence': 3,
        })

        self.icms = self.tax_model.create({
            'name': "ICMS",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })

        self.icms_inter = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 12,
            'sequence': 4,
            'price_include': True,
        })

        self.icms_st = self.tax_model.create({
            'name': "ICMS ST",
            'amount_type': 'icmsst',
            'domain': 'icmsst',
            'amount': 18,
            'price_include': False,
        })

        self.icms_difal_inter = self.tax_model.create({
            'name': "ICMS Difal Inter",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 7,
            'price_include': True,
        })

        self.icms_difal_intra = self.tax_model.create({
            'name': "ICMS Difal Intra",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 17,
            'price_include': True,
        })

        self.icms_fcp = self.tax_model.create({
            'name': "FCP",
            'amount_type': 'division',
            'domain': 'fcp',
            'amount': 2,
            'price_include': True,
        })

        self.issqn = self.tax_model.create({
            'name': "ISSQN",
            'amount_type': 'division',
            'domain': 'issqn',
            'amount': 5,
            'price_include': True,
        })

        self.ii = self.tax_model.create({
            'name': "II",
            'amount_type': 'division',
            'domain': 'ii',
            'amount': 60,
            'price_include': True,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })

        order_line_data = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'product_uom': self.default_product.uom_id.id,
                 'product_uom_qty': 10.0,
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
            (0, 0,
             {
                 'product_id': self.service.id,
                 'product_uom': self.service.uom_id.id,
                 'product_uom_qty': 10.0,
                 'name': 'product test 5',
                 'price_unit': 100.00,
                 'cfop_id': self.env.ref(
                     'br_data_account_product.cfop_5101').id,
                 'pis_cst': '01',
                 'cofins_cst': '01',
             }
             )
        ]

        default_saleorder = {
            'fiscal_position_id': self.fpos.id,
            'order_line': order_line_data,
            'payment_term_id': self.env.ref('account.account_payment_term').id,
            'quotation_date': '2017-07-01',
        }

        self.sales_order = self.env['sale.order'].create({
            **default_saleorder,
            'name': 'SO 001',
            'partner_id': self.partner_fisica.id
        })

        self.sales_order |= self.env['sale.order'].create({
            **default_saleorder,
            'name': 'SO 002',
            'partner_id': self.partner_juridica.id
        })

        self.title_type = self.env.ref('br_account.account_title_type_2')
        self.financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        self.sales_order.generate_parcel_entry(self.financial_operation,
                                               self.title_type)

    def test_sale_order_to_invoice(self):
        for item in self.sales_order:
            item.action_confirm()
            item.action_invoice_create(final=True)

            self.assertEqual(len(item.invoice_ids), 1)

            for line in item.order_line:
                self.assertEqual(len(line.invoice_lines), 1)

                inv_line = line.invoice_lines[0]

                self.assertEqual(line.icms_cst_normal,
                                 inv_line.icms_cst_normal)
                self.assertEqual(line.icms_csosn_simples,
                                 inv_line.icms_csosn_simples)
                self.assertEqual(line.cfop_id, inv_line.cfop_id)
                self.assertEqual(line.product_id.fiscal_classification_id,
                                 inv_line.fiscal_classification_id)
                self.assertEqual(line.fiscal_position_id.service_type_id,
                                 inv_line.service_type_id)
                self.assertEqual(line.product_id.origin, inv_line.icms_origem)

                self.assertEqual(line.incluir_ipi_base,
                                 inv_line.incluir_ipi_base)
                self.assertEqual(line.icms_st_aliquota_mva,
                                 inv_line.icms_st_aliquota_mva)
                self.assertEqual(line.icms_aliquota_reducao_base,
                                 inv_line.icms_aliquota_reducao_base)
                self.assertEqual(line.icms_st_aliquota_reducao_base,
                                 inv_line.icms_st_aliquota_reducao_base)
                self.assertEqual(line.tem_difal, inv_line.tem_difal)
                self.assertEqual(line.ipi_cst, inv_line.ipi_cst)
                self.assertEqual(line.ipi_reducao_bc, inv_line.ipi_reducao_bc)
                self.assertEqual(line.pis_cst, inv_line.pis_cst)
                self.assertEqual(line.cofins_cst, inv_line.cofins_cst)

    def test_generate_parcel_entry(self):

        for sale in self.sales_order:
            for parcel in sale.parcel_ids:
                self.assertEqual(parcel.date_maturity, '2017-08-31')
                self.assertEqual(parcel.old_date_maturity, '2017-08-31')
                self.assertEqual(parcel.name, '01')
                self.assertEqual(parcel.parceling_value, sale.amount_total)
                self.assertEqual(parcel.financial_operation_id.id,
                                 self.financial_operation.id)
                self.assertEqual(parcel.title_type_id.id, self.title_type.id)

    def test_action_open_periodic_entry_wizard(self):

        # O metodo deve receber apenas um record, caso contrário o retorno
        # sera comprometido. Aqui, verificamos se o metodo dispara excecao
        # quando o mesmo e invocado com mais de um record
        with self.assertRaises(ValueError):
            self.sales_order.action_open_periodic_entry_wizard()

        for sale in self.sales_order:
            action = sale.action_open_periodic_entry_wizard()

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

            # Verificamos o valor das chaves
            self.assertEqual(action['type'], 'ir.actions.act_window')
            self.assertEqual(action['res_model'], 'br_sale.parcel.wizard')
            self.assertEqual(action['view_type'], 'form')
            self.assertEqual(action['view_mode'], 'form')
            self.assertEqual(action['views'], [(False, 'form')])
            self.assertEqual(action['target'], 'new')

            self.assertEqual(action['context']['default_payment_term_id'],
                             sale.payment_term_id.id)

    def test__get_parcel_to_invoice(self):

        for sale in self.sales_order:

            for parcel in sale.parcel_ids:
                parcel_dict = self.sales_order._get_parcel_to_invoice(parcel)

                self.assertEqual(parcel_dict['pin_date'], parcel.pin_date)
                self.assertEqual(parcel_dict['name'], parcel.name)
                self.assertEqual(parcel_dict['date_maturity'],
                                 parcel.date_maturity)
                self.assertEqual(parcel_dict['title_type_id'],
                                 parcel.title_type_id.id)
                self.assertEqual(parcel_dict['financial_operation_id'],
                                 parcel.financial_operation_id.id)
                self.assertEqual(parcel_dict['parceling_value'],
                                 parcel.parceling_value)
                self.assertEqual(parcel_dict['amount_days'],
                                 parcel.amount_days)
