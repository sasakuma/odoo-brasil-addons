# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    import pytrustnfe.nfse.paulistana
    import pytrustnfe.certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')

STATE = {'edit': [('readonly', False)]}


class InvoiceElectronicItem(models.Model):
    _inherit = 'invoice.electronic.item'

    codigo_servico_paulistana = fields.Char(string=u'Código NFSe Paulistana',
                                            size=5,
                                            readonly=True,
                                            states=STATE)


class InvoiceElectronic(models.Model):
    _inherit = 'invoice.electronic'

    webservice_nfse = fields.Selection(selection_add=[
        ('nfse_paulistana', 'Nota Fiscal Paulistana'),
    ])

    observacao_nfse = fields.Text(string=u'Observação NFSe')

    # operation = fields.Selection(
    #     [('T', u'Tributado em São Paulo'),
    #      ('F', u'Tributado Fora de São Paulo'),
    #      ('A', u'Tributado em São Paulo, porém isento'),
    #      ('B', u'Tributado Fora de São Paulo, porém isento'),
    #      ('M', u'Tributado em São Paulo, porém Imune'),
    #      ('N', u'Tributado Fora de São Paulo, porém Imune'),
    #      ('X', u'Tributado em São Paulo, porém Exigibilidade Suspensa'),
    #      ('V', u'Tributado Fora de São Paulo, porém Exigibilidade Suspensa'),
    #      ('P', u'Exportação de Serviços'),
    #      ('C', u'Cancelado')],
    #     string=u'Operação',
    #     default='T',
    #     readonly=True,
    #     states=STATE)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceElectronic, self)._hook_validation()

        if self.model == '001' and self.webservice_nfse == 'nfse_paulistana':
            issqn_codigo = ''
            if not self.company_id.inscr_mun:
                errors.append(u'Inscrição municipal obrigatória')
            for eletr in self.electronic_item_ids:
                prod = u'Produto: %s - %s' % (eletr.product_id.default_code,
                                              eletr.product_id.name)
                if eletr.tipo_produto == 'product':
                    errors.append(
                        u'Esse documento permite apenas serviços - %s' % prod)
                if eletr.tipo_produto == 'service':
                    if not eletr.issqn_codigo:
                        errors.append(u'%s - Código de Serviço' % prod)
                    if not issqn_codigo:
                        issqn_codigo = eletr.issqn_codigo
                    if issqn_codigo != eletr.issqn_codigo:
                        errors.append(u'%s - Apenas itens com o mesmo código \
                                      de serviço podem ser enviados' % prod)
                    if not eletr.codigo_servico_paulistana:
                        errors.append(u'%s - Código da NFSe paulistana não \
                                      configurado' % prod)
                if not eletr.pis_cst:
                    errors.append(u'%s - CST do PIS' % prod)
                if not eletr.cofins_cst:
                    errors.append(u'%s - CST do Cofins' % prod)

        return errors

    @api.multi
    def _prepare_electronic_invoice_values(self):
        res = super(InvoiceElectronic, self)._prepare_electronic_invoice_values()  # noqa: 501

        if self.model == '001' and self.webservice_nfse == 'nfse_paulistana':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%d')

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            tomador = {
                'tipo_cpfcnpj': 2 if partner.is_company else 1,
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or '',
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'cidade_descricao': city_tomador.name or '',
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'telefone': re.sub('[^0-9]', '', partner.phone or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or ''),
                'email': self.partner_id.email or partner.email or '',
            }
            city_prestador = self.company_id.partner_id.city_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'razao_social': self.company_id.partner_id.legal_name or '',
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'telefone': re.sub('[^0-9]', '', self.company_id.phone or ''),
                'email': self.company_id.partner_id.email or '',
            }

            descricao = ''
            codigo_servico = ''
            for item in self.electronic_item_ids:
                descricao += item.name + '\n'
                codigo_servico = item.codigo_servico_paulistana

            if self.informacoes_legais:
                descricao += self.informacoes_legais + '\n'
            if self.informacoes_complementares:
                descricao += self.informacoes_complementares

            rps = {
                'tomador': tomador,
                'prestador': prestador,
                'numero': self.numero,
                'data_emissao': dt_emissao,
                'serie': self.serie.code or '',
                'aliquota_atividade': '0.000',
                'codigo_atividade': re.sub('[^0-9]', '', codigo_servico or ''),
                'municipio_prestacao': city_prestador.name or '',
                'valor_pis': str("%.2f" % self.valor_pis),
                'valor_cofins': str("%.2f" % self.valor_cofins),
                'valor_csll': str("%.2f" % 0.0),
                'valor_inss': str("%.2f" % 0.0),
                'valor_ir': str("%.2f" % 0.0),
                'aliquota_pis': str("%.2f" % 0.0),
                'aliquota_cofins': str("%.2f" % 0.0),
                'aliquota_csll': str("%.2f" % 0.0),
                'aliquota_inss': str("%.2f" % 0.0),
                'aliquota_ir': str("%.2f" % 0.0),
                'valor_servico': str("%.2f" % self.valor_final),
                'valor_deducao': '0',
                'descricao': descricao,
                'deducoes': [],
            }

            valor_servico = self.valor_final
            valor_deducao = 0.0

            cnpj_cpf = tomador['cpf_cnpj']
            data_envio = rps['data_emissao']
            inscr = prestador['inscricao_municipal']
            iss_retido = 'N'
            tipo_cpfcnpj = tomador['tipo_cpfcnpj']
            codigo_atividade = rps['codigo_atividade']
            tipo_recolhimento = \
                self.fiscal_position_id.nfse_source_operation_id.code

            assinatura = '%s%s%s%s%sN%s%015d%015d%s%s%s' % (
                str(inscr).zfill(8),
                self.serie.code.ljust(5),
                str(self.numero).zfill(12),
                str(data_envio[0:4] + data_envio[5:7] + data_envio[8:10]),
                str(tipo_recolhimento),
                str(iss_retido),
                round(valor_servico * 100),
                round(valor_deducao * 100),
                str(codigo_atividade).zfill(5),
                str(tipo_cpfcnpj),
                str(cnpj_cpf).zfill(14)
            )
            rps['assinatura'] = assinatura

            nfse_vals = {
                'cidade': prestador['cidade'],
                'cpf_cnpj': prestador['cnpj'],
                'remetente': prestador['razao_social'],
                'transacao': '',
                'data_inicio': dt_emissao,
                'data_fim': dt_emissao,
                'total_rps': '1',
                'total_servicos': str("%.2f" % self.valor_final),
                'total_deducoes': '0',
                'lote_id': '%s' % self.code,
                'lista_rps': [rps]
            }

            res.update(nfse_vals)
        return res

    @api.multi
    def action_send_electronic_invoice(self):
        super(InvoiceElectronic, self).action_send_electronic_invoice()

        if self.model == '001' and self.webservice_nfse == 'nfse_paulistana':
            self.state = 'error'

            nfse_values = self._prepare_electronic_invoice_values()
            cert = self.company_id.with_context(
                {'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)

            certificado = pytrustnfe.certificado.Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            if self.ambiente == 'producao':
                resposta = pytrustnfe.nfse.paulistana.envio_lote_rps(
                    certificado, nfse=nfse_values)
            else:
                resposta = pytrustnfe.nfse.paulistana.teste_envio_lote_rps(
                    certificado, nfse=nfse_values)

            retorno = resposta['object']

            values = {}

            if retorno.Cabecalho.Sucesso:
                values.update({
                    'state': 'done',
                    'codigo_retorno': '100',
                    'mensagem_retorno': 'Nota Fiscal Paulistana emitida com '
                                        'sucesso',
                })

                if self.ambiente == 'producao':  # Apenas producao tem essa tag
                    values.update({
                        'verify_code': retorno.ChaveNFeRPS.ChaveNFe.CodigoVerificacao,  # noqa: 501
                        'numero_nfse': retorno.ChaveNFeRPS.ChaveNFe.NumeroNFe,
                    })

                self.write(values)

            else:
                values.update({
                    'codigo_retorno': retorno.Erro.Codigo,
                    'mensagem_retorno': retorno.Erro.Descricao,
                })

                self.write(values)

            self.env['invoice.electronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_electronic_id': self.id,
            })
            self._create_attachment('nfse-envio', self, resposta['sent_xml'])
            self._create_attachment('nfse-ret', self, resposta['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):

        if self.model == '001' and self.webservice_nfse == 'nfse_paulistana':

            cert = self.company_id.with_context({'bin_size': False})
            cert_pfx = base64.decodestring(cert.nfe_a1_file)

            certificado = pytrustnfe.certificado.Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            company = self.company_id

            canc = {
                'cnpj_remetente': re.sub('[^0-9]', '', company.cnpj_cpf),
                'inscricao_municipal': re.sub('[^0-9]', '', company.inscr_mun),
                'numero_nfse': self.numero_nfse,
                'codigo_verificacao': self.verify_code,
                'assinatura': '%s%s' % (
                    re.sub('[^0-9]', '', company.inscr_mun),
                    self.numero_nfse.zfill(12)
                    if self.numero_nfse else ''.zfill(12)
                )
            }

            resposta = pytrustnfe.nfse.paulistana.cancelamento_nfe(
                certificado, cancelamento=canc)

            retorno = resposta['object']

            if self.ambiente == 'homologacao':
                # Se enviamos a nota em homologacao, entao a mesma nao será
                # criada no servidor e assim nao podemos cancelá-la. Sendo
                # assim, simulamos um retorno em sucedido
                retorno.Cabecalho.Sucesso = True

            values = {}

            if retorno.Cabecalho.Sucesso:
                values.update({
                    'state': 'cancel',
                    'codigo_retorno': '100',
                    'mensagem_retorno': 'Nota Fiscal Paulistana Cancelada',
                })
            else:
                values.update({
                    'codigo_retorno': retorno.Erro.Codigo,
                    'mensagem_retorno': retorno.Erro.Descricao,
                })

            self.write(values)

            self.env['invoice.electronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_electronic_id': self.id,
            })

            if self.ambiente == 'producao':
                self._create_attachment('canc', self, resposta['sent_xml'])
                self._create_attachment('canc-ret', self,
                                        resposta['received_xml'])

        else:
            return super(InvoiceElectronic, self).action_cancel_document(
                justificativa=justificativa, context=context)

    @api.multi
    def action_print_danfse(self):
        action = super(InvoiceElectronic, self).action_print_danfse()

        if self.model == '001' and self.webservice_nfse == 'nfse_paulistana':

            if self.invoice_id.company_id.report_nfse_id:
                report = self.invoice_id.company_id.report_nfse_id.report_name

                action = self.env['report'].get_action(self.ids, report)
                action['report_type'] = 'qweb-pdf'

            else:
                raise UserError(
                    u'Não existe um template de relatorio para NFSe '
                    u'selecionado para a empresa emissora desta Fatura. '
                    u'Por favor, selecione um template no cadastro da empresa')

        return action

    def get_nfse_observation_text(self):

        aux = []

        if self.invoice_id.invoice_model == '001' and self.webservice_nfse == 'nfse_paulistana':  # noqa: 501

            observacao_nfse = (u'(#) Esta NFS-e foi emitida com respaldo na '
                               u'Lei nº 14.097/2005; ')

            tributacao = self.fiscal_position_id.nfse_source_operation_id.code

            aux.append(observacao_nfse)

            # O documento eletronico e uma NFSe que foi enviada com sucesso
            if self.state == 'done':

                if self.company_id.fiscal_type == '1':
                    observacao_nfse = (u'(#) Documento emitido por ME ou EPP '
                                       u'optante pelo Simples Nacional; ')

                    aux.append(observacao_nfse)

                docs = self.env['invoice.electronic'].search([
                    ('invoice_id', '=', self.invoice_id.id),
                    ('state', '=', 'cancel'),
                ])

                if docs:
                    observacao_nfse = (u'(#) Esta NFS-e substitui a NFS-e '
                                       u'N° %s; ' % docs[0].numero_nfse)
                    aux.append(observacao_nfse)

                if tributacao == 'T':
                    observacao_nfse = (u'(#) Data de vencimento do ISS desta '
                                       u'NFS-e: %s; ' % self.issqn_due_date())
                    aux.append(observacao_nfse)

                    # Partner estabelecido na cidade de SP
                    issqn_tipo = self.electronic_item_ids[0].issqn_codigo

                    if self.partner_id.city_id.ibge_code == '50308' \
                            and issqn_tipo == 'R':
                        observacao_nfse = (u'(#) O ISS desta NFS-e será RETIDO'
                                           u' pelo Tomador de Serviço que '
                                           u'deverá recolher através da Guia '
                                           u'da NFS-e; ')
                        aux.append(observacao_nfse)

                elif tributacao == 'F':
                    observacao_nfse = (u'(#) O ISS desta NFS-e é devido FORA '
                                       u'do Município de São Paulo; ')
                    aux.append(observacao_nfse)

                    issqn_tipo = self.electronic_item_ids[0].issqn_codigo

                    if issqn_tipo == 'R':
                        observacao_nfse = (u'(#) O ISS desta NFS-e será RETIDO'
                                           u' pelo Tomador de Serviço; ')
                        aux.append(observacao_nfse)

                elif tributacao in ['A', 'B', 'M', 'N']:
                    observacao_nfse = (u'(#) Os serviços referentes a esta '
                                       u'NFS-e são Isentos/Imunes do ISS; ')
                    aux.append(observacao_nfse)

                elif tributacao in ['X', 'V']:
                    observacao_nfse = (u'(#) ISS suspenso por decisão '
                                       u'judicial; ')
                    aux.append(observacao_nfse)

            elif self.state == 'cancel':
                event = self.electronic_event_ids.search([
                    ('name', '=', 'Nota Fiscal Paulistana Cancelada')])

                observacao_nfse = (u'(#) Esta NFS-e foi CANCELADA em: %s; '
                                   % event[0].create_date)

                aux.append(observacao_nfse)

            elif self.state == 'draft':

                observacao_nfse = (u'(#) O RPS deverá ser substituído '
                                   u'por NF-e até o 10º (décimo) dia '
                                   u'subsequente ao de sua emissão; '
                                   u'\nA não substituição deste RPS '
                                   u'pela NF-e, ou a substituição fora '
                                   u'do prazo, sujeitará o prestador '
                                   u'de serviços às penalidades previstas '
                                   u'na legislação em vigor')
                aux.append(observacao_nfse)

            if self.state in ['done', 'cancel']:
                observacao_nfse = (u'(#) Esta NFS-e substitui o RPS Nº %d '
                                   u'Série %s, emitido em %s; ' %
                                   (self.numero,
                                    self.serie.code,
                                    self.data_emissao[:10]))
                aux.append(observacao_nfse)

            observacao_nfse = ''

            for index, value in enumerate(aux):
                observacao_nfse += value.replace('#', '%d' % (index + 1))

        return observacao_nfse

    def get_reg_code(self):
        """ Retorna codigo data_emissaoucnpjcpf presente no header do danfse"""

        if self.invoice_id.invoice_model == '001' and self.webservice_nfse == 'nfse_paulistana':  # noqa: 501

            cnpj_cpf = self.company_id.partner_id.cnpj_cpf.replace('.', '')
            cnpj_cpf = cnpj_cpf.replace('-', '')
            cnpj_cpf = cnpj_cpf.replace('/', '')

            send_date = self.data_emissao.replace('-', '')[:8]

            return send_date + 'u' + cnpj_cpf
        else:
            return ''
