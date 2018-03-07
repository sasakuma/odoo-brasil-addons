# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import base64
import logging
import time
from werkzeug import exceptions, url_decode

from datetime import datetime
from odoo import api, fields, models
from odoo.http import Controller, route, request
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import autorizar_nfe
    from pytrustnfe.nfe import retorno_autorizar_nfe
    from pytrustnfe.nfe import recepcao_evento_cancelamento
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.utils import ChaveNFe, gerar_chave, gerar_nfeproc
    from pytrustnfe.nfe.danfe import danfe
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)

STATE = {'edit': [('readonly', False)]}


class InvoiceElectronic(models.Model):
    _inherit = 'invoice.electronic'

    @api.multi
    @api.depends('chave_nfe')
    def _format_danfe_key(self):
        for item in self:
            item.chave_nfe_danfe = re.sub("(.{4})", "\\1.", item.chave_nfe, 10, re.DOTALL)  # noqa: 501

    @api.multi
    def generate_correction_letter(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.carta.correcao.eletronica',
            'views': [[False, 'form']],
            'name': 'Carta de Correção',
            'target': 'new',
            'context': {'default_electronic_doc_id': self.id},
        }

    state = fields.Selection(selection_add=[('denied', 'Denegado')])

    ambiente_nfe = fields.Selection(string='Ambiente NFe',
                                    related='company_id.tipo_ambiente',
                                    readonly=True)

    ind_final = fields.Selection([('0', 'Não'),
                                  ('1', 'Sim')],
                                 string='Consumidor Final',
                                 readonly=True,
                                 states=STATE,
                                 required=False,
                                 default='0',
                                 help='Indica operação com Consumidor final.')

    ind_pres = fields.Selection([('0', 'Não se aplica'),
                                 ('1', 'Operação presencial'),
                                 ('2', 'Operação não presencial, '
                                       'pela Internet'),
                                 ('3', 'Operação não presencial, '
                                       'Teleatendimento'),
                                 ('4', 'NFC-e em operação com entrega em '
                                       'domicílio'),
                                 ('9', 'Operação não presencial, outros')],
                                string='Indicador de Presença',
                                readonly=True,
                                states=STATE,
                                required=False,
                                default='0',
                                help='Indicador de presença do comprador no\n'
                                     'estabelecimento comercial no momento\n'
                                     'da operação.')

    ind_dest = fields.Selection([('1', '1 - Operação Interna'),
                                 ('2', '2 - Operação Interestadual'),
                                 ('3', '3 - Operação com exterior')],
                                string='Indicador Destinatário',
                                readonly=True,
                                states=STATE)

    ind_ie_dest = fields.Selection([('1', '1 - Contribuinte ICMS'),
                                    ('2', '2 - Contribuinte Isento de '
                                          'Cadastro'),
                                    ('9', '9 - Não Contribuinte')],
                                   string='Indicador IE Dest.',
                                   help='Indicador da IE do destinatário',
                                   readonly=True,
                                   states=STATE)

    tipo_emissao = fields.Selection([('1', '1 - Emissão normal'),
                                     ('2', '2 - Contingência FS-IA, '
                                           'com impressão do DANFE em '
                                           'formulário de segurança'),
                                     ('3', '3 - Contingência SCAN'),
                                     ('4', '4 - Contingência DPEC'),
                                     ('5', '5 - Contingência FS-DA, com '
                                           'impressão do DANFE em formulário '
                                           'de segurança'),
                                     ('6', '6 - Contingência SVC-AN'),
                                     ('7', '7 - Contingência SVC-RS'),
                                     ('9', '9 - Contingência off-line da NFC-e')],  # noqa: 501
                                    string='Tipo de Emissão',
                                    readonly=True,
                                    states=STATE,
                                    default='1')

    # Transporte
    modalidade_frete = fields.Selection([('0', '0 - Emitente'),
                                         ('1', '1 - Destinatário'),
                                         ('2', '2 - Terceiros'),
                                         ('9', '9 - Sem Frete')],
                                        string='Modalidade do frete',
                                        default='9',
                                        readonly=True,
                                        states=STATE)

    transportadora_id = fields.Many2one('res.partner',
                                        string='Transportadora',
                                        readonly=True,
                                        states=STATE)

    placa_veiculo = fields.Char(string='Placa do Veículo',
                                size=7,
                                readonly=True,
                                states=STATE)

    uf_veiculo = fields.Char(string='UF da Placa',
                             size=2,
                             readonly=True,
                             states=STATE)

    rntc = fields.Char(string='RNTC',
                       size=20,
                       readonly=True,
                       states=STATE,
                       help='Registro Nacional de Transportador de Carga')

    reboque_ids = fields.One2many(comodel_name='nfe.reboque',
                                  inverse_name='invoice_electronic_id',
                                  string='Reboques',
                                  readonly=True,
                                  states=STATE)

    volume_ids = fields.One2many(comodel_name='nfe.volume',
                                 inverse_name='invoice_electronic_id',
                                 string='Volumes',
                                 readonly=True,
                                 states=STATE)

    # Exportação
    uf_saida_pais_id = fields.Many2one('res.country.state',
                                       domain=[('country_id.code', '=', 'BR')],
                                       string='UF Saída do País',
                                       readonly=True,
                                       states=STATE)

    local_embarque = fields.Char(string='Local de Embarque',
                                 size=60,
                                 readonly=True,
                                 states=STATE)

    local_despacho = fields.Char(string='Local de Despacho',
                                 size=60,
                                 readonly=True,
                                 states=STATE)

    # Cobrança
    numero_fatura = fields.Char(string='Fatura',
                                readonly=True,
                                states=STATE)

    fatura_bruto = fields.Monetary(string='Valor Original',
                                   readonly=True,
                                   states=STATE)

    fatura_desconto = fields.Monetary(string='Desconto',
                                      readonly=True,
                                      states=STATE)

    fatura_liquido = fields.Monetary(string='Valor Líquido',
                                     readonly=True,
                                     states=STATE)

    duplicata_ids = fields.One2many(comodel_name='nfe.duplicata',
                                    inverse_name='invoice_electronic_id',
                                    string='Duplicatas',
                                    readonly=True,
                                    states=STATE)

    # Compras
    nota_empenho = fields.Char(string='Nota de Empenho',
                               size=22,
                               readonly=True,
                               states=STATE)

    pedido_compra = fields.Char(string='Pedido Compra',
                                size=60,
                                readonly=True,
                                states=STATE)

    contrato_compra = fields.Char(string='Contrato Compra',
                                  size=60,
                                  readonly=True,
                                  states=STATE)

    sequencial_evento = fields.Integer(string='Sequêncial Evento',
                                       default=1,
                                       readonly=True,
                                       states=STATE)

    recibo_nfe = fields.Char(string='Recibo NFe',
                             size=50,
                             readonly=True,
                             states=STATE)

    chave_nfe = fields.Char(string='Chave NFe',
                            size=50,
                            readonly=True,
                            states=STATE)

    chave_nfe_danfe = fields.Char(string='Chave Formatado',
                                  compute='_format_danfe_key')

    protocolo_nfe = fields.Char(string='Protocolo',
                                size=50,
                                readonly=True,
                                states=STATE,
                                help='Protocolo de autorização da NFe')

    nfe_processada = fields.Binary(string='Xml da NFe', readonly=True)

    nfe_processada_name = fields.Char(string='Xml da NFe',
                                      size=100,
                                      readonly=True)

    valor_icms_uf_remet = fields.Monetary(string='ICMS Remetente',
                                          readonly=True,
                                          states=STATE,
                                          help='Valor total do ICMS '
                                               'Interestadual para a UF do '
                                               'Remetente')

    valor_icms_uf_dest = fields.Monetary(string='ICMS Destino',
                                         readonly=True,
                                         states=STATE,
                                         help='Valor total do ICMS '
                                              'Interestadual para a UF de '
                                              'destino')

    valor_icms_fcp_uf_dest = fields.Monetary(string='Total ICMS FCP',
                                             readonly=True,
                                             states=STATE,
                                             help='Total total do ICMS '
                                                  'relativo Fundo de Combate '
                                                  'à Pobreza (FCP) da UF de '
                                                  'destino')

    # Documentos Relacionados
    fiscal_document_related_ids = fields.One2many(comodel_name='br_account.document.related',  # noqa: 501
                                                  inverse_name='invoice_electronic_id',  # noqa: 501
                                                  string='Documentos Fiscais Relacionados',  # noqa: 501
                                                  readonly=True, states=STATE)

    # CARTA DE CORRECAO
    cartas_correcao_ids = fields.One2many(comodel_name='carta.correcao.eletronica.evento',  # noqa: 501
                                          inverse_name='electronic_doc_id',
                                          string='Cartas de Correção',
                                          readonly=True,
                                          states=STATE)

    natureza_operacao = fields.Char(string='Natureza da Operação')

    def barcode_from_chave_nfe(self):
        """ Gera o codigo de barras a partir da chave da NFe. Utilizamos este
        metodo ao inves de utilizar request porque precisamos dele para envio
        do DANFE por email. Quando o DANFe e enviado pela fila de email o mesmo
        nao consegue chamar o metodo de geracao de codigo de barras do
        controller. Sendo precisamos gerar o DANFE diretamente.

        :return: Imagem do DANFE em Base64
        :rtype: str
        """

        try:
            barcode = self.env['ir.actions.report'].barcode('Code128',
                                                            self.chave_nfe,
                                                            width=600,
                                                            height=100,
                                                            humanreadable=0)
        except ValueError as exc:
            _logger.info('Cannot convert inn barcode. %s' % exc.message,
                         exc_info=True)
        return base64.b64encode(barcode).decode('utf-8')

    def can_unlink(self):
        res = super(InvoiceElectronic, self).can_unlink()
        return False if self.state == 'denied' else res

    @api.multi
    def unlink(self):
        for item in self:
            if item.state == 'denied':
                raise UserError(
                    'Documento Eletrônico Denegado - Proibido excluir')
        super(InvoiceElectronic, self).unlink()

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceElectronic, self)._hook_validation()

        if self.model == '55':
            if not self.company_id.partner_id.inscr_est:
                errors.append('Emitente / Inscrição Estadual')
            if not self.fiscal_position_id:
                errors.append('Configure a posição fiscal')
            if self.company_id.accountant_id and not \
                    self.company_id.accountant_id.cnpj_cpf:
                errors.append('Emitente / CNPJ do escritório contabilidade')

            for eletr in self.electronic_item_ids:
                prod = "Produto: %s - %s" % (eletr.product_id.default_code,
                                             eletr.product_id.name)
                if not eletr.cfop:
                    errors.append('%s - CFOP' % prod)
                if eletr.tipo_produto == 'product':
                    if not eletr.icms_cst:
                        errors.append('%s - CST do ICMS' % prod)
                    if not eletr.ipi_cst:
                        errors.append('%s - CST do IPI' % prod)
                if eletr.tipo_produto == 'service':
                    if not eletr.issqn_codigo:
                        errors.append('%s - Código de Serviço' % prod)
                if not eletr.pis_cst:
                    errors.append('%s - CST do PIS' % prod)
                if not eletr.cofins_cst:
                    errors.append('%s - CST do Cofins' % prod)

        return errors

    @api.multi
    def _prepare_electronic_invoice_item(self, item, invoice):
        res = super(InvoiceElectronic, self)._prepare_electronic_invoice_item(item, invoice)  # noqa: 501

        if self.model not in ('55', '65'):
            return res

        prod = {
            'cProd': item.product_id.default_code,
            'cEAN': item.product_id.barcode or '',
            'xProd': item.product_id.with_context(
                display_default_code=False).name_get()[0][1],
            'NCM': re.sub('[^0-9]', '', item.ncm or '')[:8],
            'EXTIPI': re.sub('[^0-9]', '', item.ncm or '')[8:],
            'CFOP': item.cfop,
            'uCom': '{:.6}'.format(item.uom_id.name or ''),
            'qCom': item.quantidade,
            'vUnCom': "%.02f" % item.preco_unitario,
            'vProd': "%.02f" % (item.preco_unitario * item.quantidade),
            'cEANTrib': item.product_id.barcode or '',
            'uTrib': '{:.6}'.format(item.uom_id.name or ''),
            'qTrib': item.quantidade,
            'vUnTrib': "%.02f" % item.preco_unitario,
            'vFrete': "%.02f" % item.frete if item.frete else '',
            'vSeg': "%.02f" % item.seguro if item.seguro else '',
            'vDesc': "%.02f" % item.desconto if item.desconto else '',
            'vOutro': "%.02f" % item.outras_despesas
            if item.outras_despesas else '',
            'indTot': item.indicador_total,
            'cfop': item.cfop,
            'CEST': re.sub('[^0-9]', '', item.cest or ''),
        }
        di_vals = []
        for di in item.import_declaration_ids:
            adicoes = []
            for adi in di.line_ids:
                adicoes.append({
                    'nAdicao': adi.name,
                    'nSeqAdic': adi.sequence,
                    'cFabricante': adi.manufacturer_code,
                    'vDescDI': "%.02f" % adi.amount_discount
                    if adi.amount_discount else '',
                    'nDraw': adi.drawback_number or '',
                })

            dt_registration = datetime.strptime(
                di.date_registration, DATE_FORMAT)
            dt_release = datetime.strptime(di.date_release, DATE_FORMAT)
            di_vals.append({
                'nDI': di.name,
                'dDI': dt_registration.strftime('%Y-%m-%d'),
                'xLocDesemb': di.location,
                'UFDesemb': di.state_id.code,
                'dDesemb': dt_release.strftime('%Y-%m-%d'),
                'tpViaTransp': di.type_transportation,
                'vAFRMM': "%.02f" % di.afrmm_value if di.afrmm_value else '',
                'tpIntermedio': di.type_import,
                'CNPJ': di.thirdparty_cnpj or '',
                'UFTerceiro': di.thirdparty_state_id.code or '',
                'cExportador': di.exporting_code,
                'adi': adicoes,
            })

        prod["DI"] = di_vals

        imposto = {
            'vTotTrib': "%.02f" % item.tributos_estimados,
            'ICMS': {
                'orig': item.origem,
                'CST': item.icms_cst,
                'modBC': item.icms_tipo_base,
                'vBC': "%.02f" % item.icms_base_calculo,
                'pRedBC': "%.02f" % item.icms_aliquota_reducao_base,
                'pICMS': "%.02f" % item.icms_aliquota,
                'vICMS': "%.02f" % item.icms_valor,
                'modBCST': item.icms_st_tipo_base,
                'pMVAST': "%.02f" % item.icms_st_aliquota_mva,
                'pRedBCST': "%.02f" % item.icms_st_aliquota_reducao_base,
                'vBCST': "%.02f" % item.icms_st_base_calculo,
                'pICMSST': "%.02f" % item.icms_st_aliquota,
                'vICMSST': "%.02f" % item.icms_st_valor,
                'pCredSN': "%.02f" % item.icms_valor_credito,
                'vCredICMSSN': "%.02f" % item.icms_aliquota_credito
            },
            'IPI': {
                'clEnq': item.classe_enquadramento_ipi or '',
                'cEnq': item.codigo_enquadramento_ipi,
                'CST': item.ipi_cst,
                'vBC': "%.02f" % item.ipi_base_calculo,
                'pIPI': "%.02f" % item.ipi_aliquota,
                'vIPI': "%.02f" % item.ipi_valor
            },
            'PIS': {
                'CST': item.pis_cst,
                'vBC': "%.02f" % item.pis_base_calculo,
                'pPIS': "%.02f" % item.pis_aliquota,
                'vPIS': "%.02f" % item.pis_valor
            },
            'COFINS': {
                'CST': item.cofins_cst,
                'vBC': "%.02f" % item.cofins_base_calculo,
                'pCOFINS': "%.02f" % item.cofins_aliquota,
                'vCOFINS': "%.02f" % item.cofins_valor
            },
        }
        if item.tem_difal:
            imposto['ICMSUFDest'] = {
                'vBCUFDest': "%.02f" % item.icms_bc_uf_dest,
                'pFCPUFDest': "%.02f" % item.icms_aliquota_fcp_uf_dest,
                'pICMSUFDest': "%.02f" % item.icms_aliquota_uf_dest,
                'pICMSInter': "%.02f" % item.icms_aliquota_interestadual,
                'pICMSInterPart': "%.02f" % item.icms_aliquota_inter_part,
                'vFCPUFDest': "%.02f" % item.icms_fcp_uf_dest,
                'vICMSUFDest': "%.02f" % item.icms_uf_dest,
                'vICMSUFRemet': "%.02f" % item.icms_uf_remet,
            }
        return {
            'prod': prod, 'imposto': imposto,
            'infAdProd': item.informacao_adicional,
        }

    @api.multi
    def _prepare_electronic_invoice_values(self):
        res = super(InvoiceElectronic, self)._prepare_electronic_invoice_values()  # noqa: 501

        if self.model not in ('55', '65'):
            return res

        dt_emissao = datetime.strptime(self.data_emissao, DTFT)

        ide = {
            'cUF': self.company_id.state_id.ibge_code,
            'cNF': "%08d" % self.numero_controle,
            'natOp': self.fiscal_position_id.name,
            'indPag': self.payment_term_id.indPag or '0',
            'mod': self.model,
            'serie': self.serie.code,
            'nNF': self.numero,
            'dhEmi': dt_emissao.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
            'dhSaiEnt': dt_emissao.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
            'tpNF': '0' if self.tipo_operacao == 'entrada' else '1',
            'idDest': self.ind_dest or 1,
            'cMunFG': "%s%s" % (self.company_id.state_id.ibge_code,
                                self.company_id.city_id.ibge_code),
            # Formato de Impressão do DANFE - 1 - Danfe Retrato, 4 - Danfe NFCe
            'tpImp': '1' if self.model == '55' else '4',
            'tpEmis': int(self.tipo_emissao),
            'tpAmb': 2 if self.ambiente == 'homologacao' else 1,
            'finNFe': self.finalidade_emissao,
            'indFinal': self.ind_final or '1',
            'indPres': self.ind_pres or '1',
            'procEmi': 0
        }

        # Documentos Relacionados
        documentos = []
        for doc in self.fiscal_document_related_ids:
            data = fields.Datetime.from_string(doc.date)
            if doc.document_type == 'nfe':
                documentos.append({
                    'refNFe': doc.access_key
                })
            elif doc.document_type == 'nf':
                documentos.append({
                    'refNF': {
                        'cUF': doc.state_id.ibge_code,
                        'AAMM': data.strftime("%y%m"),
                        'CNPJ': re.sub('[^0-9]', '', doc.cnpj_cpf),
                        'mod': doc.fiscal_document_id.code,
                        'serie': doc.serie,
                        'nNF': doc.internal_number,
                    }
                })

            elif doc.document_type == 'cte':
                documentos.append({
                    'refCTe': doc.access_key
                })
            elif doc.document_type == 'nfrural':
                cnpj_cpf = re.sub('[^0-9]', '', doc.cnpj_cpf)
                documentos.append({
                    'refNFP': {
                        'cUF': doc.state_id.ibge_code,
                        'AAMM': data.strftime("%y%m"),
                        'CNPJ': cnpj_cpf if len(cnpj_cpf) == 14 else '',
                        'CPF': cnpj_cpf if len(cnpj_cpf) == 11 else '',
                        'IE': doc.inscr_est,
                        'mod': doc.fiscal_document_id.code,
                        'serie': doc.serie,
                        'nNF': doc.internal_number,
                    }
                })
            elif doc.document_type == 'cf':
                documentos.append({
                    'refECF': {
                        'mod': doc.fiscal_document_id.code,
                        'nECF': doc.serie,
                        'nCOO': doc.internal_number,
                    }
                })

        ide['NFref'] = documentos

        emit = {
            'tipo': self.company_id.partner_id.company_type,
            'cnpj_cpf': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
            'xNome': self.company_id.legal_name,
            'xFant': self.company_id.name,
            'enderEmit': {
                'xLgr': self.company_id.street,
                'nro': self.company_id.number,
                'xBairro': self.company_id.district,
                'cMun': '%s%s' % (self.company_id.partner_id.state_id.ibge_code,  # noqa: 501
                                  self.company_id.partner_id.city_id.ibge_code),  # noqa: 501
                'xMun': self.company_id.city_id.name,
                'UF': self.company_id.state_id.code,
                'CEP': re.sub('[^0-9]', '', self.company_id.zip),
                'cPais': self.company_id.country_id.ibge_code,
                'xPais': self.company_id.country_id.name,
                'fone': re.sub('[^0-9]', '', self.company_id.phone or '')
            },
            'IE': re.sub('[^0-9]', '', self.company_id.inscr_est),
            'CRT': self.company_id.fiscal_type,
        }

        if self.company_id.cnae_main_id and self.company_id.inscr_mun:
            emit['IM'] = re.sub('[^0-9]', '', self.company_id.inscr_mun or '')
            emit['CNAE'] = re.sub('[^0-9]', '', self.company_id.cnae_main_id.code or '')  # noqa: 501

        dest = None
        exporta = None

        if self.commercial_partner_id:
            partner = self.commercial_partner_id
            dest = {
                'tipo': partner.company_type,
                'cnpj_cpf': re.sub('[^0-9]', '', partner.cnpj_cpf or ''),
                'xNome': partner.legal_name or partner.name,
                'enderDest': {
                    'xLgr': partner.street,
                    'nro': partner.number,
                    'xBairro': partner.district,
                    'cMun': '%s%s' % (partner.state_id.ibge_code,
                                      partner.city_id.ibge_code),
                    'xMun': partner.city_id.name,
                    'UF': partner.state_id.code,
                    'CEP': re.sub('[^0-9]', '', partner.zip or ''),
                    'cPais': (partner.country_id.bc_code or '')[-4:],
                    'xPais': partner.country_id.name,
                    'fone': re.sub('[^0-9]', '', partner.phone or '')
                },
                'indIEDest': self.ind_ie_dest,
                'IE': re.sub('[^0-9]', '', partner.inscr_est or ''),
            }
            if self.ambiente == 'homologacao':
                dest['xNome'] = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'  # noqa: 501
            if partner.country_id.id != self.company_id.country_id.id:
                dest['idEstrangeiro'] = re.sub('[^0-9]', '', partner.cnpj_cpf or '')  # noqa: 501
                dest['enderDest']['UF'] = 'EX'
                dest['enderDest']['xMun'] = 'Exterior'
                dest['enderDest']['cMun'] = '9999999'
                exporta = {
                    'UFSaidaPais': self.uf_saida_pais_id.code or '',
                    'xLocExporta': self.local_embarque or '',
                    'xLocDespacho': self.local_despacho or '',
                }

        autorizados = []
        if self.company_id.accountant_id:
            autorizados.append({
                'CNPJ': re.sub(
                    '[^0-9]', '', self.company_id.accountant_id.cnpj_cpf)
            })

        electronic_items = []
        for item in self.electronic_item_ids:
            electronic_items.append(
                self._prepare_electronic_invoice_item(item, self))
        total = {
            # ICMS
            'vBC': "%.02f" % self.valor_bc_icms,
            'vICMS': "%.02f" % self.valor_icms,
            'vICMSDeson': '0.00',
            'vBCST': "%.02f" % self.valor_bc_icmsst,
            'vST': "%.02f" % self.valor_icmsst,
            'vProd': "%.02f" % self.valor_bruto,
            'vFrete': "%.02f" % self.valor_frete,
            'vSeg': "%.02f" % self.valor_seguro,
            'vDesc': "%.02f" % self.valor_desconto,
            'vII': "%.02f" % self.valor_ii,
            'vIPI': "%.02f" % self.valor_ipi,
            'vPIS': "%.02f" % self.valor_pis,
            'vCOFINS': "%.02f" % self.valor_cofins,
            'vOutro': "%.02f" % self.valor_despesas,
            'vNF': "%.02f" % self.valor_final,
            'vFCPUFDest': "%.02f" % self.valor_icms_fcp_uf_dest,
            'vICMSUFDest': "%.02f" % self.valor_icms_uf_dest,
            'vICMSUFRemet': "%.02f" % self.valor_icms_uf_remet,
            'vTotTrib': "%.02f" % self.valor_estimado_tributos,
            # ISSQn
            'vServ': '0.00',
            # Retenções

        }
        transp = {
            'modFrete': self.modalidade_frete,
            'transporta': {
                'xNome': (self.transportadora_id.legal_name or
                          self.transportadora_id.name or ''),
                'IE': re.sub('[^0-9]', '',
                             self.transportadora_id.inscr_est or ''),
                'xEnder': "%s - %s, %s" % (self.transportadora_id.street,
                                           self.transportadora_id.number,
                                           self.transportadora_id.district)
                if self.transportadora_id else '',
                'xMun': self.transportadora_id.city_id.name or '',
                'UF': self.transportadora_id.state_id.code or ''
            },
            'veicTransp': {
                'placa': self.placa_veiculo or '',
                'UF': self.uf_veiculo or '',
                'RNTC': self.rntc or '',
            }
        }
        cnpj_cpf = re.sub('[^0-9]', '', self.transportadora_id.cnpj_cpf or '')
        if self.transportadora_id.is_company:
            transp['transporta']['CNPJ'] = cnpj_cpf
        else:
            transp['transporta']['CPF'] = cnpj_cpf

        reboques = []
        for item in self.reboque_ids:
            reboques.append({
                'placa': item.placa_veiculo or '',
                'UF': item.uf_veiculo or '',
                'RNTC': item.rntc or '',
                'vagao': item.vagao or '',
                'balsa': item.balsa or '',
            })
        transp['reboque'] = reboques
        volumes = []
        for item in self.volume_ids:
            volumes.append({
                'qVol': item.quantidade_volumes or '',
                'esp': item.especie or '',
                'marca': item.marca or '',
                'nVol': item.numeracao or '',
                'pesoL': "%.03f" % item.peso_liquido
                if item.peso_liquido else '',
                'pesoB': "%.03f" % item.peso_bruto if item.peso_bruto else '',
            })
        transp['vol'] = volumes

        duplicatas = []
        for dup in self.duplicata_ids:
            vencimento = fields.Datetime.from_string(dup.data_vencimento)
            duplicatas.append({
                'nDup': dup.numero_duplicata,
                'dVenc': vencimento.strftime('%Y-%m-%d'),
                'vDup': "%.02f" % dup.valor
            })
        cobr = {
            'fat': {
                'nFat': self.numero_fatura or '',
                'vOrig': "%.02f" % self.fatura_bruto
                if self.fatura_bruto else '',
                'vDesc': "%.02f" % self.fatura_desconto
                if self.fatura_desconto else '',
                'vLiq': "%.02f" % self.fatura_liquido
                if self.fatura_liquido else '',
            },
            'dup': duplicatas
        }
        infAdic = {
            'infCpl': self.informacoes_complementares or '',
            'infAdFisco': self.informacoes_legais or '',
        }
        compras = {
            'xNEmp': self.nota_empenho or '',
            'xPed': self.pedido_compra or '',
            'xCont': self.contrato_compra or '',
        }
        vals = {
            'Id': '',
            'ide': ide,
            'emit': emit,
            'dest': dest,
            'autXML': autorizados,
            'detalhes': electronic_items,
            'total': total,
            'transp': transp,
            'infAdic': infAdic,
            'exporta': exporta,
            'compra': compras,
        }
        if len(duplicatas) > 0:
            vals['cobr'] = cobr

        return vals

    @api.multi
    def _prepare_lote(self, lote, nfe_values):

        values = {
            'idLote': lote,
            'indSinc': 0,
            'estado': self.company_id.partner_id.state_id.ibge_code,
            'ambiente': 1 if self.ambiente == 'producao' else 2,
            'NFes': [{
                'infNFe': nfe_values,
            }]
        }
        return values

    @api.multi
    def action_post_validate(self):
        super(InvoiceElectronic, self).action_post_validate()

        if self.model not in ('55', '65'):
            return

        for item in self:
            chave_dict = {
                'cnpj': re.sub('[^0-9]', '', item.company_id.cnpj_cpf),
                'estado': item.company_id.state_id.ibge_code,
                'emissao': item.data_emissao[2:4] + item.data_emissao[5:7],
                'modelo': item.model,
                'numero': item.numero,
                'serie': item.serie.code.zfill(3),
                'tipo': int(item.tipo_emissao),
                'codigo': "%08d" % item.numero_controle
            }
            item.chave_nfe = gerar_chave(ChaveNFe(**chave_dict))

    @api.multi
    def action_send_electronic_invoice(self):
        super(InvoiceElectronic, self).action_send_electronic_invoice()

        self.write({
            'state': 'error',
            'data_emissao': datetime.now(),
        })

        if self.model not in ('55', '65'):
            return

        nfe_values = self._prepare_electronic_invoice_values()
        lote = self._prepare_lote(self.id, nfe_values)
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        resposta_recibo = None
        resposta = autorizar_nfe(certificado, **lote)
        retorno = resposta['object'].Body.nfeAutorizacaoLoteResult
        retorno = retorno.getchildren()[0]

        if retorno.cStat == 103:
            obj = {
                'estado': self.company_id.partner_id.state_id.ibge_code,
                'ambiente': 1 if self.ambiente == 'producao' else 2,
                'obj': {
                    'ambiente': 1 if self.ambiente == 'producao' else 2,
                    'numero_recibo': retorno.infRec.nRec
                }
            }
            self.recibo_nfe = obj['obj']['numero_recibo']

            while True:
                time.sleep(2)
                resposta_recibo = retorno_autorizar_nfe(certificado, **obj)
                retorno = resposta_recibo['object'].Body. \
                    nfeRetAutorizacaoLoteResult.retConsReciNFe
                if retorno.cStat != 105:
                    break

        if retorno.cStat != 104:
            values = {
                'codigo_retorno': retorno.cStat,
                'mensagem_retorno': retorno.xMotivo,
            }
        else:
            values = {
                'codigo_retorno': retorno.protNFe.infProt.cStat,
                'mensagem_retorno': retorno.protNFe.infProt.xMotivo,
            }

            if values['codigo_retorno'] == 100:
                values.update({
                    'state': 'done',
                    'protocolo_nfe': retorno.protNFe.infProt.nProt,
                    'data_autorizacao': retorno.protNFe.infProt.dhRecbto,
                })

            # Duplicidade de NF-e significa que a nota já está emitida
            # TODO Buscar o protocolo de autorização, por hora só finalizar
            elif values['codigo_retorno'] == 204:
                values.update({
                    'state': 'done',
                    'codigo_retorno': '100',
                    'mensagem_retorno': 'Autorizado o uso da NF-e',
                })

            # Denegada e nota já está denegada
            elif values['codigo_retorno'] in (302, 205):
                values.update({
                    'state': 'denied',
                })

        self.write(values)

        self.env['invoice.electronic.event'].create({
            'code': values['codigo_retorno'],
            'name': values['mensagem_retorno'],
            'invoice_electronic_id': self.id,
        })

        self._create_attachment('nfe-envio', self, resposta['sent_xml'])
        self._create_attachment('nfe-ret', self, resposta['received_xml'])

        recibo_xml = resposta['received_xml']

        if resposta_recibo:
            self._create_attachment('rec', self, resposta_recibo['sent_xml'])
            self._create_attachment('rec-ret', self,
                                    resposta_recibo['received_xml'])
            recibo_xml = resposta_recibo['received_xml']

        if self.codigo_retorno == '100':
            self.invoice_id.internal_number = int(self.numero)
            nfe_proc = gerar_nfeproc(resposta['sent_xml'].encode('utf8'),
                                     recibo_xml.encode('utf8'))
            self.write({
                'nfe_processada': base64.encodestring(nfe_proc),
                'nfe_processada_name': "NFe%08d.xml" % self.numero,
            })

    @api.multi
    def generate_nfe_proc(self):
        if self.state in ['cancel', 'done', 'denied']:
            recibo = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.electronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'rec-ret')])
            if not recibo:
                recibo = self.env['ir.attachment'].search([
                    ('res_model', '=', 'invoice.electronic'),
                    ('res_id', '=', self.id),
                    ('datas_fname', 'like', 'nfe-ret')])
            nfe_envio = self.env['ir.attachment'].search([
                ('res_model', '=', 'invoice.electronic'),
                ('res_id', '=', self.id),
                ('datas_fname', 'like', 'nfe-envio')])
            if nfe_envio.datas and recibo.datas:
                nfe_proc = gerar_nfeproc(
                    base64.decodestring(nfe_envio.datas),
                    base64.decodestring(recibo.datas)
                )
                self.nfe_processada = base64.encodestring(nfe_proc)
                self.nfe_processada_name = "NFe%08d.xml" % self.numero
        else:
            raise UserError('A NFe não está validada')

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('55', '65'):
            return super(InvoiceElectronic, self).action_cancel_document(
                context=context, justificativa=justificativa)

        if not justificativa:
            return {
                'name': 'Cancelamento NFe',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.cancel.nfe',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_edoc_id': self.id
                }
            }

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        id_canc = "ID110111%s%02d" % (self.chave_nfe, self.sequencial_evento)
        cancelamento = {
            'idLote': self.id,
            'estado': self.company_id.state_id.ibge_code,
            'ambiente': 2 if self.ambiente == 'homologacao' else 1,
            'eventos': [{
                'Id': id_canc,
                'cOrgao': self.company_id.state_id.ibge_code,
                'tpAmb': 2 if self.ambiente == 'homologacao' else 1,
                'CNPJ': re.sub('[^0-9]', '', self.company_id.cnpj_cpf),
                'chNFe': self.chave_nfe,
                'dhEvento': datetime.utcnow().strftime(
                    '%Y-%m-%dT%H:%M:%S-00:00'),
                'nSeqEvento': self.sequencial_evento,
                'nProt': self.protocolo_nfe,
                'xJust': justificativa
            }]
        }
        resp = recepcao_evento_cancelamento(certificado, **cancelamento)
        resposta = resp['object'].Body.nfeRecepcaoEventoResult.retEnvEvento

        if resposta.cStat == 128 and resposta.retEvento.infEvento.cStat in (135, 136, 155):  # noqa: 501
            values = {
                'state': 'cancel',
                'codigo_retorno': resposta.retEvento.infEvento.cStat,
                'mensagem_retorno': resposta.retEvento.infEvento.xMotivo,
                'sequencial_evento': self.sequencial_evento + 1,
            }

        elif resposta.cStat == 128:
            values = {
                'codigo_retorno': resposta.retEvento.infEvento.cStat,
                'mensagem_retorno': resposta.retEvento.infEvento.xMotivo,
            }
        else:
            values = {
                'codigo_retorno': resposta.cStat,
                'mensagem_retorno': resposta.xMotivo,
            }

        self.write(values)

        self.env['invoice.electronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_electronic_id': self.id,
        })
        self._create_attachment('canc', self, resp['sent_xml'])
        self._create_attachment('canc-ret', self, resp['received_xml'])

    @api.multi
    def action_print_einvoice_report(self):

        docs = self.search([('model', '=', '55'), ('id', 'in', self.ids)])

        if docs:
            # report = self.env.ref('br_nfe.report_br_nfe_danfe').report_name
            action = self.env.ref(
                'br_nfe.report_br_nfe_danfe').report_action(docs)
            # action = self.env['report'].get_action(docs.ids, report)
            action['report_type'] = 'qweb-pdf'
            return action
        else:
            return super(InvoiceElectronic, self).action_print_einvoice_report()
