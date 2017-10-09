# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

STATE = {'edit': [('readonly', False)]}


class InvoiceElectronic(models.Model):
    _inherit = 'invoice.electronic'

    @api.model
    def _default_webservice_nfse(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.webservice_nfse

    ambiente_nfse = fields.Selection(string='Ambiente NFe',
                                     related='company_id.tipo_ambiente_nfse',
                                     readonly=True)

    webservice_nfse = fields.Selection([],
                                       default=_default_webservice_nfse,
                                       readonly=True,
                                       states=STATE,
                                       string='Webservice NFSe')

    verify_code = fields.Char(string=u'Código Autorização',
                              size=20,
                              readonly=True,
                              states=STATE)

    numero_nfse = fields.Char(string=u'Número NFSe',
                              size=50,
                              readonly=True,
                              states=STATE)

    def _get_source_operation(self):
        return self.nfse_source_operation

    def issqn_due_date(self):
        date_emition = datetime.strptime(self.data_emissao, DTFT)
        next_month = date_emition + relativedelta(months=1)
        due_date = date(next_month.year, next_month.month, 10)
        if due_date.weekday() >= 5:
            while due_date.weekday() != 0:
                due_date = due_date + timedelta(days=1)
        date_mask = "%d/%m/%Y"
        due_date = datetime.strftime(due_date, date_mask)
        return due_date

    @api.multi
    def action_print_einvoice_report(self):

        docs = self.search([('model', '=', '001'), ('id', 'in', self.ids)])

        if docs:

            if docs[0].invoice_id.company_id.report_nfse_id:

                # Pegamos a primeira porque todas as NFSe sao/devem ser da
                # mesma prefeitura
                report = docs[0].invoice_id.company_id.report_nfse_id.report_name

                action = self.env['report'].get_action(docs.ids, report)
                action['report_type'] = 'qweb-pdf'
                return action
            else:
                raise UserError(
                    u'Não existe um template de relatorio para NFSe '
                    u'selecionado para a empresa emissora desta Fatura. '
                    u'Por favor, selecione um template no cadastro da '
                    u'empresa')
        else:
            return super(InvoiceElectronic, self).action_print_einvoice_report()
