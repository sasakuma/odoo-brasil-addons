# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

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

        self.pis_500 = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'domain': 'pis',
            'amount': 5,
            'sequence': 1,
            'price_include': True,
        })

        self.cofins_1500 = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'domain': 'cofins',
            'amount': 15,
            'sequence': 2,
            'price_include': True,
        })

        self.ipi_700 = self.tax_model.create({
            'name': "IPI",
            'amount_type': 'percent',
            'domain': 'ipi',
            'amount': 7,
            'sequence': 3,
        })

        self.icms_1700 = self.tax_model.create({
            'name': "ICMS",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })

        self.icms_inter_1200 = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 12,
            'sequence': 4,
            'price_include': True,
        })

        self.icms_st_1800 = self.tax_model.create({
            'name': "ICMS ST",
            'amount_type': 'icmsst',
            'domain': 'icmsst',
            'amount': 18,
            'price_include': False,
        })

        self.icms_difal_inter_700 = self.tax_model.create({
            'name': "ICMS Difal Inter",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 7,
            'price_include': True,
        })

        self.icms_difal_intra_1700 = self.tax_model.create({
            'name': "ICMS Difal Intra",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 17,
            'price_include': True,
        })

        self.icms_fcp_200 = self.tax_model.create({
            'name': "FCP",
            'amount_type': 'division',
            'domain': 'fcp',
            'amount': 2,
            'price_include': True,
        })

        self.issqn_500 = self.tax_model.create({
            'name': "ISSQN",
            'amount_type': 'division',
            'domain': 'issqn',
            'amount': 5,
            'price_include': True,
        })

        self.ii_6000 = self.tax_model.create({
            'name': "II",
            'amount_type': 'division',
            'domain': 'ii',
            'amount': 60,
            'price_include': True,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda',
            'position_type': 'product',
        })

        order_line_data = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'product_uom': self.default_product.uom_id.id,
                 'product_uom_qty': 10.0,
                 'name': 'product test 5',
                 'price_unit': self.default_product.list_price,
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
                 'price_unit': self.service.list_price,
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
            'partner_id': self.partner_fisica.id,
            'partner_invoice_id': self.partner_fisica.id,
            'partner_shipping_id': self.partner_fisica.id,
            'date_order': datetime.today(),
            'pricelist_id': self.env.ref('product.list0').id,
        })

        self.sales_order |= self.env['sale.order'].create({
            **default_saleorder,
            'name': 'SO 002',
            'partner_id': self.partner_juridica.id,
            'partner_invoice_id': self.partner_juridica.id,
            'partner_shipping_id': self.partner_juridica.id,
            'date_order': datetime.today(),
            'pricelist_id': self.env.ref('product.list0').id,
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

                self.assertEqual(inv_line.invoice_id.pre_invoice_date, 
                                 item.confirmation_date[0:10])

                self.assertEqual(line.valor_desconto, inv_line.valor_desconto)
                self.assertEqual(line.icms_cst_normal, inv_line.icms_cst_normal)
                self.assertEqual(line.icms_csosn_simples, inv_line.icms_csosn_simples)
                self.assertEqual(line.tax_icms_id, inv_line.tax_icms_id)
                self.assertEqual(line.tax_icms_st_id, inv_line.tax_icms_st_id)
                self.assertEqual(line.tax_icms_inter_id, inv_line.tax_icms_inter_id)
                self.assertEqual(line.tax_icms_intra_id, inv_line.tax_icms_intra_id)
                self.assertEqual(line.tax_icms_fcp_id, inv_line.tax_icms_fcp_id)
                self.assertEqual(line.tax_simples_id, inv_line.tax_simples_id)
                self.assertEqual(line.tax_ipi_id, inv_line.tax_ipi_id)
                self.assertEqual(line.tax_pis_id, inv_line.tax_pis_id)
                self.assertEqual(line.tax_cofins_id, inv_line.tax_cofins_id)
                self.assertEqual(line.tax_ii_id, inv_line.tax_ii_id)
                self.assertEqual(line.tax_issqn_id, inv_line.tax_issqn_id)
                self.assertEqual(line.tax_csll_id, inv_line.tax_csll_id)
                self.assertEqual(line.tax_irrf_id, inv_line.tax_irrf_id)
                self.assertEqual(line.tax_inss_id, inv_line.tax_inss_id)
                self.assertEqual(line.product_id.fiscal_type, inv_line.product_type)
                self.assertEqual(line.company_id.fiscal_type, inv_line.company_fiscal_type)
                self.assertEqual(line.cfop_id, inv_line.cfop_id)
                self.assertEqual(line.product_id.fiscal_classification_id, inv_line.fiscal_classification_id)
                self.assertEqual(line.fiscal_position_id.service_type_id, inv_line.service_type_id)
                self.assertEqual(line.product_id.origin, inv_line.icms_origem)
                self.assertEqual(line.incluir_ipi_base, inv_line.incluir_ipi_base)
                self.assertEqual(line.icms_st_aliquota_mva, inv_line.icms_st_aliquota_mva)
                self.assertEqual(line.icms_aliquota_inter_part, inv_line.icms_aliquota_inter_part)
                self.assertEqual(line.icms_aliquota_reducao_base, inv_line.icms_aliquota_reducao_base)
                self.assertEqual(line.icms_st_aliquota_reducao_base, inv_line.icms_st_aliquota_reducao_base)
                self.assertEqual(line.icms_st_aliquota_deducao, inv_line.icms_st_aliquota_deducao)
                self.assertEqual(line.icms_aliquota_credito, inv_line.icms_aliquota_credito)
                self.assertEqual(line.tem_difal, inv_line.tem_difal)
                self.assertEqual(line.icms_csosn_simples, inv_line.icms_csosn_simples)
                self.assertEqual(line.icms_origem, inv_line.icms_origem)
                self.assertEqual(line.incluir_ipi_base, inv_line.incluir_ipi_base)
                self.assertEqual(line.icms_rule_id, inv_line.icms_rule_id)
                self.assertEqual(line.ipi_cst, inv_line.ipi_cst)
                self.assertEqual(line.ipi_reducao_bc, inv_line.ipi_reducao_bc)
                self.assertEqual(line.ipi_rule_id, inv_line.ipi_rule_id)
                self.assertEqual(line.pis_cst, inv_line.pis_cst)
                self.assertEqual(line.pis_tipo, inv_line.pis_tipo)
                self.assertEqual(line.pis_rule_id, inv_line.pis_rule_id)
                self.assertEqual(line.cofins_cst, inv_line.cofins_cst)
                self.assertEqual(line.cofins_tipo, inv_line.cofins_tipo)
                self.assertEqual(line.cofins_rule_id, inv_line.cofins_rule_id)
                self.assertEqual(line.issqn_tipo, inv_line.issqn_tipo)
                self.assertEqual(line.ii_valor_despesas, inv_line.ii_valor_despesas)
                self.assertEqual(line.ii_valor_iof, inv_line.ii_valor_iof)
                self.assertEqual(line.ii_rule_id, inv_line.ii_rule_id)
                self.assertEqual(line.csll_rule_id, inv_line.csll_rule_id)
                self.assertEqual(line.irrf_rule_id, inv_line.irrf_rule_id)
                self.assertEqual(line.inss_rule_id, inv_line.inss_rule_id)

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

            self.assertEqual(len(sale.parcel_ids), 1)

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

    def test_create_invoice_percent(self):

        for sale in self.sales_order:

            context = {
                'active_model': 'sale.order', 
                'active_ids': [sale.id], 
                'active_id': sale.id,
            }

            sale.with_context(context).action_confirm()

            # Criamos a wizard para criação da Invoice
            payment = self.env['sale.advance.payment.inv'].create({
                'advance_payment_method': 'percentage',
                'amount': 100,
                'product_id': self.service.id,
            })

            # Criamos as invoices
            payment.with_context(context).create_invoices()

            # Recuperamos a fatura criada
            invoice = self.env['account.invoice'].search([('origin', '=', sale.name)])

            self.assertEqual(invoice.pre_invoice_date, sale.confirmation_date[:10])
            self.assertEqual(len(invoice.parcel_ids), len(sale.parcel_ids))

            for inv_parcel, order_parcel in zip(invoice.parcel_ids, sale.parcel_ids):
                self.assertEqual(inv_parcel.name, order_parcel.name)
                self.assertEqual(inv_parcel.date_maturity, order_parcel.date_maturity)
                self.assertEqual(inv_parcel.old_date_maturity, order_parcel.old_date_maturity)
                self.assertEqual(inv_parcel.financial_operation_id, order_parcel.financial_operation_id)
                self.assertEqual(inv_parcel.title_type_id, order_parcel.title_type_id)
                self.assertEqual(inv_parcel.pin_date, order_parcel.pin_date)

    def test_create_invoice_price_fix(self):

        for sale in self.sales_order:

            context = {
                'active_model': 'sale.order', 
                'active_ids': [sale.id], 
                'active_id': sale.id,
            }

            sale.with_context(context).action_confirm()

            # Criamos a wizard para criação da Invoice
            payment = self.env['sale.advance.payment.inv'].create({
                'advance_payment_method': 'fixed',
                'amount': 5,
                'product_id': self.service.id,
            })

            # Criamos as invoices
            payment.with_context(context).create_invoices()

            # Recuperamos a fatura criada
            invoice = self.env['account.invoice'].search([('origin', '=', sale.name)])

            self.assertEqual(invoice.pre_invoice_date, sale.confirmation_date[:10])
            self.assertEqual(len(invoice.parcel_ids), len(sale.parcel_ids))

            for inv_parcel, order_parcel in zip(invoice.parcel_ids, sale.parcel_ids):
                self.assertEqual(inv_parcel.name, order_parcel.name)
                self.assertEqual(inv_parcel.date_maturity, order_parcel.date_maturity)
                self.assertEqual(inv_parcel.old_date_maturity, order_parcel.old_date_maturity)
                self.assertEqual(inv_parcel.financial_operation_id, order_parcel.financial_operation_id)
                self.assertEqual(inv_parcel.title_type_id, order_parcel.title_type_id)
                self.assertEqual(inv_parcel.pin_date, order_parcel.pin_date)

    def test_invoice_pis_cofins_taxes(self):

        for order in self.sales_order:

            first_item = order.order_line[0]

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

            for item in order.order_line:
                item.tax_pis_id = self.pis_500
                item._onchange_tax_pis_id()
                item._br_sale_onchange_product_id()
                self.assertEqual(item.pis_base_calculo, item.price_total)
                self.assertEqual(item.pis_aliquota, 5.0)
                self.assertEqual(item.pis_valor, item.price_total * 0.05)

                item.tax_cofins_id = self.cofins_1500
                item._onchange_tax_cofins_id()
                item._br_sale_onchange_product_id()
                self.assertEqual(item.cofins_base_calculo, item.price_total)
                self.assertEqual(item.cofins_aliquota, 15.0)
                self.assertEqual(item.cofins_valor, item.price_total * 0.15)

                self.assertEqual(len(item.tax_id), 2)

    def test_invoice_issqn_and_ii_taxes(self):

        for order in self.sales_order:
            prod_item = order.order_line[0]
            serv_item = order.order_line[1]

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

    def test_invoice_icms_normal_tax(self):

        for order in self.sales_order:

            first_item = order.order_line[0]

            # ICMS
            first_item.tax_icms_id = self.icms_1700
            first_item._onchange_tax_icms_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.icms_base_calculo, 150.0)
            self.assertEqual(first_item.icms_valor, 25.5)
            self.assertEqual(first_item.icms_aliquota, 17.0)

            for item in order.order_line:
                item.tax_icms_id = self.icms_1700
                item._onchange_tax_icms_id()
                item._br_sale_onchange_product_id()
                self.assertEqual(item.icms_base_calculo, item.price_total)
                self.assertEqual(
                    item.icms_valor, round(item.price_total * 0.17, 2))
                self.assertEqual(item.icms_aliquota, 17.0)

                self.assertEqual(len(item.tax_id), 1)

    def test_invoice_icms_reducao_base_tax(self):

        for order in self.sales_order:

            first_item = order.order_line[0]

            # ICMS com Redução de base
            first_item.tax_icms_id = self.icms_1700
            first_item.icms_aliquota_reducao_base = 10.0
            first_item._onchange_tax_icms_id()
            self.assertEqual(first_item.price_total, 150.0)
            self.assertEqual(first_item.icms_base_calculo, 135.0)
            self.assertEqual(first_item.icms_valor, 22.95)
            self.assertEqual(first_item.icms_aliquota, 17.0)

            for item in order.order_line:
                item.tax_icms_id = self.icms_1700
                item.icms_aliquota_reducao_base = 10.0
                item._onchange_tax_icms_id()
                item._br_sale_onchange_product_id()
                self.assertEqual(
                    item.icms_base_calculo, round(item.price_total * 0.9, 2))
                self.assertEqual(
                    item.icms_valor, round(item.price_total * 0.9 * 0.17, 2))
                self.assertEqual(item.icms_aliquota, 17.0)

                self.assertEqual(len(item.tax_id), 1)

    def test__onchange_fiscal_position_id(self):

        for order in self.sales_order:

            first_item = order.order_line[0]

            res = first_item._onchange_fiscal_position_id()

            self.assertIn('domain', res)
            self.assertIn('product_id', res['domain'])
            self.assertIn(('sale_ok', '=', True), res['domain']['product_id'])
            self.assertIn(('fiscal_type', '=', self.fpos.position_type), res['domain']['product_id'])

    def test_validate_date_maturity_from_parcels(self):

        for inv in self.sales_order:
            old_quotation_date = inv.quotation_date

            inv.quotation_date = str(datetime.strptime(
                inv.quotation_date, '%Y-%m-%d') + timedelta(days=700))

            with self.assertRaises(UserError):
                inv.validate_date_maturity_from_parcels()

            inv.quotation_date = old_quotation_date
            inv.validate_date_maturity_from_parcels()

    def test_compare_total_parcel_value(self):

        for inv in self.sales_order:
            self.assertTrue(inv.compare_total_parcel_value())

            # Mudamos o valor da fatura para disparar o erro
            inv.amount_total = '1000.00'

            self.assertTrue(inv.parcel_ids)
            self.assertFalse(inv.compare_total_parcel_value())

    def test_action_br_sale_confirm(self):

        for inv in self.sales_order:
            self.assertTrue(inv.action_br_sale_confirm())

            inv.amount_total = '2000.00'
            with self.assertRaises(UserError):
                inv.action_br_sale_confirm()

            inv.parcel_ids = False
            with self.assertRaises(ValidationError):
                inv.action_br_sale_confirm()
