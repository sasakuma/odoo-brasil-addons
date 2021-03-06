# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom

from odoo import api, fields, models
from odoo.exceptions import UserError

TYPE2EDOC = {
    'out_invoice': 'saida',  # Customer Invoice
    'in_invoice': 'entrada',  # Vendor Bill
    'out_refund': 'entrada',  # Customer Refund
    'in_refund': 'saida',  # Vendor Refund
}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cert_expire_date = fields.Date(string='Expire Date',
                                   related='company_id.cert_expire_date',
                                   readonly=True)

    days_to_expire_cert = fields.Integer(string='Days to Expire Certificate',
                                         compute='_compute_days_to_expire_cert',
                                         default=60)

    cert_state = fields.Selection(string='Expire Certificate',
                                  related='company_id.cert_state')

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.electronic'].search_count(
                [('invoice_id', '=', item.id)])

    invoice_electronic_ids = fields.One2many('invoice.electronic',
                                             'invoice_id',
                                             string='Documentos Eletrônicos',
                                             readonly=True)

    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    invoice_electronic_state = fields.Selection(
        [('no_inv_doc', 'Sem Doc. Eletrônico'),
         ('draft', 'Provisório'),
         ('edit', 'Editar'),
         ('error', 'Erro'),
         ('done', 'Enviado'),
         ('cancel', 'Cancelado')],
        string='Situação da Nota Fiscal',
        default='no_inv_doc',
        store=True,
        compute='_compute_invoice_electronic_state')

    @api.depends('state', 'invoice_electronic_ids.state')
    def _compute_invoice_electronic_state(self):
        for inv in self:
            docs = inv.invoice_electronic_ids

            # Ordenamos a lista de documentos eletronicos, para garantir que
            # a mais recente esteja em primeiro, ou seja, a que possui o ID
            # maior
            docs = docs.sorted(key=lambda a: a.id, reverse=True)

            if docs:
                inv.invoice_electronic_state = docs[0].state
            else:
                inv.invoice_electronic_state = 'no_inv_doc'

    @api.multi
    def action_view_edocs(self):
        if self.total_edocs == 1:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_electronic_doc')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'br_account_invoice_electronic_form')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['view_id'] = (view_id, 'sped.electronic.doc.form')
            vals['views'][1] = (view_id, 'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            edoc = self.env['invoice.electronic'].search(
                [('invoice_id', '=', self.id)], limit=1)
            vals['res_id'] = edoc.id
            return vals
        else:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_electronic_doc')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            return vals

    def _prepare_edoc_item_vals(self, line):
        vals = {
            'name': line.name,
            'product_id': line.product_id.id,
            'tipo_produto': line.product_type,
            'cfop': line.cfop_id.code,
            'uom_id': line.uom_id.id,
            'quantidade': line.quantity,
            'preco_unitario': line.price_unit,
            'valor_bruto': line.valor_bruto,
            'desconto': line.valor_desconto,
            'valor_liquido': line.price_subtotal,
            'origem': line.icms_origem,
            'tributos_estimados': line.tributos_estimados,
            'ncm': line.fiscal_classification_id.code,
            # - ICMS -
            'icms_cst': line.icms_cst,
            'icms_aliquota': line.icms_aliquota,
            'icms_tipo_base': line.icms_tipo_base,
            'icms_aliquota_reducao_base': line.icms_aliquota_reducao_base,
            'icms_base_calculo': line.icms_base_calculo,
            'icms_valor': line.icms_valor,
            # - ICMS ST -
            'icms_st_aliquota': line.icms_st_aliquota,
            'icms_st_aliquota_mva': line.icms_st_aliquota_mva,
            'icms_st_aliquota_reducao_base':
                line.icms_st_aliquota_reducao_base,
            'icms_st_base_calculo': line.icms_st_base_calculo,
            'icms_st_valor': line.icms_st_valor,
            # - Simples Nacional -
            'icms_aliquota_credito': line.icms_aliquota_credito,
            'icms_valor_credito': line.icms_valor_credito,
            # - IPI -
            'ipi_cst': line.ipi_cst,
            'ipi_aliquota': line.ipi_aliquota,
            'ipi_base_calculo': line.ipi_base_calculo,
            'ipi_reducao_bc': line.ipi_reducao_bc,
            'ipi_valor': line.ipi_valor,
            # - II -
            'ii_base_calculo': line.ii_base_calculo,
            'ii_valor_despesas': line.ii_valor_despesas,
            'ii_valor': line.ii_valor,
            'ii_valor_iof': line.ii_valor_iof,
            # - PIS -
            'pis_cst': line.pis_cst,
            'pis_aliquota': abs(line.pis_aliquota),
            'pis_base_calculo': line.pis_base_calculo,
            'pis_valor': abs(line.pis_valor),
            'pis_valor_retencao':
                abs(line.pis_valor) if line.pis_valor < 0 else 0,
            # - COFINS -
            'cofins_cst': line.cofins_cst,
            'cofins_aliquota': abs(line.cofins_aliquota),
            'cofins_base_calculo': line.cofins_base_calculo,
            'cofins_valor': abs(line.cofins_valor),
            'cofins_valor_retencao':
                abs(line.cofins_valor) if line.cofins_valor < 0 else 0,
            # - ISSQN -
            # 'issqn_codigo': line.fservice_type_id.code,
            'issqn_codigo': line.fiscal_position_id.service_type_id.code,
            'issqn_aliquota': abs(line.issqn_aliquota),
            'issqn_base_calculo': line.issqn_base_calculo,
            'issqn_valor': abs(line.issqn_valor),
            'issqn_valor_retencao':
                abs(line.issqn_valor) if line.issqn_valor < 0 else 0,
            # - RETENÇÔES -
            'csll_base_calculo': line.csll_base_calculo,
            'csll_aliquota': abs(line.csll_aliquota),
            'csll_valor_retencao':
                abs(line.csll_valor) if line.csll_valor < 0 else 0,
            'irrf_base_calculo': line.irrf_base_calculo,
            'irrf_aliquota': abs(line.irrf_aliquota),
            'irrf_valor_retencao':
                abs(line.irrf_valor) if line.irrf_valor < 0 else 0,
            'inss_base_calculo': line.inss_base_calculo,
            'inss_aliquota': abs(line.inss_aliquota),
            'inss_valor_retencao':
                abs(line.inss_valor) if line.inss_valor < 0 else 0,
        }
        return vals

    def _prepare_edoc_vals(self, invoice):
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                                    for i in range(8)]))
        vals = {
            'invoice_id': invoice.id,
            'code': invoice.number,
            'name': 'Documento Eletrônico: nº %d' % invoice.internal_number,
            'company_id': invoice.company_id.id,
            'state': 'draft',
            'tipo_operacao': TYPE2EDOC[invoice.type],
            'model': invoice.fiscal_document_id.code,
            'serie': invoice.document_serie_id.id,
            'numero': invoice.internal_number,
            'numero_controle': num_controle,
            'numero_nfe': invoice.internal_number,
            'data_emissao': datetime.now(),
            'data_fatura': datetime.now(),
            'finalidade_emissao': '1',
            'partner_id': invoice.partner_id.id,
            'payment_term_id': invoice.payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
            'valor_icms': invoice.icms_value,
            'valor_icmsst': invoice.icms_st_value,
            'valor_ipi': invoice.ipi_value,
            'valor_pis': invoice.pis_value,
            'valor_cofins': invoice.cofins_value,
            'valor_ii': invoice.ii_value,
            'valor_bruto': invoice.total_bruto,
            'valor_desconto': invoice.total_desconto,
            'valor_final': invoice.amount_total,
            'valor_bc_icms': invoice.icms_base,
            'valor_bc_icmsst': invoice.icms_st_base,
            'valor_estimado_tributos': invoice.total_tributos_estimados,
            'valor_retencao_issqn': invoice.issqn_retention,
            'valor_retencao_pis': invoice.pis_retention,
            'valor_retencao_cofins': invoice.cofins_retention,
            'valor_bc_irrf': invoice.irrf_base,
            'valor_retencao_irrf': invoice.irrf_retention,
            'valor_bc_csll': invoice.csll_base,
            'valor_retencao_csll': invoice.csll_retention,
            'valor_bc_inss': invoice.inss_base,
            'valor_retencao_inss': invoice.inss_retention,
        }

        electronic_items = []
        for inv_line in invoice.invoice_line_ids:
            electronic_items.append((0, 0,
                                     self._prepare_edoc_item_vals(inv_line)))

        vals['electronic_item_ids'] = electronic_items
        return vals

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for item in self:
            if item.is_electronic:
                edoc_vals = self._prepare_edoc_vals(item)
                if edoc_vals:
                    electronic = \
                        self.env['invoice.electronic'].create(edoc_vals)
                    electronic.validate_invoice()
                    electronic.action_post_validate()
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for item in self:
            edocs = self.env['invoice.electronic'].search(
                [('invoice_id', '=', item.id)])

            if any(edoc.state == 'done' for edoc in edocs):
                raise UserError('Documento eletrônico emitido - Cancele o \
                                documento para poder cancelar a fatura')
        return res

    @api.multi
    def _compute_days_to_expire_cert(self):
        """ Atribui ao campo 'days_to_expire_cert' a diferença de datas entre 
        a data de expiração do certificado e a atual.E atribui 'True' ou 'False'
        ao campo 'expire_cert' dependendo da condição.
        """
        
        for inv in self:

            # Quando utilizamos multicompany, nem todas as empresas
            # cadastradas podem possuir certificados
            if inv.cert_expire_date:
                date_cert = datetime.strptime(inv.cert_expire_date, '%Y-%m-%d')
                date_today = datetime.strptime(fields.Date.today(), '%Y-%m-%d')
                inv.days_to_expire_cert = (date_cert - date_today).days
            else:
                inv.days_to_expire_cert = 0
