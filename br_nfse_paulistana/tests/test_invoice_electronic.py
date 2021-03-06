# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
import logging
import mock
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.xml import sanitize_response
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


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
            'inscr_mun': '51212300',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sp').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'currency_id': self.currency_real.id,
            'tipo_ambiente_nfse': '2',
            'webservice_nfse': 'nfse_paulistana',
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(nfe_a1_file),
        })

        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })

        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })

        self.service_type = self.env.ref('br_data_account.service_type_101')
        self.service_type.codigo_servico_paulistana = '07498'

        self.title_type = self.env.ref('br_account.account_title_type_2')
        self.financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        payment_term = self.env.ref('account.account_payment_term_net')

        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0,
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

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda',
            'fiscal_document_id': self.env.ref(
                'br_nfse.fiscal_document_001').id,
            'document_serie_id': self.env.ref(
                'br_nfse.br_document_serie_1').id,
            'service_type_id': self.service_type.id,
            'position_type': 'service',
        })

        invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.service.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
                 'product_type': self.service.fiscal_type,
                 'cfop_id': self.env.ref(
                     'br_data_account_product.cfop_5101').id,
                 'pis_cst': '01',
                 'cofins_cst': '01',
             }
             )
        ]

        default_invoice = {
            'name': 'Teste Validação',
            'reference_type': 'none',
            'fiscal_document_id': self.env.ref('br_nfse.fiscal_document_001').id,
            'document_serie_id': self.env.ref('br_nfse.br_document_serie_1').id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data,
            'webservice_nfse': 'nfse_paulistana',
            'payment_term_id': payment_term.id,
        }

        self.invoices = self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_fisica.id
        })
        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'partner_id': self.partner_juridica.id
        })

    def test_computed_fields(self):

        for invoice in self.invoices:
            self.assertEqual(invoice.total_edocs, 0)
            self.assertEqual(invoice.nfse_number, 0)
            self.assertEqual(invoice.nfse_exception_number, 0)
            self.assertEqual(invoice.nfse_exception, False)
            self.assertEqual(invoice.sending_nfse, False)

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Verifica algumas propriedades computadas que dependem do edoc
            self.assertEqual(invoice.total_edocs, 1)
            self.assertTrue(invoice.nfse_number != 0)
            self.assertTrue(invoice.nfse_exception_number != 0)
            self.assertEqual(invoice.nfse_exception, False)
            self.assertEqual(invoice.sending_nfse, True)

    def test_check_invoice_electronic_values(self):

        for invoice in self.invoices:

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            elec_inv = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            # TODO Validar os itens que foi setado no invoice e verficar
            #  com o documento eletronico
            self.assertEqual(elec_inv.partner_id, invoice.partner_id)

    @mock.patch('pytrustnfe.nfse.paulistana.teste_envio_lote_rps')
    def test_nfse_sucesso_homologacao(self, envio_lote):

        for invoice in self.invoices:

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'nfse-sucesso.xml')) as xml:
                xml_recebido = xml.read().replace('\n', '')

            resp = sanitize_response(xml_recebido.encode('utf8'))

            envio_lote.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido,
            }

            elec_inv = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            elec_inv.action_send_electronic_invoice()

            self.assertEqual(elec_inv.state, 'done')
            self.assertEqual(elec_inv.codigo_retorno, '100')
            self.assertEqual(elec_inv.numero_nfse, '99999999')
            self.assertEqual(elec_inv.verify_code, 'XXXXXXXX')
            self.assertEqual(elec_inv.invoice_id.internal_number,
                             99999999)

            events = elec_inv.electronic_event_ids

            self.assertEqual(len(events), 1)
            self.assertEqual(events.code, '100')
            self.assertEqual(events.name, elec_inv.mensagem_retorno)
            self.assertEqual(events.category, 'info')

    @mock.patch('pytrustnfe.nfse.paulistana.envio_lote_rps')
    def test_nfse_return_code_224(self, envio_lote):

        # Necessario alterar o ambiente de consulta porque o
        # erro 224 ocorre apenas em ambiente de producao
        self.main_company.tipo_ambiente_nfse = '1'

        for invoice in self.invoices:

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'retorno_envio_loterps_nfse_alertas.xml')) as xml:
                xml_recebido = xml.read().replace('\n', '')

            resp = sanitize_response(xml_recebido)

            envio_lote.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido,
            }

            elec_inv = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])
            elec_inv.action_send_electronic_invoice()

            self.assertEqual(elec_inv.state, 'done')
            self.assertEqual(elec_inv.codigo_retorno, '100')
            self.assertEqual(elec_inv.numero_nfse, '99999999')
            self.assertEqual(elec_inv.mensagem_retorno,
                             'Nota Fiscal Paulistana emitida com sucesso')
            self.assertEqual(elec_inv.invoice_id.internal_number, 99999999)

            events = elec_inv.electronic_event_ids

            # Devemos ter 2 eventos do tipo 'warning', uma vez que o 
            # xml de teste possui dos 'Alertas'
            warnings = events.filtered(lambda r: r.category == 'warning')

            self.assertEqual(len(warnings), 2)

            for warn in warnings:
                self.assertIn(warn.code, ['221', '224'])

            # Informação a respeito mensagem de retorno da NFSe
            info = events.filtered(lambda r: r.category == 'info')

            self.assertEqual(len(info), 1)
            self.assertEqual(info.code, '100')
            

    @mock.patch('pytrustnfe.nfse.paulistana.cancelamento_nfe')
    def test_nfse_cancel(self, cancelar):

        for invoice in self.invoices:

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'cancelamento-sucesso.xml')) as xml:
                xml_recebido = xml.read().replace('\n', '')

            resp = sanitize_response(xml_recebido.encode('utf8'))

            cancelar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido,
            }

            elec_inv = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            elec_inv.verify_code = '123'
            elec_inv.numero_nfse = '123'
            elec_inv.action_cancel_document(justificativa='Cancelamento de teste')

            self.assertEqual(elec_inv.state, 'cancel')
            self.assertEqual(elec_inv.codigo_retorno, '100')
            self.assertEqual(elec_inv.mensagem_retorno, 'Nota Fiscal Paulistana Cancelada')

            events = elec_inv.electronic_event_ids

            self.assertEqual(len(events), 1)
            self.assertEqual(events.code, '100')
            self.assertEqual(events.name, elec_inv.mensagem_retorno)
            self.assertEqual(events.category, 'info')

    @mock.patch('pytrustnfe.nfse.paulistana.cancelamento_nfe')
    def test_nfse_cancelamento_erro(self, cancelar):

        for invoice in self.invoices:

            # Cria parcelas
            invoice.generate_parcel_entry(self.financial_operation,
                                          self.title_type)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_br_account_invoice_open()

            # Lote recebido com sucesso
            with open(os.path.join(self.caminho, 'xml', 'cancelamento-erro.xml')) as xml:
                xml_recebido = xml.read().replace('\n', '')

            resp = sanitize_response(xml_recebido.encode('utf8'))

            cancelar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido,
            }

            elec_inv = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])
            elec_inv.verify_code = '123'
            elec_inv.numero_nfse = '123'

            elec_inv.ambiente = 'producao'

            elec_inv.action_cancel_document(
                justificativa='Cancelamento de teste')

            # Draft because I didn't send it
            self.assertEqual(elec_inv.state, 'draft')
            self.assertEqual(elec_inv.codigo_retorno, '1305')
            self.assertEqual(elec_inv.mensagem_retorno,
                             'Assinatura de cancelamento da NFS-e incorreta.')

            events = elec_inv.electronic_event_ids

            self.assertEqual(len(events), 1)
            self.assertEqual(events.code, elec_inv.codigo_retorno)
            self.assertEqual(events.name, elec_inv.mensagem_retorno)
            self.assertEqual(events.category, 'error')
