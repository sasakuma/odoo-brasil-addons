# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os

import warnings
from cryptography.utils import CryptographyDeprecationWarning

# Usado para evitar warnings da urllib3 durante os testes
import urllib3
from mock import patch
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from pytrustnfe.xml import sanitize_response

urllib3.disable_warnings(category=InsecureRequestWarning)


class TestNFeBrasil(TransactionCase):
    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestNFeBrasil, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')

        with open(os.path.join(self.caminho, 'teste.pfx'), 'rb') as f:
            nfe_a1_file = f.read()

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
            'nfe_a1_file': base64.b64encode(nfe_a1_file),
        })

        self.main_company.write({'inscr_est': '219.882.606'})

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

        partner_obj = self.env['res.partner']

        self.partner_fisica = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '545.770.154-98',
            'company_type': 'person',
            'is_company': False,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

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

        self.partner_fisica_inter = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '793.493.171-92',
            'company_type': 'person',
            'is_company': False,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_rs').id,
            'city_id': self.env.ref('br_base.city_4304606').id,
        })

        self.partner_juridica_inter = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '08.326.476/0001-29',
            'company_type': 'company',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_rs').id,
            'city_id': self.env.ref('br_base.city_4300406').id,
        })

        self.partner_juridica_sp = partner_obj.create({
            **default_partner,
            'cnpj_cpf': '37.484.824/0001-94',
            'company_type': 'company',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sp').id,
            'city_id': self.env.ref('br_base.city_3501608').id,
        })

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
        })
        self.fpos_consumo = self.env['account.fiscal.position'].create({
            'name': 'Venda Consumo',
            'ind_final': '1',
        })
        invoice_line_incomplete = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
             }
             ),
            (0, 0,
             {
                 'product_id': self.service.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
                 'product_type': self.service.fiscal_type,
             }
             )
        ]
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

        serie = self.env['br_account.document.serie'].search([
            ('fiscal_document_id', '=', fiscal_document.id),
        ])

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

        self.inv_incomplete = self.env['account.invoice'].create({
            'name': 'Teste Validação Incompleta',
            'reference_type': 'none',
            'fiscal_document_id': self.env.ref('br_data_account.fiscal_document_55').id,
            'journal_id': self.journalrec.id,
            'partner_id': self.partner_fisica.id,
            'account_id': self.receivable_account.id,
            'invoice_line_ids': invoice_line_incomplete,
            'payment_term_id': payment_term.id,
        })

        self.inv_incomplete.generate_parcel_entry(self.financial_operation,
                                                  self.title_type)

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

    def test_computed_fields(self):

        for invoice in self.invoices:
            self.assertEqual(invoice.total_edocs, 0)
            self.assertEqual(invoice.nfe_number, 0)
            self.assertEqual(invoice.nfe_exception_number, 0)
            self.assertEqual(invoice.nfe_exception, False)
            self.assertEqual(invoice.sending_nfe, False)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Verifica algumas propriedades computadas que dependem do edoc
            self.assertEqual(invoice.total_edocs, 1)
            self.assertTrue(invoice.nfe_number != 0)
            self.assertTrue(invoice.nfe_exception_number != 0)
            self.assertEqual(invoice.nfe_exception, False)
            self.assertEqual(invoice.sending_nfe, True)

    def test_check_invoice_electronic_values(self):

        for invoice in self.invoices:

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            inv_eletr = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            # TODO Validar os itens que foi setado no invoice e verficar
            # com o documento eletronico
            self.assertEqual(inv_eletr.partner_id, invoice.partner_id)

    def test_nfe_validation(self):
        with self.assertRaises(UserError):
            self.inv_incomplete.action_br_account_invoice_open()

    def test_send_nfe(self):

        with warnings.catch_warnings():
            # correcao temporaria para suprimir erro de warning
            # da lib cryptography causado pelo modulo signxml
            # E corrigido neste PR: https://github.com/XML-Security/signxml/pull/106
            # Assim que o modulo for atualizado, deve-se remover este contexto
            warnings.simplefilter('ignore', CryptographyDeprecationWarning)

            for invoice in self.invoices:

                # Confirmando a fatura deve gerar um documento eletrônico
                invoice.action_br_account_invoice_open()

                invoice_electronic = self.env['invoice.electronic'].search(
                    [('invoice_id', '=', invoice.id)])

                with self.assertRaises(Exception):
                    invoice_electronic.action_send_electronic_invoice()

    @patch('odoo.addons.br_nfe.models.invoice_electronic.retorno_autorizar_nfe')
    @patch('odoo.addons.br_nfe.models.invoice_electronic.autorizar_nfe')
    def test_success_xml_schema(self, autorizar, ret_autorizar):

        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'lote-recebido-sucesso.xml')) as xml:
                xml_recebido = xml.read()

            resp = sanitize_response(xml_recebido.encode('utf8'))

            # Precisamos atribuir abaixo porque quando a NFe possui codigo de retorno 100
            # o modulo verifica o conteudo do xml de envio em busca da tag NFe, de modo
            # a gerar o conteudo do campo 'nfe_processada'
            sent_xml = '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe></NFe></nfeProc>'

            autorizar.return_value = {
                'object': resp[1],
                'sent_xml': sent_xml,
                'received_xml': xml_recebido,
            }

            # Consultar recibo com erro 100
            with open(os.path.join(self.caminho, 'xml', 'recibo-sucesso-schema-100.xml')) as xml:
                xml_recebido = xml.read()

            resp_ret = sanitize_response(xml_recebido.encode('utf8'))

            ret_autorizar.return_value = {
                'object': resp_ret[1],
                'sent_xml': sent_xml,
                'received_xml': xml_recebido,
            }

            invoice_electronic = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            invoice_electronic.action_send_electronic_invoice()
            self.assertEqual(invoice_electronic.state, 'done')
            self.assertEqual(invoice_electronic.codigo_retorno, '100')
            self.assertTrue(invoice_electronic.nfe_processada)
            self.assertEqual(
                invoice_electronic.nfe_processada_name, "NFe%08d.xml" % invoice_electronic.numero)

    @patch('odoo.addons.br_nfe.models.invoice_electronic.retorno_autorizar_nfe')
    @patch('odoo.addons.br_nfe.models.invoice_electronic.autorizar_nfe')
    def test_wrong_xml_schema(self, autorizar, ret_autorizar):

        for invoice in self.invoices:

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'lote-recebido-sucesso.xml')) as xml:
                xml_recebido = xml.read()

            resp = sanitize_response(xml_recebido.encode('utf8'))

            autorizar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido,
            }

            # Consultar recibo com erro 225
            with open(os.path.join(self.caminho, 'xml', 'recibo-erro-schema-225.xml')) as xml:
                xml_recebido = xml.read()

            resp_ret = sanitize_response(xml_recebido.encode('utf8'))

            ret_autorizar.return_value = {
                'object': resp_ret[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_electronic = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            invoice_electronic.action_send_electronic_invoice()

            self.assertEqual(invoice_electronic.state, 'error')
            self.assertEqual(invoice_electronic.codigo_retorno, '225')

    @patch('odoo.addons.br_nfe.models.invoice_electronic.retorno_autorizar_nfe')
    @patch('odoo.addons.br_nfe.models.invoice_electronic.autorizar_nfe')
    def test_nfe_with_concept_error(self, autorizar, ret_autorizar):

        for invoice in self.invoices:

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'lote-recebido-sucesso.xml')) as xml:
                xml_recebido = xml.read()

            resp = sanitize_response(xml_recebido.encode('utf8'))

            autorizar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            # Consultar recibo com erro 694 - Nao informado o DIFAL
            with open(os.path.join(self.caminho, 'xml', 'recibo-erro-694.xml')) as xml:
                xml_recebido = xml.read()

            resp_ret = sanitize_response(xml_recebido.encode('utf8'))

            ret_autorizar.return_value = {
                'object': resp_ret[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_electronic = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            invoice_electronic.action_send_electronic_invoice()
            self.assertEqual(invoice_electronic.state, 'error')
            self.assertEqual(invoice_electronic.codigo_retorno, '694')

    @patch('odoo.addons.br_nfe.models.invoice_electronic.recepcao_evento_cancelamento')
    def test_nfe_cancelamento_ok(self, cancelar):

        for invoice in self.invoices:

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'cancelamento-sucesso.xml')) as xml:
                xml_recebido = xml.read()

            resp = sanitize_response(xml_recebido)

            cancelar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_electronic = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            invoice_electronic.action_cancel_document(
                justificativa="Cancelamento de teste")

            self.assertEqual(invoice_electronic.state, 'cancel')
            self.assertEqual(invoice_electronic.codigo_retorno, "155")
            self.assertEqual(invoice_electronic.mensagem_retorno,
                             "Cancelamento homologado fora de prazo")

    def test_barcode_from_chave_nfe(self):

        for invoice in self.invoices:

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            invoice_electronic = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            # Adicionamos uma chave especifica para o doc. eletronico
            # Isso facilitara nossa comparacao com base64 do barcode
            invoice_electronic.chave_nfe = '35171256553878000109550010000150491600857152'

            # Geramos o barcode
            barcode = invoice_electronic.barcode_from_chave_nfe()

            self.assertEqual(barcode,
                             'iVBORw0KGgoAAAANSUhEUgAAAlgAAABkCAIAAADVI9l0AAA'
                             'ExUlEQVR4nO3VsUtV/xvA8YcvSSAk4VBhJEXSKphBOIiIQ'
                             '0aFuLQVNIiJaEmEhDa6tDWFQ0SUBDlEY0tQ0NAi2i3hQi'
                             'VEQRG4FbR8vsPhe7jpP/D78bxe23nO8znHe73wjvJ/pa+vLy'
                             'IiYmxsrJQyOzsbEevr69Xdp0+fRouDBw/WBycmJiKi2Wy2Pu'
                             '3KlSsR8enTp9bhpUuXquM9PT2llOXl5Yh4/PhxdXdzczP+9u'
                             'PHj+rW3bt36+H29vba2lpEXL9+vZRy/vz5an7q1Kn6RaOjo6'
                             '3PuXXrVn1rz549rbdevnzZ+hcuLi5GxOvXr//8+VPvLC0tlV'
                             'JOnz7devDOnTullP7+/n379u34Jnt7e6ud8fHxUsr09HRENB'
                             'qN1p3Jyclqp6ura8fx48ePd3d3l1IePHhQv25ra2v3v6yrq+'
                             'vEiROllHv37kXEkydPqnmj0agPrq6ullI6Ozury2vXrtXHOz'
                             'o6quGNGzfqYXt7ezWcn5+vh21tbdVwYWGhlDI8PFxdDg0N1T'
                             'uDg4PVcGRkpB4ODAzs3bu3vrx582ZEvH37tvVTzM3NtX6x1c'
                             '9vZmYmIjY2Nlo3p6amqp1Dhw6VUlZWVupTzWbzy5cv9eX9+/'
                             'erI58/f66HDx8+rIbNZrMerqysVMMPHz5ExNTUVOsbNzY2Im'
                             'JmZqae7N+/vzo4NzdXSjl37lx12frzO3PmTDUcGBiohyMjI9'
                             'VwcHCwHg4NDVXD4eHhUsrCwkJ12dbWVu/Mz89Xw/b29vK3ky'
                             'dPdnR0lFKePXvW+h12dnaWUlZXV+tJo9H4/v17RFy8eLH1CV'
                             '+/fo2/ffz4cWtrKyIuX75cr3V3d7fuPHr0qJTS1dVVXU5OTt'
                             'abBw4cqIbT09OllPHx8eqyt7e33rlw4UI17O/vr4dnz56NiF'
                             '+/flWXS0tLscvi4mK9H//9/G7fvh0Rr169quYvXryo99+8ef'
                             'P79++IGB0dLbs8f/683lxbW9ve3t7xunfv3rXuX716NSI2Nz'
                             'e/fftW7ywvL5dSenp6jhw5suP5R48ePXbs2I7h4cOHq4MTEx'
                             'Ot8/fv3+94+8+fP9fX1yNidna2lDI2NlbN+/r6dn+W/2X/7P'
                             '5HAkAeQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'pCCEBqQghAakIIQGpCCEBqQghAakIIQGpCCEBqQghAakIIQG'
                             'r/Ah8pMgpR9XqBAAAAAElFTkSuQmCC')
